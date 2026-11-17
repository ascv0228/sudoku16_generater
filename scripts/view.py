
import argparse
from pathlib import Path

SYMBOLS = "0123456789ABCDEF"

def unpack_solution(data):
    values = []
    for b in data:
        values.append(b >> 4)
        values.append(b & 0x0F)
    return values

def show_grid(solution, mask, show_answer=False):
    for r in range(16):
        if r > 0 and r % 4 == 0:
            print("-" * 41)

        row = []
        for c in range(16):
            i = r * 16 + c
            visible = show_answer or bool(mask[i // 8] & (1 << (7 - i % 8)))
            row.append(SYMBOLS[solution[i]] if visible else ".")

        print(" | ".join(" ".join(row[i:i+4]) for i in range(0, 16, 4)))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("file")
    args = parser.parse_args()

    data = Path(args.file).read_bytes()
    header = data[:8]
    payload = data[8:]

    if len(payload) % 160 != 0:
        raise ValueError("Invalid file size")

    print("Header:", header.hex())
    print("Puzzles:", len(payload) // 160)

    for n in range(len(payload) // 160):
        block = payload[n*160:(n+1)*160]
        solution = unpack_solution(block[:128])
        mask = block[128:160]

        print(f"\n{'=' * 50}")
        print(f"Puzzle {n+1}")
        show_grid(solution, mask)

        print("\nSolution:")
        show_grid(solution, mask, show_answer=True)

if __name__ == "__main__":
    main()
