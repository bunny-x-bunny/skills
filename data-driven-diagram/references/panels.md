# Building blocks

Parts that have worked, each with the `ddfig` calls that draw it. They are parts, not a page:
which of them a figure uses, how large, and where, is decided when you compose it
(`compositions.md`). All code assumes `import ddfig as dd`; `svg` is the canvas; a part draws into
the box it is given and returns the y below itself, so that parts can be chained in whatever
layout you designed.

## Contents

- A note tied to the thing it explains
- The two or three numbers to leave with
- Real instances as pictures
- A picture drawn with shapes
- A picture, what happened on it, and an enlarged cut
- A structure with its values
- A table or memory, slot by slot
- The graph in full
- One traced step, level by level
- Many runs at once
- Rates, and the threshold they imply
- Results against a baseline
- Regimes on a number line
- A map of decisions
- Text beside pictures
- Furniture of the stacked style: head, strip, sections
- Layout arithmetic

## A note tied to the thing it explains

The best place to define a term is at the thing it names.

```python
tx, ty = cell_centre(worst_slot)                 # the target is found in the data, not placed by hand
yb = dd.callout(svg, tx, ty, note_x, note_y,
                f"A key's hash names its **home slot**. If that is taken, the key goes into the next free slot: its "
                f"**displacement**. This key sits {far} slots from home.", width=560, size=11.5)
```

- A ring marks the target; the leader ends at the nearest edge of the note by itself and is drawn
  over a white under-line, so it reads on dark and light pictures alike.
- Choose targets by a rule ("the slot with the largest displacement", "the lowest empty slot
  nearest to column 62") and place the notes by a rule too (in a row under the picture, in the
  order of their targets, never closer than a gap). `examples/hashtable/poster.py` does both.
- `n="a"` puts a letter in a badge before the note, for a sentence elsewhere to refer to.

## The two or three numbers to leave with

```python
sy = dd.stat(svg, x, y, dd.times(miss_ratio), f"fewer probes for a miss at load {load:.2f}", width,
             colour=dd.VERMILION, size=32, status="full") + 34
sy = dd.stat(svg, x, sy, dd.times(price), "the time of a hit: the price of one more comparison per probe", width, status="partial")
```

Large numbers are for the results, and for the price as well as the gain. Each says in plain
words what it measures and carries its evidence mark. More than three or four, and none stands out.

## Real instances as pictures

A row or grid of instances, each drawn from its data, with its real name, three fitted lines and
one small curve on shared axes. `dd.grid` gives the cells.

```python
for (x, y0, cw, ch), it in zip(dd.grid(left, top, width, 150, cols=len(instances)), instances):
    svg.rect(x, y0, cw, ch, fill="#000000", rx=3)
    s = min(cw / it["w"], ch / it["h"])               # fit, keeping the aspect
    svg.image(x + (cw - it["w"] * s) / 2, y0 + (ch - it["h"] * s) / 2, it["w"] * s, it["h"] * s,
              dd.png_indexed(rows_of(it), palette, scale=2))
    svg.text(x, y0 + ch + 17, f"`{it['file']}`", size=12, weight="bold", max_width=cw)
    for q, line in enumerate([f"{dd.thousands(it['w'])} × {dd.thousands(it['h'])} cells · [[{it['rule']}]]", it["what"], it["shown"]]):
        svg.text(x, y0 + ch + 31.5 + 13.5 * q, line, fill=dd.GREY, max_width=cw)
    sy, sh = y0 + ch + 68, 34.0                        # the curve: a share against steps, log x
    X, Y = dd.Log(10, 3e5, x, x + cw), dd.Lin(0, 1, sy + sh, sy)
    svg.rect(x, sy, cw, sh, fill="#f5f5f5")
    dd.log_grid(svg, X, sy, sy + sh)
    dd.curve(svg, it["series"], X, Y, colour=dd.VERMILION, sw=1.3, step=True, area=0)
    svg.text(x + cw - 3, sy + 11, dd.pct(it["late"], 0), weight="bold", anchor="end", fill=dd.VERMILION, halo="#f5f5f5")
```

Every instance gets the same statistic on the same scale, so the row can be compared at a glance.
A very sparse instance is drawn with `dd.density` and `dd.png_grey`, or it vanishes.

## A picture drawn with shapes

Points, segments or cells drawn as vector marks (a scatter of the real data, trajectories, a mesh).

```python
svg.rect(x, y, w, h, fill="#111111", picture=True)     # the ground: tells both audits this is a picture
for (px, py), group in zip(points, groups):
    svg.circle(X(px), Y(py), 1.6, fill=dd.SOFT8[group % 8])
svg.text(X(cx) + 6, Y(cy) + 4, "3", size=10.5, weight="bold", fill="#ffffff", halo="#111111")
```

Without `picture=True` the audits take the picture for empty page and do not check the text on
it. Text on a picture always has a halo in the colour of its ground. Anonymous groups take
`dd.SOFT8`; the Okabe-Ito colours stay with the named things of the project.

## A picture, what happened on it, and an enlarged cut

The showcase instance at cell = pixel, events of one step marked on it, and one region taken apart
beside it.

```python
svg.rect(x0, y, pw, ph, fill="#000000")
svg.image(x0, y, pw, ph, dd.png_indexed(rows, palette, scale=2))
svg.path("".join(f"M{x0 + k * s},{y}v{ph}" for k in range(1, pw // s)), stroke="#ffffff", sw=0.5, opacity=0.16)   # the tiling
for (mx, my) in missed:                                # what happened here: marked, counted in the caption
    svg.rect(x0 + mx, y + my, s, s, fill=dd.VERMILION, opacity=0.32)
    svg.rect(x0 + mx, y + my, s, s, stroke="#ff9d5c", sw=1.1)
# the cut: chosen by a rule (most distinct values, around an event), not by hand
zx, zy, zs = x0 + pw + 26, y + 18, 2.25
svg.cone((qx + qw, qy), (qx + qw, qy + qw), (zx, zy), (zx, zy + qw * zs), split=x0 + pw, axis=0)
svg.rect(qx, qy, qw, qw, stroke="#ffffff", sw=1.8)     # the frame in the picture
svg.image(zx, zy, qw * zs, qw * zs, dd.png_indexed(cut_rows, palette, scale=5))
svg.rect(zx, zy, qw * zs, qw * zs, stroke="#ffffff", sw=1.8)      # the same frame around the enlargement
```

- Choose the cut with a score computed from the data, so that it stays interesting when the data
  changes, and so that nobody can say it was cherry-picked by eye.
- `split` is where the picture ends: the cone's edges are white over the dark picture and grey
  over the page. For a light picture pass `inside=dd.INK`.
- The caption counts what is marked: "1,472 probes for 651 distinct windows, 103 misses (7.0 %,
  marked)".

## A structure with its values

The enlarged cut again, this time as the values the program holds for it.

```python
ids = [[tile_id[(ty + j) * nx + tx + i] for i in range(4)] for j in range(4)]
boxes = dd.cell_grid(svg, ix, zy, ids, 36, 36, blank=EMPTY, blank_text="empty")     # equal IDs share a tint
kx, ky, kw, kh = boxes[(1, 1)]
svg.rect(kx, ky, 2 * kw, 2 * kh, stroke=dd.BLUE, sw=1.8)                            # the 2 x 2 that is a key
svg.text(ex, ey - 6, "the key: the four IDs framed above", size=10.5, fill=dd.BLUE)
dd.cell_grid(svg, ex, ey, [key[:2], key[2:]], 52, 19, tint=None)
svg.arrow(ex + 109, ey + 19, ex + 129, ey + 19)
dd.cell_grid(svg, ex + 134, ey + 9.5, [[value]], 52, 19, tint=lambda v: "#dbe9f6")
```

Show the same thing in both forms side by side ("as cells" / "as IDs: 32 bytes") and check, in
the script, that they agree: step the cells with the reference and compare with the stored value.

## A table or memory, slot by slot

A contiguous run of the real table, one pixel block per slot, coloured by a property of the slot.

```python
classes = [("empty", "#eeeeee"), ("in its home slot", dd.BLUE), ("1 slot further", dd.SKY), ("2 further", dd.ORANGE), ("3 or more", dd.VERMILION)]
rows = [bytes(klass(slot) for slot in table[r * 128:(r + 1) * 128]) for r in range(30)]
svg.image(x, y, 256, 60, dd.png_indexed(rows, [dd.hex_rgb(c) for _, c in classes], scale=4))
for k, (label, colour) in enumerate(classes):
    svg.rect(lx, y + k * 12.6, 8, 8, fill=colour)
    svg.text(lx + 12, y + k * 12.6 + 8, f"{label}: {dd.pct(share[k], 0)}", size=10.5, fill=dd.GREY)   # shares of the whole table
```

Say which part is shown ("the first 3,840 of 1,048,576 slots") and give the whole table's numbers
in the key. Both hashtable examples are built on this, at two sizes.

## The graph in full

```python
from ddgraph import layered, draw_wires
L = layered(preds, x0, x1, top, bottom, in_y=in_y, out_y=out_y)   # preds: {node: [what it reads]}
draw_wires(svg, L, shade=lambda node: share_of_ones[node])        # data on the structure
for node, (gx, gy) in L.pos.items():
    if node in gates:
        svg.circle(gx, gy, 3.0, fill=GATE_COLOUR[gates[node].op], stroke="#ffffff", sw=0.5)
```

- `in_y` and `out_y` pin the ends of the graph beside pictures of the input and output (rows of
  bits, feature maps, tokens), so the graph visibly turns one into the other.
- Put an axis of levels under it, and the counts beside it in large type ("367 gates, depth 25"),
  taken from the graph.
- Evaluate the graph on the showcase instance in the script, compare with the reference, and shade
  the wires by what they carry. `examples/adder/figure.py` is the whole pattern in 190 lines.
- Hundreds of nodes are fine; thousands need the wires thinner (`node_gap`, `wire_gap`) or one
  module of the graph in full and the rest as a count.

## One traced step, level by level

For recursions, batches, layers, rounds: an icicle. One row per level, time or work left to
right, one box per batch whose width is its span; the number in the box is the size of the batch,
and a darker part of the box is the share that needed work.

```python
for level, batches in enumerate(trace):               # trace from the harness hook, in order
    yy = y + level * row_h
    svg.text(x - 6, yy + 11, level_name[level], size=10, anchor="end", fill=dd.GREY)
    for b in batches:
        bx, bw = X(b["start"]), X(b["end"]) - X(b["start"])
        svg.rect(bx, yy, bw - 1, row_h - 1, fill=dd.mix(dd.VERMILION, "#ffffff", 0.75))
        svg.rect(bx, yy, (bw - 1) * b["share"], row_h - 1, fill=dd.mix(dd.VERMILION, "#ffffff", 0.45))
        label = dd.thousands(b["n"]) if dd.text_width(dd.thousands(b["n"]), 9.5) + 3 <= bw else dd.short(b["n"])
        if dd.text_width(label, 9.5) + 3 <= bw:
            svg.text(bx + bw / 2, yy + 10.5, label, size=9.5, anchor="middle", check=False)
```

Two instances side by side, one where almost everything is known and one where everything is
new, make the point better than any one of them. A label over a two-tone box is the one case
where `check=False` is right; print it only if it fits.

## Many runs at once

Every run as a faint line, the one or two that the figure follows in full strength on top.

```python
for run in runs:
    dd.curve(svg, run["series"], X, Y, colour=COLOUR[run["method"]], sw=0.8, alpha=0.25)
dd.curve(svg, followed["series"], X, Y, colour=COLOUR[followed["method"]], sw=2.2)
```

The crowd shows the spread without a summary statistic; the reader sees whether the followed run
is typical. Mark medians with a tick, not with another line.

Where each run is one number (a final score, an ending), one dot per run along the axis:

```python
at = dd.swarm(svg, [r["final"] for r in runs], Y, centre_x, r=3, vertical=True,
              colours=[COLOUR[r["method"]] for r in runs])
fx, fy = at[runs.index(followed)]
svg.circle(fx, fy, 5.5, fill="none", stroke=dd.INK, sw=1.2)      # the run the figure follows
```

"17 of 40 ended above 5" is then seventeen dots above a line that the reader can count, and the
heap shows the distribution. A bar of the count would hide the other 23.

## Rates, and the threshold they imply

Measured rates on one log number line, with the ratios between them as brackets, then the
quantity that the ratio decides as lines crossing 1×.

```python
X = dd.Log(5e8, 3e12, x0, x0 + w)
dd.log_grid(svg, X, ry - 26, ry + 8, major="#dcdcdc")
svg.line(x0, ry, x0 + w, ry, stroke=dd.INK, sw=1, check=False)
for name, v, colour in rates:
    svg.circle(X(v), ry, 5, fill=colour)
for (a, b, label, colour), by in zip(brackets, bracket_ys):        # ρ = one rate over another
    svg.path(f"M{X(a):.1f},{ry - 7}V{by}H{X(b):.1f}V{ry - 7}", stroke=colour, sw=1.4)
    svg.text((X(a) + X(b)) / 2, by - 4.5, label, weight="bold", anchor="middle", fill=colour, halo="#ffffff")
```

Under it, the consequence: value over cost per size, one line per named thing, a dashed line at
1× labelled in words ("1×: a hit saves what a probe costs"), an open circle where each line first
exceeds it. Compute the crossing; do not place it.

For plain bars: `dd.bars(svg, x, y, w, [("[[Hutton32]] and [[Hutton32b]], 32 states", rows_a), ("[[Life]], 2 states", rows_b)])`.
All bars of one call share an axis, so they share a unit; another unit is another call
(`axis=False` when the values at the bars' ends say enough).

## Results against a baseline

```python
rows = [
    dict(group="[[Hutton32]], 32 states", name="`lotr1.ANSI-1M.rle`, first period", note="9.5 M cells, dense, all new",
         points=[("gpu", ratio)]),
    dict(group="[[Hutton32]], 32 states", name="`lotr1.ANSI-1M.rle`, once learned", note="the memo holds a period",
         points=[("gpu", fast), ("learn", with_setup, "min")]),            # a lower bound: printed with ≥
    dict(group="[[Life]], 2 states", name="nine eventful patterns", note="2^{20} or 2^{24} generations", range=("cpu", lo, hi)),
]
kinds = {"gpu": ("dot", "on the GPU, measured and verified"), "learn": ("ring", "the same, with the time to fill the memo"),
         "cpu": ("diamond", "the recursion on one CPU thread")}
y = dd.ratio_chart(svg, x, y, w, rows, kinds, 10 ** -2.6, 10 ** 6.75, label_w=218, behind="Golly faster", ahead="GHL part faster")
```

- Rows are named by what was run, a file or a configuration, with sizes in the note.
- One shape per kind of evidence; the key names them.
- Put the conditions of the comparison in the heading above the chart ("against Golly 5.1,
  HashLife at its best step size") and one honest sentence under it about where the baseline
  wins and why.
- With two or three results, `dd.stat` says it better than a chart.

## Regimes on a number line

When a model splits a quantity into regimes (too small to pay, pays at one setting, at another):
a log axis as a strip of coloured bands with the thresholds between them, and the real instances
marked on it by name, leaders where names would collide (`dd.spread`).

## A map of decisions

When the system decides per region, per layer or per item: the instance as a dim thumbnail, each
region outlined in the colour of its decision, numbered marks on the parts, and a key that names
the parts by file. Count the regions per decision in the key; give the span the map covers.

## Text beside pictures

```python
yy = svg.para(tx, y + 12, f"Counted in a table of {dd.thousands(slots)} slots ...", width)
yy = svg.para(tx, yy + 6, "The pale bands are Knuth's formulas ...", width)
```

- Short paragraphs beside what they explain, grey; the one sentence that carries the part in ink.
- First what is shown, then what to see in it, then what was checked.
- A sentence that contains a number is an f-string.
- `para` returns the next baseline: chain them, and return `max()` of the columns' bottoms.

## Furniture of the stacked style: head, strip, sections

For the composition "stacked claims with a strip" (`compositions.md`), and only for it:

```python
dd.entities({"Hutton32b": dd.BLUE, "Life": dd.GREEN})  # [[Hutton32b]] takes its colour everywhere
y = dd.title(svg, "GPU HashLife (GHL)", "HashLife above a memo floor, the rule as a circuit below it",
             note="Every picture and number is drawn from the measurement harness.",
             intro="How a universe advances, and the words used below; the number on a step is the panel that shows it.")
items = [
    dict(n=3, title="The universe: a grid of tile IDs", picture=pic_tiles,
         text="The cells are cut into square **tiles**. Equal tiles get the same **ID**, so the GPU holds a grid of numbers, not cells."),
    dict(n=5, title="Measured rates set the floor", picture=pic_floor, style="frame", at=(1, 0), text="..."),
]
boxes, bottom = dd.cards(svg, svg.M, y, svg.CW, items, cols=4)
dd.connect(svg, boxes[0], boxes[1])                  # an arrow; label= only if it fits in the gap
dd.status_legend(svg, x_of_free_slot, y + 19.3, "How far each part is built",
                 [("full", "built and measured on the GPU"), ("partial", "the CPU reference engine: not yet on the GPU"),
                  ("model", "model: operation counts at measured rates")], width=room)
y = dd.section(svg, bottom + 18, 1, "Six universes, two rules", "real patterns, named by their files", [("full", "measured")])
```

- A card is a step of the method or, with `style="frame"`, something that configures the steps.
  Arrows only where there is a flow.
- A pictogram is a function `(svg, x_right, y_centre)` drawing about 30 × 18 px of plain shapes.
- A card's title has the card's width less about 85 px (padding, badge, pictogram): roughly
  190 px at four columns, 130 at five, 100 at six. The audit tells you when it does not fit.
- `dd.status_legend` and `dd.status_row` are useful in any composition; `section(n=None)` gives
  a heading without a number.

## Layout arithmetic

- Work in px at the canvas of the destination; margins 20 to 28; a gap of 14 to 48 between columns.
- Fix the sizes of pictures by their data (cell = pixel, or an integer multiple) and let text
  take the rest.
- A part takes its box and returns the y below everything it drew; columns end at the `max()` of
  their bottoms.
- Things that must align (a grid under a picture, a frame around a cut, a chart beside a picture
  of the same height) are computed from the same variables, never positioned separately.
- When the audit reports a collision, change the layout rule, not the one coordinate: next
  week's data will collide somewhere else.
