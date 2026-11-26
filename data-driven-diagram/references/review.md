# Audit, look, land

A dense figure is never right the first time. Plan for three or four rounds of this loop; each is
quick.

## Contents

- The loop
- What the audits check
- Looking: the list of blemishes
- The cold-read test
- Reproducibility
- Landing it: caption and paper
- Final checklist

## The loop

```
python figure.py                                              # ddfig's audit runs in save()
python <skill>/scripts/figcheck.py audit figures/overview.svg # the browser's layout: must pass
python <skill>/scripts/figcheck.py shoot figures/overview.svg shots
```

then open `shots/overview.png` for composition and **every** `shots/tile_*.png` for detail. For a
second look at one place: `figcheck.py shoot figure.svg shots --region X,Y,W,H --zoom 3`.

When `figure.py` stops with `LayoutError`, it lists what collides. To see where, run it once with
`DDFIG_DEBUG=1`: the figure is written with the places marked in red.

## What the audits check

| check | ddfig (font tables) | figcheck (browser) |
|---|---|---|
| text on text | yes | yes |
| text leaving the page | yes | yes |
| text on a picture without a halo | yes | yes |
| ... on a picture drawn with shapes | if its ground is `rect(picture=True)` | the same |
| a `line` through text that has no halo | yes | yes |
| text wider than the room it was given (`max_width=`) | yes | |
| characters it could not measure | yes | |
| text straddling the edge of a box or mark | | listed, to look at |
| font size below 9 px | | listed, to look at |

The two agree when the viewer has Arial, Helvetica or Liberation Sans. They can differ by a
fraction of a pixel: a leader that grazes the corner of a letter may pass one and fail the other.
Believe the browser, and fix the rule that placed the thing, not the one coordinate. Where the
browser finds much that ddfig did not, a font was substituted: check the font stack and
`UNMEASURED`.

To exempt something on purpose: `check=False` on that one text or line, with a comment saying why
(a number centred on a two-tone bar; a rule that is meant to pass behind a haloed label).
A halo is the right fix for text over a picture or grid lines; it is the wrong fix for text over
other text.

Without a Chromium-based browser, open the SVG in whatever browser tool is at hand and evaluate
`scripts/audit_svg.js` in the page; it returns the same JSON. Report which of the two audits ran.

## Looking: the list of blemishes

All of these got past an audit at least once.

**Composition**
- the figure has the skeleton of one of this skill's examples (head, strip, numbered sections,
  ratio chart last) and no reason of its own for it: go back to `compositions.md`;
- the most impressive real thing sits in a part no larger than the others;
- an empty corner, or a column of text much shorter than the picture beside it;
- a part so full that its one important thing does not stand out;
- headings that name components instead of making claims;
- type sized for a page on a figure meant for a slide.

**Labels**
- a label that belongs to one curve sits on another curve (its halo even cuts that curve);
- a label straddles a reference line (the 1× axis) and is cut in two by it: move it to the other
  side of its point;
- two end labels that the spread moved apart no longer show which curve is whose: add leaders;
- a leader line passes through another label, or grazes its own note;
- notes placed by coordinates collide as soon as the data moves their targets;
- a caption under a small picture runs into the chart next to it.

**Meaning**
- a term used in a panel that the figure never explains;
- a key lists numbers and names in an order that can be misread ("2 6 × chaotic.rle");
- a number without its unit, or a time without the span it covers;
- "seven idle circuits" where the data has eight: any count written in words must be computed;
- two formats for one kind of number (230× here, 227× in the paper);
- a lower bound rounded up; a range printed with different precision at its two ends;
- a colour that means one thing in one part and another in the next;
- evidence labels drawn as filled boxes, which read as buttons.

**Zooms and correspondences**
- an enlargement with no frame in the source picture, or a frame with no cone;
- a cone that crosses unrelated content;
- the same object in two parts with nothing saying it is the same.

**Scales**
- a log axis without the dashed minor lines, or with them too faint to see at natural size;
- a linear and a log axis that look alike;
- an axis with one labelled tick;
- quantities of different units on one axis.

## The cold-read test

Before calling it done, read the figure as someone who has not seen the paper, top to bottom:

1. For every noun and symbol, find where **the figure** explains it. Anything unexplained gets a
   note at the thing, a clause where it is used, or a card.
2. For every picture: can you say what one pixel, one box, one line stands for?
3. For every number: its unit, what it was measured on, and whether it was measured or modelled.
4. For every part: say its claim in one sentence without looking at its heading. Does the
   heading say the same?
5. For the whole: what is seen first? Is that the thing that matters most?

A fresh reader does this better than the author. If you can hand the rendered tiles to another
agent or person, ask them only: "What do these terms mean, and what does this figure claim?" and
compare the answer with the paper.

## Reproducibility

```
<the project's one command for figures>      # harness dump, then the figure script
sha1sum figures/overview.svg                 # note it
<the same command again>
sha1sum figures/overview.svg                 # must be identical
```

If the hash moves: a clock, a random seed, an unordered container or a float printed at full
precision has reached the figure. Find it in the JSON first (hash that too).

Record how long the command takes; if it is more than a few minutes, the harness section that
dominates should be given a smaller instance.

## Landing it: caption and paper

The caption does three jobs: says what each part shows and where the paper treats it, says how
the figure was made, and repeats the one caveat that matters. Its shape follows the figure's; for
a figure of numbered panels, for instance:

> *NAME at a glance.* (1) … as … , each with … . (2) … drawn from … while it … (Section …).
> (3) … against … (Table …). Nothing in it is drawn by hand: `COMMAND` runs … on … and
> `figure.py` draws its output and the logged …, checking … on … . A filled circle marks what
> was …, a diamond what was …, a dashed circle what is … .

Then:

- every number that appears in both the figure and the paper must be the same string; print the
  log module's values and compare them with the tables. Report mismatches; change the paper's
  numbers only if the user asked you to edit it;
- list the harness command, the figure script and the copied `ddfig.py` wherever the paper lists
  its artefacts or its reproduction steps;
- the dump stays out of version control; the SVG, the script and the logs go in. Commit when the
  user asks.

## Final checklist

- [ ] The composition was designed for this content: you can say in a sentence why its largest
      element is the largest, and it is not an example's layout refilled.
- [ ] The figure script contains no typed result; the few named constants cite their source.
- [ ] Every claim a part makes is asserted in the script on the data it draws.
- [ ] `figure.py` writes the figure without `LayoutError`; `figcheck.py audit` passes.
- [ ] Every tile was looked at after the last change.
- [ ] Every term is defined in the figure; files are in monospace with extensions; named things
      have one style and colour.
- [ ] Every log axis has its dashed minor grid; every enlargement has its frame and cone.
- [ ] Each part says how much evidence stands behind it, and the figure says what the marks mean.
- [ ] Losses, bounds and caveats are in the figure.
- [ ] One command rebuilds it; two runs give the same bytes.
- [ ] The caption is in place and its numbers match the paper.
