"""Measure recall when the S-curve step moves above the threshold."""
import json
import time
from pathlib import Path
import bench
from task3_scale import YourFinder


def main():
    docs = bench.build()
    true_pairs = bench.truth(docs)
    rows = []
    for bands in (40, 30, 10):
        finder = YourFinder(bench.THRESHOLD)
        finder.bands = bands
        counter = bench.Counter()
        start = time.perf_counter()
        found = finder.find(docs, counter)
        r = finder.hash_count // bands
        rows.append({
            "hashes": finder.hash_count, "bands": bands, "rows": r,
            "step": (1 / bands) ** (1 / r),
            "candidate_probability_at_0.6": 1 - (1 - .6 ** r) ** bands,
            "true_pairs": len(true_pairs), "found_pairs": len(found),
            "recall": len(found & true_pairs) / len(true_pairs),
            "comparisons": counter.calls, "seconds": time.perf_counter() - start,
        })
        print(json.dumps(rows[-1]), flush=True)
    path = Path(__file__).parent / 'out' / 'sensitivity.json'
    path.write_text(json.dumps(rows, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
