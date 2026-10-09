"""Read-only registry discovery for the installed Origins executable."""
import sys, struct
import pefile
from ue3_inspect import ProcessMemory

pm = ProcessMemory(int(sys.argv[1]))
pe = pefile.PE(r'C:\Program Files (x86)\Steam\steamapps\common\Batman Arkham Origins\SinglePlayer\Binaries\Win32\BatmanOrigins.exe')
base = pe.OPTIONAL_HEADER.ImageBase
raw = bytearray(pe.OPTIONAL_HEADER.SizeOfImage)
for address, size, *_ in pm.regions():
    lo, hi = max(address, base), min(address + size, base + len(raw))
    if lo < hi:
        chunk = pm.read(lo, hi-lo)
        raw[lo-base:lo-base+len(chunk)] = chunk
print('BASE', hex(base), 'SIZE', hex(len(raw)), flush=True)
for i in range(0, len(raw)-12, 4):
    data, count, maximum = struct.unpack_from('<Iii', raw, i)
    if not (5000 < count <= maximum < 500000 and data > 0x10000):
        continue
    sample = pm.read(data, 32)
    if len(sample) != 32:
        continue
    ptrs = struct.unpack('<8I', sample)
    for off in (8, 12, 16):
        vals = [pm.read(a+off, 32).split(b'\0')[0] for a in ptrs[:4] if a]
        if vals and (vals[0] == b'None' or pm.read(ptrs[0]+off, 10) == b'N\0o\0n\0e\0\0\0'):
            print('NAMES', hex(base+i), hex(data), count, 'offset', off, vals, flush=True)
    vals = [pm.read(a, 48) for a in ptrs if a]
    if len(vals) > 4 and all(len(v)==48 and base <= struct.unpack_from('<I', v)[0] < base+len(raw) for v in vals):
        print('OBJECTS', hex(base+i), hex(data), count, 'first', [(hex(a),v.hex()) for a,v in zip(ptrs,vals)][:2], flush=True)
pm.close()
