#!/usr/bin/env python3
"""Full ECS: entities, components, systems, queries, events."""
import sys
from collections import defaultdict

class World:
    def __init__(self):
        self.next_id = 0; self.components = defaultdict(dict)
        self.systems = []; self.events = defaultdict(list); self.event_queue = []
    def spawn(self, **components):
        eid = self.next_id; self.next_id += 1
        for comp_type, data in components.items(): self.components[comp_type][eid] = data
        return eid
    def despawn(self, eid):
        for comp_type in list(self.components): self.components[comp_type].pop(eid, None)
    def get(self, eid, comp_type): return self.components[comp_type].get(eid)
    def set(self, eid, comp_type, data): self.components[comp_type][eid] = data
    def query(self, *comp_types):
        if not comp_types: return []
        entities = set(self.components[comp_types[0]])
        for ct in comp_types[1:]: entities &= set(self.components[ct])
        return [(eid, {ct: self.components[ct][eid] for ct in comp_types}) for eid in entities]
    def add_system(self, system, priority=0): self.systems.append((priority, system)); self.systems.sort()
    def emit(self, event_type, data=None): self.event_queue.append((event_type, data))
    def on(self, event_type, handler): self.events[event_type].append(handler)
    def tick(self):
        for _, system in self.systems: system(self)
        while self.event_queue:
            etype, data = self.event_queue.pop(0)
            for handler in self.events.get(etype, []): handler(self, data)

def movement_system(world):
    for eid, comps in world.query("position", "velocity"):
        pos, vel = comps["position"], comps["velocity"]
        world.set(eid, "position", {"x":pos["x"]+vel["dx"],"y":pos["y"]+vel["dy"]})

def collision_system(world):
    entities = world.query("position", "collider")
    for i, (eid1, c1) in enumerate(entities):
        for eid2, c2 in entities[i+1:]:
            p1, p2 = c1["position"], c2["position"]
            r1, r2 = c1["collider"]["radius"], c2["collider"]["radius"]
            dx, dy = p1["x"]-p2["x"], p1["y"]-p2["y"]
            if dx*dx+dy*dy < (r1+r2)**2:
                world.emit("collision", {"a":eid1,"b":eid2})

def main():
    world = World()
    world.add_system(movement_system, 0); world.add_system(collision_system, 1)
    player = world.spawn(position={"x":0,"y":0}, velocity={"dx":1,"dy":0.5}, collider={"radius":1}, health={"hp":100})
    enemy = world.spawn(position={"x":5,"y":3}, velocity={"dx":-0.5,"dy":-0.3}, collider={"radius":1}, health={"hp":50})
    bullet = world.spawn(position={"x":0,"y":0}, velocity={"dx":2,"dy":1})
    collisions = []
    world.on("collision", lambda w, d: collisions.append(d))
    for tick in range(10):
        world.tick()
    pos = world.get(player, "position")
    print(f"  Player pos after 10 ticks: ({pos['x']:.1f}, {pos['y']:.1f})")
    print(f"  Entities with health: {len(world.query('health'))}")
    print(f"  Collisions detected: {len(collisions)}")

if __name__ == "__main__": main()
