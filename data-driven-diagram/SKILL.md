---
name: data-driven-diagram
description: Build the headline figure of a research project as evidence, not decoration - one SVG infographic in which every picture and number is computed by the project's own code or read from its logs, and which is self-explanatory - a reader can tell what every term means from the figure alone, without reading deep into the paper. Real data as pixels, real data structures and graphs in full, gridded log axes, results against a baseline with losses shown; drawn by a script that checks what it draws and audits its own layout. Use this skill whenever the user wants an overview figure, Figure 1, a graphical abstract, a poster, README or talk infographic, or a diagram of how an algorithm, system, model or experiment works - and whenever they call a diagram not good enough, too schematic, just boxes and arrows or hard to understand, or ask for data-driven, more impressive, real data or visualized data structures. Also for polishing such a figure. Not for one ordinary chart or image-model illustrations.
---

# Data-driven diagrams

A reader gives a headline figure a few seconds before deciding whether to read on, and an expert
reads it as evidence. A schematic of boxes and arrows serves neither: it could have been drawn
before the work was done, and it shows nothing that can be checked. This skill builds the other
kind of figure: one SVG in which every picture is the project's real data, every number is computed
or read from a log, and the script that draws it also verifies it.

## What is fixed, and what is free

Two requirements are fixed. Everything else in this skill serves them.

- **It is evidence.** Nothing in it could have been drawn before the work was done.
- **It explains itself.** The figure is read first, often alone. A reader must be able to tell
  what every term, symbol, colour and mark in it means from the figure itself, without reading
  deep into the paper. A figure that needs the paper to be understood has failed, however good
  its data: the reader it was made for never gets that far.

One thing is free, and must stay free:

- **The composition is designed for the content.** What is largest, what is read first, where
  the explanations sit, the shape of the canvas: these follow from this project's claims and
  from where the figure will be shown. The examples in this skill show the discipline in three
  different layouts. Copy the discipline. A figure that reuses an example's layout for different
  content is a template filled in, and readers of two such figures see one figure twice.

```
data-driven-diagram/
├── scripts/ddfig.py            the drawing library: copy it into the project (no dependencies)
├── scripts/ddgraph.py          layered layout for drawing a real graph in full: copy when needed
├── scripts/figcheck.py         audit and screenshots in headless Chrome/Edge: run from here
├── scripts/audit_svg.js        the browser audit itself, for any browser tool or console
├── scripts/font_metrics.py     width tables for another typeface or more characters
├── references/principles.md    the rules, each with the reader's complaint behind it
├── references/compositions.md  choosing a layout from the content; eight that have worked
├── references/harness.md       getting real data out of a project; "the real thing" per field
├── references/panels.md        building blocks, with ddfig code
├── references/review.md        the audit-and-look loop, the list of blemishes, the caption
└── examples/                   hashtable/figure.py (stacked claims, for a paper), hashtable/poster.py
                                (the same data as a hero with notes, for a slide), adder/figure.py
                                (two real gate networks in full)
```

Read `references/principles.md` once before planning: it is short, and every rule in it was paid
for by a reader who stumbled. Read the others when you reach their step.

## Workflow

### 1. Read the project until you can state its claims

Read the paper or README, the code that produces the results (the *harness*: benchmark runner,
experiment script, test bench, notebook), and the results it has left behind (logs, tables,
checkpoints, datasets). Then write down, for yourself:

- the **claims** the figure must carry (three to five), and for each the real thing that would show it;
- the **mechanism**: how the method works, and the words an outsider will not know. Every one of
  those words has to be explained inside the figure;
- one **showcase instance**: a real input that is interesting to look at and does something
  recognisable. It is carried through the figure, so that the reader follows one object from the
  raw picture through the internals to the result. Pick it by a rule that the figure states ("the
  first start at which random seeding ends above 5"): an instance chosen for its outcome is a
  selection, and the reader is owed the rule and a view of all the others;
- which numbers already appear in the paper. The figure prints them the same way, to the same
  rounding, or readers will find two versions of one result. Where the paper disagrees with
  itself, follow its commonest convention and list the cells that differ in your report; change
  numbers in the paper only if the user asked you to edit it.

If the project has no measurements yet, say so and build the figure from what the code can compute;
do not invent plausible data to fill a panel.

### 2. Compose: design the layout for this content

Before any code, decide four things and write each down in a sentence
(`references/compositions.md` has the reasoning and eight compositions to start from):

- the **hero**: the one real thing to be seen first and remembered. It gets the most area;
- the **reading path**: a process left to right, a zoom from whole to detail, an argument top to
  bottom, or outwards from the hero;
- the **destination**: paper page, README, slide, poster. It sets the canvas and the type sizes;
- **where the explanations live**: at the thing itself (a note with a leader), on arrows and
  axes, in a strip of steps, in a key. Prefer the place where the reader is already looking.

Then sketch the layout as a rough box diagram with proportions, and check it against the
examples: if it has the same boxes as one of them, the reasons must be this project's. Tell the
user the sketch and its reasons in a few lines, and go on; a plan this cheap to revise is not
worth a round trip.

### 3. Decide what each part shows, and on what evidence

For every part of the sketch: the claim it carries, what is drawn, where the data comes from, and
how much evidence stands behind it.

| a part shows | usually | source |
|---|---|---|
| what the work operates on | real instances as pictures, one statistic each | recomputed |
| how it works inside | a structure with its real values; the real graph; one traced step | recomputed, artefacts |
| why the design is what it is | measured rates, a break-even or threshold | logs, a model |
| what it buys | results against a baseline, wins and losses | logs |

Not every figure has all four, and they need not be separate panels: a hero picture with notes
can carry the first two at once. Headings, where there are any, state claims ("Above the floor:
tiles, IDs and a memo table"), never component names ("Architecture").

### 4. Get the data out of the project

The figure script draws; it does not compute results. Three sources, in this order of preference:

1. **Recompute it.** Add a command to the project's own harness, in the project's language
   (`overview` is a good name), that runs the real code on the showcase instances and writes one
   JSON file of everything the figure needs: the instances as raw data, snapshots of the data
   structures, a trace of one step, per-item statistics. Deterministic, and quick enough to rerun
   on every build (aim for a minute or two).
2. **Read the logs.** Timings and other measurements that differ from run to run are measured
   once and kept as raw logs; the figure finds each number by the line that reports it
   (`ddfig.Logs.find`), and a missing line is an error.
3. **Parse the artefact.** A netlist, a model file, a config, a dataset in the repository is read
   directly.

Never type a result into the figure script. A typed number is right on the day it is typed and
wrong after the next change, and nobody will notice. If one figure exists only in the paper's
prose (a threshold defined there), give it a named constant with a comment saying where it comes
from, and keep that list short. `references/harness.md` covers the command, the JSON, determinism,
and what counts as "the real thing" in different fields.

### 5. Write the figure script

Copy `scripts/ddfig.py` (and `ddgraph.py` if you draw a graph) next to the figure script inside the
project: the figure has to rebuild from the repository alone, on a machine that has never seen
this skill. Then write plain Python: one function per part of your sketch, each drawing into the
box the sketch gave it.

```python
import ddfig as dd
from ddfig import Svg, Logs

def build():
    D = json.load(open(DATA)); logs = Logs(LOG_DIR)
    svg = Svg(1280)                       # the canvas of the destination; height follows
    hero(svg, x, y, w, h, D)              # the parts of your sketch, in your layout
    notes(svg, ...)
    results(svg, ..., logs)
    svg.save(OUT, height)                 # refuses to write a figure whose text collides
```

`ddfig` has three layers, and the layout comes from the first two:

- **primitives**: `text`, `para`, `rect`, `line`, `path`, `image`, `cone`, scales and grids,
  PNG writers: enough to draw anything;
- **layout-free parts**: `grid` (cells of your layout), `callout` (a note tied to the thing it
  explains), `stat` (one large number with its meaning), `cell_grid`, `curve`, `bars`,
  `ratio_chart`, status marks;
- **furniture of one page style**: `title`, `cards`, `section`. Use them when your composition
  is the stacked one, not because they are there.

`references/panels.md` shows each in use; `examples/` has three complete scripts. What matters
while writing, whatever the layout:

- **Lay out by measurement.** `dd.text_width` and `dd.wrap` know the fonts, so text is fitted,
  not guessed; give a text its room with `max_width=` wherever it sits in a box. Positions that
  depend on data (a note beside a target, labels at the ends of curves) are computed by a rule,
  never typed as coordinates: the data will move.
- **Mark up names as you write them**: `` `file.ext` `` for files, commands and identifiers,
  `[[Name]]` for the named things of the project (register their colours once with
  `dd.entities`, the same colours as their curves), `**term**` where a word is defined.
- **Build sentences from data.** A sentence with a number in it is an f-string over the data,
  including the title's claim. So are "the largest", "twice", "in every case": compute them.
- **Check what you draw, in the script.** Whatever a part asserts, assert it on the data it is
  drawn from: the two structures hold the same keys, the network reproduces the reference on every
  input, the entry equals the recomputed value, the curves said to coincide are equal. Then say
  so in the figure ("checked while drawing"). This is what turns a picture into evidence, and it
  catches your own mistakes in the harness.
- **One function per kind of number** (`dd.times`, `dd.sci`, `dd.pct`, `dd.thousands`, `dd.num`),
  so a value is printed the same way everywhere. A lower bound is cut with `dd.floor_sig`, never
  rounded up.

### 6. Make it explain itself

The figure sits above the abstract; its reader has not read the paper, and should not have to.
Go through every word, symbol and colour in it and ask whether that reader knows what it means.
Words that are everyday to the authors ("floor", "memo", "hit", "miss", "wave" in the figure this
skill grew out of) are exactly the ones that stop everyone else. Whatever the composition:

- every term of the method is **defined in the figure**, in one plain sentence, before or where
  it is first needed: best in a note at the thing it names, otherwise on the arrow or axis that
  carries it, or in a strip when the terms build on each other;
- things are called by **their real names**: a file with its extension, in monospace; a rule, model
  or dataset in its own style and colour, the same in text and in charts;
- every colour, mark and line style has a **key next to where it is used**;
- the figure says **how much evidence** stands behind each part (`full`, `partial`, `model`)
  and what those marks mean in this project. Marks with plain text: a filled rounded box around
  such a label looks like a button, and readers try to click it;
- sentences are short and literal. "A window is worth a memo entry only if a hit saves more than
  the probe costs", not "the floor optimises the hit/miss trade-off".

### 7. Audit, then look

`svg.save` refuses to write a figure in which text overlaps text, leaves the page, lies on a
picture without a halo, or is crossed by a line (`LayoutError`; `DDFIG_DEBUG=1` writes it anyway
with the places marked red). A picture drawn with shapes instead of an image (a scatter of
points) is declared with `svg.rect(..., picture=True)` so that the audits know it. The font
tables are a model; the browser has the last word:

```
python <skill>/scripts/figcheck.py audit figures/overview.svg       # must pass
python <skill>/scripts/figcheck.py shoot figures/overview.svg shots  # overview.png and 2x tiles
```

Then read **every** tile image. An audit finds collisions; it does not find a label that sits on
another curve, a leader that points at the wrong place, a caption that says less than the
picture, or a corner with nothing in it. `references/review.md` has the list of blemishes that
have actually occurred and the cold-read test. Fix, rebuild, repeat until a full pass finds
nothing. If no Chromium-based browser is installed, use any browser tool you have with
`audit_svg.js`, and say in your report which checks ran.

### 8. Make it reproducible, and land it

- One command rebuilds it, wired into whatever the project already uses (`make figures`,
  `reproduce.sh figures`): harness command, then figure script. If the project has no such
  script, let the figure script run the harness command itself, and say so.
- Run that command twice and compare the hashes of the SVG. Byte-identical output is what lets
  the figure live in version control and proves nothing in it depends on the clock or the machine.
- Put the figure where it is used (paper, README) with a caption that says what each part shows,
  which sections or tables it corresponds to, and that nothing in it is drawn by hand; name the
  command that regenerates it. `references/review.md` has a template.
- Keep the JSON dump out of version control and the SVG in it. Commit only if the user asks.
- In your report, give the composition and its reasons in two lines, so the user can disagree
  with the design and not only with the details.

## The rules in brief

Each is explained, with the complaint that produced it, in `references/principles.md`.

1. Every picture and number is computed or read from a log; nothing is typed or sketched.
2. Show the real thing: data as pixels, structures with their values, the graph in full.
3. One showcase instance runs through the figure.
4. Every enlarged cut is tied to its source by a frame and a cone.
5. A logarithmic axis has dashed minor grid lines at 2…9 per decade, so it looks logarithmic.
6. Text never overlaps anything; this is audited, not eyeballed.
7. The figure explains itself: every term is defined inside it, in plain words, before it is used.
8. Files in monospace with their extension; named things in one style and colour everywhere.
9. Unlike things are not mixed in one series: a divider and a heading per group, an axis per unit.
10. Each part says how much evidence stands behind it; the marks are not buttons.
11. What loses is drawn as plainly as what wins; caveats are stated in the figure.
12. The script checks what it draws and says so.
13. The layout is designed from the content: two projects, two layouts.

## When the project is not like the examples

- **No harness, only data files or a notebook**: the "harness command" is a small script that
  loads the files and writes the same kind of JSON. The rules do not change.
- **Not Python**: the harness command is written in the project's language; only the figure
  script is Python, and it needs nothing but the standard library.
- **A theory paper**: the real things are the objects themselves: the actual construction at a
  small size, enumerated cases, the proof's dependency graph, a verified computation.
- **The project's own instructions ask for generated illustrations**: an image model cannot
  place exact data or reliable text, so it cannot make this figure. Build it from data and tell
  the user why.
- **Another typeface or script**: `font_metrics.py` writes width tables from the font files;
  `ddfig` reports characters it cannot measure instead of guessing silently.
- **More than seven categories**: the Okabe-Ito colours go to the named things; anonymous
  categories (clusters, classes) take `dd.SOFT8` or a ramp, and never colour alone.

## Things that go wrong

- The figure comes out looking like `examples/hashtable/figures/overview.svg`. That means step
  2 was skipped. Go back to the hero and the destination.
- `python -I` (and Python 3.11+ with `-P`) does not put the script's folder on the path: the
  figure script should do `sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))`.
- Write files with `newline="\n"` (ddfig does) or Windows and Linux will produce different bytes.
- The first headless browser start takes about ten seconds; later ones about one.
- Pictures of data are written at 2-4 times their display size (`png_indexed(..., scale)`); a
  raster written at display size blurs when the reader zooms in.
- Type sized for a page is too small on a slide: choose sizes at the canvas of the destination.
