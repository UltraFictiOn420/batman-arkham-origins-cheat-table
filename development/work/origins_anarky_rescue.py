"""Temporary, bounded hold for the uniquely identified live Anarky countdown.
No code or mission flags changed. Exit when the timer stops, process exits,
identity changes, or three minutes pass. Later CT uses the native pause flag.
"""
import sys,struct,time
from ue3_inspect import ProcessMemory
pid,target=int(sys.argv[1]),int(sys.argv[2],0)
pm=ProcessMemory(pid)
def floating(a):
    raw=pm.read(a,4)
    return struct.unpack('<f',raw)[0] if len(raw)==4 else None
def ident():return tuple(pm.u32(target+off) for off in (4,0x18,0x1c,0x20,0x24))
snapshot=ident()
index=snapshot[0]
data=pm.u32(0x18b1acc)
assert index is not None and data and pm.u32(data+index*4)==target
flags=pm.u32(target+0x108)
start=pm.u32(target+0xf0)
value=floating(target+0x100)
assert flags is not None and flags&2 and not flags&28 and start in (230,160,180)
assert value is not None and 0<value<=start
held=max(1,int(value))
print('Temporarily holding Anarky countdown at',held,'seconds for up to 180 seconds.',flush=True)
deadline=time.monotonic()+180
try:
    while time.monotonic()<deadline:
        data=pm.u32(0x18b1acc)
        flags=pm.u32(target+0x108)
        now=floating(target+0x100)
        if ident()!=snapshot or not data or pm.u32(data+index*4)!=target or flags is None or not flags&2 or flags&28 or not now or not 0<now<=start:
            print('Timer stopped or changed; released.',flush=True);break
        pm.write(target+0x100,struct.pack('<f',float(held)))
        pm.write(target+0x104,struct.pack('<i',held))
        time.sleep(0.1)
finally:
    pm.close()
print('Temporary hold ended; no pause/code/mission flag patches remain.',flush=True)
