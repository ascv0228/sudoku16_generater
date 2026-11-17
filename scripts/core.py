import hashlib, random, struct
from z3 import Int, Solver, Distinct, Or, sat, unsat

N=16
MAGIC=b'S16P'

def solved(rng):
    base=4
    rows=[g*4+r for g in rng.sample(range(4),4) for r in rng.sample(range(4),4)]
    cols=[g*4+c for g in rng.sample(range(4),4) for c in rng.sample(range(4),4)]
    digits=rng.sample(range(16),16)
    return bytes(digits[(4*(rows[i]%4)+rows[i]//4+cols[j])%16] for i in range(16) for j in range(16))

def unique(puzzle, solution):
    # The known complete solution is excluded: UNSAT proves uniqueness.
    x=[[Int(f'x_{r}_{c}') for c in range(16)] for r in range(16)]
    s=Solver()
    for r in range(16):
        for c in range(16):
            s.add(x[r][c]>=0,x[r][c]<16)
        s.add(Distinct(x[r]))
    for c in range(16): s.add(Distinct([x[r][c] for r in range(16)]))
    for br in range(0,16,4):
        for bc in range(0,16,4):
            s.add(Distinct([x[r][c] for r in range(br,br+4) for c in range(bc,bc+4)]))
    for i,v in enumerate(puzzle):
        if v!=255: s.add(x[i//16][i%16]==v)
    s.add(Or([x[i//16][i%16]!=solution[i] for i in range(256)]))
    return s.check()==unsat

def make(seed, tier, max_attempts=20):
    rng=random.Random(seed)
    # Heuristic clue bands, NOT a logical-solving difficulty rating.
    bands={'easy':(176,192),'medium':(144,160),'hard':(112,128)}
    lo,hi=bands[tier]
    for _ in range(max_attempts):
        answer=solved(rng)
        puzzle=bytearray(answer)
        order=list(range(256));rng.shuffle(order)
        target=rng.randint(lo,hi)
        # Removing a clue preserves uniqueness only if a second solution is impossible.
        for idx in order:
            if sum(v!=255 for v in puzzle)<=target: break
            old=puzzle[idx];puzzle[idx]=255
            if not unique(puzzle,answer): puzzle[idx]=old
        clues=sum(v!=255 for v in puzzle)
        if lo<=clues<=hi:
            return bytes(puzzle),answer,clues
    raise RuntimeError(f'Could not reach {tier} clue band; retry with a different seed')

def encode(puzzle,answer):
    # 128 bytes solution nibbles + 32 bytes clue bitset = 160 bytes/record
    packed=bytes((answer[i]<<4)|answer[i+1] for i in range(0,256,2))
    mask=bytearray(32)
    for i,v in enumerate(puzzle):
        if v!=255: mask[i//8]|=1<<(i%8)
    return packed+bytes(mask)

def decode(blob):
    assert len(blob)==160
    answer=bytes(v for b in blob[:128] for v in (b>>4,b&15))
    mask=blob[128:]
    puzzle=bytes(answer[i] if mask[i//8]&(1<<(i%8)) else 255 for i in range(256))
    return puzzle,answer
