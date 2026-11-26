"""The overview figure of the miniature project in this folder, written the way the skill asks:

  * out/overview.json   counts, recomputed by `python harness.py overview` (exact, deterministic)
  * logs/bench.txt      wall-clock times, measured once by `python harness.py bench` and kept
  * nothing typed in: every picture, number and sentence with a number in it is built from those

While drawing, the script checks what it shows (the asserts): that both tables hold the same keys
in the same slots, that the distances from home add up to the same total, that the two curves said
to coincide are the same numbers.

    python harness.py overview && python figure.py        ->  figures/overview.svg
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "scripts"))     # in a project: copy ddfig.py next to this file instead
import ddfig as dd  # noqa: E402
from ddfig import BLUE, GREY, INK, MID, NUM, VERMILION, Lin, Log, Logs, Svg, thousands, times  # noqa: E402

DATA = os.path.join(HERE, "out", "overview.json")
OUT = os.path.join(HERE, "figures", "overview.svg")
RULES = ("linear", "robinhood")
NAME = {"linear": "linear probing", "robinhood": "Robin Hood"}
COLOUR = {"linear": BLUE, "robinhood": VERMILION}
dd.entities({NAME[r]: COLOUR[r] for r in RULES})        # a rule's name in a sentence has the colour of its curve

# distance from home in classes: one palette for both tables, tied to neither rule
CLASSES = ["empty", "at home", "1–3 slots away", "4–15", "16–63", "64 or more"]
CLASS_COLOUR = ["#ececec", "#fde725", "#5ec962", "#21918c", "#3b528b", "#440154"]


def klass(d):
    return 0 if d < 0 else 1 if d == 0 else 2 if d <= 3 else 3 if d <= 15 else 4 if d <= 63 else 5


# ---- the strip: how it works, and the words --------------------------------------------------------

def _slots(svg, xr, yc, fills):
    for k, f in enumerate(fills):
        svg.rect(xr - 7 * len(fills) + k * 7, yc - 3.5, 6, 7, fill=f)


def pic_home(svg, xr, yc):
    _slots(svg, xr, yc, ["#d2d2d2", BLUE, "#d2d2d2", "#d2d2d2", "#d2d2d2"])


def pic_probe(svg, xr, yc):
    _slots(svg, xr, yc + 3, ["#d2d2d2", "#8f8f8f", "#8f8f8f", BLUE, "#d2d2d2"])
    svg.path(f"M{xr - 25:.1f},{yc - 2:.1f}q3.5,-7 7,0q3.5,-7 7,0", stroke=INK, sw=0.9)


def pic_lookup(svg, xr, yc):
    _slots(svg, xr - 12, yc, ["#8f8f8f", "#8f8f8f", "#8f8f8f", "#ffffff"])
    svg.rect(xr - 19, yc - 3.5, 6, 7, stroke="#8f8f8f", sw=0.8)
    svg.path(f"M{xr - 9:.1f},{yc + 0.2:.1f}l2.6,2.8l4.6,-5.6", stroke=INK, sw=1.4)


def pic_swap(svg, xr, yc):
    svg.rect(xr - 30, yc - 3.5, 8, 7, fill=VERMILION)
    svg.rect(xr - 9, yc - 3.5, 8, 7, fill="#8f8f8f")
    svg.path(f"M{xr - 22:.1f},{yc - 5:.1f}q7,-6 13,0", stroke=INK, sw=0.9, arrow=True)
    svg.path(f"M{xr - 9:.1f},{yc + 5:.1f}q-7,6 -13,0", stroke=INK, sw=0.9, arrow=True)


def strip(svg, y):
    items = [
        dict(n=1, title="A key has a home slot", picture=pic_home,
             text="The table is a row of **slots**. A hash of the key names one of them, its **home slot**: the place to look first."),
        dict(n=1, title="Taken? On to the next", picture=pic_probe,
             text="If that slot is taken, the key goes into the next free one: **linear probing**. How far from home it ends up is its **displacement**."),
        dict(n=2, title="Looking a key up", picture=pic_lookup,
             text="A lookup walks the same way. Every slot it looks at is a **probe**. A key that is there is a **hit**; one that is not, a **miss**, shows only at an empty slot."),
        dict(n=3, title="Robin Hood's rule", picture=pic_swap, style="frame",
             text="[[Robin Hood]] changes one thing: when two keys want a slot, the one further from home gets it and the other moves on."),
    ]
    boxes, bottom = dd.cards(svg, svg.M, y, svg.CW, items, cols=5)
    dd.connect(svg, boxes[0], boxes[1])
    dd.connect(svg, boxes[1], boxes[2])
    x, _, w, _ = boxes[3]
    lx = x + w + 22 + 10
    dd.status_legend(svg, lx, y + 19.3, "Where each number comes from", [
        ("full", "counted by `harness.py`: exact, the same on every run"),
        ("partial", "timed once, on one machine: `logs/bench.txt`"),
        ("model", "a formula, not an observation")], width=svg.W - svg.M - lx)
    return bottom + 18


# ---- 1. the two tables, slot by slot ---------------------------------------------------------------

def panel_tables(svg, y, D):
    m = D["map"]
    cols, px = 128, 4
    rows_n = m["slots"] // cols
    w, h = cols * px, rows_n * px
    disp = {r: m[r]["disp"] for r in RULES}

    # what the picture claims, checked on the data it is drawn from
    taken = {r: [i for i, d in enumerate(disp[r]) if d >= 0] for r in RULES}
    assert taken["linear"] == taken["robinhood"], "the two rules fill different slots"
    for r in RULES:
        assert sorted(o for o in m[r]["order"] if o >= 0) == list(range(m["keys"])), "a key is missing or doubled"
    total = {r: sum(d for d in disp[r] if d >= 0) for r in RULES}
    assert total["linear"] == total["robinhood"], "the distances from home do not add up to the same"
    far = {r: max(disp[r]) for r in RULES}

    # the enlarged cut: 24 slots of one row of the picture, around the key that linear probing pushed furthest
    n_cut = 24
    worst = disp["linear"].index(far["linear"])
    start = worst // cols * cols + min(max(worst % cols - n_cut // 2, 0), cols - n_cut)
    palette = [dd.hex_rgb(c) for c in CLASS_COLOUR]
    xs = {"linear": svg.M, "robinhood": svg.W - svg.M - w}
    ry, gy, ch = y + 22, y + 22 + h + 44, 20.0
    cw = w / n_cut
    for r in RULES:
        x = xs[r]
        svg.text(x, y + 12, f"[[{NAME[r]}]]", size=13)
        svg.text(x + w, y + 12, f"the furthest key is {far[r]} slots from home", anchor="end", fill=GREY)
        rows = [bytes(klass(d) for d in disp[r][j * cols:(j + 1) * cols]) for j in range(rows_n)]
        svg.image(x, ry, w, h, dd.png_indexed(rows, palette, 8))
        cx, cy = x + (start % cols) * px, ry + (start // cols) * px
        svg.cone((cx, cy + px), (cx + n_cut * px, cy + px), (x, gy), (x + w, gy), split=ry + h, axis=1, inside=INK, outside=MID)
        svg.rect(cx - 1, cy - 1, n_cut * px + 2, px + 2, stroke=INK, sw=1.2)
        dd.cell_grid(svg, x, gy, [disp[r][start:start + n_cut]], cw, ch, blank=-1, tint=lambda d: dd.mix(CLASS_COLOUR[klass(d)], "#ffffff", 0.6))
        svg.text(x, gy + ch + 13, f"slots {thousands(start)} to {thousands(start + n_cut - 1)}: how far each key sits from home", size=10, fill=GREY)
    # the key of the colours, between the two pictures
    lx = svg.M + w + 22
    for k, (label, colour) in enumerate(zip(CLASSES, CLASS_COLOUR)):
        svg.rect(lx, ry + 6 + k * 19, 10, 10, fill=colour, stroke=MID if k == 0 else None, sw=0.5)
        svg.text(lx + 15, ry + 15 + k * 19, label, size=10.5, fill=GREY)
    mean = total["linear"] / m["keys"]
    return svg.para(svg.M, gy + ch + 36,
                    f"Two tables of {thousands(m['slots'])} slots, one cell per slot, row after row, with the same {thousands(m['keys'])} keys put in in the same order "
                    f"(load {m['load']:.2f}). Which slots are taken does not depend on the rule, only who sits where: the two pictures have the same empty slots, and the "
                    f"distances from home add up to the same {thousands(total['linear'])} in both, {mean:.2f} per key (checked while drawing). What differs is how that total "
                    f"is shared out. [[{NAME['linear']}]] leaves the keys that came last far out, up to {far['linear']} slots; [[{NAME['robinhood']}]] keeps every key within "
                    f"{far['robinhood']}.", svg.CW, size=11.5, fill=INK)


# ---- 2. probes per lookup against load -------------------------------------------------------------

def panel_load(svg, y, D):
    s = D["series"]
    loads = s["loads"]
    lin, rob = s["linear"], s["robinhood"]
    assert all(a["hit_mean"] == b["hit_mean"] and a["insert_mean"] == b["insert_mean"] for a, b in zip(lin, rob)), "the means differ"
    x0, cw, ch = svg.M + 40, 520.0, 204.0
    top = y + 20
    X, Y = Lin(0.05, 0.98, x0, x0 + cw), Log(1, 3000, top + ch, top)
    svg.text(x0, y + 10, "probes per lookup", fill=GREY)
    svg.rect(x0, top, cw, ch, fill="#f5f5f5")
    dd.log_grid(svg, Y, x0, x0 + cw, vertical=False)
    ticks = [0.1, 0.3, 0.5, 0.7, 0.9]
    dd.lin_grid(svg, X, top, top + ch, ticks=ticks, colour="#ffffff")
    for e in Y.decades():
        svg.text(x0 - 6, Y(10.0 ** e) + 3.5, dd.pow10(e), size=10, anchor="end", fill=GREY)
    for v in ticks:
        svg.text(X(v), top + ch + 13, f"{v:.1f}", size=10, anchor="middle", fill=GREY)
    svg.text(x0 + cw, top + ch + 28, "load α: the share of slots in use", size=10.5, anchor="end", fill=GREY)

    # the model, as pale bands under the counts: Knuth's formulas for linear probing
    grid = [0.05 + 0.005 * i for i in range(181)]
    knuth = {"hit": lambda a: 0.5 * (1 + 1 / (1 - a)), "miss": lambda a: 0.5 * (1 + 1 / (1 - a) ** 2)}
    for f in knuth.values():
        dd.curve(svg, [(a, f(a)) for a in grid], X, Y, colour="#c9c9c9", sw=6)
    series = [
        ("the worst hit, [[linear probing]]", lin, "hit_max", BLUE, 1.0),
        ("a miss, [[linear probing]]", lin, "miss_mean", BLUE, 2.0),
        ("the worst hit, [[Robin Hood]]", rob, "hit_max", VERMILION, 1.0),
        ("a miss, [[Robin Hood]]", rob, "miss_mean", VERMILION, 2.0),
        ("a hit, either rule", lin, "hit_mean", INK, 2.0),
    ]
    for _, rows, key, colour, sw in series:
        pts = [(a, r[key]) for a, r in zip(loads, rows)]
        dd.curve(svg, pts, X, Y, colour=colour, sw=sw)
        for a, v in pts:
            svg.circle(X(a), Y(v), 2.4 if sw > 1 else 1.9, fill=colour)
    # the names at the ends of the curves, kept apart
    ends = [Y(rows[-1][key]) for _, rows, key, _, _ in series]
    for (label, _, _, colour, _), want, at in zip(series, ends, dd.spread(ends, 13.5)):
        ex = X(loads[-1])
        svg.line(ex + 4, want, ex + 14, at, stroke=colour, sw=0.8, check=False)
        svg.text(ex + 17, at + 3.6, label, size=10.5, fill=GREY)

    i90, last = loads.index(0.9), len(loads) - 1
    tx = x0 + cw + 200
    tw = svg.W - svg.M - tx
    yy = svg.para(tx, y + 12, f"Counted in a table of {thousands(s['slots'])} slots that is filled step by step; the misses with {thousands(s['absent'])} keys that are "
                  "not in it. One probe means the key was at home.", tw)
    yy = svg.para(tx, yy + 6, "The pale bands are Knuth's formulas for linear probing: ½(1 + 1/(1−α)) for a hit and ½(1 + 1/(1−α)^{2}) for a miss. "
                  f"At α = {loads[i90]:.2f} they give {knuth['hit'](loads[i90]):.2f} and {knuth['miss'](loads[i90]):.1f}; "
                  f"the counts are {lin[i90]['hit_mean']:.2f} and {lin[i90]['miss_mean']:.1f}.", tw)
    yy = svg.para(tx, yy + 6, f"[[Robin Hood]] leaves the average hit where it was: the two rules give the same number at every load (checked), so one curve stands for both. "
                  f"It shortens the worst hit, {rob[last]['hit_max']} probes instead of {thousands(lin[last]['hit_max'])} at α = {loads[last]:.2f}, and a miss can stop "
                  "at the first key that sits closer to home than the walk is long.", tw)
    return max(top + ch + 38, yy)


# ---- 3. against linear probing ---------------------------------------------------------------------

def panel_ratio(svg, y, D, logs):
    s = D["series"]
    rows, quoted = [], {}
    for load in (0.5, 0.9):
        i = s["loads"].index(load)
        l, r = s["linear"][i], s["robinhood"][i]
        t = {rule: dict(zip(("hit", "miss", "insert"), logs.find("bench.txt", rf"^load {load:.2f} {rule}\s+hit\s+{NUM} ns\s+miss\s+{NUM} ns\s+insert\s+{NUM} ns")))
             for rule in RULES}
        group = f"at load {load:.2f}"
        ratio = {k: t["linear"][k] / t["robinhood"][k] for k in ("hit", "miss", "insert")}
        quoted[load] = dict(ratio, miss_count=l["miss_mean"] / r["miss_mean"])
        rows += [
            dict(group=group, name="lookup, the key is there", note="a hit", points=[("count", l["hit_mean"] / r["hit_mean"]), ("time", ratio["hit"])]),
            dict(group=group, name="lookup, the key is not there", note="a miss", points=[("count", quoted[load]["miss_count"]), ("time", ratio["miss"])]),
            dict(group=group, name="insert", note=f"the same probes; {r['insert_moves']:.1f} keys moved on per insert", points=[("count", l["insert_mean"] / r["insert_mean"]), ("time", ratio["insert"])]),
            dict(group=group, name="the worst hit", note=f"{l['hit_max']} probes against {r['hit_max']}", points=[("count", l["hit_max"] / r["hit_max"])]),
        ]
    kinds = {"count": ("dot", "probes: counted"), "time": ("diamond", "time per operation: measured on one machine")}
    cw = 720
    bottom = dd.ratio_chart(svg, svg.M, y, cw, rows, kinds, 0.3, 30, label_w=236, behind="[[linear probing]] cheaper", ahead="[[Robin Hood]] cheaper", colour=VERMILION)
    q = quoted[0.9]
    tx = svg.M + cw + 30
    tw = svg.W - svg.M - tx
    yy = svg.para(tx, y + 24, f"How many times cheaper [[Robin Hood]] is than [[linear probing]]: at load 0.90 a miss takes {times(q['miss_count'])[:-1]} times fewer probes.", tw)
    yy = svg.para(tx, yy + 6, f"The clock agrees in direction, not in size: that miss is {times(q['miss'])[:-1]} times faster, and a hit, although it looks at the same slots, "
                  f"takes {1 / q['hit']:.1f} times as long. This table is plain Python, where the one extra comparison per probe costs as much as the probe.", tw)
    yy = svg.para(tx, yy + 6, "Times are medians of five runs on one machine, kept in `logs/bench.txt`; the counts are exact and are recomputed whenever the figure is built.", tw)
    return max(bottom, yy)


# ---- composition -----------------------------------------------------------------------------------

def build():
    if not os.path.exists(DATA):
        sys.exit("out/overview.json is missing: run `python harness.py overview` first")
    with open(DATA, encoding="utf-8") as f:
        D = json.load(f)
    logs = Logs(os.path.join(HERE, "logs"))
    svg = Svg(1200)
    y = dd.title(svg, "Robin Hood hashing", "the same average walk to a key, a far shorter worst one",
                 note="Every picture and number is computed by `harness.py` or read from its log.",
                 intro="How a hash table with open addressing finds a key, and the words used below; the number on a card is the panel that shows it.")
    y = strip(svg, y)
    y = dd.section(svg, y, 1, "Two tables, the same keys, slot by slot", "colour: how far a key sits from its home slot", [("full", "counted by the harness")])
    y = panel_tables(svg, y, D)
    y = dd.section(svg, y + 4, 2, "What a lookup costs as the table fills", None, [("full", "counted"), ("model", "pale bands: Knuth's formulas")])
    y = panel_load(svg, y, D)
    y = dd.section(svg, y + 10, 3, "Against linear probing", "above 1×, Robin Hood is the cheaper one", [("full", "probes: counted"), ("partial", "time: one machine")])
    y = panel_ratio(svg, y, D, logs)
    svg.save(OUT, y + 8, title="Robin Hood hashing against linear probing: the tables slot by slot, probes per lookup against load, and the ratios")


if __name__ == "__main__":
    build()
