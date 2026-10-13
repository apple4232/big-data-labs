"""One-pass, packed-hash correctness, and full retained-memory checks."""
import hashlib
import sys
import unittest
from unittest.mock import patch
from task1_sketches import BloomFilter, fm_registers, flajolet_martin, reservoir_sample
from task3_budget import YourFilter


class Once:
    def __init__(self, values):
        self.values = values
        self.used = False

    def __iter__(self):
        if self.used:
            raise AssertionError('stream iterated twice')
        self.used = True
        yield from self.values


class SketchTests(unittest.TestCase):
    def test_bloom_padding_duplicates_and_no_false_negatives(self):
        bf = BloomFilter(19, 3)
        for item in range(50):
            bf.add(item)
            bf.add(item)
        self.assertTrue(all(item in bf for item in range(50)))
        self.assertEqual(len(bf.bits), 3)
        self.assertEqual(bf.expected_fp_rate(0), 0)

    def test_invalid_sizes(self):
        with self.assertRaises(ValueError):
            BloomFilter(0, 3)
        with self.assertRaises(ValueError):
            reservoir_sample(range(5), -1)
        with self.assertRaises(ValueError):
            flajolet_martin(range(5), n_hashes=0)

    def test_packed_maxima_equal_independent_scalar_oracle(self):
        for count in (1, 3, 8, 64):
            expected = [0] * count
            for item in range(600):
                digest = hashlib.shake_256(b'fm:246\0' + str(item).encode()).digest(8 * count)
                for lane in range(count):
                    value = int.from_bytes(digest[8*lane:8*lane+8], 'little')
                    trailing = (value & -value).bit_length()-1 if value else 64
                    expected[lane] = max(expected[lane], trailing)
            self.assertEqual(fm_registers(Once(range(600)), count), expected)

    def test_packed_zero_and_high_bit_boundaries(self):
        values = (1, 0, 1 << 63, 2)
        raw = b''.join(value.to_bytes(8, 'little') for value in values)
        with patch('hashlib.shake_256') as shake:
            shake.return_value.digest.return_value = raw
            self.assertEqual(fm_registers(['item'], 4), [0, 64, 63, 1])

    def test_empty_and_duplicate_streams(self):
        self.assertEqual(flajolet_martin(iter(())), 0)
        self.assertEqual(fm_registers(['a'] * 1000), fm_registers(['a']))

    def test_reservoir_unknown_length_and_short_stream(self):
        self.assertEqual(reservoir_sample(Once(range(3)), 5), [0, 1, 2])
        sample = reservoir_sample(Once(range(1000)), 17)
        self.assertEqual(len(sample), 17)
        self.assertEqual(len(set(sample)), 17)
        self.assertTrue(all(0 <= value < 1000 for value in sample))
        self.assertEqual(reservoir_sample(range(4), 0), [])

    def test_full_budget_independently_counts_all_owned_state(self):
        for budget in (1600, 79999, 80000):
            f = YourFilter(budget)
            self.assertFalse(hasattr(f, '__dict__'))
            owned = sys.getsizeof(f) + sys.getsizeof(f.bits)
            self.assertEqual(f.memory_bits(), 8 * owned)
            self.assertLessEqual(8 * owned, budget)
            before = owned
            seed = bytes(f.bits[:8])
            for item in range(1000):
                f.add(item)
            self.assertEqual(bytes(f.bits[:8]), seed)
            self.assertTrue(all(item in f for item in range(1000)))
            self.assertEqual(sys.getsizeof(f) + sys.getsizeof(f.bits), before)


if __name__ == '__main__':
    unittest.main(verbosity=2)
