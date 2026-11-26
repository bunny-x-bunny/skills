# Seeding k-means

A small study of how the choice of the first centroids changes what Lloyd's algorithm finds.

- `kmeans.py`: the algorithm, two seeding methods (`random`, `plusplus`), the data set (`make_points`).
- `experiments.py run`: 40 starts per method on the data set; prints one line per start and a summary per method.
- `logs/runs.txt`: the output of that command, as used in the paper.
- `paper.md`: the draft.

Everything is plain Python 3 with no dependencies. Clustering results are deterministic (the
random numbers come from `kmeans.Rng`); the times in the log are not.

```
python experiments.py run > logs/runs.txt
```

## What we found, in short

On 900 points from eight blobs of unequal size and spread, with k = 8:

- k-means++ starts much closer: the inertia after the first assignment is about a quarter of what
  random seeding gives.
- It avoids the bad endings: far fewer starts end with an inertia above 5, and its worst start is
  about half as bad as random seeding's worst.
- It does not find the best clustering more often, and it does not need noticeably fewer
  iterations.
- Seeding itself costs milliseconds against tens of milliseconds for Lloyd's iterations.
