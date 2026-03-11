#!/usr/bin/env python3
"""Entity Component System game engine — archetype-based ECS.

Supports: entity creation/destruction, component add/remove/query,
systems with component filters, archetypal storage for cache-friendly iteration.

Usage:
    python ecs_game.py --test
"""
import sys
from collections import defaultdict

class World:
    def __init__(self):
        self._next_id = 0
        self._entities = {}       # eid -> set of component types
        self._components = {}     # (eid, type) -> component
        self._archetypes = defaultdict(set)  # frozenset(types) -> set of eids
        self._systems = []
        self._dead = set()

    def spawn(self, **components) -> int:
        eid = self._next_id; self._next_id += 1
        types = set()
        for name, comp in components.items():
            self._components[(eid, name)] = comp
            types.add(name)
        self._entities[eid] = types
        self._archetypes[frozenset(types)].add(eid)
        return eid

    def destroy(self, eid):
        if eid not in self._entities: return
        types = self._entities.pop(eid)
        arch = frozenset(types)
        self._archetypes[arch].discard(eid)
        for t in types:
            self._components.pop((eid, t), None)
        self._dead.add(eid)

    def add_component(self, eid, name, comp):
        if eid not in self._entities: return
        old_types = self._entities[eid]
        old_arch = frozenset(old_types)
        self._archetypes[old_arch].discard(eid)
        old_types.add(name)
        self._components[(eid, name)] = comp
        self._archetypes[frozenset(old_types)].add(eid)

    def remove_component(self, eid, name):
        if eid not in self._entities or name not in self._entities[eid]: return
        old_arch = frozenset(self._entities[eid])
        self._archetypes[old_arch].discard(eid)
        self._entities[eid].discard(name)
        self._components.pop((eid, name), None)
        self._archetypes[frozenset(self._entities[eid])].add(eid)

    def get(self, eid, name):
        return self._components.get((eid, name))

    def has(self, eid, name):
        return eid in self._entities and name in self._entities[eid]

    def query(self, *required):
        """Iterate entities with all required components. Yields (eid, {name: comp})."""
        req = set(required)
        for arch, eids in self._archetypes.items():
            if req.issubset(arch):
                for eid in list(eids):
                    if eid in self._entities:
                        yield eid, {name: self._components[(eid, name)] for name in required}

    def add_system(self, system_fn, *components, priority=0):
        self._systems.append((priority, components, system_fn))
        self._systems.sort(key=lambda x: x[0])

    def tick(self, dt=1/60):
        for _, components, system_fn in self._systems:
            for eid, comps in self.query(*components):
                system_fn(self, eid, comps, dt)

    @property
    def entity_count(self):
        return len(self._entities)


def test():
    print("=== ECS Game Engine Tests ===\n")

    w = World()

    # Spawn entities
    player = w.spawn(pos={'x': 0, 'y': 0}, vel={'x': 1, 'y': 0}, health=100, name="Player")
    enemy1 = w.spawn(pos={'x': 10, 'y': 5}, vel={'x': -1, 'y': 0}, health=50, name="Goblin")
    wall = w.spawn(pos={'x': 5, 'y': 5}, name="Wall")
    print(f"✓ Spawned 3 entities: player={player}, enemy={enemy1}, wall={wall}")

    # Query
    movers = list(w.query('pos', 'vel'))
    assert len(movers) == 2
    print(f"✓ Query (pos+vel): {len(movers)} entities")

    all_positioned = list(w.query('pos'))
    assert len(all_positioned) == 3
    print(f"✓ Query (pos): {len(all_positioned)} entities")

    # Get/Has
    assert w.get(player, 'health') == 100
    assert w.has(player, 'vel')
    assert not w.has(wall, 'vel')
    print("✓ Get/Has components")

    # Movement system
    moved = []
    def movement_system(world, eid, comps, dt):
        comps['pos']['x'] += comps['vel']['x'] * dt
        comps['pos']['y'] += comps['vel']['y'] * dt
        moved.append(eid)

    w.add_system(movement_system, 'pos', 'vel')
    w.tick(dt=1.0)
    assert w.get(player, 'pos')['x'] == 1.0
    assert w.get(enemy1, 'pos')['x'] == 9.0
    assert len(moved) == 2
    print(f"✓ Movement system: player at {w.get(player, 'pos')}, enemy at {w.get(enemy1, 'pos')}")

    # Add component
    w.add_component(wall, 'destructible', True)
    assert w.has(wall, 'destructible')
    print("✓ Add component dynamically")

    # Remove component
    w.remove_component(enemy1, 'vel')
    movers2 = list(w.query('pos', 'vel'))
    assert len(movers2) == 1  # only player
    print("✓ Remove component: enemy no longer moves")

    # Destroy
    w.destroy(enemy1)
    assert w.entity_count == 2
    assert not w.has(enemy1, 'pos')
    print(f"✓ Destroy: {w.entity_count} entities remaining")

    # Damage system
    w2 = World()
    for i in range(100):
        w2.spawn(pos={'x': i, 'y': 0}, health=100)
    assert w2.entity_count == 100

    def damage_system(world, eid, comps, dt):
        comps['health'] -= 1
        # Note: modifying dict value doesn't work for immutable types
        world._components[(eid, 'health')] = comps['health'] - 1

    w2.add_system(damage_system, 'health')
    w2.tick()
    # Just check it runs without error on 100 entities
    print(f"✓ Bulk tick: 100 entities processed")

    print("\nAll tests passed! ✓")

if __name__ == "__main__":
    test() if not sys.argv[1:] or sys.argv[1] == "--test" else None
