# The rules of a data-driven figure

Each rule below is stated with the complaint that produced it. The complaints are real: they are
what an author and expert reader said about earlier versions of the figure this skill grew out of.
When a rule seems not to fit your case, go back to the complaint and solve that.

## Contents

1. Evidence, not illustration
2. Show the real thing
3. One instance, carried through
4. Tie every enlargement to its source
5. Logarithmic axes that look logarithmic
6. Text never overlaps
7. The figure explains itself
8. Names look like names
9. Do not mix unlike things
10. Say how much evidence stands behind each panel
11. Losses and caveats in plain view
12. The script checks what it draws
13. The layout follows the content
14. Numbers, colour, type and space
15. What this kind of figure is not

## 1. Evidence, not illustration

*"Not good enough. Use rich data-driven infographics. Hook into the existing harness to collect
real data."*

A schematic says what the authors intend. A reader who doubts the paper gets nothing from it. A
figure whose every element is computed says what the code did, and a doubt can be settled by
looking closer. So the test for every element is: **could this have been drawn before the work
was done?** If yes, replace it with something that could not.

In practice: no number is typed into the figure script; no shape stands for data that exists; the
caption can truthfully say "nothing in it is drawn by hand". The exceptions are furniture (frames,
arrows, pictograms a few pixels wide in the strip) and they stay small.

## 2. Show the real thing

*"Visualize data structures. Show real patterns rasterized."* / *"Show the netlist, as it is one of
the most impressive results of the paper."*

Three kinds of real thing, in rising order of effect on a reader:

- **Data as pixels.** The instance itself, cell for cell, pixel for pixel, in its own colours: a
  simulation state, an image with the model's output on it, a matrix, a memory map, an alignment.
  A large sparse object is shown as density, not as plain pixels that vanish (`dd.density`).
- **Structures with their values.** Not a box labelled "hash table" but 3,840 of its slots
  coloured by displacement, and one entry spelled out: these four IDs give that ID. Not "tile
  IDs" but the 4 × 4 grid of actual IDs with equal ones tinted alike (`dd.cell_grid`).
- **The graph in full.** If the result is a circuit, a network, a plan or a proof, draw all of
  it, every node and edge, laid out from the data (`ddgraph.layered`), and put data on it: wires
  shaded by the values they carry. A reader who sees all 367 gates believes the number 367. The
  part of the work the authors are proudest of deserves the most area.

When the real thing is too large, show a real part of it at full detail and say which part
("the first 3,840 of 1,048,576 slots"), never a simplified whole.

## 3. One instance, carried through

*"Use squares: it shows an actually interesting circuit, one that computes and displays the
sequence of integer squares."*

Pick one instance that is worth looking at for its own sake and does something a reader can
recognise, and let the panels follow it: the picture of it, the 32 cells of it that go through
the circuit, the tiles it is cut into, the step that was traced. Mark in each panel where the
previous panel's part lies ("the 32 cells of panel 2"). Panels that each use a different example
read as five unrelated figures.

Other instances appear where the claim is about variety (small multiples of the evaluation
set), each with the same one statistic so they can be compared.

Choosing the instance is a selection, and a selection by outcome (the run where the baseline
fails, the image the model gets right) biases the picture. State the rule that picked it in the
figure ("the first start at which random seeding ends above 5"), and show somewhere what all the
others did, so the reader can see how typical the chosen one is.

## 4. Tie every enlargement to its source

*"It is not obvious which part of the image corresponds to the zoomed cuts. Add lines between
them."*

An enlargement beside a picture is a puzzle unless the two are joined: a frame around the region
in the picture, the same frame style around the enlargement, and a cone between their facing
edges (`Svg.cone`). When an enlargement is enlarged again, chain the cones. When two views show
the same object in different forms (cells and IDs), frame the corresponding part in both in the
same colour and say so ("the key: the four IDs framed above").

## 5. Logarithmic axes that look logarithmic

*"In all logarithmic charts, add unevenly spaced dashed grid lines, so that the logarithmic scale
is instantly recognizable."*

Evenly spaced grid lines labelled 10³, 10⁴, 10⁵ look linear at a glance, and a glance is all most
readers give. Minor lines at 2, 3 … 9 times each power bunch up towards the next power; that
pattern is the signature of a log scale. `dd.log_grid` draws them dashed and thin, with a solid
line at each power. Linear axes get evenly spaced solid lines and nothing else, so the two kinds
can be told apart on the same page. This holds for the smallest sparkline too.

Bars on a log axis have no meaningful length; where that could mislead, use dots on stems
(`dd.bars(dots=True)`) and always print the value at the mark.

## 6. Text never overlaps

*"There are a lot of text overlaps in panel 1."*

Dense figures fail here first, and the author is the last to see it because the author knows what
the text says. Do not eyeball it:

- lay text out from measured widths (`dd.text_width`, `dd.wrap`, `max_width=`);
- text on a picture, a bar or grid lines gets a halo in the colour behind it (`halo=`);
- labels at the ends of curves that end close together are spread (`dd.spread`) and joined to
  their curves by short leaders;
- `Svg.finish` runs an audit and refuses to write a figure that fails it; `figcheck.py audit`
  repeats it with the browser's real fonts.

The audit cannot see a label that sits on the wrong curve, or one that straddles a reference line
and is cut in two by its own halo. Those are found by looking (see `review.md`).

## 7. The figure explains itself

*"While reading the diagram, I had a really hard time understanding what certain terms mean, e.g.
floor, memo, miss, hit, waves. One would need to read deep into the paper first, but the figure is
on the headline."* / *"Figures must be more or less self-explanatory. The reader should be able to
understand what a term means without reading deep into the paper."*

The author of those sentences wrote the software the figure describes. If the terms stopped them,
they stop everyone. The headline figure is read before anything else, and often instead of
anything else (in a talk, a README, a tweet, a reviewer's first pass), so it must carry its own
vocabulary. This is a requirement of the same rank as rule 1: a figure full of real data that
cannot be understood without the paper has not done its job. What it takes:

- every term is defined once, in one plain sentence, the word in bold at the point of definition;
- the definition stands where the reader is looking. Best: a note tied to the thing the word
  names, so that the word is learned while looking at what it means. Next: on the arrow or axis
  that carries it ("load: the share of slots in use"). When the method is a sequence of steps
  whose terms build on each other, a strip of cards at the head does it: one step per card, a
  small pictogram that gives the word something to look at, and on each card the number of the
  part that shows that step;
- no part uses a word the figure has not yet defined; a late term is defined where it is used
  ("one pass over the grid, a sweep");
- symbols are introduced in words first ("a probe costs as much as ρ = R_B / R_P cell-updates of
  brute force: R_B is the rate of brute force, R_P that of probes");
- a number comes with its unit and its span ("model time for those 1,024 generations: 18.6 ms").

To test it, list every noun in the figure and find where the figure itself explains it.

## 8. Names look like names

*"For all pattern names, add the file extension and perhaps a different font."* / *"Rule names
should look distinct as well."*

In running text, "squares" is a word and "chaotic" is an adjective. `squares.rle` in monospace is
plainly a file the reader could open. So:

- files, commands and identifiers: the real name with its extension, monospaced (`` `name` ``);
- the named things the project compares (rules, models, datasets, algorithms): one style, bold
  italic, each in its own colour, and that colour is also the colour of its curve and its bars
  (`[[Name]]`, `dd.entities`);
- a term at its definition: bold (`**term**`), and plain afterwards.

Three styles are enough. More, and style stops carrying meaning.

## 9. Do not mix unlike things

*"In the chart of brute force rates, two rules are conflated with each other. Add a horizontal
divider: on top Hutton32, on the bottom Life."*

Six bars in one block are read as six values of one thing. If they belong to two rules, two
datasets or two machines, the comparison across the groups is not the one the reader should make,
and the chart must say so: a line between the groups and a heading on each (`dd.bars` takes
groups). Quantities with different units do not share an axis at all: one small chart each.

## 10. Say how much evidence stands behind each panel

*"At the top right of each panel are blocks 'measured on the GPU', 'CPU reference engine' ... What
were they meant to represent? Visually, they look like tab buttons or tags."*

Most projects are not finished when the figure is drawn: some parts are measured on the real
system, some by a reference implementation or on one machine, some only modelled. Hiding that is
dishonest, and readers who find out stop trusting the rest. Mark it, on every panel, at three
levels (`full`, `partial`, `model`), and print the legend once, worded for the project.

The first version drew these as filled rounded rectangles, and they were read as buttons. A small
mark with plain grey text is read as a note. Use the same shapes for the points in the comparison
chart, so that "measured" looks the same everywhere.

## 11. Losses and caveats in plain view

A comparison that shows only wins is not believed. The ratio chart has a line at 1× and names both
sides; cases where the baseline wins are drawn with the same weight; the baseline runs at its best
settings and the chart says which. Lower bounds are printed with ≥ and cut, not rounded. When
parts of a system were measured separately and never ran together, the figure says so in its
first line. Readers forgive limits they are told about.

## 12. The script checks what it draws

A figure script is code that nobody tests, drawing data that nobody else will look at this
closely. Put the tests in it: assert each claim a panel makes on the data the panel is drawn
from, exhaustively where that is cheap (all 2¹⁶ inputs, every cell of the frame). Then print the
fact in the figure: "checked while drawing: on all 357,120 cells of this frame the network gives
the next generation of the pattern's own rule table". These checks have repeatedly found real
errors, in the harness and in the paper's text.

## 13. The layout follows the content

*"Across all test runs so far, all diagrams share the exact same layout and look too similar."*

The first figures made with this skill all had a head, a strip of cards, numbered panels down the
page and a ratio chart at the bottom, whatever they were about, because the skill had described
that one layout as the method. The method is rules 1 to 12. The layout is designed each time:
from the hero (the one real thing to be seen first, which gets the most area), the reading path,
the destination (a page, a slide, a poster) and the number of terms that need explaining.
`compositions.md` has eight arrangements that have worked and how to choose among them.

The test: put two figures made for different projects side by side. If a stranger would take
them for two fillings of one template, one of them was not designed. And for a single figure:
you can say in a sentence why its largest element is the largest.

## 14. Numbers, colour, type and space

- **Numbers**: one function per kind (`dd.times`, `dd.sci`, `dd.pct`, `dd.thousands`), matching
  the paper's rounding; a count that must fit a small box uses `dd.short`.
- **Colour**: the Okabe–Ito palette (in `ddfig`) for categories; one colour per named thing,
  everywhere; viridis or a single-hue ramp for magnitudes; grey for furniture. Do not let colour
  be the only carrier: add shape or a label.
- **More than seven categories**: Okabe–Ito has seven colours, and the named things of the
  project take them first. Categories without names of their own (clusters, classes, shards)
  get `dd.SOFT8` or a ramp, and a second carrier: a number, a position, an outline.
- **Type**: Arial/Helvetica metrics; sizes chosen at the canvas of the destination: nothing below
  9.5 px on a page read closely (about 1200 px wide), nothing below 11 to 12 px on a slide. Body
  text in grey, the things to be read first in ink and bold. No rotated text except, rarely, an
  axis title.
- **Space**: area says importance, so the hero gets the most. Explanatory text sits beside the
  thing it explains, in short paragraphs. Empty corners are a sign that a part was planned too
  small or a column too wide: rebalance rather than fill with decoration.
- **Titles claim**: "Why a floor, and what it buys", not "Performance analysis".

## 15. What this kind of figure is not

- Not an image-model illustration: those cannot place exact data, and their text is unreliable.
- Not a graph-drawing tool's default output: a default layout of a few boxes is the schematic
  this skill replaces; the layout here serves a real graph of hundreds of nodes.
- Not a dashboard: every element supports a claim of the paper; nothing is there because it was
  available.
- Not a single chart: if one chart of one table is all that is needed, make that chart.
