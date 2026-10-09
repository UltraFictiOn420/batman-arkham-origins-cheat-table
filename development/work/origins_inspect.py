"""Read-only Origins UObject/property inspection."""
import sys, struct, re
from functools import lru_cache
from ue3_inspect import ProcessMemory

pm = ProcessMemory(int(sys.argv[1]))
nd, nc = pm.u32(0x18B1A98), pm.u32(0x18B1A9C)
np = struct.unpack('<%dI' % nc, pm.read(nd, nc*4))
od, oc = pm.u32(0x18B1ACC), pm.u32(0x18B1AD0)
op = struct.unpack('<%dI' % oc, pm.read(od, oc*4))
@lru_cache(None)
def name(i):
    if i is None or i >= nc: return '?'
    e = np[i]
    raw = pm.read(e+12, 256)
    return raw.decode('utf-16le', errors='ignore').split('\0')[0] if (pm.u32(e) or 0)&1 else raw.split(b'\0')[0].decode('latin1')
@lru_cache(None)
def oname(o): return name(pm.u32(o+0x1C)) if o else '?'
@lru_cache(None)
def cn(o): return oname(pm.u32(o+0x24))
def path(o):
    parts = []
    for _ in range(10):
        if not o: break
        parts.append(oname(o)); o = pm.u32(o+0x18)
    return '.'.join(reversed(parts))
mode = sys.argv[2]
pattern = re.compile(sys.argv[3], re.I)
owner = re.compile(sys.argv[4] if len(sys.argv)>4 else '.*', re.I)
for o in op:
    if not o: continue
    n, c = oname(o), cn(o)
    if mode == 'instances' and pattern.search(c):
        print(hex(o), c, path(o), 'header', pm.read(o, 0x40).hex())
    if mode == 'properties' and c.endswith('Property') and pattern.search(n) and owner.search(oname(pm.u32(o+0x18))):
        packed=pm.u32(o+0x3c)
        print(hex(o), c, path(o), 'offset',hex(packed>>16),'size',packed&65535,'mask',hex(pm.u32(o+0x58)))
    if mode == 'functions' and c=='Function' and pattern.search(n) and owner.search(oname(pm.u32(o+0x18))):
        print(hex(o),path(o),'raw',pm.read(o+0x30,0x60).hex())
    if mode == 'classes' and c=='Class' and pattern.search(n):
        print(hex(o), n, 'raw', pm.read(o+0x28,0x30).hex())
pm.close()
