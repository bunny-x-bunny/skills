"""The experiments of the paper.

    python experiments.py run > logs/runs.txt      40 starts per seeding method on the paper's data set
"""
import statistics
import sys
import time

from kmeans import SEEDERS, Rng, lloyd, make_points

K, STARTS = 8, 40


def run():
    points = make_points()
    print(f"# k-means, k = {K}, {len(points)} points, {STARTS} starts per method")
    table = {}
    for name, seeder in SEEDERS.items():
        rows = []
        for start in range(STARTS):
            t0 = time.perf_counter()
            first = seeder(points, K, Rng(start))
            t1 = time.perf_counter()
            _, _, history = lloyd(points, first)
            t2 = time.perf_counter()
            rows.append((len(history), history[-1], history[0], (t1 - t0) * 1e3, (t2 - t1) * 1e3))
            print(f"start {start:2d} {name:<9} iterations {len(history):3d}  inertia {history[-1]:.6f}  first {history[0]:.6f}  "
                  f"seeding {rows[-1][3]:6.2f} ms  lloyd {rows[-1][4]:7.2f} ms")
        table[name] = rows
    best = min(r[1] for rows in table.values() for r in rows)
    print(f"# best inertia over all starts: {best:.6f}")
    for name, rows in table.items():
        near = sum(1 for r in rows if r[1] <= 1.01 * best)
        print(f"summary {name:<9} median iterations {statistics.median(r[0] for r in rows):5.1f}  median inertia {statistics.median(r[1] for r in rows):.6f}  "
              f"worst inertia {max(r[1] for r in rows):.6f}  within 1 % of best {near}/{len(rows)}  "
              f"median seeding {statistics.median(r[3] for r in rows):.2f} ms  median lloyd {statistics.median(r[4] for r in rows):.2f} ms")


if __name__ == "__main__":
    if sys.argv[1:] == ["run"]:
        run()
    else:
        sys.exit(__doc__)
