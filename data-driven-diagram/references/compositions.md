# Composing the figure

*"Across all test runs so far, all diagrams share the exact same layout and look too similar."*

That was said of the first figures made with this skill, and it was the skill's fault: it had
described one layout (a head, a strip of cards, numbered panels stacked down the page) as if it
were the method. It is not. The method is a discipline: everything computed, everything checked,
everything explained in the figure. The layout is a design decision that you make anew for each
project, from its content. Two figures for different projects should look alike only where their
content is alike.

## Contents

- Decide four things first
- Compositions that have worked
- Where the explanations live
- How the reader is led
- Size and shape
- A sketch before any code
- Signs that you copied instead of composed

## Decide four things first

1. **The hero.** What is the one real thing a reader should see first, and remember? The full
   network, the two tables side by side, the trajectory, the reconstructed image, the curve that
   bends. It gets the most area, often half the figure. If you cannot name a hero, the content
   is several claims of equal weight, and that too is an answer (see the stacked composition).
2. **The reading path.** In what order must things be seen for the claim to land: left to right
   as a process, outside in as a zoom, top to bottom as an argument, or centre out from the hero?
3. **The destination.** A paper's page (portrait, read closely, text of 10 px at 1200 px wide is
   fine), a README (scrolls: can be tall), a slide (16:9, seen from afar: few words, large type),
   a poster (seen from two metres, then from thirty centimetres: one hero, layers of detail).
4. **The vocabulary load.** How many terms does an outsider need? Two or three can be defined
   where they occur. Eight need a place of their own.

Write the four answers down in a sentence each before sketching. They are the reason for the
layout, and you will state them when you report.

## Compositions that have worked

Starting points, to combine and bend. Each is listed with the content it suits.

**Hero with notes.** One large real picture takes most of the area; notes with leaders define
its parts where they are; a column or band beside it carries one chart and two or three large
numbers. For work whose subject is an object: a structure, a circuit, a model, a dataset, an
apparatus. `examples/hashtable/poster.py`.

```
┌─────────────────────────────┬───────────┐
│ note ─○                     │  chart    │
│     HERO PICTURE            ├───────────┤
│              ○─ note        │  8.7×     │
├─────────────────────────────┤  12×      │
│     its counterpart   ○     │  1.9×     │
│  note ────────────────┘     │  key      │
└─────────────────────────────┴───────────┘
```

**Zoom ladder.** The same object at three or four scales, each cut framed in the one before and
joined to it by a cone: whole, region, element, the element's inner workings. For multi-scale
systems, and whenever the claim is "this large thing is made of these small things".

```
┌────────────┐   ┌───────┐   ┌─────┐   ┌──────────────┐
│ whole    □─┼──▶│ region│──▶│ cell│──▶│ what a cell  │
│            │   │    □──┼─  │     │   │ is made of   │
└────────────┘   └───────┘   └─────┘   └──────────────┘
```

**Stages of a process.** Left to right, the real data after each stage of the method, with the
operation named on the arrow between; under each stage one sentence and one measured number. For
pipelines, compilers, training procedures, protocols. The stages are pictures of data, never
boxes with names.

**Two sides.** The method and its baseline (or before and after) mirrored about a centre line:
same rows, same scales, differences marked where they occur. For claims of the form "the same
except for". `examples/adder/figure.py` is close to this, one above the other.

**Small multiples.** A grid of many real instances under one or two conditions, identical axes,
one statistic each; the pattern across the grid is the message. For claims about breadth,
robustness, or a trend over a parameter.

**A trace along time.** A horizontal axis of time or steps; above it snapshots of the state at
chosen moments, below it the quantities that change, aligned to the same axis. For dynamics,
training runs, simulations, executions.

**One result with its evidence pinned on.** One large chart of the main result; selected points
in it are joined to small pictures of the instances they stand for. For papers with one
headline result and the question "what does a point on this curve look like?".

**Stacked claims with a strip.** A strip of cards defines the vocabulary; numbered panels
follow, one claim each, of equal weight. For a paper with four or five separate claims and a
method of several steps with many terms. The figure this skill grew out of is of this kind, and
so is `examples/hashtable/figure.py`. It is the right choice less often than it is the easy one.

Most good figures are two of these: a hero with notes whose side column is a small trace; a
zoom ladder that ends in two sides.

## Where the explanations live

The figure must explain itself in every composition. How is a choice:

- **At the thing**: a note with a leader to the element it names (`dd.callout`). The strongest
  form, since the reader learns the word while looking at what it means. Use it whenever the
  term has a place in a picture.
- **On the arrows and axes**: the name of an operation on the arrow that performs it; the
  meaning of a quantity in the axis title ("load: the share of slots in use").
- **In a strip of steps**: when the method is a sequence and its terms build on each other
  (`dd.cards`).
- **In a key**: for colours, marks and line styles, next to where they are used, not in a
  distant corner.
- **In a sentence under a panel**: for what was measured and what was checked.

Whichever it is, each term is defined once, in plain words, before or where it is first needed.

## How the reader is led

Numbers on panels are one device, suited to a paper whose caption refers to (1), (2), (3). Others:
position alone (a left-to-right process needs no numbers), arrows and cones, a hero whose size
says "start here", lettered notes that the text refers to. Use the lightest device that works.

## Size and shape

- Set the canvas to the destination: about 1200 px wide for a paper's column or a README,
  1280 × 720 for a slide, wider for a poster. Text sizes are chosen for that natural size:
  nothing below 9.5 px for a page read closely, nothing below 11 to 12 px for a slide.
- Let the hero fix the grid: its pixel size comes from its data (one cell = n px), the rest of
  the layout is what remains.
- Tall is fine where the reader scrolls and bad on a slide. If the content will not fit a
  slide, it is two slides.

## A sketch before any code

Draw the layout as a rough box diagram in your plan, with proportions and with the hero marked,
and add one line of reasons:

```
hero: the two slot maps (60 % of the area), because the claim is visible in them
path: maps first, then the cost curve, then three numbers
for: a slide, 1280 x 720; terms: 6, all with a place in the maps -> notes at the thing
```

If the sketch has the same boxes as an example in this skill, check that the reasons are your
project's and not the example's.

## Signs that you copied instead of composed

- The figure has a head, a strip, numbered sections and a ratio chart at the bottom, and you
  cannot say why the content needs each of them.
- The most impressive real thing in the project is in a panel the same size as the others.
- The intro line or a caption is a sentence from an example with the nouns replaced.
- Every helper under "furniture" in `ddfig.py` was called, in the order it appears there.
