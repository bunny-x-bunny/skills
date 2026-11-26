# What k-means++ seeding buys, and what it does not

*Draft.*

<!-- FIGURE 1 GOES HERE: an overview of the method and the findings. -->

**Abstract.** Lloyd's algorithm for k-means converges to a local optimum that depends on where its
centroids start. k-means++ chooses the starting centroids one at a time, each with probability
proportional to its squared distance from those already chosen. On a data set of 900 points in
eight clusters of unequal size and spread we compare it with uniform random seeding over 40 starts
each. k-means++ starts with about a quarter of the inertia and almost never ends in a poor local
optimum, but it reaches the best clustering no more often than random seeding does, and needs about
as many iterations.

## 1. Method

**Inertia** is the sum over all points of the squared distance to the nearest centroid. Lloyd's
algorithm alternates two steps until nothing changes: assign every point to its nearest centroid;
move every centroid to the mean of its points. Each step can only lower the inertia, so the
algorithm stops, but where it stops depends on the first centroids (the *seeding*).

*Random seeding* takes k distinct points uniformly. *k-means++* takes the first uniformly and each
further one with probability proportional to D², the squared distance from the nearest centroid
chosen so far, so that new centroids tend to land in parts of the data that have none yet.

## 2. Data and runs

`kmeans.make_points()` draws 900 points from eight Gaussian blobs with shares between 6 % and 20 %
and spreads between 0.020 and 0.060 in the unit square. Each seeding method is run from 40 starts
(`experiments.py run`, output in `logs/runs.txt`), k = 8.

## 3. Results

**Table 1.** 40 starts per method.

| | random | k-means++ |
|---|---|---|
| inertia after the first assignment, median | 27.98 | 7.50 |
| final inertia, median | 3.606 | 3.497 |
| final inertia, worst start | 16.37 | 9.00 |
| starts ending above an inertia of 5 | 17 | 4 |
| starts within 1 % of the best inertia found (2.860) | 8 | 4 |
| iterations, median | 9 | 8.5 |

k-means++ removes most of the poor endings: 4 of 40 starts end above an inertia of 5, against 17
for random seeding, and its worst start is about half as bad. The median ending is almost the same
for both, and the best clustering found (inertia 2.860) is reached by 8 random starts and 4
k-means++ starts: on this data k-means++ protects against bad luck rather than finding better
optima.

## 4. Reproduction

`python experiments.py run > logs/runs.txt` reproduces the runs; the clustering columns of the log
are deterministic.
