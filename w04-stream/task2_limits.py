#!/usr/bin/env python3
"""Week 4 · Task 2 — Find the size where exact stops being possible.

Textbook §4.1 (the stream model), §4.4, §4.5.

Sketches exist because the exact answer does not fit. That sentence is easy to
agree with and hard to feel, so this task makes you watch it happen on your own
machine: hold every distinct item in a set, keep raising the stream size, and
record where your laptop stops coping.

    python3 task2_limits.py --sizes 100000,400000,1600000
    python3 task2_limits.py --sizes 6400000            # keep going

Your numbers will not match anybody else's. That is the point.
"""
import argparse, json, os, platform, time, tracemalloc


HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")


def machine():
    info = {"platform": platform.platform(),
            "processor": platform.processor() or platform.machine(),
            "python": platform.python_version()}
    context = os.path.join(OUT, 'machine-context.json')
    if os.path.exists(context):
        with open(context, encoding='utf-8-sig') as f:
            info.update(json.load(f))
    return info


def stream(n, distinct_ratio=0.4, seed=246):
    """A stream of n items with about n*distinct_ratio distinct values."""
    import random
    rng = random.Random(seed)
    span = max(1, int(n * distinct_ratio))
    for _ in range(n):
        yield f"key-{rng.randrange(span)}"


class MeasurementStopped(RuntimeError):
    def __init__(self, details):
        self.details = details
        super().__init__(details['stop_reason'])


def exact_distinct(n, time_limit=None, memory_limit=None):
    """The honest answer: hold every distinct item."""
    tracemalloc.start()
    t0 = time.perf_counter()
    seen = set()
    for processed, x in enumerate(stream(n), 1):
        seen.add(x)
        if processed % 100_000 == 0 and (time_limit or memory_limit):
            elapsed = time.perf_counter() - t0
            _, peak = tracemalloc.get_traced_memory()
            reason = ('predeclared wall-time limit' if time_limit and elapsed >= time_limit else
                      'predeclared traced-memory limit' if memory_limit and peak >= memory_limit else None)
            if reason:
                details = {'status': 'stopped', 'stop_reason': reason,
                           'items_processed': processed, 'partial_distinct': len(seen),
                           'exact_s': elapsed, 'exact_peak_bytes': peak,
                           'time_limit_s': time_limit, 'memory_limit_bytes': memory_limit}
                tracemalloc.stop()
                raise MeasurementStopped(details)
    elapsed = time.perf_counter() - t0
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return len(seen), elapsed, peak


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--sizes", default="100000,400000,1600000")
    p.add_argument('--exact-time-limit', type=float, default=None,
                   help='optional practical stopping boundary; stopped runs are never reported as completed')
    p.add_argument('--max-exact-mib', type=float, default=None,
                   help='optional traced-memory stopping boundary')
    a = p.parse_args()
    os.makedirs(OUT, exist_ok=True)

    try:
        from task1_sketches import flajolet_martin
    except Exception:
        flajolet_martin = None

    path = os.path.join(OUT, "limits.json")
    if os.path.exists(path):
        with open(path, encoding='utf-8') as f:
            prior = json.load(f)
    else:
        prior = {'runs': []}
    prior['machine'] = machine()

    def save(row):
        prior['runs'].append(row)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(prior, f, indent=2)

    for n in [int(x) for x in a.sizes.split(",")]:
        if n <= 0:
            raise ValueError('stream sizes must be positive')
        print(f'  Starting exact n={n:,}', flush=True)
        try:
            true, t_exact, m_exact = exact_distinct(n, a.exact_time_limit,
                                                  a.max_exact_mib * 1024**2 if a.max_exact_mib else None)
        except MeasurementStopped as exc:
            row = dict(n=n, true_distinct=None, **exc.details)
            save(row)
            print(f"  STOPPED n={n:,}: {row['stop_reason']}; processed={row['items_processed']:,}, "
                  f"time={row['exact_s']:.2f}s, traced peak={row['exact_peak_bytes']/1e6:.1f} MB", flush=True)
            continue
        row = {"n": n, "true_distinct": true, "exact_s": t_exact,
               "exact_peak_bytes": m_exact, 'status': 'completed'}

        if flajolet_martin is not None:
            try:
                tracemalloc.start()
                t0 = time.perf_counter()
                print(f'  Starting FM n={n:,} (exact {t_exact:.2f}s, {m_exact/1e6:.1f} MB)', flush=True)
                est = flajolet_martin(stream(n))
                t_fm = time.perf_counter() - t0
                _, m_fm = tracemalloc.get_traced_memory()
                tracemalloc.stop()
                row.update({"fm_estimate": est, "fm_s": t_fm,
                            "fm_peak_bytes": m_fm,
                            "fm_ratio": est / true if true else None})
            except NotImplementedError:
                tracemalloc.stop()

        save(row)
        line = (f"  n={n:>10,}  distinct {true:>9,}   exact {t_exact:>7.2f}s "
                f"{m_exact / 1e6:>8.1f} MB")
        if "fm_s" in row:
            line += (f"   |  fm {row['fm_s']:>7.2f}s {row['fm_peak_bytes'] / 1e6:>6.2f} MB"
                     f"  {row['fm_ratio']:.2f}x")
        print(line, flush=True)

    print(f"\n  -> out/limits.json  ({len(prior['runs'])} measurement(s))")
    print("  Keep raising --sizes until the exact version is unbearable. "
          "Record where, and what ran out.")


if __name__ == "__main__":
    main()
