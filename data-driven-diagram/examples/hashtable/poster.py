"""The same project and the same data as figure.py, composed differently, to make one point: the
discipline is fixed (computed, checked, self-explanatory), the layout is not.

figure.py stacks three numbered panels under a strip of cards: right for a paper, where each claim
gets its panel. This one is for a slide or a poster: the two tables are the hero and take most of
the area, every term is defined by a note tied to the thing itself, and the results are three
large numbers. No strip, no sections, no ratio chart.

    python harness.py overview && python poster.py        ->  figures/poster.svg
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from figure import CLASS_COLOUR, CLASSES, COLOUR, DATA, NAME, RULES, klass  # noqa: E402  (also puts ddfig on the path)
import ddfig as dd  # noqa: E402
from ddfig import GREY, INK, MID, NUM, VERMILION, Lin, Log, Logs, Svg, thousands, times  # noqa: E402

OUT = os.path.join(HERE, "figures", "poster.svg")
W, M = 1280, 28            # a 16:9 slide at its natural size: text set for that width
COLS, PX = 128, 6


def cell(x0, y0, slot):
    """The centre of a slot's cell in a picture whose corner is (x0, y0)."""
    return x0 + (slot % COLS + 0.5) * PX, y0 + (slot // COLS + 0.5) * PX


def nearest(disp, want, at):
    """A slot whose displacement satisfies `want`: in the lowest row of the picture that has one,
    the one nearest to column `at` (so that the note under the picture gets a short leader)."""
    for r in reversed(range(len(disp) // COLS)):
        found = [s for s in range(r * COLS, (r + 1) * COLS) if want(disp[s])]
        if found:
            return min(found, key=lambda s: (abs(s % COLS - at), s))
    raise ValueError("no such slot in the table")


def notes_under(svg, y, notes, gap=34):
    """Notes in a row under a picture, in the order of their targets and never closer than `gap`:
    [(target x, target y, text, width)]. A rule, not coordinates: the targets move with the data."""
    free = M
    for tx, ty, text, width in sorted(notes):
        x = max(tx + 26, free)
        dd.callout(svg, tx, ty, x, y, text, width, size=11.5)
        free = x + width + gap


def build():
    if not os.path.exists(DATA):
        sys.exit("out/overview.json is missing: run `python harness.py overview` first")
    with open(DATA, encoding="utf-8") as f:
        D = json.load(f)
    logs = Logs(os.path.join(HERE, "logs"))
    m, s = D["map"], D["series"]
    disp = {r: m[r]["disp"] for r in RULES}
    rows_n = m["slots"] // COLS
    w, h = COLS * PX, rows_n * PX

    # what the poster claims, on the data it is drawn from
    assert [d >= 0 for d in disp["linear"]] == [d >= 0 for d in disp["robinhood"]], "the two rules fill different slots"
    total = {r: sum(d for d in disp[r] if d >= 0) for r in RULES}
    assert total["linear"] == total["robinhood"], "the distances from home do not add up to the same"
    far = {r: max(disp[r]) for r in RULES}
    lin, rob = s["linear"], s["robinhood"]
    assert all(a["hit_mean"] == b["hit_mean"] for a, b in zip(lin, rob)), "the mean walks differ"

    svg = Svg(W, margin=M)
    name_w = svg.text(M, 52, "Robin Hood hashing", size=32, weight="bold")
    svg.text(M + name_w + 20, 52, f"the same slots, the same average walk to a key; the furthest key {far['robinhood']} slots from home instead of {far['linear']}", size=15)

    x0, yl = M, 132
    yr = yl + h + 70
    palette = [dd.hex_rgb(c) for c in CLASS_COLOUR]
    for r, y0 in (("linear", yl), ("robinhood", yr)):
        svg.text(x0, y0 - 12, f"[[{NAME[r]}]]", size=16)
        rows = [bytes(klass(d) for d in disp[r][j * COLS:(j + 1) * COLS]) for j in range(rows_n)]
        svg.image(x0, y0, w, h, dd.png_indexed(rows, palette, 2 * PX))          # twice the display size: crisp when zoomed
    kx = x0 + w - 6                                   # the key of the colours, at the right end of the row between the pictures
    for label, colour in reversed(list(zip(CLASSES, CLASS_COLOUR))):
        kx -= dd.text_width(label, 10.5)
        svg.text(kx, yr - 12, label, size=10.5, fill=GREY)
        kx -= 14
        svg.rect(kx, yr - 21, 10, 10, fill=colour, stroke=MID, sw=0.5)
        kx -= 14
    svg.text(kx, yr - 12, "one cell per slot; colour: how far its key sits from home", size=10.5, anchor="end", fill=GREY)

    # the terms, each said at the thing itself; the targets are found in the data, not placed by hand
    worst = disp["linear"].index(far["linear"])
    tx, ty = cell(x0, yl, worst)
    dd.callout(svg, tx, ty, x0 + 200, yl - 36,
               f"A key's hash names its **home slot**. If that is taken, the key goes into the next free slot, however far: its **displacement**. "
               f"This key came late into a long run of taken slots, a **cluster**, and sits {far['linear']} slots from home.", 560, size=11.5)
    home = nearest(disp["linear"], lambda d: d == 0, 14)
    empty = nearest(disp["linear"], lambda d: d < 0, 62)
    notes_under(svg, yl + h + 22, [
        (*cell(x0, yl, home), "A key **at home**: a lookup finds it with one **probe**, one slot looked at.", 250),
        (*cell(x0, yl, empty), "An **empty slot** ends a search: only here is it known that a key is not in the table, a **miss**.", 300)])
    rworst = disp["robinhood"].index(far["robinhood"])
    rx, ry = cell(x0, yr, rworst)
    nx = min(max(rx + 26, x0), x0 + w - 620)
    by = dd.callout(svg, rx, ry, nx, yr + h + 24,
                    f"[[{NAME['robinhood']}]] changes one rule: when two keys want a slot, the one further from home gets it and the other moves on. "
                    f"The same {thousands(m['keys'])} keys end up in the same slots, and the distances from home add up to the same {thousands(total['linear'])} "
                    f"(checked while drawing), but the furthest key, this one, is {far['robinhood']} slots out.", 620, size=11.5)

    # right column: the cost as the table fills
    cx = x0 + w + 48
    cw = W - M - cx
    svg.text(cx, yl - 12, "Probes per lookup as the table fills", size=14, weight="bold")
    px0, top, ph = cx + 34, yl, h - 26
    X, Y = Lin(0.05, 0.98, px0, cx + cw), Log(1, 3000, top + ph, top)
    svg.rect(px0, top, cx + cw - px0, ph, fill="#f5f5f5")
    dd.log_grid(svg, Y, px0, cx + cw, vertical=False)
    ticks = [0.1, 0.3, 0.5, 0.7, 0.9]
    dd.lin_grid(svg, X, top, top + ph, ticks=ticks, colour="#ffffff")
    for e in Y.decades():
        svg.text(px0 - 6, Y(10.0 ** e) + 3.5, dd.pow10(e), size=10, anchor="end", fill=GREY)
    for v in ticks:
        svg.text(X(v), top + ph + 13, f"{v:.1f}", size=10, anchor="middle", fill=GREY)
    svg.text(cx + cw, top + ph + 26, "load: the share of slots in use", size=10.5, anchor="end", fill=GREY)
    loads = s["loads"]
    for rows, key, colour, sw in ((lin, "hit_max", COLOUR["linear"], 1.0), (rob, "hit_max", COLOUR["robinhood"], 1.0),
                                  (lin, "miss_mean", COLOUR["linear"], 2.4), (rob, "miss_mean", COLOUR["robinhood"], 2.4), (lin, "hit_mean", INK, 2.4)):
        pts = [(a, r[key]) for a, r in zip(loads, rows)]
        dd.curve(svg, pts, X, Y, colour=colour, sw=sw)
        for a, v in pts:
            svg.circle(X(a), Y(v), 2.4 if sw > 1 else 1.9, fill=colour)
    ky = top + ph + 46
    for q, (sw, colour, label) in enumerate(((2.4, MID, "thick: a miss"), (1.0, MID, "thin: the worst hit"), (2.4, INK, "black: a hit, the same for both rules (checked)"))):
        svg.line(cx, ky - 3.6 + q * 14, cx + 22, ky - 3.6 + q * 14, stroke=colour, sw=sw, check=False)
        svg.text(cx + 28, ky + q * 14, label, size=10.5, fill=GREY)

    # right column: what a reader should leave with
    i90 = loads.index(0.9)
    t = {rule: logs.find("bench.txt", rf"^load 0\.90 {rule}\s+hit\s+{NUM} ns\s+miss\s+{NUM} ns") for rule in RULES}
    sy = yr + 30
    for value, label, status, colour in (
            (times(lin[i90]["miss_mean"] / rob[i90]["miss_mean"]), f"fewer probes for a miss at load {loads[i90]:.2f}", "full", VERMILION),
            (times(lin[i90]["hit_max"] / rob[i90]["hit_max"]), f"shorter worst hit there: {rob[i90]['hit_max']} probes instead of {lin[i90]['hit_max']}", "full", VERMILION),
            (times(t["robinhood"][0] / t["linear"][0]), "the time of a hit in plain Python: the price of one more comparison per probe", "partial", INK)):
        sy = dd.stat(svg, cx, sy, value, label, cw, colour=colour, size=32, status=status) + 34
    dd.status_legend(svg, cx, max(sy - 8, by - 40), "Where each number comes from",
                     [("full", "counted by `harness.py`: exact, the same on every run"), ("partial", "timed once, on one machine: `logs/bench.txt`")], width=cw)
    svg.save(OUT, by + 16, title="Robin Hood hashing against linear probing: two tables slot by slot with the terms explained at the slots, probes against load, three results")


if __name__ == "__main__":
    build()
