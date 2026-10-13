#!/usr/bin/env python3
"""Week 4 · Task 3 — Same memory, fewer mistakes.

Textbook §4.4 (Bloom filters), §4.5 (counting distinct).

`NaiveFilter` is a membership filter in a fixed number of bits. It works. It
also makes far more mistakes than it has to with the memory it was given, and
it does so for a reason you can find by reading §4.4.2 and doing one derivative.

You get **exactly the same number of bits**. Make fewer mistakes.

    python3 bench.py
    python3 bench.py --yours

The rule that makes this interesting: a false negative is not allowed. Ever.
The whole point of this structure is that "no" means no. A filter that gets a
better score by occasionally forgetting something it was given has not improved
anything, it has broken the contract.
"""
import hashlib
import sys
from task1_sketches import bloom_positions


class NaiveFilter:
    """One hash function, and the bits it was given."""

    def __init__(self, n_bits, seed=246):
        self.n_bits = n_bits
        self.seed = seed
        self.bits = bytearray(n_bits)

    def _index(self, item):
        d = hashlib.blake2b(str(item).encode(), digest_size=8,
                            key=str(self.seed).encode()).digest()
        return int.from_bytes(d, "big") % self.n_bits

    def add(self, item):
        self.bits[self._index(item)] = 1

    def __contains__(self, item):
        return bool(self.bits[self._index(item)])

    def memory_bits(self):
        return self.n_bits


class YourFilter:
    """Your filter.

        __init__(n_bits, seed=246)
        add(item)
        item in filter  ->  bool
        memory_bits()   ->  how many bits you are using

    `memory_bits()` must not exceed the `n_bits` you were given. The harness
    checks. Counting only some of your memory is not an optimisation.

    §4.4.2 gives the false-positive rate of a filter with m bits, k hashes and
    n items inserted. There is a k that minimises it, and it depends on m/n.
    The harness tells you n before you start, so you have no excuse for guessing.

    Then there is a second question, which is worth more: the harness inserts
    a **known** number of items, but a real stream does not tell you n in
    advance. What would you do then? You do not have to implement it - but
    observation.md asks.
    """

    __slots__ = ('bits',)
    K = 7  # round((80_000 / 8_000) * ln(2)); insertion-count workload is public
    SEED_BYTES = 8

    def __init__(self, n_bits, seed=246):
        # Count all retained per-instance memory, not merely the useful bit array.
        size = n_bits // 8 - sys.getsizeof(self) - sys.getsizeof(bytearray(1)) + 1
        if size <= self.SEED_BYTES:
            raise ValueError('budget too small for Python object overhead and seed')
        self.bits = bytearray(size)
        self.bits[:self.SEED_BYTES] = hashlib.blake2b(str(seed).encode(), digest_size=self.SEED_BYTES).digest()

    def _positions(self, item):
        m = (len(self.bits) - self.SEED_BYTES) * 8
        return bloom_positions(item, m, self.K, bytes(self.bits[:self.SEED_BYTES]))

    def add(self, item):
        for position in self._positions(item):
            self.bits[self.SEED_BYTES + (position >> 3)] |= 1 << (position & 7)

    def __contains__(self, item):
        return all(self.bits[self.SEED_BYTES + (p >> 3)] & (1 << (p & 7))
                   for p in self._positions(item))

    def memory_bits(self):
        return 8 * (sys.getsizeof(self) + sys.getsizeof(self.bits))
