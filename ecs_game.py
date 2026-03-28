#!/usr/bin/env python3
"""ECS — Entity Component System for game architecture."""
import sys
class World:
    def __init__(self): self.next_id=0; self.components={}; self.entities=set()
    def create(self):
        eid=self.next_id; self.next_id+=1; self.entities.add(eid); return eid
    def add(self, eid, comp_type, data):
        self.components.setdefault(comp_type,{})[eid]=data
    def get(self, eid, comp_type):
        return self.components.get(comp_type,{}).get(eid)
    def query(self, *comp_types):
        if not comp_types: return []
        sets=[set(self.components.get(ct,{}).keys()) for ct in comp_types]
        return list(sets[0].intersection(*sets[1:]))
    def remove(self, eid):
        self.entities.discard(eid)
        for ct in self.components: self.components[ct].pop(eid, None)
def cli():
    w=World()
    player=w.create(); w.add(player,"pos",{"x":0,"y":0}); w.add(player,"vel",{"dx":1,"dy":0}); w.add(player,"health",100)
    enemy=w.create(); w.add(enemy,"pos",{"x":10,"y":5}); w.add(enemy,"vel",{"dx":-1,"dy":0}); w.add(enemy,"health",50)
    bullet=w.create(); w.add(bullet,"pos",{"x":5,"y":0}); w.add(bullet,"vel",{"dx":2,"dy":0})
    # Movement system
    for eid in w.query("pos","vel"):
        pos,vel=w.get(eid,"pos"),w.get(eid,"vel")
        pos["x"]+=vel["dx"]; pos["y"]+=vel["dy"]
    for eid in w.query("pos"):
        print(f"  Entity {eid}: pos={w.get(eid,'pos')} health={w.get(eid,'health')}")
    print(f"  Movable entities: {w.query('pos','vel')}")
    print(f"  With health: {w.query('health')}")
if __name__=="__main__": cli()
