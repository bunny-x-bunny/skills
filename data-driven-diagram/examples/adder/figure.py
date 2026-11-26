"""Two 8-bit adders, gate by gate: a second miniature, for a figure whose subject is a graph.

Nothing here is a sketch of an adder. The script builds the two networks (ripple carry and
Kogge-Stone), runs each on all 65,536 pairs of inputs at once (one bit of a big integer per pair),
checks the sums, and then draws every gate and every wire with ddgraph's layered layout. The shade
of a wire is data too: the share of the 65,536 cases in which it carries a 1.

    python figure.py        ->  figures/adders.svg
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "scripts"))     # in a project: copy ddfig.py and ddgraph.py next to this file
import ddfig as dd  # noqa: E402
from ddfig import BLUE, GREEN, GREY, INK, MID, ORANGE, Svg, pct, thousands  # noqa: E402
from ddgraph import draw_wires, layered  # noqa: E402

OUT = os.path.join(HERE, "figures", "adders.svg")
BITS = 8
CASES = 1 << (2 * BITS)                # every pair (a, b)
GATE = {"AND": BLUE, "OR": ORANGE, "XOR": GREEN}
OP = {"AND": int.__and__, "OR": int.__or__, "XOR": int.__xor__}


class Net:
    """Two-input gates in the order they were made; `outs`: name of an output -> the node that drives it."""

    def __init__(self, name):
        self.name, self.gates, self.outs = name, {}, {}
        self.inputs = [f"{v}{i}" for i in range(BITS) for v in "ab"]

    def gate(self, op, x, y):
        g = f"{op.lower()}{len(self.gates)}"
        self.gates[g] = (op, [x, y])
        return g

    def prune(self):
        """Drop the gates that no output depends on."""
        live, stack = set(), list(self.outs.values())
        while stack:
            g = stack.pop()
            if g in self.gates and g not in live:
                live.add(g)
                stack += self.gates[g][1]
        self.gates = {g: v for g, v in self.gates.items() if g in live}

    def evaluate(self, words):
        val = dict(words)
        for g, (op, (x, y)) in self.gates.items():
            val[g] = OP[op](val[x], val[y])
        return val

    def depth(self):
        lvl = {i: 0 for i in self.inputs}
        for g, (_, args) in self.gates.items():
            lvl[g] = 1 + max(lvl[a] for a in args)
        return max(lvl.values())


def ripple():
    n = Net("ripple carry")
    carry = None
    for i in range(BITS):
        p, g = n.gate("XOR", f"a{i}", f"b{i}"), n.gate("AND", f"a{i}", f"b{i}")
        if carry is None:
            n.outs[f"s{i}"], carry = p, g
        else:
            n.outs[f"s{i}"] = n.gate("XOR", p, carry)
            carry = n.gate("OR", g, n.gate("AND", p, carry))
    n.outs["carry"] = carry
    return n


def kogge_stone():
    n = Net("Kogge-Stone")
    p0 = [n.gate("XOR", f"a{i}", f"b{i}") for i in range(BITS)]
    P, G = list(p0), [n.gate("AND", f"a{i}", f"b{i}") for i in range(BITS)]
    k = 1
    while k < BITS:              # after this round, (P[i], G[i]) span the bits i-2k+1 .. i
        P2, G2 = list(P), list(G)
        for i in range(k, BITS):
            G2[i] = n.gate("OR", G[i], n.gate("AND", P[i], G[i - k]))
            P2[i] = n.gate("AND", P[i], P[i - k])
        P, G, k = P2, G2, 2 * k
    n.outs["s0"] = p0[0]
    for i in range(1, BITS):
        n.outs[f"s{i}"] = n.gate("XOR", p0[i], G[i - 1])
    n.outs["carry"] = G[BITS - 1]
    n.prune()
    return n


def all_cases():
    """Input words: bit c of a_i is bit i of a in case c, where a = c mod 256 and b = c div 256."""
    words = {f"{v}{i}": 0 for i in range(BITS) for v in "ab"}
    want = {**{f"s{i}": 0 for i in range(BITS)}, "carry": 0}
    for c in range(CASES):
        a, b = c & (2 ** BITS - 1), c >> BITS
        for i in range(BITS):
            words[f"a{i}"] |= ((a >> i) & 1) << c
            words[f"b{i}"] |= ((b >> i) & 1) << c
            want[f"s{i}"] |= (((a + b) >> i) & 1) << c
        want["carry"] |= ((a + b) >> BITS) << c
    return words, want


def sub(name):
    """a3 -> a_{3}"""
    return f"{name[0]}_{{{name[1:]}}}" if name[1:].isdigit() else name


def draw(svg, net, val, x0, y, level_w, height):
    """One network in full; returns the layout."""
    depth = net.depth()
    x1 = x0 + level_w * (depth + 1)
    in_y = {name: y + k * height / (len(net.inputs) - 1) for k, name in enumerate(net.inputs)}
    outs = list(net.outs)
    out_y = {net.outs[o]: y + height / 2 + (k - (len(outs) - 1) / 2) * 17 for k, o in enumerate(outs)}
    L = layered({g: args for g, (_, args) in net.gates.items()}, x0, x1, y, y + height, in_y=in_y, out_y=out_y)
    assert L.depth == depth
    svg.rect(x0 - 4, y - 12, x1 - x0 + 8, height + 24, fill="#f7f7f7")
    draw_wires(svg, L, shade=lambda node: bin(val[node]).count("1") / CASES)
    for g, (op, _) in net.gates.items():
        gx, gy = L.pos[g]
        svg.circle(gx, gy, 3.4, fill=GATE[op], stroke="#ffffff", sw=0.6)
    for name in net.inputs:
        px, py = L.pos[name]
        svg.circle(px, py, 2, fill=INK)
        svg.text(px - 8, py + 3.5, sub(name), size=10, anchor="end", fill=GREY)
    for o in outs:
        px, py = L.pins[net.outs[o]]
        svg.circle(px, py, 2, fill=INK)
        svg.text(px + 8, py + 3.5, sub(o), size=10, fill=GREY)
    for lv in range(1, depth + 1):
        svg.line(x0 + lv * level_w, y + height + 14, x0 + lv * level_w, y + height + 18, stroke=MID, sw=0.8, check=False)
        svg.text(x0 + lv * level_w, y + height + 29, str(lv), size=9.5, anchor="middle", fill=GREY)
    svg.text(x0, y + height + 29, "logic level", size=9.5, anchor="end", fill=GREY)
    return L


def counts(net):
    c = {op: sum(1 for o, _ in net.gates.values() if o == op) for op in GATE}
    return ", ".join(f"{v} {op}" for op, v in c.items())


def build():
    nets = [ripple(), kogge_stone()]
    words, want = all_cases()
    vals = []
    for n in nets:                                   # the sums, on every pair of inputs, before anything is drawn
        val = n.evaluate(words)
        for o, node in n.outs.items():
            assert val[node] == want[o], f"{n.name}: output {o} is wrong"
        vals.append(val)
    dd.entities({"ripple carry": INK, "Kogge-Stone": INK})

    svg = Svg(1200)
    r, ks = nets
    y = dd.title(svg, "Two 8-bit adders, gate by gate", f"the same sums in {ks.depth()} logic levels instead of {r.depth()}, for {len(ks.gates) / len(r.gates):.1f} times the gates",
                 note="Both networks are built, checked and laid out by `figure.py`.",
                 intro="Every gate and wire is drawn. A wire is darker the more often it carries a 1 over all "
                       f"{thousands(CASES)} pairs of inputs; depth, the longest path, is what limits the speed.")
    x0, level_w, height = svg.M + 40, 68.0, 250.0
    y += 6
    layouts = []
    for k, (n, val) in enumerate(zip(nets, vals)):
        svg.text(svg.M, y + 8, f"[[{n.name}]]", size=14)
        svg.text(svg.M + dd.text_width(n.name, 14, True) + 12, y + 8, f"{len(n.gates)} gates ({counts(n)}), depth {n.depth()}", size=11.5, fill=GREY)
        L = draw(svg, n, val, x0, y + 34, level_w, height)
        layouts.append(L)
        y += 34 + height + 48
    # beside the shallower network: the trade, as numbers taken from the two networks
    bx = x0 + level_w * (ks.depth() + 1) + 110
    by = y - (34 + height + 48) + 34
    bw = svg.W - svg.M - bx
    dd.legend(svg, bx, by + 2, [(GATE[op], op) for op in GATE])
    yy = by + 22
    for heading, a, b in (("gates", len(r.gates), len(ks.gates)), ("depth, in logic levels", r.depth(), ks.depth()),
                          ("wire crossings in these drawings", layouts[0].crossings, layouts[1].crossings)):
        # three quantities, three units: a scale each, and no axis (the values stand at the bars)
        yy = dd.bars(svg, bx, yy, bw, [(heading, [(f"[[{r.name}]]", a, MID), (f"[[{ks.name}]]", b, INK, True)])],
                     log=False, axis=False, label_w=96, fmt=lambda v: f"{v:.0f}") + 6
    carry = max(bin(vals[0][g]).count("1") / CASES for g in r.gates)
    svg.para(bx, yy + 14, f"Checked before drawing: each network gives a + b on all {thousands(CASES)} pairs. [[{r.name}]] passes the carry from bit to bit, "
             f"so its last sum waits {r.depth()} levels; [[{ks.name}]] works the carries out side by side in {ks.depth()}, with "
             f"{len(ks.gates) / len(r.gates):.1f} times the gates. The darkest wire is 1 in {pct(carry, 0)} of the cases.", bw)
    svg.save(OUT, y - 8, title="A ripple-carry and a Kogge-Stone adder for 8 bits, every gate and wire, verified on all inputs")


if __name__ == "__main__":
    build()
