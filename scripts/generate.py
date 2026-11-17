import argparse, hashlib, json, pathlib, random, struct
from core import make, encode, decode, unique

p=argparse.ArgumentParser()
p.add_argument('--tier',choices=['easy','medium','hard'],required=True)
p.add_argument('--shard',type=int,required=True)
p.add_argument('--count',type=int,default=500)
p.add_argument('--out',default='out')
a=p.parse_args()
out=pathlib.Path(a.out);out.mkdir(parents=True,exist_ok=True)
path=out/f'{a.tier}-{a.shard:03d}.bin'
if path.exists(): raise SystemExit(f'Output exists: {path}')
seen=set(); records=[]
for i in range(a.count):
    # deterministic across workflow retries
    seed=int.from_bytes(hashlib.sha256(f'v1:{a.tier}:{a.shard}:{i}'.encode()).digest()[:8],'big')
    for retry in range(50):
        puzzle,answer,clues=make(seed+retry*1000000007,a.tier)
        record=encode(puzzle,answer)
        digest=hashlib.sha256(record).digest()
        if digest not in seen: break
    else: raise RuntimeError('Duplicate record retry limit')
    seen.add(digest)
    assert decode(record)==(puzzle,answer)
    # make() has already checked uniqueness after each successful clue removal.
    records.append(record)
    if (i+1)%25==0: print(f'{a.tier} shard {a.shard}: {i+1}/{a.count}',flush=True)
path.write_bytes(b'S16P'+struct.pack('<I',len(records))+b''.join(records))
print(path, path.stat().st_size)
