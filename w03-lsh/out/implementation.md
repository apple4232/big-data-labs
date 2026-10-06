# Implementation and reproducibility notes

Source: https://github.com/codingchild2424/2026-lecture-bigdata-practice
Source revision: 849281e44e483188cc59f199d90267381dc13ead (main observed 2026-10-06).

## Task 1

Jaccard returns zero for an empty union. MinHash first indexes nonzero row membership, then scans the row range once. Each occupied row is hashed once for each hash function and updates all its owning columns. It does not sort rows or scan the matrix separately for each column. The membership index uses O(nonzero entries) memory; this API already supplies resident column sets, so this is not a disk streaming implementation.

Banding uses tuple keys scoped to each band, de-duplicates pairs, and returns i < j. Nonpositive band counts, uneven division, zero-length signatures, and unequal signature lengths raise ValueError. Empty columns retain infinity signatures and are excluded from candidates; their Jaccard similarity is zero. This explicit rejection policy prevents silently discarding leftover hashes.

## Task 2

The supplied loop used `bench.build()[:n]`, but that generator returns only 2,120 documents. Requested sizes above 2,120 would therefore record misleading n values and identical work. Only the measurement script was repaired: `build_sized(n)` generates exactly n documents using seed 246, 60 shingles, vocabulary 5,000, and approximately 120/2,120 planted clones, following the original mutation process. The recorded n is the actual length and brute_calls must equal n(n-1)/2. Results are saved after each completed size.

Wall time uses perf_counter with tracemalloc active for both methods. Peak memory is Python allocation peak during find, excluding the already-generated input; it is not whole-process resident memory. CPU and physical RAM are obtained from Windows. Codex and its browser remain open; background load is not experimentally controlled. These are measurements on this Windows computer, rather than copied reference times.

## Task 3

120 seeded affine hashes modulo 2,147,483,647 and 40 bands of 3 rows generate candidates. Shingles are mapped to dense row IDs, allowing the sparse Task 1 implementation to be reused. Each candidate is checked once with the supplied counted similarity function. Hash count and band count can be adjusted on a finder instance for the recorded sensitivity experiment. Affine hashes are a practical approximation to independent random permutations; the S-curve probabilities are theoretical guidance, not guarantees for a fixed seed.

`bench.py`, `test_tasks.py`, and the repository's `check.py` are unchanged. Existing Week 5 files are preserved.

Reproduce from this directory:

```text
python task1_minhash.py --verify
python task2_crossover.py --sizes 125,250,500,1000,2000,4000
python bench.py --yours
python test_tasks.py
python ../check.py w03
```

The timing script appends new runs; repeated execution preserves earlier measurements.
