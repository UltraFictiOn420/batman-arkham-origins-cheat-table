from pathlib import Path
import xml.etree.ElementTree as ET
from luaparser import ast

ROOT=Path(__file__).resolve().parents[1]
runtime=(ROOT/'work/arkham_origins_runtime.lua').read_text(encoding='utf-8')
ast.parse(runtime)
table=ET.Element('CheatTable',CheatEngineTableVersion='45')
entries=ET.SubElement(table,'CheatEntries')
def node(parent,id,title,script=None,key=None,group=False):
    e=ET.SubElement(parent,'CheatEntry')
    ET.SubElement(e,'ID').text=str(id)
    ET.SubElement(e,'Description').text='"'+title+'"'
    if script:
        ET.SubElement(e,'VariableType').text='Auto Assembler Script'
        ET.SubElement(e,'AssemblerScript').text=script
    if group:
        ET.SubElement(e,'GroupHeader').text='1'
        ET.SubElement(e,'Options',moHideChildren='1')
    if key:
        hot=ET.SubElement(ET.SubElement(e,'Hotkeys'),'Hotkey')
        ET.SubElement(hot,'Action').text='Toggle Activation'
        ET.SubElement(ET.SubElement(hot,'Keys'),'Key').text=str(key)
        ET.SubElement(hot,'ID').text='0'
    return e
root=node(entries,1,'[Required] Initialize Arkham Origins - Original v5',f'[ENABLE]\n{{$lua}}\nif syntaxcheck then return end\n{runtime}\n{{$asm}}\n[DISABLE]\n{{$lua}}\nif syntaxcheck then return end\nif AO and AO.shutdown then AO.shutdown() end\nAO=nil\n{{$asm}}')
ET.SubElement(root,'Options',moHideChildren='1',moDeactivateChildrenAsWell='1')
children=ET.SubElement(root,'CheatEntries')
status=node(children,2,'Runtime Status (read-only; no popup)')
ET.SubElement(status,'VariableType').text='String'
ET.SubElement(status,'Length').text='500'
ET.SubElement(status,'Unicode').text='0'
ET.SubElement(status,'Address').text='AO_RuntimeStatus'
def group(id,title): return ET.SubElement(node(children,id,title,group=True),'CheatEntries')
def flag(parent,id,title,name,key=None,other=None):
    extra=f'local other=getAddressList().getMemoryRecordByID({other});if other and other.Active then other.Active=false end\n' if other else ''
    script=f"[ENABLE]\n{{$lua}}\nif syntaxcheck then return end\nif not AO then error('Enable Initialize Arkham Origins first.') end\n{extra}AO.setFlag('{name}',true)\n{{$asm}}\n[DISABLE]\n{{$lua}}\nif syntaxcheck then return end\nif AO then AO.setFlag('{name}',false) end\n{{$asm}}"
    return node(parent,id,title,script,key=key)
def action(parent,id,title,fn,key=None):
    script=f"[ENABLE]\n{{$lua}}\nif syntaxcheck then return end\nif not AO then error('Enable Initialize Arkham Origins first.') end\nAO.action(memrec,function() {fn} end)\n{{$asm}}\n[DISABLE]"
    return node(parent,id,title,script,key=key)
survival=group(10,'Player / Survival')
flag(survival,11,'Infinite Health','health')
combat=group(20,'Enemies / Combat')
flag(combat,21,'Freeze Enemies (animations preserved) [Test]','freeze')
flag(combat,22,'Super Damage (enemy HP / 10 + Batarang KO) [-] [Batarangs: Test]','superDamage',189,23)
flag(combat,23,'One-Hit Knockout (Melee + Batarangs) [=] [Test]','oneHit',187,22)
reach=group(30,'Gadgets / Reach')
flag(reach,31,'Extra-Long Grapple Distance [Test]','grappleRange')
flag(reach,32,'Extra-Long Batarang Distance [Test]','batarangRange')
upgrades=group(40,'WayneTech / Upgrades')
flag(upgrades,41,'Infinite Upgrade Points (minimum 99) [Test]','upgradePoints')
missions=group(70,'Side Missions / Anarky Bombs')
flag(missions,71,'Hold Anarky Bomb Countdowns (auto-follow next bomb) [Test]','anarkyTimer')
challenge=group(50,'Challenge Modes [Require Gameplay Testing]')
flag(challenge,51,'Combat Challenge HUD Score = Target [Test]','score')
target=node(challenge,52,'Challenge Score Target')
ET.SubElement(target,'VariableType').text='4 Bytes'
ET.SubElement(target,'Address').text='AO_ChallengeScoreTarget'
flag(challenge,53,'Pause Challenge / Modifier Countdown Timer [Test]','challengeTimer')
action(challenge,54,'Reset Challenge Timer (countdown refills; count-up resets) [Test]','AO.resetChallenge()')
flag(challenge,55,'Freeze Predator Challenge Timer [Test]','predatorTimer')
action(challenge,56,'Reset Predator Challenge Timer to 0 [Test]','AO.resetPredator()')
teleport=group(60,'Positions / Teleport (same character session only)')
action(teleport,61,'Save Position [J] [Test]','AO.save()',74)
action(teleport,62,'Teleport to Saved Position [K] [Test]','AO.teleport()',75)
action(teleport,63,'Undo / Redo Last Teleport [L] [Test]','AO.undoTeleport()',76)
for i,n in enumerate([1,2,5,10]): action(teleport,64+i,f'Teleport Up {n} Body Height(s) [F{i+1}] [Test]',f'AO.up({n})',112+i)
ET.SubElement(table,'UserdefinedSymbols')
ET.SubElement(table,'Comments').text='Original Origins v2, Steam single-player only. Ports the relevant City v6 feature set: health, effective super damage, one-hit knockouts, Batarang damage/KO flag, enemy freeze, grapple/Batarang reach, challenge HUD score, challenge/modifier timers, predator timer, save/teleport/undo and upward teleports. City-only Zsasz phone race deliberately excluded. No Gameplay/Time, console unlocker, shared VM patch, armor, fly, XP, combo, upgrade-point, waypoint, scan/input or story-flag edits. v1 health and melee super damage user-confirmed; v2 additions require gameplay tests. Reflected offsets/masks checked before activation. Freeze affects AI controller ticks and positions, not pawn animation ticks. Reversible flags/ranges/projectile damage restored on disable; reduced enemy HP persists until reload/respawn. Boss-named classes excluded; disable damage modifiers during scripted/tutorial/boss/interrogation encounters. Batarang KO path is a port requiring quickfire/aimed tests; other gadgets not claimed supported. Challenge score is a HUD-field experiment, not verified medal/save manipulation. Timer scripts only touch active challenge-marked HUD timers; no claim to cover every special event. Teleports stay in the same live pawn/world/session and do not stream areas or check walls; J saves, K teleports, L undoes/redoes. F1/F2/F3/F4 raise by 1/2/5/10 body heights. Main keyboard -/= toggle Super Damage/One-Hit, mutually exclusive. Infinite health replenishes HP, not true invulnerability. Disable old initializer before replacing table; reinitialize after game restart. No popup logging. Back up saves; do not combine tables. Original code, no third-party table code imported.'
comments=table.find('Comments')
comments.text=comments.text.replace('XP, combo, upgrade-point, waypoint','XP, combo, waypoint')+' Infinite Upgrade Points added at user request: keeps at least 99 available in the current world-linked RPersistentShared object. Does not auto-unlock any upgrades or prerequisites. Granted points and purchased upgrades can persist in saves; disabling stops refill but does not reset the balance or undo purchases. Current live balance of 1 was verified; refill/disable tested with simulated writes. All v2 tests used live reads plus an overlay, not in-game cheat activation.'
comments.text=comments.text.replace('Original Origins v2','Original Origins v3')+' v3 adds a separate Anarky countdown pause: selects exactly one active non-challenge count-down in the observed OpenWorld__ChA1234 package with starting time 230, 160, or 180 seconds. Only the first 230-second mission has been live identified; later variants need tests. Binds object identity at activation, sets only the native bPauseTimer bit, and restores its original bit on disable. Does not complete/disarm bombs or reset mission progress. After finishing a bomb, retoggle during the next bomb countdown. Initial live countdown matched the user event; a bounded temporary helper held remaining time while this CT was built. No claim of native-pause gameplay confirmation yet.'
comments.text=comments.text.replace('Original Origins v3','Original Origins v4').replace('Only the first 230-second mission has been live identified; later variants need tests.','Both the 230-second and 160-second timers have now been live identified during user Anarky races; the 180-second variant still needs gameplay confirmation.').replace('Binds object identity at activation','Tracks object identity and automatically rebinds to the next eligible active bomb timer').replace('After finishing a bomb, retoggle during the next bomb countdown.','Leave enabled between bombs: it waits when none is running, restores the completed timer pause bit, and follows the next eligible countdown.').replace('No claim of native-pause gameplay confirmation yet.','User reports the first bomb froze with v3, but a temporary helper was also used; native pause confirmation on subsequent bombs is still needed.')+' v4 fixes v3 staying bound to a completed timer. The current second timer starts at 160 seconds and was running unpaused while the first was stopped. Ambiguous selection fails closed; story/challenge timers outside the observed package/durations are ignored.'
comments.text=comments.text.replace('Original Origins v4','Original Origins v5').replace('sets only the native bPauseTimer bit, and restores its original bit on disable','holds the remaining-time float and matching HUD integer, with no timer flag writes').replace('restores the completed timer pause bit, and follows','stops holding the completed timer, and follows').replace('native pause confirmation on subsequent bombs is still needed','the helper result did not establish that the native pause bit worked')+' v5 diagnosis: the second timer was decreasing with bPauseTimer already set (flags 3). Native pause is ignored for this event. Hold uses the captured current RemainingTime and IntRemainingTime, equivalent to the successful temporary helper. Off stops writes and allows natural countdown, not restoration to pre-enable time. Auto-follow, identity/lifetime checks and scoped selection retained. User reports v4 did not freeze; v5 requires a standalone CE test without a temporary helper.'
ET.indent(table,space='  ')
out=ROOT/'outputs/Batman Arkham Origins - Original v5.CT'
ET.ElementTree(table).write(out,encoding='utf-8',xml_declaration=True)
for e in ET.parse(out).findall('.//AssemblerScript'):
    for block in e.text.split('{$lua}')[1:]: ast.parse(block.split('{$asm}')[0])
print(out)
print('XML and all embedded Lua syntax validated.')
parsed=ET.parse(out)
ids=[e.text for e in parsed.findall('.//CheatEntry/ID')]
assert len(ids)==len(set(ids))
assert not {'42','43'} & set(ids)
assert {str(n) for n in [11,21,22,23,31,32,41,51,52,53,54,55,56,61,62,63,64,65,66,67,71]} <= set(ids)
print('Unique records and City v6 feature coverage verified (excluding City-only phone race).')
