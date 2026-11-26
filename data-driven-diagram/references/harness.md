# Getting real data out of the project

The figure script draws. Everything it draws comes from one of three places: a dump that the
project's own code writes on request, the raw logs of measurements, or artefacts that are in the
repository. This file is about setting those up.

## Contents

- The overview command
- What to dump
- The JSON
- Determinism
- Measured numbers: logs
- Artefacts
- The short list of typed constants
- When there is no harness
- What "the real thing" is, by field

## The overview command

Add one command to the project's harness, in the project's language, next to the commands that
already produce its results: `overview` (or `figure-data`). It runs the real code, the same
functions the experiments call, on the showcase instances and writes one JSON file.

- **Same code path.** Call the engine, do not reimplement it for the figure. If the engine does
  not expose what a panel needs (the windows of one recursion step, the slots of the table), add
  an optional hook to the engine: a field that is `None` unless the figure asks, filled where the
  work happens. It costs nothing when unused, and it is the real trace, not a reconstruction.
- **Sections.** Write the dump as named sections (`patterns`, `sweep`, `table`, `waves` ...), print
  each section's name and time as it finishes, and accept a filter (`--sections waves,table`) so
  that one panel can be iterated without recomputing the rest.
- **Bounded.** A minute or two in total. If a section would take longer, shrink its instance and
  say so in the figure ("the curve is that of a smaller ROM of the same kind"), or cache
  nothing and accept the time: a cache is a second source of truth.
- **Self-describing.** Put names and parameters in the dump: the file each instance was read
  from, the rule or model it used, sizes, step counts, seeds. The figure prints these instead of
  the figure script knowing them. This is what lets a caption say `lotr1.PPMd-244K.rle` without
  anyone typing it.

The output goes to an ignored directory (`out/overview.json`); only the figure is committed.

## What to dump

Dump raw data and let the figure script decide how to draw it. A dump that contains pre-rendered
images or pre-formatted strings cannot be drawn differently next week.

| for a panel that shows | dump |
|---|---|
| the instances | each instance's raw content at one or two moments, its size, its source file |
| a statistic per instance | the series behind it (per step, per batch), not the summary: the figure may want a curve |
| a data structure | a contiguous slice of it, verbatim (IDs, keys, slots), plus totals and a histogram of the whole |
| one traced step | every unit of work in order, with its parent: batches, levels, calls, messages |
| a map of decisions | per region or item: the decision and the quantities it was based on |
| the enlarged cut | nothing extra: the figure cuts it from the instance, so the two cannot disagree |

Include what the figure needs to **check** its own drawing: the next state as the reference
engine computed it, the expected outputs, the totals that must add up.

## The JSON

Keep it compact and boring.

- A grid of small integers as one string, one character per cell (base 32 covers states up to 31:
  `0-9a-v`), with `w` and `h` beside it. A megapixel is a megabyte, which is fine.
- Larger values as arrays of numbers. Floats rounded to the figures that matter (six is plenty),
  so that the file is stable across platforms.
- Keys in a fixed order, no timestamps, no host names, no absolute paths.
- Write with `\n` line ends.

## Determinism

The figure must come out byte-identical on every run and machine, or it cannot live in version
control and nobody can tell a real change from noise.

- Seed every random choice explicitly, with a generator the project controls (a ten-line LCG
  beats a library whose stream may change between versions).
- Iterate in a defined order: sort keys; never rely on hash-map order or thread scheduling.
- Keep timing out of the dump. Counts are recomputed; clocks go to logs.
- Test it: run the command twice, hash the output.

## Measured numbers: logs

Wall-clock rates, memory high-water marks, anything from other hardware or other software (the
baseline) cannot be recomputed deterministically. Measure them with the harness's ordinary
commands, keep the raw output as text files under a dated directory (`logs/2026-11-25/`), commit
those, and let the figure read them:

```python
from ddfig import Logs, NUM
logs = Logs("logs/2026-11-25")
rate, = logs.find("kernel.txt", rf"bit-plane kernel: .* = {NUM} cell-updates/s")
rows = logs.all("probe.txt", rf"^\s+(\d+)\s+(\d+) MiB\s+\d+\s+{NUM}\s")
t = logs.find("bench.txt", rf"^load 0\.90 robinhood\s+hit\s+{NUM} ns", after="# run 2")
```

- Find a number by the **line that reports it**, with enough of the line in the pattern that only
  that line matches. A missing line raises: the figure cannot keep a number the logs have lost.
- Collect all log reading in one module or function that returns a dictionary, and give it a
  `__main__` that prints everything it found. That printout is the quickest way to compare the
  figure with the paper's tables.
- Aggregate as the paper does (median of the runs, the best step size of the baseline) and to the
  same number of figures.
- Ratios against a baseline are computed here, from both logs, never copied from the paper.
- When the script checks recomputed values against a log, compare at the log's precision: format
  the recomputed value the way the log line prints it and compare the strings, or allow half a
  unit of its last digit. Exact equality of floats against rounded text fails for no reason.

## Artefacts

Results that are files (a netlist, a trained model, an optimisation log, a config) are parsed
directly by the figure script or a small module beside it. Evaluate them too where you can: a
parsed netlist can be run on the showcase instance and compared with the harness's reference,
which is both a check and a picture (the wires shaded by what they carry).

## The short list of typed constants

Sometimes a number is in the paper's prose and nowhere else: a threshold a model yields, a
figure from the literature. Give it a name and a comment that says where it comes from:

```python
# Active cells from which a floor of 32x32 and of 16x16 windows pays for its dispatches: the model
# of paper.md, Table XXVII (the one pair of numbers here that no log file holds).
DEPTH_A1, DEPTH_A2 = 1.0e6, 1.3e7
```

Two or three of these in a figure are honest. More means the model should be computed by the
harness.

## When there is no harness

- **Results are data files** (CSV, parquet, npz, a database export): write `figure_data.py` that
  loads them and writes the JSON. It is the harness now; the same rules hold.
- **Results are in a notebook**: move the cells that compute them into a script the notebook
  imports, and call that script.
- **The code is not yours to change** (a vendored tool, a closed binary): drive it from outside
  and parse what it prints, as a log.
- **Nothing runs** (the paper is a design): the figure can still show real objects, such as the
  actual schedule, the real state machine, the enumerated cases; mark every panel `model` and say
  that nothing was measured.

## What "the real thing" is, by field

| field | instances as pixels | structures with values | the graph in full | measured, on log axes |
|---|---|---|---|---|
| algorithms, data structures | inputs before and after; memory maps | table slots, tree nodes, heaps with their keys | call or recursion tree of one run; the automaton | operations and time against n; against the standard library |
| systems, compilers | traces as timelines; page or cache maps | queues, logs, page tables at one instant | dataflow of one query; the IR of one function | latency percentiles; throughput against load |
| hardware, circuits | waveforms; layout | truth tables, state registers | the netlist | gates, depth, area, power; against the previous design |
| machine learning | actual samples with predictions; attention or saliency on them | weight and activation matrices; a confusion matrix with counts | the computation graph of the real model | loss against steps; accuracy against compute; against baselines |
| simulation, physics | field snapshots at chosen times | the mesh or particle cells near a feature | the solver's dependency or stencil graph | error against resolution; cost against size |
| biology, medicine | alignments; expression matrices; segmented images | the records behind one data point | pathways or pedigrees as they are in the data | effect sizes with intervals; cohort flow with counts |
| theory | the construction at a small size, drawn exactly | the table of cases, enumerated | the dependency graph of lemmas; the reduction | bounds against computed values |

If a cell of this table is empty for your project, that panel does not exist; do not fill it
with a cartoon.
