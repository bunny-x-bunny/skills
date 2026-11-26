"""The measurement harness of a miniature research project: hash tables with open addressing,
linear probing against Robin Hood hashing. It stands in for whatever your project measures with.

    python harness.py overview    counts for the figure -> out/overview.json  (exact, the same on every run)
    python harness.py bench       wall-clock times      -> logs/bench.txt     (differ from run to run: kept as a log)

The split is the point. What can be counted is recomputed whenever the figure is built, so the
figure cannot drift from the code. What must be timed is measured once, kept as a raw log, and read
from there, so the figure is the same on every machine.
"""
import json
import os
import platform
import statistics
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
MASK = (1 << 64) - 1
GOLDEN = 0x9E3779B97F4A7C15          # Fibonacci hashing: the top bits of key * 2^64 / phi


def stream(seed=1):
    """Distinct 64-bit keys (a linear congruential generator of full period): no library, no
    platform, no Python version can change them."""
    x = seed
    while True:
        x = (x * 6364136223846793005 + 1442695040888963407) & MASK
        yield x


def take(it, n):
    return [next(it) for _ in range(n)]


class Table:
    def __init__(self, bits, robin):
        self.bits, self.n, self.robin = bits, 1 << bits, robin
        self.key = [None] * self.n       # the key in each slot
        self.home = [-1] * self.n        # that key's home slot
        self.order = [-1] * self.n       # the number of the insert that brought it
        self.count = self.moves = 0

    def insert(self, key):
        """Returns the number of slots looked at."""
        n1, K, H, O = self.n - 1, self.key, self.home, self.order
        h = ((key * GOLDEN) & MASK) >> (64 - self.bits)
        i, d, probes, o = h, 0, 0, self.count
        while True:
            probes += 1
            if K[i] is None:
                K[i], H[i], O[i] = key, h, o
                break
            if self.robin:
                dc = (i - H[i]) & n1
                if dc < d:               # the resident is closer to home than we are: it moves on
                    K[i], key, H[i], h, O[i], o, d = key, K[i], h, H[i], o, O[i], dc
                    self.moves += 1
            i = (i + 1) & n1
            d += 1
        self.count += 1
        return probes

    def find(self, key):
        """(found, slots looked at)."""
        n1, K, H = self.n - 1, self.key, self.home
        i = ((key * GOLDEN) & MASK) >> (64 - self.bits)
        d = probes = 0
        while True:
            probes += 1
            k = K[i]
            if k is None:
                return False, probes
            if k == key:
                return True, probes
            if self.robin and ((i - H[i]) & n1) < d:      # our key would have taken this slot
                return False, probes
            i = (i + 1) & n1
            d += 1

    def displacement(self):
        """Per slot: how far its key sits from home; -1 for an empty slot."""
        return [(i - h) & (self.n - 1) if h >= 0 else -1 for i, h in enumerate(self.home)]


RULES = (("linear", False), ("robinhood", True))


def overview():
    out = {"meta": {"hash": "Fibonacci, 64 bit", "seed": 1}}

    # two small tables with the same keys, slot by slot: the picture
    bits, load = 12, 0.90
    keys = take(stream(), round(load * (1 << bits)))
    out["map"] = {"slots": 1 << bits, "load": load, "keys": len(keys)}
    for name, robin in RULES:
        t = Table(bits, robin)
        for k in keys:
            t.insert(k)
        assert all(t.find(k)[0] for k in keys), "a key was lost"
        out["map"][name] = {"disp": t.displacement(), "order": t.order}

    # a larger table filled step by step: probes per lookup against load
    bits = 15
    n = 1 << bits
    loads = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.85, 0.9, 0.95]
    it = stream()
    present = take(it, round(loads[-1] * n))
    absent = take(it, 4096)
    out["series"] = {"slots": n, "absent": len(absent), "loads": loads}
    for name, robin in RULES:
        t, rows, feed = Table(bits, robin), [], iter(present)
        for a in loads:
            before, probes, moves = t.count, 0, t.moves
            while t.count < round(a * n):
                probes += t.insert(next(feed))
            disp = [d for d in t.displacement() if d >= 0]
            miss = [t.find(k)[1] for k in absent]
            rows.append({"keys": t.count,
                         "hit_mean": round(1 + sum(disp) / len(disp), 6), "hit_max": 1 + max(disp),
                         "miss_mean": round(sum(miss) / len(miss), 6), "miss_max": max(miss),
                         "insert_mean": round(probes / (t.count - before), 6),
                         "insert_moves": round((t.moves - moves) / (t.count - before), 6)})
        out["series"][name] = rows

    path = os.path.join(HERE, "out", "overview.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(out, f, separators=(",", ":"))
        f.write("\n")
    print("wrote", path, f"({os.path.getsize(path) / 1024:.0f} KiB)")


def bench(repeats=5):
    bits = 15
    n = 1 << bits
    lines = [f"# harness.py bench: {n} slots, median of {repeats} runs; Python {platform.python_version()}, {platform.system()} {platform.machine()}"]
    for load in (0.5, 0.9):
        it = stream()
        keys = take(it, round(load * n))
        absent = take(it, 20000)
        sample = keys[::max(1, len(keys) // 20000)]
        for name, robin in RULES:
            ins, hit, miss = [], [], []
            for _ in range(repeats):
                t = Table(bits, robin)
                t0 = time.perf_counter_ns()
                for k in keys:
                    t.insert(k)
                t1 = time.perf_counter_ns()
                for k in sample:
                    t.find(k)
                t2 = time.perf_counter_ns()
                for k in absent:
                    t.find(k)
                t3 = time.perf_counter_ns()
                ins.append((t1 - t0) / len(keys))
                hit.append((t2 - t1) / len(sample))
                miss.append((t3 - t2) / len(absent))
            lines.append(f"load {load:.2f} {name:<10} hit {statistics.median(hit):8.1f} ns   miss {statistics.median(miss):8.1f} ns   insert {statistics.median(ins):8.1f} ns")
            print(lines[-1])
    path = os.path.join(HERE, "logs", "bench.txt")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")
    print("wrote", path)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "overview":
        overview()
    elif cmd == "bench":
        bench()
    else:
        sys.exit(__doc__)
