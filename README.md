# Sudoku 16×16 offline dataset generator

Creates 60,000 unique-solution 16×16 puzzles (15k easy, 15k medium, 30k hard) and publishes three binary files plus SHA-256 manifest in GitHub Releases.

## Important caveats

- Difficulty is **clue-count proxy**, NOT measured human solving difficulty: easy 176–192, medium 144–160, hard 112–128 clues. A real technique-based difficulty evaluator is a separate future feature.
- Generation is computationally expensive. 120 matrix jobs of 500 puzzles each may take longer than GitHub-hosted job limits. Benchmark before running the full workflow, and consider self-hosted runners, persistent shard caching, or splitting into separate runs.
- The solver proves uniqueness by asserting Sudoku rules, given clues, and at least one cell different from the stored solution. UNSAT means unique. Solver `unknown` is treated as failure.
- Generated puzzles are derived from a randomized canonical Latin Sudoku grid, so despite distinct records some puzzles may be structurally isomorphic. There is no global isomorphism deduplication.
- Release manifests are SHA-256 integrity checks, not authenticity guarantees. Use a trusted GitHub owner/repo and pinned release tag, or add a signature for stronger security.

## Local smoke test

```bash
python -m pip install -r requirements.txt
python scripts/generate.py --tier easy --shard 0 --count 2 --out test-shards
```

## Publish

Push to your repository, then Actions → Build and publish Sudoku 16x16 dataset → Run workflow with a new immutable tag such as `dataset-v1`. On success, Release contains `easy.bin`, `medium.bin`, `hard.bin`, and `manifest.json`.

## Binary format

Each `.bin` has `S16P` ASCII magic (4 bytes), little-endian unsigned record count (4 bytes), followed by 160-byte records. Each record stores 128 bytes of answer nibbles (0–15) and a 32-byte clue mask (bit `i%8` of byte `i//8`, 1 means given). Each record therefore reconstructs both the puzzle and answer. Files total ~9.6 MB excluding the 24-byte headers, before compression.

## Android update

See `android/DatasetUpdater.kt`. Run on a background dispatcher, use `dataset-v1` (or a newer explicit tag) and compare local SHA-256 to manifest. The updater skips unchanged files, downloads changed files, verifies hashes and then replaces files. This example does not implement automatic discovery of latest releases, cryptographic manifest signing, resumable downloads, or a database import.
