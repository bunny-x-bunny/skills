"""ddfig: data-driven figures as one SVG file, with no plotting library and no third-party package.

Copy this file next to your figure script (the figure must rebuild from the repository alone) and
write the figure as plain Python: one function per part of the layout you designed, each drawing
onto the one `Svg` in the box it is given. The module does not decide the layout. What it gives you:

  numbers     thousands, num, sci, times, pct, short, floor_sig, pow10, tick_labels: one way to print each kind
  text        widths from font tables (text_width, wrap), so text can be fitted, right-aligned and
              audited without a browser; markup in every string:
                  ^{2}  _{i}        superscript, subscript
                  `squares.rle`     a file name, identifier or command: monospaced
                  [[Hutton32b]]     a named thing of the project: bold italic, in its own colour
                  **memo**          a term being defined: bold
  Svg         text, para, rect, line, path, circle, image, arrow, badge, cone ... and an audit:
              finish() refuses to write a figure with overlapping or clipped text
  rasters     png_indexed, png_grey, png_rgb (real data as pixels), ramp, mix, quantize, density;
              rect(picture=True) for the ground of a picture drawn with shapes
  scales      Lin, Log, log_grid (dashed minor lines at 2..9 per decade), lin_grid, spread
  layout      grid (cells of a layout you design), callout (a note tied to the thing it explains),
              stat (one large number with what it measures), cell_grid (a slice of a real array)
  furniture   ready-made parts of one page style, to use where they fit and not otherwise: title,
              section, cards (a strip that defines terms), status marks and their legend, legend
  charts      bars (groups divided and headed), ratio_chart (against a baseline, log scale), curve,
              swarm (one dot per run along an axis)
  sources     Logs: measured numbers found in raw log files by the lines that report them

Run `python ddfig.py` for a self-test.
"""
import base64
import math
import os
import re
import struct
import sys
import unicodedata
import zlib
from xml.sax.saxutils import escape

INK, GREY, MID, LIGHT, FAINT = "#1a1a1a", "#555555", "#8c8c8c", "#d6d6d6", "#f3f3f3"
# Okabe-Ito: distinguishable with the common colour-vision deficiencies
BLUE, SKY, ORANGE, GREEN, VERMILION, PURPLE, YELLOW = "#0072B2", "#56B4E9", "#E69F00", "#009E73", "#D55E00", "#CC79A7", "#F0E442"
TINTS = ["#dbe9f6", "#fdebc8", "#d5efe6", "#f9dccb", "#efd9e8", "#e4e4e4"]
# For categories without names of their own (clusters, classes, shards): eight soft colours
# (ColorBrewer Set2) that leave the Okabe-Ito colours to the named things of the project.
SOFT8 = ["#66c2a5", "#fc8d62", "#8da0cb", "#e78ac3", "#a6d854", "#ffd92f", "#e5c494", "#b3b3b3"]
# Arial first: the width tables below are Arial's. Helvetica and Liberation Sans share its widths.
SANS = "Arial, Helvetica, 'Liberation Sans', sans-serif"
MONO = "'DejaVu Sans Mono', Menlo, Consolas, 'Liberation Mono', 'Courier New', monospace"


# ---- numbers ---------------------------------------------------------------------------------------
# One function per kind of number, used everywhere, so that the figure prints a value the same way
# each time and the same way as the paper does.

def thousands(n):
    """12,345 (rounded to an integer)."""
    return f"{int(round(n)):,}"


def num(v, sig=3, trim=False):
    """A plain number to `sig` significant figures: 0.0123, 1.23, 12.3, 123, 1,230. `trim` drops
    zeros at the end of the decimals, for counts and their medians: 5, 8.5 and not 5.00, 8.50."""
    if v == 0:
        return "0"
    e = math.floor(math.log10(abs(v)))
    if e >= sig - 1:
        unit = 10 ** (e - sig + 1)
        return thousands(round(v / unit) * unit)
    s = f"{v:.{sig - 1 - e}f}"
    return s.rstrip("0").rstrip(".") if trim else s


def sci(v, sig=2):
    """1.4·10^{4}: the mantissa to `sig` figures, the exponent as a superscript (markup)."""
    if v == 0:
        return "0"
    e = math.floor(math.log10(abs(v)))
    m = round(v / 10 ** e, sig - 1)
    if abs(m) >= 10:
        m, e = m / 10, e + 1
    return f"{m:.{sig - 1}f}·10^{{{e}}}"


def times(v):
    """A ratio to two figures: 0.055×, 0.64×, 4.4×, 18×, 227×, 1.4·10^{4}×."""
    if v >= 1000:
        return sci(v) + "×"
    if v >= 10:
        return f"{v:.0f}×"
    if v >= 1:
        return f"{v:.1f}×"
    return f"{v:.2f}×" if v >= 0.095 else f"{v:.3f}×"


def floor_sig(v, sig=2):
    """`v` cut, not rounded, to `sig` figures: a lower bound must never be rounded up."""
    unit = 10.0 ** (math.floor(math.log10(abs(v))) - sig + 1)
    return math.floor(v / unit + 1e-9) * unit


def pct(v, digits=1):
    """A share in [0, 1] as a percentage: 7.0 %."""
    return f"{100 * v:.{digits}f} %"


def short(n):
    """A count in little room: 912, 9.1k, 36k, 1.2M, 36M."""
    for unit, suffix in ((1e9, "G"), (1e6, "M"), (1e3, "k")):
        if abs(n) >= unit:
            v = n / unit
            return f"{v:.1f}{suffix}" if abs(v) < 9.95 else f"{v:.0f}{suffix}"
    return f"{n:.0f}"


def tick_labels(ticks):
    """The ticks of a linear axis with as many decimals as their step needs, the same for all: 0, 20, 40 or 0.0, 0.5, 1.0."""
    d = next((d for d in range(7) if all(abs(round(t, d) - t) < 1e-9 * max(1.0, abs(t)) for t in ticks)), 6)
    return [f"{t:,.{d}f}" for t in ticks]


def pow10(e):
    """A power of ten as an axis label: 0.01, 0.1, 1, 10, 10^{2}, 10^{-3}."""
    return {-2: "0.01", -1: "0.1", 0: "1", 1: "10"}.get(e, f"10^{{{e}}}")


# ---- text metrics ----------------------------------------------------------------------------------
# Arial's advance widths. Italic text is measured as upright: exact for Latin, within a few percent
# for Greek and Cyrillic. For another typeface or more characters: font_metrics.py.
# 559 characters, as runs from a first code point. An entry is the advance width in 1/1000 em;
# regular/bold where the two differ. Written by font_metrics.py.
METRICS = {
    0x0020: "278,278/333,355/474,556,556,889,667/722,191/238,333,333,389,584,278,333,278,278,556,556,556,556,"
            "556,556,556,556,556,556,278/333,278/333,584,584,584,556/611,1015/975,667/722,667/722,722,722,667,611,778,"
            "722,278,500/556,667/722,556/611,833,722,778,667,778,722,667,611,722,667,944,667,667,611,278/333,"
            "278,278/333,469/584,556,333,556,556/611,500/556,556/611,556,278/333,556/611,556/611,222/278,222/278,500/556,222/278,833/889,556/611,556/611,"
            "556/611,556/611,333/389,500/556,278/333,556/611,500/556,722/778,500/556,500/556,500,334/389,260/280,334/389,584",
    0x00A0: "278,333,556,556,556,556,260/280,556,333,737,370,556,584,333,737,552,400,549,333,333,"
            "333,576,537/556,333,333,333,365,556,834,834,834,611,667/722,667/722,667/722,667/722,667/722,667/722,1000,722,"
            "667,667,667,667,278,278,278,278,722,722,778,778,778,778,778,584,778,722,722,722,"
            "722,667,667,611,556,556,556,556,556,556,889,500/556,556,556,556,556,278,278,278,278,"
            "556/611,556/611,556/611,556/611,556/611,556/611,556/611,549,611,556/611,556/611,556/611,556/611,500/556,556/611,500/556,667/722,556,667/722,556,"
            "667/722,556,722,500/556,722,500/556,722,500/556,722,500/556,722,615/719,722,556/611,667,556,667,556,667,556,"
            "667,556,667,556,778,556/611,778,556/611,778,556/611,778,556/611,722,556/611,722,556/611,278,278,278,278,"
            "278,278,278,222/278,278,278,735/785,444/556,500/556,222/278,667/722,500/556,500/556,556/611,222/278,556/611,222/278,556/611,292/385,556/611,"
            "334/479,556/611,222/278,722,556/611,722,556/611,722,556/611,604/708,723,556/611,778,556/611,778,556/611,778,556/611,1000,944,"
            "722,333/389,722,333/389,722,333/389,667,500/556,667,500/556,667,500/556,667,500/556,611,278/333,611,375/479,611,278/333,"
            "722,556/611,722,556/611,722,556/611,722,556/611,722,556/611,722,556/611,944,722/778,667,500/556,667,611,500,611,"
            "500,611,500,222/278",
    0x0192: "556",
    0x01CD: "667/722,556",
    0x01E6: "778,556/611",
    0x0218: "667,500/556,611,278/333",
    0x0391: "667/722,667/722,551/601,668/719,667,611,722,778,278,667/722,668/667,833,722,650/644,778,722,667",
    0x03A3: "618/600,611,667,798/821,667,835/809,748/802,278,667,578/615,446/451,556/611,222/278,547/582,578/615,575/610,500/556,557/606,446/475,441/460,"
            "556/611,556/541,222/278,500/558,500/556,576/612,500/556,448/445,556/611,690/766,569/619,482/520,617/684,395/446,547/582,648/715,525/576,713/753,781/845",
    0x03D1: "547/582",
    0x03D5: "560/750,781/845",
    0x0400: "667,667/669,865/885,542/567,719/711,667,278,278/276,500/556,1057/1094,1010/1062,854/875,583/610,719,635/622,719,667/722,656/719,667/722,542/567,"
            "677/712,667,923/904,604/626,719,719,583/610,656/702,833,722,778,719,667,722,611,635/622,760/854,667,740/730,667/703,"
            "917/1005,938/1019,792/870,885/979,656/719,719/711,1010/1031,722/719,556,573/618,531/615,365/417,583/635,556,669/709,458/497,559/615,559/615,438/500,583/635,"
            "688/740,552/604,556/611,542/604,556/611,500/556,458/490,500/556,823/875,500/556,573/615,521/581,802/833,823/844,625/729,719/854,521/615,510/552,750/854,542/583,"
            "556,556,556/611,365/417,510/552,500/556,222/278,278/281,222/278,906/969,812/906,556/611,438/500,559/615,500/556,552/604",
    0x0490: "489/487,411/447,542/567,365/417",
    0x049A: "583/610,438/500",
    0x04A2: "722,552/604",
    0x04AE: "556,500/556,556,500/556,667,500/556",
    0x04BA: "667/703,556/611",
    0x04D8: "752/726,556",
    0x04E8: "778,556/611",
    0x2013: "556,1000",
    0x2018: "222/278,222/278,222/278",
    0x201C: "333/500,333/500,333/500",
    0x2020: "556,556,350",
    0x2026: "1000",
    0x2030: "1000",
    0x2032: "188/240,354/479",
    0x2039: "333,333",
    0x2070: "333",
    0x2074: "333,333,333,333,333,333",
    0x207F: "365/396",
    0x20AC: "556",
    0x2113: "323/489",
    0x2116: "1073/1115",
    0x2122: "1000",
    0x212E: "600",
    0x2190: "1000,500,1000,500,1000,500",
    0x2202: "494",
    0x2206: "612",
    0x220F: "823",
    0x2211: "713,584",
    0x2215: "167",
    0x2219: "278,549",
    0x221E: "713",
    0x2229: "719/722",
    0x222B: "274",
    0x2248: "549",
    0x2260: "549,583",
    0x2264: "549,549",
    0x25A1: "604",
    0x25AA: "354,354",
    0x25CA: "494",
}

_ADV = ({}, {})
for _start, _run in METRICS.items():
    for _i, _entry in enumerate(_run.split(",")):
        _r, _, _b = _entry.partition("/")
        _ADV[0][chr(_start + _i)] = int(_r)
        _ADV[1][chr(_start + _i)] = int(_b or _r)
MONO_SCALE, MONO_ADV = 0.93, 602      # monospaced spans a little smaller; the advance of the widest font of MONO
ASCENT, DESCENT = 0.74, 0.22          # the ink of a line of text above and below its baseline, in em
ENTITY_COLOURS = {}
UNMEASURED = set()                    # characters met that the tables lack; their width is a guess

_TOK = re.compile(r"([_^])\{([^}]*)\}|`([^`]*)`|\[\[([^\]]*)\]\]|\*\*([^*]*)\*\*")
_SPAN = re.compile(r"`[^`]*`|\[\[[^\]]*\]\]|\*\*[^*]*\*\*")
# a number and the unit after it are not parted at the end of a line: 0.02 ms, 7.0 %, 9.5 M
_UNIT = re.compile(r"(?<=\d) (?=(?:%|‰|[kMGT]?i?B|[mµμn]?s|min|h|px|pt|[kMG]?Hz|[kM]?W|[cmk]?m|[mk]?g|bits?|[kMGT])(?![\w(]))")


def entities(colours):
    """Give the named things of the project ([[name]] in any text) their colours: the colours of
    their curves and bars, so that a name in a sentence and its series in a chart read as one."""
    ENTITY_COLOURS.update(colours)


def add_metrics(extra):
    """Widths for characters the tables lack: {char: (regular, bold)}, from font_metrics.py --chars."""
    for ch, (r, b) in extra.items():
        _ADV[0][ch], _ADV[1][ch] = r, b
        UNMEASURED.discard(ch)


def _plain(s, bold):
    adv, total = _ADV[1 if bold else 0], 0
    for c in s:
        w = adv.get(c)
        if w is None:
            UNMEASURED.add(c)
            w = 1000 if unicodedata.east_asian_width(c) in "WF" else 600
        total += w
    return total


def text_width(s, size, bold=False):
    """The width of `s` (markup included) at `size` px."""
    total, pos = 0.0, 0
    for m in _TOK.finditer(s):
        total += _plain(s[pos:m.start()], bold)
        if m.group(1):
            total += 0.72 * _plain(m.group(2), bold)
        elif m.group(3) is not None:
            total += len(m.group(3)) * MONO_ADV * MONO_SCALE
        else:
            total += _plain(m.group(4) if m.group(4) is not None else m.group(5), True)
        pos = m.end()
    return (total + _plain(s[pos:], bold)) * size / 1000


def wrap(s, size, width, bold=False):
    """Lines no wider than `width`. A file name, an entity or a term is never broken; a newline in
    `s` starts a new line."""
    lines = []
    for part in s.split("\n"):
        part = _UNIT.sub("\u00a0", _SPAN.sub(lambda m: m.group(0).replace(" ", "\u00a0"), part))
        cur = ""
        for word in part.split(" "):
            trial = f"{cur} {word}" if cur else word
            if cur and text_width(trial, size, bold) > width:
                lines.append(cur)
                cur = word
            else:
                cur = trial
        lines.append(cur)
    return lines


def rich(s, size, neutral=True):
    """`s` escaped, with the markup applied. In black or grey text (`neutral`) an entity takes its
    colour and a term is set in ink; in coloured text both keep the colour of the text."""
    out, pos, cur = [], 0, 0.0

    def emit(text, attrs=""):
        nonlocal cur
        if not text:
            return
        if cur:
            attrs += f' dy="{-cur:.1f}"'
            cur = 0.0
        out.append(f"<tspan{attrs}>{escape(text)}</tspan>" if attrs else escape(text))

    for m in _TOK.finditer(s):
        emit(s[pos:m.start()])
        if m.group(1):
            target = -0.36 * size if m.group(1) == "^" else 0.22 * size
            out.append(f'<tspan dy="{target - cur:.1f}" font-size="{round(size * 0.72, 1)}">{escape(m.group(2))}</tspan>')
            cur = target
        elif m.group(3) is not None:
            emit(m.group(3), f' font-family="{MONO}" font-size="{round(size * MONO_SCALE, 1)}"')
        elif m.group(4) is not None:
            colour = ENTITY_COLOURS.get(m.group(4).replace("\u00a0", " "), INK)     # wrap() has made its spaces unbreakable
            emit(m.group(4), ' font-weight="bold" font-style="italic"' + (f' fill="{colour}"' if neutral else ""))
        else:
            emit(m.group(5), ' font-weight="bold"' + (f' fill="{INK}"' if neutral else ""))
        pos = m.end()
    emit(s[pos:])
    return "".join(out)


# ---- the canvas ------------------------------------------------------------------------------------

class LayoutError(Exception):
    """The figure has text that overlaps, leaves the canvas or cannot be read where it stands."""


def _overlap(a, b):
    return min(a[2], b[2]) - max(a[0], b[0]), min(a[3], b[3]) - max(a[1], b[1])


def _crosses(seg, box):
    """Does the segment (x1, y1, x2, y2) pass through the box (Liang-Barsky)?"""
    x1, y1, x2, y2 = seg
    t0, t1 = 0.0, 1.0
    dx, dy = x2 - x1, y2 - y1
    for p, q in ((-dx, x1 - box[0]), (dx, box[2] - x1), (-dy, y1 - box[1]), (dy, box[3] - y1)):
        if p == 0:
            if q < 0:
                return False
        else:
            r = q / p
            if p < 0:
                if r > t1:
                    return False
                t0 = max(t0, r)
            else:
                if r < t0:
                    return False
                t1 = min(t1, r)
    return t1 - t0 > 0


class Svg:
    """One page of fixed width. Elements are painted in the order of the calls, so draw a picture
    before the labels on it. Coordinates are px; y grows downwards; a text's y is its baseline."""

    def __init__(self, width=1200, margin=20, font=SANS, background="#ffffff"):
        self.W, self.M = width, margin
        self.CW = width - 2 * margin          # the width of the content
        self.font, self.background = font, background
        self.o = []
        self._texts, self._images, self._lines, self._notes, self._markers = [], [], [], [], {}

    # -- text --
    def text(self, x, y, s, size=11, weight=None, anchor="start", fill=INK, halo=None, rotate=None, max_width=None, check=True):
        """One line at baseline y. `halo`: the colour behind the text, painted as an outline, for
        text over a picture, a bar or grid lines. `max_width`: the room this text has; the audit
        reports it when the text is wider. `rotate`: degrees about (x, y); only -90 and 90 are audited."""
        bold = weight == "bold"
        w = text_width(s, size, bold)
        if max_width is not None and w > max_width + 0.5:
            self._notes.append((f"text is {w:.0f} px wide, its room is {max_width:.0f} px: {s!r}", None))
        a = f' font-weight="{weight}"' if weight else ""
        a += f' text-anchor="{anchor}"' if anchor != "start" else ""
        a += f' stroke="{halo}" stroke-width="3.2" stroke-linejoin="round" paint-order="stroke"' if halo else ""
        a += f' transform="rotate({rotate} {x:.1f} {y:.1f})"' if rotate else ""
        self.o.append(f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}"{a}>{rich(s, size, fill in (INK, GREY))}</text>')
        dx = -w if anchor == "end" else -w / 2 if anchor == "middle" else 0.0
        up, down = ASCENT * size, DESCENT * size
        if not rotate:
            box = (x + dx, y - up, x + dx + w, y + down)
        elif rotate == -90:
            box = (x - up, y - dx - w, x + down, y - dx)
        elif rotate == 90:
            box = (x - down, y + dx, x + up, y + dx + w)
        else:
            box, check = None, False
        if box:
            self._texts.append(dict(box=box, s=s, halo=bool(halo), check=check))
        return w

    def para(self, x, y, s, width, size=11, fill=GREY, lead=None, weight=None):
        """`s` wrapped to `width`, first baseline at y; returns the baseline below the last line."""
        lead = lead or round(size * 1.27, 1)
        for line in wrap(s, size, width, weight == "bold"):
            self.text(x, y, line, size=size, fill=fill, weight=weight)
            y += lead
        return y

    # -- shapes --
    def rect(self, x, y, w, h, fill="none", stroke=None, sw=1, rx=0, dash=None, opacity=None, picture=False):
        """`picture=True`: this rectangle is the ground of a picture drawn with shapes (a scatter
        of points, a map of cells). Both audits then treat it like an image: text on it needs a halo."""
        a = f' stroke="{stroke}" stroke-width="{sw}"' if stroke else ""
        a += f' rx="{rx}"' if rx else ""
        a += f' stroke-dasharray="{dash}"' if dash else ""
        a += f' opacity="{opacity}"' if opacity is not None else ""
        a += ' data-ddfig="picture"' if picture else ""
        self.o.append(f'<rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" fill="{fill}"{a}/>')
        if picture:
            self._images.append((x, y, x + w, y + h))

    def line(self, x1, y1, x2, y2, stroke=INK, sw=1, dash=None, arrow=False, opacity=None, check=True):
        """`check=False` for a line that is meant to pass behind text (the text needs a halo then)."""
        a = f' stroke-dasharray="{dash}"' if dash else ""
        a += f' marker-end="url(#{self._marker(stroke)})"' if arrow else ""
        a += f' opacity="{opacity}"' if opacity is not None else ""
        self.o.append(f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" stroke="{stroke}" stroke-width="{sw}"{a}/>')
        if check:
            self._lines.append((x1, y1, x2, y2))

    def path(self, d, stroke=INK, sw=1, fill="none", opacity=None, dash=None, arrow=False, join=None):
        a = f' stroke="{stroke}" stroke-width="{sw}"' if stroke else ""
        a += f' opacity="{opacity}"' if opacity is not None else ""
        a += f' stroke-dasharray="{dash}"' if dash else ""
        a += f' marker-end="url(#{self._marker(stroke)})"' if arrow and stroke else ""
        a += f' stroke-linejoin="{join}"' if join else ""
        self.o.append(f'<path d="{d}" fill="{fill}"{a}/>')

    def circle(self, x, y, r, fill=INK, stroke=None, sw=1, opacity=None, dash=None):
        a = f' stroke="{stroke}" stroke-width="{sw}"' if stroke else ""
        a += f' opacity="{opacity}"' if opacity is not None else ""
        a += f' stroke-dasharray="{dash}"' if dash else ""
        self.o.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{r}" fill="{fill}"{a}/>')

    def diamond(self, x, y, r, fill="#ffffff", stroke=INK, sw=1.3):
        self.path(f"M{x - r:.1f},{y:.1f}L{x:.1f},{y - r:.1f}L{x + r:.1f},{y:.1f}L{x:.1f},{y + r:.1f}Z", stroke=stroke, sw=sw, fill=fill)

    def arrow(self, x1, y1, x2, y2, colour=GREY, sw=1.3, dash=None):
        self.line(x1, y1, x2, y2, stroke=colour, sw=sw, dash=dash, arrow=True)

    def badge(self, x, y, n, r=11.0, size=13.5):
        """A number in a filled circle: the number of a panel."""
        self.circle(x, y, r, fill=INK)
        self.text(x, y + size * 0.35, str(n), size=size, weight="bold", anchor="middle", fill="#ffffff", check=False)

    def _marker(self, colour):
        return self._markers.setdefault(colour, "ah-" + re.sub(r"[^0-9a-zA-Z]", "", colour))

    # -- pictures --
    def image(self, x, y, w, h, png, pixelated=False):
        """A PNG (bytes) at (x, y), scaled to w x h. Write pictures of data at 2-4 times their
        display size (png_indexed's `scale`), so that the viewer's smooth scaling keeps them crisp
        at any zoom; `pixelated` is for a small raster enlarged many times."""
        uri = "data:image/png;base64," + base64.b64encode(png).decode("ascii")
        a = ' style="image-rendering:pixelated"' if pixelated else ""
        self.o.append(f'<image x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" preserveAspectRatio="none" href="{uri}" xlink:href="{uri}"{a}/>')
        self._images.append((x, y, x + w, y + h))

    def cone(self, p1, p2, q1, q2, split=None, axis=0, inside="#ffffff", outside=MID, fill=("#ffffff", 0.15, "#000000", 0.05)):
        """A zoom cone from the edge p1-p2 of a region of a picture to the edge q1-q2 of its
        enlargement: what says which part of the picture the enlargement shows. A dark picture
        ends at `split` along `axis` (0: x, 1: y): up to there the two border lines are drawn in
        `inside`, beyond it in `outside`."""
        d = f"M{p1[0]:.1f},{p1[1]:.1f}L{q1[0]:.1f},{q1[1]:.1f}L{q2[0]:.1f},{q2[1]:.1f}L{p2[0]:.1f},{p2[1]:.1f}Z"
        self.path(d, stroke=None, fill=fill[0], opacity=fill[1])
        self.path(d, stroke=None, fill=fill[2], opacity=fill[3])
        for p, q in ((p1, q1), (p2, q2)):
            t = 0.0
            if split is not None and q[axis] != p[axis]:
                t = min(max((split - p[axis]) / (q[axis] - p[axis]), 0.0), 1.0)
            mx, my = p[0] + t * (q[0] - p[0]), p[1] + t * (q[1] - p[1])
            if inside and t > 0:
                self.line(p[0], p[1], mx, my, stroke=inside, sw=1, opacity=0.9, check=False)
            self.line(mx, my, q[0], q[1], stroke=outside, sw=1, check=False)

    # -- the audit --
    def problems(self, height=None):
        """What a reader would trip over, as [(message, boxes)]: text on text, text off the page,
        text on a picture without a halo, a line through text, text wider than its room. Widths
        come from the font tables, so this runs anywhere; a browser has the last word
        (figcheck.py audit)."""
        out = list(self._notes)
        texts = [t for t in self._texts if t["check"]]
        for i, a in enumerate(texts):
            for b in texts[i + 1:]:
                ox, oy = _overlap(a["box"], b["box"])
                if ox > 0.5 and oy > 0.5:
                    out.append((f"texts overlap: {a['s']!r} and {b['s']!r}", [a["box"], b["box"]]))
        for t in texts:
            b = t["box"]
            if b[0] < 0 or b[1] < 0 or b[2] > self.W or (height is not None and b[3] > height):
                out.append((f"text leaves the page: {t['s']!r}", [b]))
            if t["halo"]:
                continue
            ink = (b[0] + 0.5, b[1] + 0.12 * (b[3] - b[1]), b[2] - 0.5, b[3] - 0.18 * (b[3] - b[1]))
            for im in self._images:
                ox, oy = _overlap(ink, im)
                if ox > 0.5 and oy > 0.5:
                    out.append((f"text on a picture without a halo: {t['s']!r}", [b]))
                    break
            for seg in self._lines:
                if _crosses(seg, ink):
                    out.append((f"a line runs through text: {t['s']!r}", [b]))
                    break
        if UNMEASURED:
            out.append(("no width known for " + "".join(sorted(UNMEASURED)) + ": their widths are guesses (see font_metrics.py --chars, add_metrics)", None))
        return out

    def finish(self, height, strict=True, title=None):
        """The SVG as a string. With problems (see `problems`) it raises LayoutError; set the
        environment variable DDFIG_DEBUG=1 to get the figure anyway, the places marked in red."""
        found = self.problems(height)
        debug = os.environ.get("DDFIG_DEBUG") == "1"
        marks = []
        if found:
            report = f"{len(found)} layout problem(s):\n" + "\n".join("  " + m for m, _ in found[:40]) + ("\n  ..." if len(found) > 40 else "")
            if strict and not debug:
                raise LayoutError(report + "\nSet DDFIG_DEBUG=1 to write the figure with these places marked.")
            print(report, file=sys.stderr)
            for _, boxes in found:
                for b in boxes or []:
                    marks.append(f'<rect x="{b[0] - 1.5:.1f}" y="{b[1] - 1.5:.1f}" width="{b[2] - b[0] + 3:.1f}" height="{b[3] - b[1] + 3:.1f}" '
                                 'fill="#ff0000" fill-opacity="0.18" stroke="#ff0000"/>')
        head = [f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{self.W}" height="{height:.0f}" '
                f'viewBox="0 0 {self.W} {height:.0f}" font-family="{self.font}">']
        if title:
            head.append(f"<title>{escape(title)}</title>")
        head.append("<defs>")
        for colour, name in self._markers.items():
            head.append(f'<marker id="{name}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6.5" markerHeight="6.5" orient="auto-start-reverse">'
                        f'<path d="M0,0.8 L10,5 L0,9.2 z" fill="{colour}"/></marker>')
        head += ["</defs>", f'<rect width="{self.W}" height="{height:.0f}" fill="{self.background}"/>']
        return "\n".join(head + self.o + marks + ["</svg>"]) + "\n"

    def save(self, path, height, **kw):
        """Write the figure (LF line ends, so that it is byte-identical on every platform)."""
        out = self.finish(height, **kw)
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(out)
        print("wrote", os.path.abspath(path), f"({len(out) / 1024:.0f} KiB)")


# ---- real data as pixels ---------------------------------------------------------------------------

def _chunk(tag, body):
    return struct.pack(">I", len(body)) + tag + body + struct.pack(">I", zlib.crc32(tag + body) & 0xFFFFFFFF)


def _png(w, h, colour_type, raw, palette=None):
    plte = _chunk(b"PLTE", b"".join(bytes(c) for c in palette)) if palette else b""
    return (b"\x89PNG\r\n\x1a\n" + _chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, colour_type, 0, 0, 0)) + plte
            + _chunk(b"IDAT", zlib.compress(bytes(raw), 9)) + _chunk(b"IEND", b""))


def png_indexed(rows, palette, scale=1):
    """A palette PNG. `rows`: one bytes object per row, a colour index per cell; `palette`:
    [(r, g, b)]; every cell becomes `scale` x `scale` pixels. The format for states, classes and
    anything quantized (see `quantize`, `ramp`)."""
    raw = bytearray()
    for r in rows:
        line = bytearray(len(r) * scale)
        for k in range(scale):
            line[k::scale] = r
        raw += (b"\x00" + bytes(line)) * scale
    return _png(len(rows[0]) * scale, len(rows) * scale, 3, raw, palette)


def png_grey(rows):
    """A greyscale PNG; `rows`: bytes, 0 black .. 255 white."""
    return _png(len(rows[0]), len(rows), 0, b"".join(b"\x00" + bytes(r) for r in rows))


def png_rgb(rows):
    """A truecolour PNG; `rows`: bytes of r, g, b triples."""
    return _png(len(rows[0]) // 3, len(rows), 2, b"".join(b"\x00" + bytes(r) for r in rows))


def hex_rgb(c):
    return tuple(int(c[i:i + 2], 16) for i in (1, 3, 5))


def mix(a, b, t):
    """The colour a share t of the way from hex colour a to b: mix(BLUE, "#ffffff", 0.7) is a tint."""
    return "#%02x%02x%02x" % tuple(round(x + (y - x) * t) for x, y in zip(hex_rgb(a), hex_rgb(b)))


def ramp(stops, n=256):
    """A palette of `n` colours through the given hex colours, for png_indexed."""
    cs = [hex_rgb(c) for c in stops]
    out = []
    for i in range(n):
        t = i / (n - 1) * (len(cs) - 1)
        k = min(int(t), len(cs) - 2)
        f = t - k
        out.append(tuple(round(a + (b - a) * f) for a, b in zip(cs[k], cs[k + 1])))
    return out


VIRIDIS = ramp(["#440154", "#472d7b", "#3b528b", "#2c728e", "#21918c", "#28ae80", "#5ec962", "#addc30", "#fde725"])
GREYS = ramp(["#ffffff", "#000000"])
DIVERGING = ramp(["#2166ac", "#92c5de", "#f7f7f7", "#f4a582", "#b2182b"])     # below, at and above a midpoint


def quantize(rows, lo=None, hi=None, log=False):
    """Rows of numbers as rows of bytes 0..255 between `lo` and `hi` (default: the data's range),
    for png_indexed with a 256-colour ramp. For a diverging ramp pass lo = -hi."""
    f = (lambda v: math.log10(v)) if log else (lambda v: v)
    flat = [f(v) for r in rows for v in r]
    lo = min(flat) if lo is None else f(lo)
    hi = max(flat) if hi is None else f(hi)
    span = (hi - lo) or 1.0
    return [bytes(min(255, max(0, int(255 * (f(v) - lo) / span + 0.5))) for v in r) for r in rows]


def density(rows, out_w, out_h, gain=1.6, gamma=0.55):
    """A large sparse 0/1 picture reduced to out_w x out_h greys by the share of set cells per
    block (for png_grey): shown small as plain pixels, sparse data would vanish."""
    h, w = len(rows), len(rows[0])
    fx, fy = w / out_w, h / out_h
    out = []
    for j in range(out_h):
        ya, yb = int(j * fy), max(int(j * fy) + 1, int((j + 1) * fy))
        line = bytearray(out_w)
        for i in range(out_w):
            xa, xb = int(i * fx), max(int(i * fx) + 1, int((i + 1) * fx))
            live = sum(1 for r in rows[ya:yb] for v in r[xa:xb] if v)
            line[i] = min(255, int(255 * min(1.0, gain * live / ((xb - xa) * (yb - ya))) ** gamma))
        out.append(bytes(line))
    return out


# ---- scales and grids ------------------------------------------------------------------------------

class Lin:
    """value -> coordinate, linearly: Lin(0, 1, x0, x1). For a y axis pass (bottom, top)."""

    def __init__(self, lo, hi, a, b):
        self.lo, self.hi, self.a, self.b = lo, hi, a, b

    def __call__(self, v):
        return self.a + (self.b - self.a) * (v - self.lo) / (self.hi - self.lo)

    def ticks(self, n=5):
        raw = (self.hi - self.lo) / n
        mag = 10 ** math.floor(math.log10(raw))
        step = min((1, 2, 5, 10), key=lambda m: abs(m * mag - raw)) * mag
        k = math.ceil(self.lo / step - 1e-9)
        out = []
        while k * step <= self.hi + 1e-9 * abs(self.hi):
            out.append(round(k * step, 12))
            k += 1
        return out


class Log:
    """value -> coordinate, logarithmically: Log(1e3, 1e9, x0, x1)."""

    def __init__(self, lo, hi, a, b):
        self.lo, self.hi, self.a, self.b = lo, hi, a, b
        self.l0, self.l1 = math.log10(lo), math.log10(hi)

    def __call__(self, v):
        return self.a + (self.b - self.a) * (math.log10(v) - self.l0) / (self.l1 - self.l0)

    def decades(self):
        """The exponents of the powers of ten on the axis."""
        return list(range(math.ceil(self.l0 - 1e-9), math.floor(self.l1 + 1e-9) + 1))


def log_grid(svg, scale, a, b, vertical=True, major="#ffffff", minor="#c9c9c9", major_sw=1.0):
    """The grid of a logarithmic axis: a solid line at every power of ten and dashed lines at 2..9
    times it. They bunch up towards the next power, and that is what lets a reader see at a glance
    that the axis is logarithmic. The lines run from a to b across the other axis. `major` suits a
    tinted plot area; on white pass a grey."""
    solid, dashed = [], []
    for e in range(math.floor(scale.l0), math.ceil(scale.l1) + 1):
        for k in range(1, 10):
            v = k * 10.0 ** e
            if not scale.lo * 0.999 <= v <= scale.hi * 1.001:
                continue
            c = scale(v)
            (solid if k == 1 else dashed).append(f"M{c:.1f},{a:.1f}V{b:.1f}" if vertical else f"M{a:.1f},{c:.1f}H{b:.1f}")
    if dashed:
        svg.path("".join(dashed), stroke=minor, sw=0.6, dash="2 2")
    if solid and major:
        svg.path("".join(solid), stroke=major, sw=major_sw)


def lin_grid(svg, scale, a, b, ticks=None, vertical=True, colour="#e2e2e2", sw=0.8):
    """Solid lines at the ticks of a linear axis (evenly spaced: the mark of a linear scale)."""
    ticks = scale.ticks() if ticks is None else ticks
    d = "".join(f"M{scale(v):.1f},{a:.1f}V{b:.1f}" if vertical else f"M{a:.1f},{scale(v):.1f}H{b:.1f}" for v in ticks)
    if d:
        svg.path(d, stroke=colour, sw=sw)


def _isotonic(z):
    """Least-squares non-decreasing fit (pool adjacent violators)."""
    blocks = []
    for v in z:
        blocks.append([v, 1])
        while len(blocks) > 1 and blocks[-2][0] * blocks[-1][1] > blocks[-1][0] * blocks[-2][1]:
            t, c = blocks.pop()
            blocks[-1][0] += t
            blocks[-1][1] += c
    out = []
    for t, c in blocks:
        out += [t / c] * c
    return out


def spread(wanted, gap):
    """Where to put labels that want to sit at the coordinates `wanted` but need `gap` between
    them: the order is kept and they move as little as possible. For the names at the ends of
    curves that end close together. Returns the coordinates in the order given."""
    idx = sorted(range(len(wanted)), key=lambda i: wanted[i])
    z = _isotonic([wanted[i] - k * gap for k, i in enumerate(idx)])
    out = [0.0] * len(wanted)
    for k, i in enumerate(idx):
        out[i] = z[k] + k * gap
    return out


def curve(svg, pts, xs, ys, colour=BLUE, sw=1.6, step=False, area=None, opacity=0.26, dash=None, alpha=None):
    """A series through (x value, y value) points on the scales xs, ys. `step`: each value holds
    from the point before it (counts per interval). `area`: the y value to fill down to, at
    `opacity`. `alpha`: the opacity of the line itself, for many runs drawn over each other."""
    xy = [(xs(a), ys(b)) for a, b in pts]
    if step:
        d, px = [], xy[0][0]
        for x, y in xy:
            d.append(f"{px:.1f},{y:.1f} {x:.1f},{y:.1f}")
            px = x
    else:
        d = [f"{x:.1f},{y:.1f}" for x, y in xy]
    if area is not None:
        base = ys(area)
        svg.path(f"M{xy[0][0]:.1f},{base:.1f} L" + " L".join(d) + f" L{xy[-1][0]:.1f},{base:.1f} Z", stroke=None, fill=colour, opacity=opacity)
    svg.path("M" + " L".join(d), stroke=colour, sw=sw, join="round", dash=dash, opacity=alpha)


# ---- layout ----------------------------------------------------------------------------------------
# The composition of a figure is designed for its content: these parts fit any of them.

def grid(x, y, w, h, cols, rows=1, gap=14.0, row_gap=None):
    """The cells of a grid in the box (x, y, w, h), row by row, as [(x, y, w, h)]. For small
    multiples, tiles of numbers, or the frames of a layout sketched on paper."""
    row_gap = gap if row_gap is None else row_gap
    cw, ch = (w - (cols - 1) * gap) / cols, (h - (rows - 1) * row_gap) / rows
    return [(x + c * (cw + gap), y + r * (ch + row_gap), cw, ch) for r in range(rows) for c in range(cols)]


def callout(svg, tx, ty, x, y, s, width, n=None, side="left", size=10.5, fill=GREY, ring=5.0, colour=INK):
    """A note tied to the thing it explains: a ring at the target (tx, ty) on a picture, a leader,
    and the text wrapped to `width` with its first baseline at y. The way to define a term where
    the reader is looking at the thing itself. `side`: which edge of the note is at x ("left" or
    "right"); the leader finds the nearest point of the note by itself. `n`: a number or letter in
    a badge before the text, for referring to the note.
    The leader is drawn over a white under-line, so it shows on dark and on light pictures.
    Returns the baseline below the note."""
    indent = 20 if n is not None else 0
    lines = wrap(s, size, width - indent)
    lead = round(size * 1.27, 1)
    left = x if side == "left" else x - width
    # the leader ends at the point of the note's edge nearest to the target: it never crosses its own text
    right = left + indent + max(text_width(l, size) for l in lines)
    ax = min(max(tx, left - 6), right + 6)
    ay = min(max(ty, y - size * 0.8 - 4), y + (len(lines) - 1) * lead + size * 0.25 + 4)
    svg.line(tx, ty, ax, ay, stroke="#ffffff", sw=3.0, opacity=0.85, check=False)
    svg.line(tx, ty, ax, ay, stroke=colour, sw=1.0)
    svg.circle(tx, ty, ring + 1.2, fill="none", stroke="#ffffff", sw=1.6)
    svg.circle(tx, ty, ring, fill="none", stroke=colour, sw=1.4)
    tx0 = left
    if n is not None:
        svg.badge(left + 7.5, y - size * 0.34, n, r=7.5, size=10)
        tx0 += 20
    for q, line in enumerate(lines):
        svg.text(tx0, y + q * lead, line, size=size, fill=fill)
    return y + len(lines) * lead


def stat(svg, x, y, value, label, width, colour=INK, size=30, status=None, anchor="start"):
    """One number set large, with what it measures in plain words under it: for the two or three
    results a reader should leave with. `value` is a string (from times, pct, sci ...), baseline at
    y; `status`: an evidence mark before the label ("full", "partial", "model").
    Returns the baseline below the label."""
    ax = x + (width if anchor == "end" else width / 2 if anchor == "middle" else 0)
    svg.text(ax, y, value, size=size, weight="bold", fill=colour, anchor=anchor, max_width=width)
    yy = y + size * 0.32 + 11
    indent = 13 if status else 0
    if status:
        status_mark(svg, status, x + 4.6, yy - 3.6)
    for q, line in enumerate(wrap(label, 10.5, width - indent)):
        svg.text(x + indent, yy, line, size=10.5, fill=GREY)
        yy += 13.3
    return yy


def swarm(svg, values, scale, centre, r=3.0, gap=0.6, colour=BLUE, colours=None, vertical=False, stroke="#ffffff", opacity=None):
    """One dot per value along an axis, pushed sideways from the line `centre` only as far as needed
    to keep the dots apart: every run stays visible, and the heap they form is the distribution.
    For "17 of 40 ended above 5", where a bar would hide the 40. `scale` maps a value to its
    coordinate along the axis; `vertical`: the axis runs up the page; `colours`: one per value.
    Returns the centres [(x, y)] in the order of the values, for marking some of them."""
    step, need = r * 0.5, (2 * r + gap) ** 2
    placed, pos = [], [None] * len(values)
    for i in sorted(range(len(values)), key=lambda i: (scale(values[i]), i)):
        a, k = scale(values[i]), 0
        while True:
            off = 0.0 if k == 0 else step * ((k + 1) // 2) * (1 if k % 2 else -1)
            if all((a - pa) ** 2 + (off - po) ** 2 >= need for pa, po in placed):
                break
            k += 1
        placed.append((a, off))
        pos[i] = (centre + off, a) if vertical else (a, centre + off)
    for i, (x, y) in enumerate(pos):
        svg.circle(x, y, r, fill=colours[i] if colours else colour, stroke=stroke, sw=0.6 if stroke else 1, opacity=opacity)
    return pos


# ---- furniture -------------------------------------------------------------------------------------
# Ready-made parts of one page style (a head, a strip of cards, numbered sections). They suit a
# figure of several claims of equal weight. Other content wants other compositions: do not reach
# for these by default.

def title(svg, name, tagline=None, note=None, intro=None):
    """The head of the figure: its name, what it claims in one line, where its content comes from
    (`note`, at the right), and a line that says how to read it. Returns the y below."""
    svg.text(svg.M, 34, name, size=26, weight="bold")
    if tagline:
        svg.text(svg.M + text_width(name, 26, True) + 16, 34, tagline, size=14)
    if note:
        svg.text(svg.W - svg.M, 34, note, anchor="end", fill=GREY)
    if intro:
        svg.text(svg.M, 53, intro, fill=GREY, max_width=svg.CW)
    return 64 if intro else 48


# How much evidence stands behind what is drawn. Three levels cover most projects; the legend of the
# figure says what each means there (status_legend):
#   "full"     observed on the real thing and reproducible: measured on the target system, counted
#              exactly, proved                                                       a filled circle
#   "partial"  observed, with a caveat that the legend names: a reference implementation or a
#              simulation in place of the system, one machine, a subset of the data  a diamond
#   "model"    not observed: computed from a model, estimated, projected             a dashed circle
def status_mark(svg, kind, x, y, colour=INK):
    if kind == "full":
        svg.circle(x, y, 4, fill=colour)
    elif kind == "partial":
        svg.diamond(x, y, 4.6, stroke=colour)
    elif kind == "model":
        svg.circle(x, y, 3.7, fill="#ffffff", stroke=GREY if colour == INK else colour, sw=1.2, dash="2 1.6")
    else:
        raise ValueError(f"status {kind!r}: use full, partial or model")


def status_row(svg, x_right, y, items, size=11):
    """Marks with their texts in a row that ends at x_right: [(kind, text)]. Plain grey text beside
    a small mark: a filled, outlined box around such a label reads as a button."""
    widths = [13 + text_width(t, size) for _, t in items]
    x = x_right - sum(widths) - 18 * (len(items) - 1)
    for (kind, t), w in zip(items, widths):
        status_mark(svg, kind, x + 4.6, y - size * 0.34)
        svg.text(x + 13, y, t, size=size, fill=GREY)
        x += w + 18


def status_legend(svg, x, y, heading, items, size=10.5, lead=13.2, width=None):
    """The key of the status marks, once per figure: a heading and [(kind, what it means here)].
    With `width` the texts are wrapped to it. Returns the baseline below the last line."""
    svg.text(x, y, heading, size=12.5, weight="bold", max_width=width)
    y += 18.7
    for kind, t in items:
        status_mark(svg, kind, x + 4.6, y - 3.6)
        for line in (wrap(t, size, width - 15) if width else [t]):
            svg.text(x + 15, y, line, size=size, fill=GREY)
            y += lead
    return y


def section(svg, y, n, heading, sub=None, status=None):
    """A heading across the page: the claim of the panel, a subtitle, and at the right how far its
    content is built ([(kind, text)], see status_row). `n`: the panel's number in a badge, or None.
    Returns the y below it."""
    svg.line(svg.M, y, svg.W - svg.M, y, stroke=LIGHT, sw=1)
    cy = y + 25
    hx = svg.M
    if n is not None:
        svg.badge(svg.M + 11, cy - 5.5, n)
        hx += 30
    svg.text(hx, cy, heading, size=17, weight="bold")
    if sub:
        svg.text(hx + text_width(heading, 17, True) + 12, cy, sub, size=12.5, fill=GREY)
    if status:
        status_row(svg, svg.W - svg.M, cy, status)
    return y + 42


def cards(svg, x, y, width, items, cols=4, gap=22.0, row_gap=26.0, pad=10.0, size=10.5):
    """The strip at the head of a figure: the method as a few steps, each card defining the words it
    introduces, so that a reader meets every term before a panel uses it.

    items: dicts with
        title    a short bold line
        text     two or three plain sentences; **terms** in bold where they are defined
        n        the number of the panel that shows this step (optional)
        picture  a function (svg, x_right, y_centre) that draws a pictogram of about 30 x 18 px (optional)
        at       (row, column); default: in reading order
        style    "step" (default), or "frame": a dashed outline for what is not a step (a setting, an input)
    Returns ({index: (x, y, w, h)}, the y below), so that arrows can be drawn between the cards."""
    cw = (width - (cols - 1) * gap) / cols
    lead = round(size * 1.26, 1)
    lines = [wrap(it["text"], size, cw - 2 * pad) for it in items]
    h = 30 + lead * max(len(l) for l in lines) + 3
    boxes = {}
    for k, it in enumerate(items):
        row, col = it.get("at", divmod(k, cols))
        cx, cy = x + col * (cw + gap), y + row * (h + row_gap)
        frame = it.get("style") == "frame"
        svg.rect(cx, cy, cw, h, fill="#ffffff" if frame else FAINT, stroke=GREY if frame else None, sw=1, rx=6, dash="3 2" if frame else None)
        tx = cx + pad
        if it.get("n") is not None:
            svg.badge(cx + pad + 8, cy + 15, it["n"], r=8.5, size=11)
            tx += 22
        room = cw - (tx - cx) - pad - (40 if it.get("picture") else 0)
        svg.text(tx, cy + 19.3, it["title"], size=12.5, weight="bold", max_width=room)
        if it.get("picture"):
            it["picture"](svg, cx + cw - pad, cy + 15)
        for q, line in enumerate(lines[k]):
            svg.text(cx + pad, cy + 38 + q * lead, line, size=size, fill=GREY)
        boxes[k] = (cx, cy, cw, h)
    rows = 1 + max(it.get("at", divmod(k, cols))[0] for k, it in enumerate(items))
    return boxes, y + rows * h + (rows - 1) * row_gap


def connect(svg, a, b, label=None, dash=None, colour=GREY):
    """An arrow from card box `a` to card box `b` (boxes of `cards`): sideways when they share a
    row, downwards or upwards when they share a column."""
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    if abs(ay - by) < 1:
        y = ay + ah / 2
        x1, x2 = (ax + aw + 4, bx - 4) if bx > ax else (ax - 4, bx + bw + 4)
        svg.arrow(x1, y, x2, y, colour=colour, dash=dash)
        if label:
            svg.text((x1 + x2) / 2, y - 7, label, size=10.5, anchor="middle", fill=GREY, max_width=abs(x2 - x1) + 6)
    else:
        x = ax + aw / 2
        y1, y2 = (ay + ah + 4, by - 4) if by > ay else (ay - 4, by + bh + 4)
        svg.arrow(x, y1, x, y2, colour=colour, dash=dash)
        if label:
            svg.text(x + 7, (y1 + y2) / 2 + 3.6, label, size=10.5, fill=GREY)


def legend(svg, x, y, items, size=10.5, gap=18.0):
    """Swatches with labels in a row from x: [(colour, label)]. Returns the x after the last."""
    for colour, label in items:
        svg.rect(x, y - 8.5, 9, 9, fill=colour)
        svg.text(x + 13, y, label, size=size, fill=GREY)
        x += 13 + text_width(label, size) + gap
    return x - gap


def cell_grid(svg, x, y, rows, cw, ch, fmt=str, size=9.5, blank=None, blank_text="", tint="repeats", stroke=MID):
    """A slice of a real array, table or grid of IDs as boxes with their values: the data structure
    itself, not a symbol of it. `tint`: "repeats" gives equal values that occur more than once a
    shared tint, so that sharing can be seen; a function value -> colour; or None.
    Returns {(row, column): (x, y, w, h)} for frames and cones."""
    flat = [v for r in rows for v in r]
    seen, boxes = {}, {}
    for j, r in enumerate(rows):
        for i, v in enumerate(r):
            if v == blank:
                fill = FAINT
            elif callable(tint):
                fill = tint(v)
            elif tint == "repeats" and flat.count(v) > 1:
                fill = TINTS[seen.setdefault(v, len(seen)) % len(TINTS)]
            else:
                fill = "#ffffff"
            bx, by = x + i * cw, y + j * ch
            svg.rect(bx, by, cw, ch, fill=fill, stroke=stroke, sw=0.8)
            s = blank_text if v == blank else fmt(v)
            if s:
                svg.text(bx + cw / 2, by + ch / 2 + size * 0.36, s, size=size, anchor="middle", fill=GREY if v == blank else INK, max_width=cw - 2)
            boxes[(j, i)] = (bx, by, cw, ch)
    return boxes


# ---- charts ----------------------------------------------------------------------------------------

def bars(svg, x, y, w, groups, lo=None, hi=None, log=True, label_w=None, pitch=18.0, bar_h=13.0, fmt=None, size=11, dots=False, axis=True):
    """Horizontal bars in groups: [(heading or None, [(label, value, colour, strong)])]. All bars
    share one axis, so they must share a unit. Things of one unit that still must not be read as one
    series (two rules, two datasets, two machines) go into separate groups: a line divides them and
    each has its heading. Quantities of different units get a call each, with `axis=False` (no grid,
    no ticks: the values are printed at the bars' ends anyway; `strong` sets a value in bold).
    `dots`: a dot on a thin stem instead of a bar (on a logarithmic axis a bar's length means
    nothing: the stem makes no such claim). Returns the y below."""
    fmt = fmt or (sci if log else num)
    rows = [r for _, rs in groups for r in rs]
    vals = [r[1] for r in rows]
    if label_w is None:
        label_w = max(text_width(r[0], size) for r in rows) + 12
    room = max(text_width(fmt(v), size, True) for v in vals) + 12
    bx0, bx1 = x + label_w, x + w - room
    if log:
        lo = lo or 10.0 ** math.floor(math.log10(min(vals)))
        hi = hi or 10.0 ** math.ceil(math.log10(max(vals)))
        scale = Log(lo, hi, bx0, bx1)
    else:
        scale = Lin(lo or 0.0, hi or max(vals) * 1.02, bx0, bx1)
    head_h = 17.0
    total = len(rows) * pitch + sum(head_h for h, _ in groups if h) + 6 * (len(groups) - 1)
    if axis and log:
        log_grid(svg, scale, y, y + total, major="#dcdcdc", minor="#cfcfcf")
    elif axis:
        lin_grid(svg, scale, y, y + total)
    yy = y
    for g, (heading, rs) in enumerate(groups):
        if g:
            svg.line(x, yy + 3, x + w, yy + 3, stroke=MID, sw=0.8, check=False)
            yy += 6
        if heading:
            svg.text(x, yy + 12.5, heading, size=size, fill=GREY, halo="#ffffff")
            yy += head_h
        svg.line(bx0, yy, bx0, yy + pitch * len(rs), stroke=INK, sw=1, check=False)     # the axis, beside the bars only
        for r in rs:
            label, v, colour = r[0], r[1], r[2]
            strong = len(r) > 3 and r[3]
            cy = yy + pitch / 2
            svg.text(bx0 - 8, cy + size * 0.35, label, size=size, anchor="end")
            if dots:
                svg.line(bx0, cy, scale(v), cy, stroke=colour, sw=1.2, check=False)
                svg.circle(scale(v), cy, 4.2, fill=colour)
                end = scale(v) + 4.2
            else:
                svg.rect(bx0, cy - bar_h / 2, scale(v) - bx0, bar_h, fill=colour)
                end = scale(v)
            svg.text(end + 5, cy + size * 0.35, fmt(v), size=size, weight="bold" if strong else None, halo="#ffffff")
            yy += pitch
    if not axis:
        return y + total + 4
    ticks = [(10.0 ** e, pow10(e)) for e in scale.decades()] if log else list(zip(scale.ticks(), tick_labels(scale.ticks())))
    for v, label in ticks:
        svg.text(scale(v), y + total + 12, label, size=9.5, anchor="middle", fill=GREY)
    return y + total + 18


def ratio_chart(svg, x, y, w, rows, kinds, lo, hi, label_w=200.0, row_h=24.0, behind="the baseline ahead", ahead="ahead of the baseline", colour=BLUE):
    """Results against a baseline as ratios on a logarithmic axis: 1× is a line down the chart, its
    two sides are shaded and named, and what loses is drawn as plainly as what wins.

    rows: dicts with
        name    what was run (a file name in backticks, a configuration)
        note    a smaller second line: sizes, lengths, conditions (optional)
        group   a heading; rows of one group stay together, a line divides the groups (optional)
        points  [(kind, ratio)] or [(kind, ratio, "min")] for a lower bound (printed with ≥); or
        range   (kind, low, high): several results in one row
    kinds: {kind: (shape, text for the key)}; shape is "dot", "ring" or "diamond". Give each kind of
        evidence its own shape (measured here, with setup cost included, on other hardware ...).
    Returns the y below the key."""
    px0, pw = x + label_w, w - label_w - 4
    P = Log(lo, hi, px0, px0 + pw)
    groups = []
    for r in rows:
        if r.get("group") and r["group"] not in groups:
            groups.append(r["group"])
    head_h = 17.0
    ty = y + 18
    total = len(rows) * row_h + len(groups) * head_h
    one = P(1)
    svg.rect(px0, ty - 4, one - px0, total + 8, fill="#f3f3f3")
    svg.rect(one, ty - 4, px0 + pw - one, total + 8, fill="#e9f2f9")
    log_grid(svg, P, ty - 4, ty + total + 4, minor="#c4ccd2")
    for e in P.decades():
        svg.text(P(10.0 ** e), ty + total + 17, pow10(e) + "×", size=10, anchor="middle", fill=GREY)
    svg.line(one, ty - 4, one, ty + total + 4, stroke=INK, sw=1.2, check=False)
    svg.text(one - 7, ty - 10, behind, size=10.5, anchor="end", fill=GREY)
    svg.text(one + 7, ty - 10, ahead, size=10.5, fill=colour)

    def shade(xx):
        return "#f3f3f3" if xx < one else "#e9f2f9"

    def mark(kind, xx, yy):
        shape = kinds[kind][0]
        if shape == "dot":
            svg.circle(xx, yy, 5, fill=colour)
        elif shape == "ring":
            svg.circle(xx, yy, 4.3, fill="#ffffff", stroke=colour, sw=1.7)
        elif shape == "diamond":
            svg.diamond(xx, yy, 5.5, sw=1.4)
        else:
            raise ValueError(f"shape {shape!r}: use dot, ring or diamond")

    group, yy, used = None, ty, []
    for r in rows:
        if r.get("group") and r["group"] != group:
            group = r["group"]
            if yy > ty:
                svg.line(x, yy, px0 + pw, yy, stroke=MID, sw=0.8, check=False)
            svg.rect(x - 3, yy + 1, pw + label_w + 3, head_h - 2, fill="#ffffff", opacity=0.82)
            svg.text(x, yy + 12.5, group, fill=GREY)
            yy += head_h
        cy = yy + row_h / 2
        note = r.get("note")
        svg.text(px0 - 9, cy - 0.5 if note else cy + 3.8, r["name"], anchor="end", max_width=label_w - 9)
        if note:
            svg.text(px0 - 9, cy + 10, note, size=9.5, anchor="end", fill=GREY, max_width=label_w - 9)
        if "range" in r:
            kind, a, b = r["range"]
            svg.line(P(a), cy, P(b), cy, stroke=INK, sw=1.4, check=False)
            mark(kind, P(a), cy)
            mark(kind, P(b), cy)
            svg.text(P(b) + 10, cy + 3.8, f"{times(a)[:-1]}–{times(b)}", size=10.5, halo=shade(P(b) + 30))
            used.append(kind)
        else:
            pts = sorted(r["points"], key=lambda p: p[1])
            xs = [P(p[1]) for p in pts]
            if len(pts) > 1:
                svg.line(xs[0], cy, xs[-1], cy, stroke=MID, sw=1, check=False)
            for p, xx in zip(pts, xs):
                mark(p[0], xx, cy)
                used.append(p[0])
            for k, (p, xx) in enumerate(zip(pts, xs)):
                txt = "≥ " + times(floor_sig(p[1])) if len(p) > 2 and p[2] == "min" else times(p[1])
                tw = text_width(txt, 10.5)
                left = len(pts) > 1 and k == 0
                if left and xx - 12 - tw < one < xx - 8:       # never across the 1× line: the other side instead
                    left = False
                if not left and k + 1 < len(pts) and xx + 12 + tw > xs[k + 1] - 8:
                    continue                                    # no room between two close marks: the outer labels say it
                if not left and xx + 12 + tw > px0 + pw and (k == 0 or xx - 12 - tw > xs[k - 1] + 8):
                    left = True                                 # no room before the edge of the chart
                svg.text(xx - 10 if left else xx + 10, cy + 3.8, txt, size=10.5, anchor="end" if left else "start",
                         halo=shade(xx - 30 if left else xx + 30))
        yy += row_h
    ly, lx = ty + total + 38, x
    for kind, (_, label) in kinds.items():
        if kind in used:
            mark(kind, lx + 6, ly - 4)
            svg.text(lx + 16, ly, label, size=10.5, fill=GREY)
            lx += 16 + text_width(label, 10.5) + 18
    return ly + 8


# ---- sources ---------------------------------------------------------------------------------------

NUM = r"([0-9][0-9.]*(?:[eE][+-]?[0-9]+)?)"        # a number in a pattern for Logs


class Logs:
    """The measured numbers of a figure, read from the raw logs of the runs. Nothing is typed in:
    every number is found by the line that reports it, and a missing line is an error, so a figure
    cannot silently keep a number that the logs no longer hold.

        logs = Logs("logs/2026-11-25")
        rate, = logs.find("kernel.txt", rf"bit-plane kernel: .* = {NUM} cell-updates/s")
    """

    def __init__(self, directory):
        self.dir, self._cache = directory, {}

    def lines(self, name):
        if name not in self._cache:
            with open(os.path.join(self.dir, name), encoding="utf-8") as f:
                self._cache[name] = f.read().splitlines()
        return self._cache[name]

    @staticmethod
    def _groups(m):
        return [float(x) if re.fullmatch(NUM, x or "") else x for x in m.groups()]

    def find(self, name, pattern, after=None, nth=0):
        """The groups of the `nth` line of file `name` that matches `pattern` (numbers as floats),
        looking only below the first line that contains `after` if that is given."""
        lines, start = self.lines(name), 0
        if after is not None:
            start = next((i for i, l in enumerate(lines) if after in l), None)
            if start is None:
                raise KeyError(f"{name}: no line contains {after!r}")
        hits = [m for m in (re.search(pattern, l) for l in lines[start:]) if m]
        if len(hits) <= nth:
            raise KeyError(f"{name}: {pattern!r} not found" + (f" after {after!r}" if after else ""))
        return self._groups(hits[nth])

    def all(self, name, pattern):
        """The groups of every matching line."""
        return [self._groups(m) for m in (re.search(pattern, l) for l in self.lines(name)) if m]


# ---- self-test -------------------------------------------------------------------------------------

def _selftest():
    assert thousands(1234567.4) == "1,234,567" and num(0.012345) == "0.0123" and num(1234.5) == "1,230"
    assert num(5.0) == "5.00" and num(5.0, trim=True) == "5" and num(8.5, trim=True) == "8.5" and num(120.0, trim=True) == "120"
    assert sci(14321) == "1.4·10^{4}" and sci(9.96e5) == "1.0·10^{6}" and times(0.0551) == "0.055×" and times(4.44) == "4.4×"
    assert abs(floor_sig(4.49) - 4.4) < 1e-9 and abs(floor_sig(4.4) - 4.4) < 1e-9 and short(9106) == "9.1k" and short(36480) == "36k"
    assert abs(text_width("Hello, width", 20) - 103.36) < 0.01, text_width("Hello, width", 20)
    assert text_width("a **b** c", 10) > text_width("a b c", 10) and text_width("x^{2}", 10) < text_width("x2", 10)
    assert wrap("one `two three` four", 10, 60) == ["one", "`two\u00a0three`", "four"]
    assert wrap("it took 0.02 ms and 7.0 % of 5 hours", 10, 1000) == ["it took 0.02\u00a0ms and 7.0\u00a0% of 5 hours"]
    entities({"Robin Hood": VERMILION})
    assert VERMILION in rich(wrap("by [[Robin Hood]]", 10, 500)[0], 10) and VERMILION not in rich("[[Robin Hood]]", 10, neutral=False)
    assert Lin(0, 1, 0, 100).ticks() == [0, 0.2, 0.4, 0.6, 0.8, 1.0] and Log(1e3, 1e6, 0, 3).decades() == [3, 4, 5, 6]
    assert tick_labels([0, 20.0, 40.0]) == ["0", "20", "40"] and tick_labels([0, 0.5, 1.0]) == ["0.0", "0.5", "1.0"] and tick_labels([0, 2500]) == ["0", "2,500"]
    png = png_indexed([bytes([0, 1]), bytes([1, 0])], [(0, 0, 0), (255, 255, 255)], 3)
    assert png[:8] == b"\x89PNG\r\n\x1a\n" and struct.unpack(">II", png[16:24]) == (6, 6)
    assert quantize([[0.0, 0.5, 1.0]]) == [bytes([0, 128, 255])] and len(VIRIDIS) == 256 and mix("#000000", "#ffffff", 0.5) == "#808080"
    assert spread([10, 11, 30], 5) == [8.0, 13.0, 30.0] and spread([30, 10], 5) == [30, 10]
    s = Svg(400)
    s.text(20, 30, "first")
    s.text(22, 32, "second")
    s.text(390, 60, "off the page")
    s.image(20, 80, 40, 40, png)
    s.text(25, 100, "on it")
    s.text(25, 115, "haloed", halo="#000000", fill="#ffffff")
    s.line(10, 150, 200, 150)
    s.text(20, 153, "struck through")
    s.rect(220, 80, 60, 40, fill="#111111", picture=True)
    s.text(225, 100, "on shapes", fill="#ffffff")
    found = [m for m, _ in s.problems(200)]
    assert len(found) == 5 and "overlap" in found[0] and "leaves" in found[1] and "picture" in found[2] and "line" in found[3] and "picture" in found[4], found
    try:
        s.finish(200)
        raise AssertionError("finish() accepted a figure with problems")
    except LayoutError:
        pass
    ok = Svg(760)
    y = section(ok, title(ok, "Test", "a tagline"), 1, "A heading", "with a subtitle", [("full", "measured"), ("partial", "on one machine"), ("model", "a model")])
    boxes, y = cards(ok, ok.M, y, ok.CW, [dict(title="One", text="A **term** and `a file`.", n=1), dict(title="Two", text="[[Thing]] in x^{2}.", style="frame")], cols=2)
    connect(ok, boxes[0], boxes[1], "then")
    y = bars(ok, ok.M, y + 20, ok.CW, [("group a", [("first", 3.4e8, MID), ("second", 3.0e11, BLUE, True)]), ("group b", [("third", 1.4e12, GREEN)])])
    y = ratio_chart(ok, ok.M, y + 10, ok.CW, [dict(name="`a.dat`", note="large", group="g", points=[("m", 18.0), ("r", 0.64)]),
                                              dict(name="`b.dat`", group="g", points=[("m", 5.8e5), ("s", 4.44, "min")]),
                                              dict(name="others", group="h", range=("r", 0.36, 1.07))],
                    dict(m=("dot", "measured"), s=("ring", "with setup"), r=("diamond", "reference")), 10 ** -1.5, 10 ** 6.5, label_w=90)
    cell_grid(ok, ok.M, y + 6, [[1, 2, 2], [None, 3, 1]], 30, 18)
    cells = grid(ok.M + 140, y + 6, 580, 100, 3, gap=20)
    assert len(cells) == 3 and abs(cells[2][0] + cells[2][2] - (ok.M + 720)) < 1e-9
    ok.rect(*cells[0], fill="#111111", picture=True)
    yy = callout(ok, cells[0][0] + 40, y + 40, cells[1][0], y + 20, "a **term**, said where the thing is", cells[1][2], n="a")
    assert yy > y + 20
    stat(ok, cells[2][0], y + 40, times(8.7), "fewer probes for a miss", cells[2][2], status="full")
    section(ok, y + 120, None, "A heading without a number")
    y += 150
    at = swarm(ok, [5, 5, 5.2, 5.1, 9, 5], Lin(0, 10, ok.M, ok.M + 300), y + 40)
    assert len(at) == 6 and min((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 for i, a in enumerate(at) for b in at[i + 1:]) >= 6.6 ** 2 - 1e-9
    assert at[4][1] == y + 40 and sum(1 for _, yy in at if yy == y + 40) >= 2
    y += 70
    out = ok.finish(y + 50)
    assert out.startswith("<svg") and "ah-555555" in out and not ok.problems(y + 50), ok.problems(y + 50)
    print("ddfig self-test: ok,", len(_ADV[0]), "characters measured")


if __name__ == "__main__":
    _selftest()
