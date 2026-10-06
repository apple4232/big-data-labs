# Week 3 observations

## Task 1
I index nonzero row membership and scan the rows once, so each occupied row's hashes are reused        across every column containing it; this avoids repeated column scans, while still requiring O(nonzeros) index memory with the supplied resident-set API.
I reject a signature length not divisible by the positive band count with ValueError, rather than drop leftover hashes or create unequal bands.
S1-S4 has estimated similarity 1.0 with two hashes but exact Jaccard 2/3; more independent hashes reduce sampling error (roughly O(1/sqrt(k))) at the cost of signature memory and hash/update work.

## Task 2
On this Intel i7-9750H / 15.85 GiB Windows computer, the measured crossover is bracketed by 500-1000 documents; Codex and its browser were open, background load was uncontrolled, and times include allocation tracing.
For 1,000 -> 2,000 documents, brute force grew 3.860x, close to 4; exact n(n-1)/2 counts and endpoint exponent 2.091 support quadratic work despite noisy short-run timings (see curve.md).
At 4,000 documents brute force took 129.20s, crossing the one-minute stopping criterion; LSH took 13.12s, with traced peaks 0.0280/16.9890 MiB (input and process RSS excluded), and no observed OOM.

## Task 3
I chose k=120 hashes, b=40 bands, r=3: the step (1/40)^(1/3)=0.2924 lies below 0.6, giving P(candidate|s=0.6)=1-(1-0.6^3)^40=0.999941; extra candidates buy recall, then exact Jaccard removes false positives. The official harness found all 121 pairs with 248 comparisons rather than 2,246,140 (99.98896% avoided), recall/precision 100%.
With the same 120 hashes but b=10, r=12, the step rises to 0.8254 and P(0.6) falls to 0.021556; measured recall fell to 32.23% (39/121), versus 100.00% for b=40; b=30 gave 98.35%. See sensitivity.json for the actual experiment.
Free hashing is a comparison-count scoring rule, not free runtime: below the measured crossover its setup already loses; with larger vocabularies or long documents, 120-hash work, signature memory, indexing, and bucket traffic can dominate even when comparisons are scarce.
