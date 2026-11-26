# Examples

Three figures from two miniature projects. Run them, read their scripts, and take from them the
discipline: everything computed, everything checked, everything explained in the figure. Do not
take their layouts. Each was composed for its content and its destination, and the first two
show how far two layouts of the same data can differ.

All three figures are in the repository, so you can look before you run anything
(`python ../scripts/figcheck.py shoot hashtable/figures/poster.svg shots` renders one to PNG).

## hashtable/ : one project, two compositions

A hash table with linear probing against Robin Hood hashing.

```
python harness.py overview     # counts -> out/overview.json (exact, deterministic, about 3 s)
python figure.py               # -> figures/overview.svg   for a paper: stacked claims with a strip
python poster.py               # -> figures/poster.svg     for a slide: a hero with notes
python harness.py bench        # optional: re-measure the times kept in logs/bench.txt
```

| | `figure.py` | `poster.py` |
|---|---|---|
| made for | a paper, read closely, 1200 px wide and tall | a slide, 1280 × 720 |
| composition | three numbered panels of equal weight under a strip of cards | the two tables as the hero, a side column |
| terms are defined | in the strip, before the panels | in notes tied to the slots themselves |
| results are shown as | a chart of ratios on both sides of 1× | three large numbers, the price among them |
| the cut of 24 slots with values | yes: a frame, a cone, a row of cells | no: the tables are large enough to read |

What the two share is the skill: the same dump and log, the same assertions on the data before
anything is drawn, sentences built from the numbers, a key beside every colour, an evidence mark
on every result.

Where to look in `figure.py`:

| in the figure | technique | function |
|---|---|---|
| two tables as pictures, one cell per slot | real data as pixels; one palette for both | `panel_tables` |
| a frame, a cone and 24 slots with their values | an enlarged cut tied to its source | `panel_tables` |
| "checked while drawing" | the claim asserted on the data before it is drawn | the `assert`s |
| five curves on a log axis, named at their ends | dashed minor grid; `spread` labels with leaders; a model as a pale band | `panel_load` |
| ratios against the baseline | wins and losses; one shape per kind of evidence | `panel_ratio` |

And in `poster.py`: targets of the notes found in the data by a rule (`nearest`), notes placed by
a rule (`notes_under`), `dd.callout` and `dd.stat`.

`harness.py` shows the split that makes a figure reproducible: what can be counted is recomputed
on every build; what must be timed is measured once and kept as a raw log that the figure reads.

## adder/ : a real graph, drawn in full

Two 8-bit adders, a ripple-carry and a Kogge-Stone, one above the other at the same scale, so
that the difference in depth is a difference in width. The script builds both networks, runs each
on all 65,536 pairs of inputs at once, checks every sum, then draws every gate and wire with
`ddgraph.layered`. Wires are shaded by how often they carry a 1.

```
python figure.py               # -> figures/adders.svg (about 4 s)
```

Use it when the subject of the figure is a circuit, a computation graph, a pipeline or any other
graph the project really has: pin the inputs and outputs, lay it out from the data, put data on
the wires, and take the numbers beside it (nodes, depth) from the graph itself.

## In your own project

The example scripts import `ddfig.py` from `../../scripts` so that they stay in step with the
library. In a project, copy `ddfig.py` (and `ddgraph.py`) next to the figure script instead: the
figure must rebuild on a machine that has never seen this skill.
