"""Report FM combining alternatives and repeated fixed-size accuracy trials."""
import json
import math
from pathlib import Path
import random
import statistics
import sys
from task1_sketches import BloomFilter, combine_fm, fm_registers, flajolet_martin, reservoir_sample
from task3_budget import YourFilter

OUT = Path(__file__).parent / 'out'


def analyze():
    rng = random.Random(246)
    # This evaluation alone stores the small verification fixture for ground truth;
    # each sketch itself sees it through a one-pass iterator and retains no items.
    data = [f'k{rng.randrange(20_000)}' for _ in range(120_000)]
    truth = len(set(data))
    registers = fm_registers(iter(data))
    alternatives = {'arithmetic_mean_of_2_to_R': statistics.mean(2.0 ** r for r in registers),
                    'median_of_2_to_R': statistics.median(2.0 ** r for r in registers),
                    'median_of_group_geometric_means_with_max_R_correction': combine_fm(registers)}
    trials = []
    for n in (1000, 20_000, 100_000):
        for seed in range(8):
            estimate = flajolet_martin(range(n), seed=seed)
            trials.append({'distinct': n, 'seed': seed, 'estimate': estimate, 'ratio': estimate/n})
    bf = BloomFilter(8192, 5)
    for i in range(800):
        bf.add(f'item-{i}')
    false_positive = sum(f'other-{i}' in bf for i in range(20_000))
    f = YourFilter(80_000)
    usable = (len(f.bits) - f.SEED_BYTES) * 8
    result = {'bloom': {'predicted_rate': bf.expected_fp_rate(800),
                        'false_positives': false_positive, 'queries': 20_000,
                        'measured_rate': false_positive / 20_000},
              'fm_combining': {'truth': truth, 'registers': registers,
                               'rules': {name: {'estimate': value, 'ratio': value/truth}
                                         for name, value in alternatives.items()}},
              'fm_trials': trials,
              'budget': {'total_retained_bits': f.memory_bits(),
                         'instance_bytes': sys.getsizeof(f), 'buffer_bytes_including_header': sys.getsizeof(f.bits),
                         'seed_bytes_inside_buffer': f.SEED_BYTES, 'usable_bits': usable,
                         'hashes': f.K, 'continuous_k_optimum_at_10_bits': 10 * math.log(2),
                         'bloom_floor_at_10_bits': math.exp(-10 * math.log(2)**2),
                         'predicted_at_effective_bits': (-math.expm1(-f.K * 8000 / usable))**f.K}}
    (OUT / 'sketch-analysis.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps({k: v for k, v in result.items() if k != 'fm_trials'}, indent=2))
    ratios = [row['ratio'] for row in trials]
    print(f'24 independent-count trials: min={min(ratios):.3f}x, max={max(ratios):.3f}x; '
          f'within 2x={sum(0.5 <= r <= 2 for r in ratios)}/{len(ratios)}')


if __name__ == '__main__':
    analyze()
