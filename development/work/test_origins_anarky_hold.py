"""Verify v5 Anarky actual Lua with live reads and simulated writes only."""
from pathlib import Path
harness=(Path(__file__).parent/'test_city_runtime.py').read_text(encoding='utf-8')
exec(compile(harness.split('source=(Path')[0],str(Path(__file__)),'exec'))
lua.execute((Path(__file__).parent/'arkham_origins_runtime.lua').read_text(encoding='utf-8'))
C=g.AO
C.setFlag('anarkyTimer',True)
assert C.anarky and C.anarkyHeld
t=C.anarky.owner;held=C.anarky.held;flags=ri(t+0x108)
print('LIVE SELECTED TIMER',hex(t),'START',ri(t+0xf0),'HELD',held,'FLAGS',hex(flags),flush=True)
assert rf(t+0x100)==held and ri(t+0x104)==int(held)
game_writes=[a for a,_,_ in writes if a<0x7fe00000]
assert set(game_writes)=={t+0x100,t+0x104}, 'Only countdown values may be written'
write(t+0x100,held-3.0,'float');write(t+0x104,int(held-3),'int')
C.loop()
assert rf(t+0x100)==held and ri(t+0x104)==int(held) and ri(t+0x108)==flags
C.setFlag('anarkyTimer',False)
write(t+0x100,held-5.0,'float');C.loop()
assert rf(t+0x100)==held-5.0 and ri(t+0x108)==flags
print('CAPTURED FLOAT / HUD INTEGER REFILL / NO FLAG WRITES / DISABLE PASSED',flush=True)
others=[o for _,o in C.timers.items() if o!=t and ri(o+0xf0) in (230,160,180)]
assert others
next_timer=others[-1]
write(t+0x108,flags&~2,'int')
write(next_timer+0x108,2,'int');write(next_timer+0x100,100.0,'float')
C.flags.anarkyTimer=True;C.loop()
assert C.anarky.owner==next_timer and C.anarky.held==100.0 and C.anarkyHeld
write(next_timer+0x100,97.0,'float');C.loop();assert rf(next_timer+0x100)==100.0
assert ri(next_timer+0x108)==2 and ri(t+0x108)==flags&~2
write(next_timer+0x108,0,'int');C.loop()
assert C.anarky is None and not C.anarkyHeld
C.setFlag('anarkyTimer',True)
assert C.anarky is None, 'Can arm while waiting for the next race'
write(next_timer+0x108,2,'int');write(next_timer+0x100,90.0,'float');C.loop()
assert C.anarky.owner==next_timer and C.anarky.held==90.0
C.setFlag('anarkyTimer',False)
write(t+0x108,2,'int');C.setFlag('anarkyTimer',True)
assert C.anarky is None and not C.anarkyHeld, 'Refuse ambiguous initial candidates'
C.setFlag('anarkyTimer',False)
write(next_timer+0x108,2|8,'int');assert not C.anarkyCandidate(next_timer)
write(next_timer+0x108,2|4,'int');assert not C.anarkyCandidate(next_timer)
print('NEXT-BOMB AUTO-FOLLOW / WAIT / STOP / AMBIGUITY / CHALLENGE AND COUNT-UP EXCLUSION PASSED',flush=True)
C.shutdown();pm.close()
print('All test writes were simulated; no live flags or countdowns changed by this test.')
