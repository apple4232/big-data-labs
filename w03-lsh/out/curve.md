# Task 2: measured crossover

Measured on 2026-10-06, Intel(R) Core(TM) i7-9750H CPU @ 2.60GHz, 15.85 GiB usable physical RAM, Windows-11-10.0.26200-SP0, Python 3.12.2.
Codex and its browser were open; other background load was not controlled.
Times include tracemalloc overhead for both methods. One run per size, not repeated medians; system memory pressure and background load can cause variation.

| Actual documents | Brute seconds | LSH seconds | Brute comparisons | LSH comparisons | Brute peak MiB | LSH peak MiB | LSH recall |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 125 | 0.0922 | 2.1406 | 7,750 | 11 | 0.0075 | 1.6032 | 100.0% |
| 250 | 0.5658 | 3.5053 | 31,125 | 17 | 0.0078 | 2.2918 | 100.0% |
| 500 | 1.8654 | 4.9834 | 124,750 | 31 | 0.0099 | 3.5546 | 100.0% |
| 1,000 | 8.2636 | 5.2272 | 499,500 | 82 | 0.0117 | 5.6339 | 100.0% |
| 2,000 | 31.8984 | 7.9133 | 1,999,000 | 221 | 0.0207 | 9.4589 | 100.0% |
| 4,000 | 129.2005 | 13.1198 | 7,998,000 | 694 | 0.0280 | 16.9890 | 100.0% |

## Quadratic check (A4)

| Doubling n | Time multiplier (expected about 4) | Comparison multiplier |
|---|---:|---:|
| 125 -> 250 | 6.137x | 4.0161x |
| 250 -> 500 | 3.297x | 4.0080x |
| 500 -> 1000 | 4.430x | 4.0040x |
| 1000 -> 2000 | 3.860x | 4.0020x |
| 2000 -> 4000 | 4.050x | 4.0010x |

The endpoint empirical exponent is 2.091 (quadratic is 2). Comparison counts exactly equal n(n-1)/2 at every size; the underlying work is quadratic. The observed time multipliers are not all exactly 4: short runs, background activity, allocation tracing, and high system memory pressure affect the constant factors. These are possible explanations, not separately measured causes. The 1,000 -> 2,000 result is especially close to 4; I retain the irregular points rather than claiming perfectly smooth timing.

## Crossover and cost (A7-A8)

The sampled crossover is between 500 and 1000 documents: brute/LSH are 1.865/4.983s at the lower size and 8.264/5.227s at the upper size. The exact crossover inside that interval was not measured.
LSH pays to collect and remap the shingle universe, build the nonzero row index, evaluate 120 hashes per occupied row, update document signatures, and create 40 band keys per document. At small n, those costs exceed checking the few n(n-1)/2 pairs. The shared vocabulary saturates near 5,000 shingles, so row hashing is shared across documents and is not strictly a fresh 120-hash computation for every shingle in every document.

## Where it became unpleasant and memory (A2, A5-A6)

At n=4,000, brute force took 129.20s and LSH 13.12s. This is the first sampled brute-force run above a minute; I stopped increasing n after completing both methods at this size. Waiting time was the stopping criterion; no out-of-memory failure was observed.
At that size, brute-force peak was 29,352 bytes (0.0280 MiB), versus LSH 17,814,228 bytes (16.9890 MiB). These are peak traced Python allocations inside find, excluding already-built document sets, process RSS, and other applications. Brute force retains almost no intermediate state; LSH trades extra signature/index/bucket memory for far fewer comparisons.
The final Windows snapshot reports 97% system memory load and 327.7 MiB available RAM. System pressure was already high before large-size measurement; I do not attribute it solely to this algorithm.

## Generator correction

The original `bench.build()[:n]` silently capped input at 2,120. `task2_crossover.py` now generates exactly the requested number, preserving seed, vocabulary, set size, clone fraction, and mutation process. See `implementation.md`. The official Task 3 harness is untouched. Raw measurements are in `crossover.json`; all completed rows were saved incrementally.
