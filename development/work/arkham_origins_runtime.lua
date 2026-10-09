-- Original Origins v5: scoped data edits, no console or shared VM patches.
if AO and AO.shutdown then AO.shutdown() end
AO=nil
openProcess('BatmanOrigins.exe')
local base=getAddressSafe('BatmanOrigins.exe')
if not base then error('Start Arkham Origins single-player and load into gameplay first.') end
local C={pid=getOpenedProcessID(),flags={},names={},classes={},isa={},enemies={},gadgets={},projectiles={},timers={},originals={},captures={},frozen={},layout={},tick=0,damageWrites=0}
local function ri(a) if a then local ok,v=pcall(readInteger,a);if ok then return v end end end
local function wi(a,v) return writeInteger(a,v) end
local function rf(a) if a then local ok,v=pcall(readFloat,a);if ok then return v end end end
local function bit(v,m) return v and v%(m*2)>=m end
local function setbit(v,m,on) if not v then return end if bit(v,m)~=on then return on and v+m or v-m end return v end
local function wf(a,v) return writeFloat(a,v) end
local function finite(v) return v and v==v and math.abs(v)<10000000 end
C.gnames=base+0x14B1A98;C.gobjects=base+0x14B1ACC
function C.name(i)
  if not i or i<0 then return end
  if C.names[i] then return C.names[i] end
  local count,data=ri(C.gnames+4),ri(C.gnames)
  if not count or count<1000 or count>500000 or not data or i>=count then return end
  local e=ri(data+i*4);if not e or e<0x10000 then return end
  local encoding=ri(e);if not encoding then return end
  local ok,n=pcall(readString,e+12,192,bit(encoding,1))
  if ok and n and n~='' then C.names[i]=n;return n end
end
function C.oname(o) if o and o>0x10000 then return C.name(ri(o+0x1C)) end end
function C.class(o) return o and ri(o+0x24) end
function C.cn(o)
  local c=C.class(o);if not c or c<0x10000 then return end
  if not C.classes[c] then C.classes[c]=C.oname(c) end
  return C.classes[c]
end
function C.isA(o,n)
  local c=C.class(o);if not c then return false end
  local key=tostring(c)..':'..n
  if C.isa[key]~=nil then return C.isa[key] end
  for _=1,50 do
    if not c or c<0x10000 then break end
    if C.oname(c)==n then C.isa[key]=true;return true end
    c=ri(c+0x38)
  end
  C.isa[key]=false;return false
end
function C.registered(o)
  if getOpenedProcessID()~=C.pid or not o or o<0x10000 then return false end
  local count,data,index=ri(C.gobjects+4),ri(C.gobjects),ri(o+4)
  return count and data and index and index>=0 and index<count and ri(data+index*4)==o
end
function C.live(o,n)
  if not C.registered(o) or not C.isA(o,n) then return false end
  local name=C.oname(o)
  if not name or name:sub(1,9)=='Default__' then return false end
  if C.isA(o,'Actor') and bit(ri(o+0xA0),8) then return false end
  return true
end
local function identity(o)
  return {index=ri(o+4),class=C.class(o),name=ri(o+0x1C),number=ri(o+0x20),outer=ri(o+0x18)}
end
local function same(o,x)
  return x and C.registered(o) and ri(o+4)==x.index and C.class(o)==x.class and ri(o+0x1C)==x.name and ri(o+0x20)==x.number and ri(o+0x18)==x.outer
end
function C.remember(key,o,offset,kind,mask)
  C.originals[key]=C.originals[key] or {}
  local a=o+offset;local map=C.originals[key]
  if map[a] and same(o,map[a].identity) then return map[a].value end
  local v=kind=='float' and rf(a) or ri(a)
  if v~=nil then map[a]={owner=o,identity=identity(o),offset=offset,kind=kind,value=v,mask=mask} end
  return v
end
function C.restore(key)
  for a,e in pairs(C.originals[key] or {}) do
    if same(e.owner,e.identity) then
      if e.kind=='float' then wf(a,e.value)
      elseif e.mask then wi(a,setbit(ri(a),e.mask,bit(e.value,e.mask)))
      else wi(a,e.value) end
    end
  end
  C.originals[key]=nil
end
local function bytes(a,n)
  local ok,b=pcall(readBytes,a,n,true);if ok and b and #b==n then return b end
end
local function u32(b,i) return b[i]+b[i+1]*256+b[i+2]*65536+b[i+3]*16777216 end
function C.scan()
  if getOpenedProcessID()~=C.pid then return end
  local count,data=ri(C.gobjects+4),ri(C.gobjects)
  if not count or count<1000 or count>500000 or not data then return end
  local raw=bytes(data,count*4);if not raw then return end
  C.classes={};C.isa={}
  local enemies,gadgets,projectiles,timers,controller,hud,gameInfo={},{},{},{},nil,nil,nil
  for i=1,#raw,4 do
    local o=u32(raw,i)
    if o>0x10000 then
      local cn=C.cn(o)
      if cn then
        if cn:find('PlayerController') and C.live(o,'RPlayerController') then
          local p=ri(o+0x1C8)
          if C.live(p,'RPawnPlayer') then controller=o end
        elseif cn:find('GameInfo') and C.live(o,'RGameInfoBase') then gameInfo=o
        elseif cn:find('ChallengeHUD') and C.live(o,'RGFxMovieChallengeHUD') then hud=o
        elseif cn=='RSeqAct_HUDTimer' and C.live(o,cn) then timers[#timers+1]=o
        elseif (cn:find('Batarang') and C.live(o,'RBatarang')) or (cn:find('GrappleGun') and C.live(o,'RGrappleGun')) then gadgets[#gadgets+1]=o
        elseif cn:find('BatarangProjectile') and C.registered(o) and C.isA(o,'RBatarangProjectile') then projectiles[#projectiles+1]=o
        elseif cn:find('Pawn') and not cn:lower():find('boss') and C.live(o,'RBMPawnAI') and C.isA(o,'RPawnVillain') and not C.isA(o,'RPawnPlayer') then
          enemies[#enemies+1]=o
        end
      end
    end
  end
  C.controller,C.enemies,C.gadgets,C.projectiles,C.timers,C.hud=controller,enemies,gadgets,projectiles,timers,hud
  C.gameInfo=gameInfo
end
function C.pawn()
  if not C.live(C.controller,'RPlayerController') then return end
  local p=ri(C.controller+0x1C8)
  if C.live(p,'RPawnPlayer') then return p end
end
function C.shared()
  local p=C.pawn();local game=C.gameInfo
  if not p or not C.live(game,'RGameInfoBase') or ri(game+0xC0)~=ri(p+0xC0) then return end
  local shared=ri(game+0x364)
  if C.live(shared,'RPersistentShared') and ri(shared+0x18)==game then return shared end
end
function C.anarkyCandidate(t)
  if not C.live(t,'RSeqAct_HUDTimer') then return false end
  local root=t
  for _=1,12 do local parent=ri(root+0x18);if not parent or parent==0 then break end root=parent end
  if C.oname(root)~='OpenWorld__ChA1234' then return false end
  local start,flags,remaining=ri(t+0xF0),ri(t+0x108),rf(t+0x100)
  return (start==230 or start==160 or start==180) and bit(flags,2) and not bit(flags,4) and not bit(flags,8) and not bit(flags,16) and finite(remaining) and remaining>0 and remaining<=start
end
function C.findAnarky()
  local target
  for _,t in ipairs(C.timers) do
    if C.anarkyCandidate(t) then
      if target then return nil,'AMBIGUOUS (multiple countdowns)' end
      target=t
    end
  end
  return target,target and 'HELD' or 'WAITING (next bomb)'
end
function C.bindAnarky()
  C.validate('anarkyTimer');C.scan()
  local target,state=C.findAnarky()
  C.anarkyState=state
  C.anarky=target and {owner=target,identity=identity(target),held=rf(target+0x100)} or nil
end
function C.holdAnarky()
  local bound=C.anarky;local t=bound and bound.owner
  if not t or not same(t,bound.identity) or not C.anarkyCandidate(t) then
    if C.originals.anarkyPause then C.restore('anarkyPause') end
    C.anarky=nil;C.anarkyHeld=false
    local target,state=C.findAnarky()
    C.anarkyState=state
    if target then C.anarky={owner=target,identity=identity(target),held=rf(target+0x100)};t=target else return end
  end
  local held=C.anarky and C.anarky.held
  if not finite(held) or held<=0 then C.anarkyHeld=false;return end
  -- Origins' Anarky countdown ignores bPauseTimer even while its bit is set.
  -- Hold the real float and matching HUD integer instead. No mission flags.
  wf(t+0x100,held);wi(t+0x104,math.floor(held))
  C.anarkyHeld=true;C.anarkyState='HELD'
end
function C.status(s)
  if C.statusAddress and getOpenedProcessID()==C.pid then pcall(writeString,C.statusAddress,s:sub(1,500)..'\0',false) end
end
function C.position(p)
  local x,y,z=rf(p+0x48),rf(p+0x4C),rf(p+0x50)
  if not finite(x) or not finite(y) or not finite(z) then error('Invalid player position.') end
  return {x=x,y=y,z=z,pawn=p,identity=identity(p),world=ri(p+0xC0)}
end
function C.move(target)
  C.validate('positions')
  local p=C.pawn();if not p then error('No controlled player is loaded.') end
  if not target then error('Save a position with J first.') end
  if p~=target.pawn or not same(p,target.identity) or ri(p+0xC0)~=target.world then error('Saved position belongs to a different character/session. Save again with J.') end
  if not finite(target.x) or not finite(target.y) or not finite(target.z) then error('Invalid teleport destination.') end
  C.undo=C.position(p)
  wf(p+0x10C,0);wf(p+0x110,0);wf(p+0x114,0)
  wf(p+0x48,target.x);wf(p+0x4C,target.y);wf(p+0x50,target.z)
end
function C.save()
  C.validate('positions')
  local p=C.pawn();if not p then error('No controlled player is loaded.') end
  C.saved=C.position(p)
end
function C.teleport() C.move(C.saved) end
function C.undoTeleport() if not C.undo then error('No teleport to undo.') end C.move(C.undo) end
function C.up(n)
  C.validate('positions');C.validate('height')
  local p=C.pawn();if not p then error('No controlled player is loaded.') end
  local cylinder=ri(p+0x388)
  if not C.registered(cylinder) or not C.isA(cylinder,'CylinderComponent') then error('Player cylinder is unavailable.') end
  local half,scale=rf(cylinder+0x1B8),rf(p+0x60)
  if not half or half<10 or half>300 or not scale or scale<=0 or scale>10 then error('Invalid player height.') end
  local target=C.position(p);target.z=target.z+half*2*scale*n;C.move(target)
end
function C.action(record,fn)
  local ok,e=pcall(fn);C.lastResult=ok and 'SUCCESS' or tostring(e)
  C.status('Last action: '..C.lastResult)
  if not ok and playSound then pcall(playSound,'SystemHand') end
  local t=createTimer(nil,false);t.Interval=100
  t.OnTimer=function(self) self.Enabled=false;pcall(function() record.Active=false end);self.destroy() end;t.Enabled=true
end
local function hold(key,o,offset)
  local e=C.captures[key]
  if not e or e.owner~=o or not same(o,e.identity) then e={owner=o,identity=identity(o),value=rf(o+offset)};C.captures[key]=e end
  if finite(e.value) then wf(o+offset,e.value) end
end
function C.resetPredator()
  C.validate('predatorTimer');C.scan()
  if not C.live(C.hud,'RGFxMovieChallengeHUD') then error('Enter a predator challenge first.') end
  wf(C.hud+0x2F4,0);C.captures.predator=nil
end
function C.resetChallenge()
  C.validate('challengeTimer');C.scan();local changed=false
  for _,t in ipairs(C.timers) do
    local flags=ri(t+0x108)
    if C.live(t,'RSeqAct_HUDTimer') and bit(flags,2) and (bit(flags,8) or bit(flags,16)) then
      local value=bit(flags,4) and 0 or ri(t+0xF0)
      if value and value>=0 and value<86400 then wf(t+0x100,value);wi(t+0x104,math.floor(value));changed=true end
    end
  end
  if not changed then error('No active challenge countdown/count-up timer found.') end
end
function C.loop()
  if getOpenedProcessID()~=C.pid then return end
  C.tick=C.tick+1
  if C.tick%40==0 then C.scan() end
  local p=C.pawn()
  if C.flags.health and p then
    local max=ri(p+0x2E0)
    if not max or max<=0 then max=ri(p+0x10C8) end
    local hp=ri(p+0x2DC)
    -- Do not revive a dead pawn or override a scripted death transition.
    if hp and hp>0 and max and max>0 and max<100000 and hp<max then wi(p+0x2DC,max) end
  end
  if C.flags.upgradePoints then
    local shared=C.shared();local points=shared and ri(shared+0x458)
    if points and points>=0 and points<100000 and points<99 then wi(shared+0x458,99) end
  end
  if C.flags.anarkyTimer then C.holdAnarky() else C.anarkyHeld=false end
  if C.flags.superDamage or C.flags.oneHit or C.flags.freeze then
    for _,e in ipairs(C.enemies) do
      if C.live(e,'RBMPawnAI') and C.isA(e,'RPawnVillain') and not C.isA(e,'RPawnPlayer') and not (C.cn(e) or ''):lower():find('boss') then
        local hp,max=ri(e+0x2DC),rf(e+0xBF0)
        if (C.flags.superDamage or C.flags.oneHit) and hp and hp>0 then
          C.remember('batarangKO',e,0x914,'int',0x100000)
          wi(e+0x914,setbit(ri(e+0x914),0x100000,true))
        end
        if C.flags.freeze and hp and hp>0 then
          local controller=ri(e+0x1E4)
          if C.live(controller,'Controller') then C.remember('freeze',controller,0xA0,'int',0x40);wi(controller+0xA0,setbit(ri(controller+0xA0),0x40,true)) end
          local saved=C.frozen[e]
          if not saved or not same(e,saved.identity) then saved=C.position(e);C.frozen[e]=saved end
          wf(e+0x10C,0);wf(e+0x110,0);wf(e+0x114,0)
          wf(e+0x48,saved.x);wf(e+0x4C,saved.y);wf(e+0x50,saved.z)
        elseif C.frozen[e] then
          local controller=ri(e+0x1E4);local map=C.originals.freeze
          local saved=map and controller and map[controller+0xA0]
          if saved and same(controller,saved.identity) then wi(controller+0xA0,setbit(ri(controller+0xA0),0x40,bit(saved.value,0x40)));map[controller+0xA0]=nil end
          C.frozen[e]=nil
        end
        if (C.flags.superDamage or C.flags.oneHit) and hp and hp>0 and hp<100000 and max and max==max and max>0 and max<100000 then
          local cap=C.flags.oneHit and 1 or math.max(1,math.floor(max/10))
          if hp>cap then if wi(e+0x2DC,cap) then C.damageWrites=C.damageWrites+1 end end
        end
      end
    end
  end
  if not C.flags.freeze then if C.originals.freeze then C.restore('freeze') end C.frozen={} end
  if not C.flags.superDamage and not C.flags.oneHit and C.originals.batarangKO then C.restore('batarangKO') end
  for _,b in ipairs(C.gadgets) do
    local key,offsets
    if C.flags.batarangRange and C.live(b,'RBatarang') then key='batarangRange';offsets={0x410,0x414}
    elseif C.flags.grappleRange and C.live(b,'RGrappleGun') then key='grappleRange';offsets={0x3D8,0x3E0,0x3E8,0x46C,0x5EC} end
    if key then
      for _,offset in ipairs(offsets) do
        local original=C.remember(key,b,offset,'float')
        if finite(original) and original>=0 then wf(b+offset,math.max(original,50000)) end
      end
    end
  end
  for _,key in ipairs({'grappleRange','batarangRange'}) do if not C.flags[key] and C.originals[key] then C.restore(key) end end
  if C.flags.superDamage or C.flags.oneHit then
    for _,b in ipairs(C.projectiles) do
      if C.registered(b) and C.isA(b,'RBatarangProjectile') and ((C.oname(b) or ''):sub(1,9)=='Default__' or C.live(b,'RBatarangProjectile')) then
        local original=C.remember('batarangDamage',b,0x310,'float')
        if original and original>=0 and original<100000 then wf(b+0x310,C.flags.oneHit and 10000 or math.max(1,original*10)) end
      end
    end
  elseif C.originals.batarangDamage then C.restore('batarangDamage') end
  if C.live(C.hud,'RGFxMovieChallengeHUD') then
    if C.flags.score then local target=ri(C.score);if target and target>=0 and target<=99999999 then wi(C.hud+0x250,target) end end
    if C.flags.predatorTimer then hold('predator',C.hud,0x2F4) else C.captures.predator=nil end
  else C.captures.predator=nil end
  if C.flags.challengeTimer then
    for _,t in ipairs(C.timers) do
      local flags=ri(t+0x108)
      if C.live(t,'RSeqAct_HUDTimer') and bit(flags,2) and (bit(flags,8) or bit(flags,16)) then
        C.remember('challengePause',t,0x108,'int',1);wi(t+0x108,setbit(flags,1,true))
      end
    end
  elseif C.originals.challengePause then C.restore('challengePause') end
  if C.tick%10==0 then
    local shared=C.shared()
    C.status(string.format('v5 | %s | HP %s/%s | Health %s | Damage %s | Enemies %d | Gadgets %d | Upgrade points %s | Anarky %s | %s',p and C.cn(p) or 'waiting for player',tostring(p and ri(p+0x2DC) or '?'),tostring(p and ri(p+0x2E0) or '?'),C.flags.health and 'ON' or 'OFF',C.flags.oneHit and 'ONE-HIT' or C.flags.superDamage and 'SUPER' or 'OFF',#C.enemies,#C.gadgets,tostring(shared and ri(shared+0x458) or '?'),C.flags.anarkyTimer and (C.anarkyState or 'WAITING') or 'OFF',C.lastResult or ''))
  end
end
function C.setFlag(key,on)
  if on then C.validate(key) end
  if on and key=='anarkyTimer' then C.bindAnarky() end
  C.flags[key]=on
  if on then C.scan();C.loop();if C.timer then C.timer.Enabled=true end end
  if not on then
    if key=='freeze' then C.restore('freeze');C.frozen={} end
    if key=='grappleRange' or key=='batarangRange' then C.restore(key) end
    if key=='challengeTimer' then C.restore('challengePause') end
    if key=='predatorTimer' then C.captures.predator=nil end
    if key=='anarkyTimer' then C.restore('anarkyPause');C.anarky=nil;C.anarkyHeld=false;C.anarkyState='OFF' end
    if not C.flags.superDamage and not C.flags.oneHit then C.restore('batarangKO');C.restore('batarangDamage') end
  end
end
local specs={
  positions={['Actor.Location']={0x48,12},['Actor.Velocity']={0x10C,12},['Actor.WorldInfo']={0xC0,4}},
  height={['Pawn.CylinderComponent']={0x388,4},['CylinderComponent.CollisionHeight']={0x1B8,4},['Actor.DrawScale']={0x60,4}},
  freeze={['Pawn.Controller']={0x1E4,4},['Actor.bTickIsDisabled']={0xA0,4,0x40}},
  grappleRange={['RGrappleGun.MaxGrappleHeight']={0x3D8,4},['RGrappleGun.MaxGrappleHorizontalDistance']={0x3E0,4},['RGrappleGun.MaxHorizontalDistanceForAimedGrapple']={0x3E8,4},['RGrappleGun.MaxHorizontalRange']={0x46C,4},['RGrappleGun.AerialGrappleRange']={0x5EC,4}},
  batarangRange={['RBatarang.BatarangRange']={0x410,4},['RBatarang.AutoTargetRange']={0x414,4}},
  superDamage={['RBatarangProjectile.DefaultDamage']={0x310,4},['RBMPawnAI.bBatarangCanKill']={0x914,4,0x100000}},
  score={['RGFxMovieChallengeHUD.TotalScore']={0x250,4}},
  upgradePoints={['RPersistentShared.UpgradePoints']={0x458,4},['RGameInfoBase.PersistentShared']={0x364,4}},
  anarkyTimer={['RSeqAct_HUDTimer.TimeInSeconds']={0xF0,4},['RSeqAct_HUDTimer.RemainingTime']={0x100,4},['RSeqAct_HUDTimer.IntRemainingTime']={0x104,4},['RSeqAct_HUDTimer.bTimerRunning']={0x108,4,2},['RSeqAct_HUDTimer.bCountUp']={0x108,4,4},['RSeqAct_HUDTimer.bChallengeModifierTimer']={0x108,4,8},['RSeqAct_HUDTimer.bBespokeChallengeTimer']={0x108,4,16}},
  predatorTimer={['RGFxMovieChallengeHUD.PredatorTime']={0x2F4,4}},
  challengeTimer={['RSeqAct_HUDTimer.RemainingTime']={0x100,4},['RSeqAct_HUDTimer.IntRemainingTime']={0x104,4},['RSeqAct_HUDTimer.TimeInSeconds']={0xF0,4},['RSeqAct_HUDTimer.bPauseTimer']={0x108,4,1},['RSeqAct_HUDTimer.bTimerRunning']={0x108,4,2},['RSeqAct_HUDTimer.bCountUp']={0x108,4,4},['RSeqAct_HUDTimer.bChallengeModifierTimer']={0x108,4,8},['RSeqAct_HUDTimer.bBespokeChallengeTimer']={0x108,4,16}}
}
specs.oneHit=specs.superDamage
function C.validate(key)
  if key=='health' then return end
  local spec=specs[key];if not spec then error('Unknown Origins option: '..key) end
  for name,expected in pairs(spec) do
    local actual=C.layout[name]
    if not actual then error('Game metadata unavailable for '..name..'. Reinitialize after loading the relevant mode.') end
    if actual.offset~=expected[1] or actual.size~=expected[2] or (expected[3] and actual.mask~=expected[3]) then error('Unsupported Origins layout: '..name) end
  end
  if key=='freeze' then C.validate('positions') end
end
-- Verify reflected offsets before allowing any gameplay write.
if C.name(0)~='None' then error('Unsupported Origins name registry.') end
local count,data=ri(C.gobjects+4),ri(C.gobjects)
if not count or count<1000 or count>500000 or not data then error('Unsupported Origins object registry.') end
local required={['Pawn.Health']=0x2DC,['Pawn.HealthMax']=0x2E0,['RPawnPlayer.MaxHealth']=0x10C8,['Controller.Pawn']=0x1C8,['RBMPawnAI.MaxHealth']=0xBF0,['Actor.bDeleteMe']=0xA0}
local wanted={}
for _,spec in pairs(specs) do for key in pairs(spec) do wanted[key]=true end end
local raw=bytes(data,count*4);if not raw then error('Cannot read Origins metadata.') end
for i=1,#raw,4 do
  local o=u32(raw,i);local cn=o>0x10000 and C.cn(o)
  if cn and cn:sub(-8)=='Property' then
    local key=(C.oname(ri(o+0x18)) or '')..'.'..(C.oname(o) or '')
    if wanted[key] then local packed=ri(o+0x3C);if packed then C.layout[key]={offset=math.floor(packed/65536),size=packed%65536,mask=ri(o+0x58)} end end
    if required[key] then
      local packed=ri(o+0x3C)
      if not packed or math.floor(packed/65536)~=required[key] or packed%65536~=4 then error('Unsupported field layout: '..key) end
      if key=='Actor.bDeleteMe' and ri(o+0x58)~=8 then error('Unsupported actor lifetime flag.') end
      required[key]=nil
    end
  end
end
for key in pairs(required) do error('Required Origins metadata missing: '..key) end
C.scan()
if not C.pawn() then error('Load Origins single-player into gameplay before initializing.') end
C.statusAddress=allocateMemory(512)
if not C.statusAddress then error('Unable to allocate table status.') end
registerSymbol('AO_RuntimeStatus',C.statusAddress,true)
C.score=allocateMemory(4)
if not C.score then pcall(unregisterSymbol,'AO_RuntimeStatus');pcall(deAlloc,C.statusAddress);error('Unable to allocate challenge setting.') end
registerSymbol('AO_ChallengeScoreTarget',C.score,true);wi(C.score,1000000)
C.status('v5 initialized; cheats OFF')
function C.shutdown()
  if C.timer then C.timer.destroy();C.timer=nil end
  C.flags={}
  local keys={};for key in pairs(C.originals) do keys[#keys+1]=key end
  for _,key in ipairs(keys) do pcall(C.restore,key) end
  pcall(unregisterSymbol,'AO_RuntimeStatus')
  pcall(unregisterSymbol,'AO_ChallengeScoreTarget')
  if C.statusAddress and getOpenedProcessID()==C.pid then pcall(deAlloc,C.statusAddress) end
  if C.score and getOpenedProcessID()==C.pid then pcall(deAlloc,C.score) end
end
AO=C
C.timer=createTimer(nil,false);C.timer.Interval=50
C.timer.OnTimer=function()
  if getOpenedProcessID()~=C.pid then C.timer.Enabled=false;return end
  local ok,e=pcall(C.loop)
  if not ok then C.timer.Enabled=false;C.status('PAUSED ERROR: '..tostring(e)) end
end
C.timer.Enabled=true
