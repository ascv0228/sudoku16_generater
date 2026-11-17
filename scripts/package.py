import argparse, hashlib, json, pathlib, struct, zipfile
from core import decode, unique
p=argparse.ArgumentParser();p.add_argument('--input',default='shards');p.add_argument('--out',default='release');p.add_argument('--version',default='v1');p.add_argument('--recheck',action='store_true');a=p.parse_args()
src=pathlib.Path(a.input);dst=pathlib.Path(a.out);dst.mkdir(parents=True,exist_ok=True)
expected={'easy':15000,'medium':15000,'hard':30000}
files=[]
for tier,total in expected.items():
    chunks=sorted(src.glob(f'{tier}-*.bin'))
    if not chunks: raise RuntimeError(f'Missing {tier} shards')
    records=[]
    for f in chunks:
        data=f.read_bytes()
        if data[:4]!=b'S16P': raise ValueError(f'Invalid magic: {f}')
        n=struct.unpack('<I',data[4:8])[0]
        if len(data)!=8+160*n: raise ValueError(f'Invalid length: {f}')
        records.extend(data[8+i*160:8+(i+1)*160] for i in range(n))
    if len(records)!=total: raise RuntimeError(f'{tier}: expected {total}, got {len(records)}')
    if len(set(records))!=total: raise RuntimeError(f'{tier}: duplicate puzzles')
    for i,record in enumerate(records):
        puzzle,answer=decode(record)
        if any(v!=255 and v!=answer[j] for j,v in enumerate(puzzle)): raise ValueError('Bad puzzle')
        if a.recheck and not unique(puzzle,answer): raise ValueError(f'Non-unique {tier} #{i}')
    payload=b'S16P'+struct.pack('<I',total)+b''.join(records)
    name=f'{tier}.bin';(dst/name).write_bytes(payload)
    files.append({'name':name,'count':total,'bytes':len(payload),'sha256':hashlib.sha256(payload).hexdigest()})
manifest={'schema':1,'version':a.version,'boardSize':16,'recordBytes':160,'format':'S16P-v1','files':files}
(dst/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
print(json.dumps(manifest,indent=2))
