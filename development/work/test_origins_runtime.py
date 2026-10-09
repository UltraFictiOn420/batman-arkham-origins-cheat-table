"""Test the actual Origins Lua with live reads and simulated writes only."""
from pathlib import Path

# Reuse our existing CE API simulation, stopping before City code executes.
harness=(Path(__file__).parent/'test_city_runtime.py').read_text(encoding='utf-8')
exec(compile(harness.split('source=(Path')[0], str(Path(__file__)), 'exec'))
source=(Path(__file__).parent/'arkham_origins_runtime.lua').read_text(encoding='utf-8')
start=time.monotonic()
lua.execute(source)
C=g.AO
p=C.pawn()
assert p and C.live(p,'RPawnPlayer')
assert all(0x7fe00000<=a<0x7fe10000 for a,_,_ in writes), 'Initializer must not change gameplay memory'
print('INITIALIZED',round(time.monotonic()-start,2),'seconds; PLAYER',hex(p),C.cn(p),'HP',ri(p+0x2dc),'MAX',ri(p+0x2e0),'ENEMIES',len(C.enemies), flush=True)
maxhp=ri(p+0x2e0)
assert maxhp and 0<maxhp<100000
write(p+0x2dc,5,'int')
C.setFlag('health',True)
assert ri(p+0x2dc)==maxhp
C.setFlag('health',False)
write(p+0x2dc,5,'int')
before=len(writes);C.loop()
assert len(writes)==before and ri(p+0x2dc)==5
C.flags.health=True
write(p+0x2dc,0,'int')
before=len(writes);C.loop()
assert len(writes)==before, 'Do not resurrect a dead pawn'
print('HEALTH RESTORE / DISABLE / DEAD-PAWN GUARDS PASSED', flush=True)
# Inspect streamed enemies and test their real reflected fields in the overlay.
C.flags.health=False
for _,e in C.enemies.items():
    print('ENEMY',hex(e),C.cn(e),C.oname(e),'HP',ri(e+0x2dc),'MAX',rf(e+0xbf0),flush=True)
    assert not C.isA(e,'RPawnPlayer')
if len(C.enemies)>0:
    e=C.enemies[1]
    write(e+0x2dc,100,'int');write(e+0xbf0,100.0,'float')
    C.flags.superDamage=True;C.loop();assert ri(e+0x2dc)==10
    C.flags.superDamage=False;write(e+0x2dc,100,'int');C.loop()
    assert ri(e+0x2dc)==100
    print('LIVE ENEMY CLASS / SIMULATED HEALTH CAP PASSED',flush=True)
# Exercise boss exclusion with simulated membership; never write live memory.
live=C.live;isa=C.isA;cn=C.cn
C.enemies=lua.table_from([p])
C.live=lambda o,n: True if o==p and n=='RBMPawnAI' else live(o,n)
C.isA=lambda o,n: n in ('RBMPawnAI','RPawnVillain') if o==p else isa(o,n)
C.cn=lambda o: 'TEST_ONLY_RPawnVillain' if o==p else cn(o)
write(p+0x2dc,100,'int');write(p+0xbf0,100.0,'float')
C.flags.superDamage=True;C.loop()
assert ri(p+0x2dc)==10
C.flags.superDamage=False;write(p+0x2dc,100,'int');C.loop()
assert ri(p+0x2dc)==100
C.flags.superDamage=True;C.cn=lambda o: 'TEST_ONLY_RPawnBoss' if o==p else cn(o)
C.loop();assert ri(p+0x2dc)==100
C.live=live;C.isA=isa;C.cn=cn;C.enemies=lua.table_from([])
print('SIMULATED ENEMY CAP / DISABLE / BOSS EXCLUSION PASSED', flush=True)
C.flags.superDamage=False
# Restore simulated player health and rediscover real classes/instances.
write(p+0x2dc,maxhp,'int');C.scan()
for key in ['positions','height','freeze','grappleRange','batarangRange','superDamage','oneHit','score','challengeTimer','predatorTimer','upgradePoints']:
    C.validate(key)
print('ALL FEATURE OFFSETS / SIZES / MASKS MATCH LIVE METADATA',flush=True)
shared=C.shared()
assert shared and C.live(shared,'RPersistentShared')
print('LIVE UPGRADE POINTS',ri(shared+0x458),flush=True)
write(shared+0x458,1,'int');C.flags.upgradePoints=True;C.loop();assert ri(shared+0x458)==99
write(shared+0x458,98,'int');C.loop();assert ri(shared+0x458)==99
C.setFlag('upgradePoints',False);write(shared+0x458,98,'int');C.loop();assert ri(shared+0x458)==98
write(shared+0x458,120,'int');C.flags.upgradePoints=True;C.loop();assert ri(shared+0x458)==120
write(shared+0x458,0xffffffff,'int');C.loop();assert ri(shared+0x458)==0xffffffff
C.flags.upgradePoints=False
print('UPGRADE POINTS REFILL / DISABLE / NO REDUCTION / INVALID VALUE GUARDS PASSED',flush=True)
C.save();saved=C.saved
for n in [1,2,5,10]:
    C.up(n)
    assert rf(p+0x50)>saved.z
    C.undoTeleport();assert abs(rf(p+0x50)-saved.z)<0.01
C.teleport();assert abs(rf(p+0x48)-saved.x)<0.01
print('SAVE / TELEPORT / UNDO / ALL UPWARD DISTANCES PASSED',flush=True)
grapples=[o for _,o in C.gadgets.items() if C.live(o,'RGrappleGun')]
batarangs=[o for _,o in C.gadgets.items() if C.live(o,'RBatarang')]
assert grapples and batarangs
initial={o:{off:rf(o+off) for off in ([0x3d8,0x3e0,0x3e8,0x46c,0x5ec] if o in grapples else [0x410,0x414])} for o in grapples+batarangs}
C.flags.grappleRange=True;C.flags.batarangRange=True;C.loop()
for o,offsets in initial.items():
    for off,v in offsets.items():
        if v>=0:assert rf(o+off)==max(v,50000)
C.setFlag('grappleRange',False);C.setFlag('batarangRange',False)
for o,offsets in initial.items():
    for off,v in offsets.items():assert rf(o+off)==v
print('GADGET REACH / RESTORE PASSED',len(grapples),len(batarangs),flush=True)
enemy_live,enemy_isa,enemy_cn=C.live,C.isA,C.cn
if len(C.enemies)>0:
    e=C.enemies[1]
else:
    print('No live thugs remain here: enemy mechanics use an overlay-only stand-in.',flush=True)
    e=p;C.enemies=lua.table_from([e])
    C.live=lambda o,n: True if o==e and n=='RBMPawnAI' else enemy_live(o,n)
    C.isA=lambda o,n: n in ('RBMPawnAI','RPawnVillain') if o==e else enemy_isa(o,n)
    C.cn=lambda o: 'TEST_ONLY_RPawnVillain' if o==e else enemy_cn(o)
write(e+0x2dc,100,'int');write(e+0xbf0,100.0,'float')
ko=ri(e+0x914);write(e+0x914,ko&~0x100000,'int');ko=ri(e+0x914)
projectiles=[o for _,o in C.projectiles.items()]
assert projectiles
projectile_damage={o:rf(o+0x310) for o in projectiles}
C.flags.oneHit=True;C.loop()
assert ri(e+0x2dc)==1 and ri(e+0x914)&0x100000
assert (ri(e+0x914)&~0x100000)==(ko&~0x100000)
for o in projectiles:assert rf(o+0x310)==10000
C.setFlag('oneHit',False)
assert ri(e+0x914)==ko
for o,v in projectile_damage.items():assert rf(o+0x310)==v
write(e+0x2dc,10,'int')
ctrl=ri(e+0x1e4);actor_flags=ri(e+0xa0);ctrl_flags=ri(ctrl+0xa0)
assert C.live(ctrl,'Controller')
C.flags.freeze=True;C.loop()
assert ri(e+0xa0)==actor_flags, 'Never disable enemy pawn animation ticks'
assert ri(ctrl+0xa0)&64
assert (ri(ctrl+0xa0)&~64)==(ctrl_flags&~64)
C.setFlag('freeze',False);assert ri(ctrl+0xa0)==ctrl_flags
print('ONE-HIT / BATARANG MASK / PROJECTILE RESTORE / FREEZE CONTROLLER RESTORE PASSED',flush=True)
C.live=enemy_live;C.isA=enemy_isa;C.cn=enemy_cn
C.enemies=lua.table_from([])
# Challenge mechanics are simulated on safe overlay objects; the story scene
# has no live challenge HUD/timer. This is NOT a gameplay/medal test.
live=C.live
C.hud=p;C.timers=lua.table_from([e])
C.live=lambda o,n: True if (o==p and n=='RGFxMovieChallengeHUD') or (o==e and n=='RSeqAct_HUDTimer') else live(o,n)
write(p+0x2f4,12.5,'float');write(e+0x108,2|8,'int')
write(e+0xf0,60,'int');write(e+0x100,14.0,'float');write(e+0x104,14,'int')
C.flags.score=True;C.flags.predatorTimer=True;C.flags.challengeTimer=True
C.loop();assert ri(p+0x250)==1000000 and rf(p+0x2f4)==12.5
assert ri(e+0x108)==2|8|1
write(p+0x2f4,15.0,'float');C.loop();assert rf(p+0x2f4)==12.5
C.setFlag('challengeTimer',False);assert ri(e+0x108)==2|8
write(e+0x108,2,'int');C.flags.challengeTimer=True;C.loop()
assert ri(e+0x108)==2, 'Ignore story/non-challenge timers'
C.flags.challengeTimer=False;C.flags.score=False;C.setFlag('predatorTimer',False)
write(p+0x2f4,20.0,'float');C.loop();assert rf(p+0x2f4)==20.0
scan=C.scan;C.scan=lambda:None
C.resetPredator();assert rf(p+0x2f4)==0
write(e+0x108,2|8,'int');C.resetChallenge()
assert rf(e+0x100)==60 and ri(e+0x104)==60
write(e+0x108,2|8|4,'int');C.resetChallenge()
assert rf(e+0x100)==0 and ri(e+0x104)==0
C.scan=scan;C.live=live;C.scan()
print('SIMULATED CHALLENGE SCORE / TIMER HOLD / RESET / SCOPE / DISABLE PASSED',flush=True)
before=len(writes);current[0]=pid+1;C.loop();assert len(writes)==before
current[0]=pid
write(p+4,0xffffffff,'int');before=len(writes);C.loop();assert len(writes)==before
print('RETARGET / STALE POINTER GUARDS PASSED', flush=True)
C.shutdown();pm.close()
print('All gameplay writes were simulated. Live game memory unchanged.')
