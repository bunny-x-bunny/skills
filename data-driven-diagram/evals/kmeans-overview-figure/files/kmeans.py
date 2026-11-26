"""k-means clustering (Lloyd's algorithm) with two ways of choosing the first centroids:
uniformly at random, and k-means++ (each next centroid drawn with probability proportional to the
squared distance from the centroids chosen so far).

Pure Python, deterministic: the random numbers come from the generator below.
"""
import math

MASK = (1 << 64) - 1


class Rng:
    def __init__(self, seed):
        self.x = (seed * 2862933555777941757 + 3037000493) & MASK
        for _ in range(4):
            self.next()

    def next(self):
        self.x = (self.x * 6364136223846793005 + 1442695040888963407) & MASK
        return self.x >> 11

    def uniform(self):
        return self.next() / (1 << 53)

    def normal(self):
        u, v = max(self.uniform(), 1e-300), self.uniform()
        return math.sqrt(-2 * math.log(u)) * math.cos(2 * math.pi * v)


# centre x, centre y, spread, share of the points
BLOBS = [(0.18, 0.22, 0.035, 0.20), (0.24, 0.74, 0.050, 0.16), (0.52, 0.48, 0.030, 0.10), (0.58, 0.86, 0.025, 0.08),
         (0.78, 0.20, 0.060, 0.18), (0.84, 0.62, 0.040, 0.14), (0.46, 0.14, 0.020, 0.06), (0.66, 0.42, 0.022, 0.08)]


def make_points(n=900, seed=7):
    """The data set of the paper: n points from eight blobs of unequal size and spread."""
    rng, pts = Rng(seed), []
    for cx, cy, s, share in BLOBS:
        for _ in range(round(n * share)):
            pts.append((cx + s * rng.normal(), cy + s * rng.normal()))
    return pts


def d2(p, q):
    return (p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2


def seed_random(points, k, rng):
    chosen = []
    while len(chosen) < k:
        p = points[int(rng.uniform() * len(points))]
        if p not in chosen:
            chosen.append(p)
    return chosen


def seed_plusplus(points, k, rng):
    chosen = [points[int(rng.uniform() * len(points))]]
    near = [d2(p, chosen[0]) for p in points]
    while len(chosen) < k:
        r, acc = rng.uniform() * sum(near), 0.0
        for p, w in zip(points, near):
            acc += w
            if acc >= r:
                chosen.append(p)
                break
        near = [min(a, d2(p, chosen[-1])) for p, a in zip(points, near)]
    return chosen


def lloyd(points, centres, max_iter=200):
    """Returns (centroids, the cluster of every point, inertia after every assignment step)."""
    centres, assign, history = list(centres), None, []
    for _ in range(max_iter):
        new, inertia = [], 0.0
        for p in points:
            best = min(range(len(centres)), key=lambda c: d2(p, centres[c]))
            new.append(best)
            inertia += d2(p, centres[best])
        history.append(inertia)
        if new == assign:
            break
        assign = new
        for c in range(len(centres)):
            mine = [p for p, a in zip(points, assign) if a == c]
            if mine:
                centres[c] = (sum(p[0] for p in mine) / len(mine), sum(p[1] for p in mine) / len(mine))
    return centres, assign, history


SEEDERS = {"random": seed_random, "plusplus": seed_plusplus}
