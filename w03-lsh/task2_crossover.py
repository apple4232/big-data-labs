#!/usr/bin/env python3
"""Week 3 · Task 2 — Find the crossover on your own machine.

Textbook §3.4.

Everybody knows brute force is quadratic and LSH is not. That is not the
interesting question. The interesting question is **where, on the machine in
front of you, does it start to matter** - and that answer is yours alone. It
depends on your CPU, your memory, and how big your shingle sets are.

This script gives you the timing loop. The two methods are yours: import them
from Task 1 and Task 3.

    python3 task2_crossover.py --sizes 500,1000,2000,4000
    python3 task2_crossover.py --sizes 8000,16000          # keep going

Write down where it hurts. That is the deliverable.
"""
import argparse, json, os, platform, time, tracemalloc, random

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")


def machine():
    info = {
        "platform": platform.platform(),
        "processor": platform.processor() or platform.machine(),
        "python": platform.python_version(),
        "background_activity": "Codex and its browser were open; other background load was not controlled.",
        "measurement": "perf_counter wall time with tracemalloc; peak excludes prebuilt input documents and process RSS",
    }
    if os.name == "nt":
        import ctypes, winreg
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                           r"HARDWARE\DESCRIPTION\System\CentralProcessor\0") as key:
            info["processor"] = winreg.QueryValueEx(key, "ProcessorNameString")[0].strip()
        class MemoryStatus(ctypes.Structure):
            _fields_ = [("length", ctypes.c_ulong), ("load", ctypes.c_ulong)] + [
                (name, ctypes.c_ulonglong) for name in (
                    "total", "available", "page_total", "page_available",
                    "virtual_total", "virtual_available", "extended")]
        status = MemoryStatus()
        status.length = ctypes.sizeof(status)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
            info.update(ram_bytes=status.total, available_ram_bytes=status.available,
                        memory_load_percent=status.load)
    return info


def build_sized(n):
    """Generate exactly n documents; bench.build() is capped at 2,120.

    Use the same seed, shingle counts, vocabulary, and mutation process.
    About 120/2120 of the total documents are planted clones.
    """
    import bench
    if n < 1:
        raise ValueError("document count must be positive")
    rng = random.Random(bench.SEED)
    planted = round(n * bench.PLANTED / (bench.N_DOCS + bench.PLANTED))
    base = n - planted
    docs = [set(rng.sample(range(bench.VOCAB), bench.SHINGLES)) for _ in range(base)]
    for _ in range(planted):
        clone = set(docs[rng.randrange(base)])
        for _ in range(rng.randint(4, 14)):
            clone.discard(rng.choice(list(clone)))
            clone.add(rng.randrange(bench.VOCAB))
        docs.append(clone)
    rng.shuffle(docs)
    assert len(docs) == n
    return docs


def timed(fn, *args):
    """Wall time and peak memory of one call."""
    tracemalloc.start()
    t0 = time.perf_counter()
    result = fn(*args)
    elapsed = time.perf_counter() - t0
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return result, elapsed, peak


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--sizes", default="250,500,1000,2000",
                   help="comma-separated document counts to try")
    p.add_argument("--threshold", type=float, default=0.6)
    a = p.parse_args()
    os.makedirs(OUT, exist_ok=True)

    import bench
    from task3_scale import BruteForce
    try:
        from task3_scale import YourFinder
    except Exception:
        YourFinder = None

    for n in [int(x) for x in a.sizes.split(",")]:
        docs = build_sized(n)
        sim = bench.Counter()
        found_brute, t_brute, m_brute = timed(BruteForce(a.threshold).find, docs, sim)
        c_brute = sim.calls

        row = {"n": len(docs), "threshold": a.threshold, "brute_pairs": len(found_brute), "brute_s": t_brute, "brute_calls": c_brute,
               "brute_peak_bytes": m_brute}

        if YourFinder is not None:
            sim2 = bench.Counter()
            try:
                found_lsh, t_lsh, m_lsh = timed(YourFinder(a.threshold).find, docs, sim2)
                row.update({"lsh_pairs": len(found_lsh), "lsh_recall": len(found_lsh & found_brute) / len(found_brute) if found_brute else 1.0, "lsh_s": t_lsh, "lsh_calls": sim2.calls,
                            "lsh_peak_bytes": m_lsh})
            except NotImplementedError:
                pass

        line = f"  n={n:>6}  brute {t_brute:>8.2f}s  {c_brute:>12,} cmp"
        if "lsh_s" in row:
            line += f"   |  lsh {row['lsh_s']:>7.2f}s  {row['lsh_calls']:>9,} cmp"
        print(line, flush=True)
        path = os.path.join(OUT, "crossover.json")
        prior = json.load(open(path)) if os.path.exists(path) else {"runs": []}
        prior["machine"] = machine()
        prior["runs"].append(row)
        with open(path, "w") as output:
            json.dump(prior, output, indent=2)

    path = os.path.join(OUT, "crossover.json")
    prior = json.load(open(path)) if os.path.exists(path) else {"runs": []}
    print(f"\n  -> out/crossover.json  ({len(prior['runs'])} measurement(s))")
    print("  Keep raising --sizes until something becomes unpleasant. Record where.")


if __name__ == "__main__":
    main()
