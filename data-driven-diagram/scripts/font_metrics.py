"""Advance widths of a TrueType/OpenType font, read straight from the font file (cmap + hmtx), in
1/1000 em. ddfig.py lays text out with such tables instead of a browser, so that a figure script can
wrap text, right-align numbers and audit overlaps on any machine. Use this when

  * a figure needs characters that ddfig's built-in Arial tables lack (ddfig reports them as
    "unmeasured"), or
  * a venue or house style asks for another typeface than Arial / Helvetica / Liberation Sans.

    python font_metrics.py REGULAR.ttf BOLD.ttf                 # a METRICS table to paste into ddfig.py
    python font_metrics.py REGULAR.ttf BOLD.ttf --chars "∮⌈⌉"   # an EXTRA dict for these characters
    python font_metrics.py REGULAR.ttf --text "Hello" --size 11 # the width of a string in px

No third-party packages. Reads .ttf / .otf, and .ttc collections with --index.
"""
import argparse
import struct
import sys

# what the built-in table covers: Basic Latin, Latin-1, Latin Extended-A, Greek, Cyrillic, and the
# punctuation, arrows and operators that scientific text uses
RANGES = [(0x20, 0x7E), (0xA0, 0xFF), (0x100, 0x17F), (0x391, 0x3C9), (0x400, 0x45F)]
SCATTER = ("ƒǍǎǦǧȘșȚț" "ϑϕϖ" "ҐґҒғҚқҢңҮүҰұҲҳҺһӘәӨө"
           "–—‘’‚“”„†‡•…‰′″‹›⁰⁴⁵⁶⁷⁸⁹⁺⁻ⁿ₀₁₂₃₄₅₆₇₈₉€ℓ№™Ω℮"
           "←↑→↓↔↕⇐⇒⇔∀∂∃∅∆∇∈∉∋∏∑−∓∕∗∘∙√∝∞∠∧∨∩∪∫∴∼≅≈≠≡≤≥≪≫⊂⊃⊆⊇⊕⊗⊥⋅⌀□▪▫◊")


def _tables(data, index=0):
    base = 0
    if data[:4] == b"ttcf":
        n = struct.unpack(">I", data[8:12])[0]
        if not 0 <= index < n:
            raise SystemExit(f"the collection holds {n} fonts; --index must be below that")
        base = struct.unpack(">I", data[12 + 4 * index:16 + 4 * index])[0]
    n = struct.unpack(">H", data[base + 4:base + 6])[0]
    out = {}
    for i in range(n):
        tag, _, off, length = struct.unpack(">4sIII", data[base + 12 + 16 * i:base + 28 + 16 * i])
        out[tag.decode("latin-1")] = data[off:off + length]
    return out


def _cmap(t):
    """code point -> glyph, from the best Unicode subtable (format 12, else format 4)."""
    n = struct.unpack(">H", t[2:4])[0]
    subs = []
    for i in range(n):
        plat, enc, off = struct.unpack(">HHI", t[4 + 8 * i:12 + 8 * i])
        fmt = struct.unpack(">H", t[off:off + 2])[0]
        rank = {(3, 10, 12): 0, (0, 4, 12): 1, (0, 6, 12): 1, (3, 1, 4): 2, (0, 3, 4): 3}.get((plat, enc, fmt))
        if rank is None and plat == 0 and fmt in (4, 12):
            rank = 4
        if rank is not None:
            subs.append((rank, fmt, off))
    if not subs:
        raise SystemExit("no Unicode cmap subtable (format 4 or 12) in this font")
    _, fmt, off = min(subs)
    out = {}
    if fmt == 12:
        groups = struct.unpack(">I", t[off + 12:off + 16])[0]
        for g in range(groups):
            a, b, start = struct.unpack(">III", t[off + 16 + 12 * g:off + 28 + 12 * g])
            for c in range(a, b + 1):
                out[c] = start + c - a
        return out
    seg = struct.unpack(">H", t[off + 6:off + 8])[0] // 2
    p = off + 14
    ends = struct.unpack(f">{seg}H", t[p:p + 2 * seg])
    p += 2 * seg + 2
    starts = struct.unpack(f">{seg}H", t[p:p + 2 * seg])
    p += 2 * seg
    deltas = struct.unpack(f">{seg}h", t[p:p + 2 * seg])
    p += 2 * seg
    offs = struct.unpack(f">{seg}H", t[p:p + 2 * seg])
    for i in range(seg):
        for c in range(starts[i], ends[i] + 1):
            if c == 0xFFFF:
                continue
            if offs[i] == 0:
                g = (c + deltas[i]) & 0xFFFF
            else:
                q = p + 2 * i + offs[i] + 2 * (c - starts[i])
                g = struct.unpack(">H", t[q:q + 2])[0]
                if g:
                    g = (g + deltas[i]) & 0xFFFF
            if g:
                out[c] = g
    return out


class Font:
    def __init__(self, path, index=0):
        with open(path, "rb") as f:
            t = _tables(f.read(), index)
        self.upm = struct.unpack(">H", t["head"][18:20])[0]
        self.n_metrics = struct.unpack(">H", t["hhea"][34:36])[0]
        self.hmtx = t["hmtx"]
        self.cmap = _cmap(t["cmap"])

    def advance(self, ch):
        """Advance width of a character in 1/1000 em, or None if the font has no glyph for it."""
        g = self.cmap.get(ord(ch))
        if g is None:
            return None
        g = min(g, self.n_metrics - 1)
        return round(struct.unpack(">H", self.hmtx[4 * g:4 * g + 2])[0] * 1000 / self.upm)


def _runs(regular, bold):
    """Consecutive characters that both fonts have, as {first code point: (widths, bold widths)}."""
    points = sorted({c for a, b in RANGES for c in range(a, b + 1)} | set(map(ord, SCATTER)))
    runs, prev = {}, None
    for c in points:
        r, b = regular.advance(chr(c)), bold.advance(chr(c))
        if r is None or b is None:
            prev = None
            continue
        if prev is not None and c == prev + 1:
            runs[start][0].append(r)
            runs[start][1].append(b)
        else:
            start = c
            runs[start] = ([r], [b])
        prev = c
    return runs


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("regular")
    ap.add_argument("bold", nargs="?")
    ap.add_argument("--chars", help="print an EXTRA dict for exactly these characters")
    ap.add_argument("--text", help="measure this string with the regular font")
    ap.add_argument("--size", type=float, default=11.0)
    ap.add_argument("--index", type=int, default=0, help="font number inside a .ttc collection")
    a = ap.parse_args()
    reg = Font(a.regular, a.index)
    bold = Font(a.bold, a.index) if a.bold else reg
    if a.text is not None:
        missing = [c for c in a.text if reg.advance(c) is None]
        w = sum(reg.advance(c) or 0 for c in a.text) * a.size / 1000
        print(f"{w:.2f} px at {a.size:g} px" + (f"; no glyph for {''.join(missing)!r}" if missing else ""))
        return
    if a.chars:
        print("EXTRA = {")
        for c in a.chars:
            r, b = reg.advance(c), bold.advance(c)
            if r is None or b is None:
                print(f"    # {c!r} (U+{ord(c):04X}): no glyph in this font", file=sys.stderr)
                continue
            print(f"    {ascii(c)}: ({r}, {b}),")
        print("}")
        return
    runs = _runs(reg, bold)
    total = sum(len(r) for r, _ in runs.values())
    print(f"# {total} characters, as runs from a first code point. An entry is the advance width in 1/1000 em;")
    print("# regular/bold where the two differ. Written by font_metrics.py.")
    print("METRICS = {")
    for start, (r, b) in runs.items():
        entries = [str(x) if x == y else f"{x}/{y}" for x, y in zip(r, b)]
        lines = [",".join(entries[i:i + 20]) for i in range(0, len(entries), 20)]
        print(f"    0x{start:04X}: " + "\n            ".join(f'"{l},"' for l in lines[:-1]) + ("\n            " if len(lines) > 1 else "") + f'"{lines[-1]}",')
    print("}")


if __name__ == "__main__":
    main()
