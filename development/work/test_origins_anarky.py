"""Actual v4 Lua against live reads with simulated writes, no game edits."""
from pathlib import Path
harness=(Path(__file__).parent/'test_city_runtime.py').read_text(encoding='utf-8')
exec(compile(harness.split('source=(Path')[0],str(Path(__file__)),'exec'))
lua.execute((Path(__file__).parent/'arkham_origins_runtime.lua').read_text(encoding='utf-8'))
C=g.AO
C.setFlag('anarkyTimer',True)
t=C.anarky.owner
assert t==0x714044c0, 'Must bind the second bomb countdown identified for this session'
print('ANARKY TIMER',hex(t),'START',ri(t+0xf0),'REMAINING',rf(t+0x100),flush=True)
assert ri(t+0x108)&1 and C.anarkyHeld
game_writes=[a for a,_,_ in writes if a<0x7fe00000]
assert set(game_writes)=={t+0x108}, 'Only native pause bit may change'
C.setFlag('anarkyTimer',False)
assert ri(t+0x108)==2
siblings=[o for _,o in C.timers.items() if o!=t]
before={o:ri(o+0x108) for o in siblings}
C.setFlag('anarkyTimer',True)
write(t+0x108,1,'int');C.loop()
assert ri(t+0x108)==0 and not C.anarkyHeld, 'Stop holding when mission timer stops'
for o,v in before.items(): assert ri(o+0x108)==v
next_timer=0x714099c0
assert next_timer in siblings
write(next_timer+0x108,2,'int');write(next_timer+0x100,180.0,'float')
C.loop()
assert C.anarky.owner==next_timer and ri(next_timer+0x108)==3 and C.anarkyHeld
assert ri(t+0x108)==0, 'Previous timer remains stopped, not revived'
C.setFlag('anarkyTimer',False)
assert ri(next_timer+0x108)==2
write(next_timer+0x108,0,'int')
write(t+0x108,0,'int');C.setFlag('anarkyTimer',True)
assert C.anarky is None and not C.anarkyHeld, 'Can enable before a bomb begins'
write(next_timer+0x108,2,'int');C.loop()
assert C.anarky.owner==next_timer and ri(next_timer+0x108)==3
C.setFlag('anarkyTimer',False);write(next_timer+0x108,0,'int')
write(t+0x108,2,'int');write(next_timer+0x108,2,'int')
C.setFlag('anarkyTimer',True)
assert C.anarky is None and not C.anarkyHeld
assert ri(t+0x108)==2 and ri(next_timer+0x108)==2, 'Ambiguous candidates must not be paused'
C.setFlag('anarkyTimer',False)
print('AUTO-FOLLOW NEXT BOMB / WAIT BEFORE RACE / DISABLE / AMBIGUITY GUARDS PASSED',flush=True)
write(t+0x108,2|8,'int');assert not C.anarkyCandidate(t)
write(t+0x108,2|4,'int');assert not C.anarkyCandidate(t)
write(t+0x108,2,'int');write(t+0xf0,25,'int');assert not C.anarkyCandidate(t)
print('PAUSE / RESTORE / STOP / SIBLING SCOPE / CHALLENGE AND COUNT-UP EXCLUSION PASSED',flush=True)
C.flags.anarkyTimer=False;C.shutdown();pm.close()
print('All writes simulated; no live pause flag or mission flag changed.')
