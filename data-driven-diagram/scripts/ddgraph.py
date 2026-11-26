"""ddgraph: a real graph drawn in full. A circuit, a computation graph, a pipeline, a dependency
graph: when the project has one, the figure shows that graph, every node and every edge, laid out
from the data, instead of a few boxes that stand for it.

    L = layered(preds, x0, x1, top, bottom)     # preds: {node: [the nodes it reads from]}
    draw_wires(svg, L, shade=...)               # edges, optionally shaded by a value they carry
    for node, (x, y) in L.pos.items(): ...      # draw each node as the project's kind of node

The layout is the classical layered one: a column per level (longest path from the sources), nodes
moved inside their slack to shorten the wires, columns ordered by barycentre sweeps to reduce
crossings, heights by least squares under the order (isotonic regression). An edge that spans
several columns passes a point in each of them, and a node with several consumers runs as one wire
with a branch per consumer, as in a circuit diagram. A few hundred nodes take about a second.

Copy this file next to ddfig.py when the figure draws a graph. Run it for a self-test.
"""
import bisect


class _Trunk(tuple):
    """(node, column): where the wire of `node` passes a column on its way to a later one."""


class _Pin(tuple):
    """(node,): the end of the wire of a pinned node at the right edge."""


class Layout:
    """pos: node -> (x, y); pins: pinned node -> (x, y) of its end at the right edge;
    wires: [(node whose value the segment carries, (x1, y1), (x2, y2))];
    level: node -> column; depth: the last column of nodes; dx: the distance between columns;
    crossings: wire crossings in the drawing."""


def _isotonic(z):
    """Least-squares non-decreasing fit (pool adjacent violators)."""
    blocks = []
    for v in z:
        blocks.append([v, 1])
        while len(blocks) > 1 and blocks[-2][0] * blocks[-1][1] > blocks[-1][0] * blocks[-2][1]:
            s, c = blocks.pop()
            blocks[-1][0] += s
            blocks[-1][1] += c
    out = []
    for s, c in blocks:
        out += [s / c] * c
    return out


def _crossings(edges):
    """Crossings between two columns; edges are (rank in the left column, rank in the right)."""
    seen, n = [], 0
    for _, v in sorted(edges):
        n += len(seen) - bisect.bisect_right(seen, v)
        bisect.insort(seen, v)
    return n


def _topological(preds):
    order, state = [], {}
    for root in preds:
        stack = [(root, iter(preds[root]))]
        if state.get(root):
            continue
        state[root] = 1
        while stack:
            node, it = stack[-1]
            for p in it:
                if state.get(p) == 1:
                    raise ValueError(f"the graph has a cycle through {p!r}")
                if not state.get(p):
                    state[p] = 1
                    stack.append((p, iter(preds[p])))
                    break
            else:
                state[node] = 2
                order.append(node)
                stack.pop()
    return order


def layered(preds, x0, x1, top, bottom, in_y=None, out_y=None, node_gap=5.4, wire_gap=2.3, sweeps=40):
    """Place a directed acyclic graph in the box x0..x1, top..bottom, sources at the left.

    preds   {node: [predecessors]}; nodes that only occur as predecessors are sources
    in_y    {source: y}: fixed heights for the sources, e.g. beside the rows of a picture of the
            input (optional; every source must be given)
    out_y   {node: y}: these nodes get an end point at the right edge at that height, e.g. beside
            a picture of the output (optional)
    node_gap, wire_gap   least distance between two nodes, and between two passing wires, of a column
    """
    preds = {n: list(p) for n, p in preds.items()}
    for ps in list(preds.values()):
        for p in ps:
            preds.setdefault(p, [])
    order = _topological(preds)
    cons = {n: [] for n in order}
    for n in order:
        for p in preds[n]:
            cons[p].append(n)
    inner = [n for n in order if preds[n]]
    lvl = {}
    for n in order:
        lvl[n] = 1 + max(lvl[p] for p in preds[n]) if preds[n] else 0
    depth = max(lvl.values())
    pinned = dict(out_y or {})
    for s in pinned:
        if s not in preds:
            raise KeyError(f"out_y names {s!r}, which is not a node")
        if not cons[s] and preds[s]:
            lvl[s] = depth                         # ends of the graph in the last column
    last = depth + 1 if pinned else depth          # the last column of the drawing

    def far(sig, without=None, at=None):
        """The last column the wire of `sig` reaches (its consumer `without` taken to be at `at`)."""
        m = depth + 1 if sig in pinned else 0
        for c in cons[sig]:
            m = max(m, at if c == without else lvl[c])
        return m

    # shorten the wires: move every node inside its slack to where the wires it touches are shortest
    for _ in range(12):
        moved = False
        for g in list(reversed(inner)) + inner:
            if not cons[g]:
                continue
            args = preds[g]
            lo = 1 + max(lvl[a] for a in args)
            hi = min(lvl[c] for c in cons[g]) - 1
            if lo >= hi:
                continue
            best, best_cost = lvl[g], None
            for cand in range(lo, hi + 1):
                cost = (far(g) - cand) + sum(far(a, g, cand) - lvl[a] for a in set(args))
                if best_cost is None or cost < best_cost or (cost == best_cost and abs(cand - lvl[g]) < abs(best - lvl[g])):
                    best, best_cost = cand, cost
            if best != lvl[g]:
                lvl[g], moved = best, True
        if not moved:
            break

    # the nodes of every column: real nodes, the points where longer wires pass, the pins
    cols = [[] for _ in range(last + 1)]
    for n in order:
        cols[lvl[n]].append(n)
    pin = {s: _Pin((s,)) for s in pinned}
    if pinned:
        cols[last] = list(pin.values())
    left, right = {}, {}                           # node -> its neighbours in the column before / after

    def link(a, b):
        right.setdefault(a, []).append(b)
        left.setdefault(b, []).append(a)

    for sig in order:
        end = far(sig)
        prev = sig
        targets = {}
        for c in cons[sig]:
            targets.setdefault(lvl[c], []).append(c)
        if sig in pinned:
            targets.setdefault(last, []).append(pin[sig])
        for col in range(lvl[sig] + 1, end + 1):
            for t in targets.get(col, []):
                link(prev, t)
            if col < end:
                node = _Trunk((sig, col))
                cols[col].append(node)
                link(prev, node)
                prev = node

    # order the columns by barycentre sweeps; columns with given heights keep their order
    first_free = 1 if in_y is not None else 0
    last_free = depth
    if in_y is not None:
        cols[0].sort(key=lambda n: in_y[n])
    if pinned:
        cols[last].sort(key=lambda p: pinned[p[0]])
    rank = {}

    def rerank(c):
        n = len(cols[c])
        for i, node in enumerate(cols[c]):
            rank[node] = (i + 0.5) / n

    for c in range(last + 1):
        rerank(c)

    def total():
        return sum(_crossings([(rank[a], rank[b]) for b in cols[c] for a in left.get(b, [])]) for c in range(1, last + 1))

    best_order, best_x = [list(c) for c in cols], total()
    for it in range(sweeps):
        forward = it % 2 == 0
        for c in (range(first_free, last_free + 1) if forward else range(last_free, first_free - 1, -1)):
            nb = left if forward else right
            key = {n: (sum(rank[m] for m in nb[n]) / len(nb[n]) if nb.get(n) else rank[n]) for n in cols[c]}
            cols[c].sort(key=lambda n: key[n])
            rerank(c)
        x = total()
        if x < best_x:
            best_x, best_order = x, [list(c) for c in cols]
    cols = best_order
    for c in range(last + 1):
        rerank(c)

    # heights: pull every node towards its neighbours, keeping the order and the least distances
    def gap(a, b):
        ta, tb = isinstance(a, _Trunk), isinstance(b, _Trunk)
        return wire_gap if ta and tb else node_gap if not ta and not tb else (node_gap + wire_gap) / 2

    y, offs = {}, {}
    free = [c for c in range(last + 1) if not (c == 0 and in_y is not None) and not (c == last and pinned)]
    if in_y is not None:
        for n in cols[0]:
            y[n] = in_y[n]
    for p in pin.values():
        y[p] = pinned[p[0]]
    for c in free:
        o, acc = [0.0], 0.0
        for a, b in zip(cols[c], cols[c][1:]):
            acc += gap(a, b)
            o.append(acc)
        scale = min(1.0, (bottom - top) / acc) if acc > 0 else 1.0
        offs[c] = [v * scale for v in o]
        for i, n in enumerate(cols[c]):
            y[n] = (top + bottom - offs[c][-1]) / 2 + offs[c][i]

    def trunk(a, b):
        """Two points of one wire: these should be level with each other before anything else."""
        sa = a[0] if isinstance(a, _Trunk) else a
        sb = b[0] if isinstance(b, _Trunk) else b
        return (isinstance(a, _Trunk) or isinstance(b, _Trunk)) and sa == sb

    for it in range(80):
        forward = it % 2 == 0
        for c in (free if forward else reversed(free)):
            want = []
            for n in cols[c]:
                num = den = 0.0
                for nb, w0 in ((left, 1.0 if forward or it > 50 else 0.35), (right, 1.0 if not forward or it > 50 else 0.35)):
                    for m in nb.get(n, []):
                        w = w0 * (3.0 if trunk(n, m) else 1.0)
                        num += w * y[m]
                        den += w
                want.append(num / den if den else y[n])
            o = offs[c]
            z = _isotonic([w - d for w, d in zip(want, o)])
            hi = bottom - o[-1]
            for n, v, d in zip(cols[c], z, o):
                y[n] = min(max(v, top), hi) + d

    L = Layout()
    L.dx = (x1 - x0) / max(1, last)
    at = {n: (x0 + (x1 - x0) * c / max(1, last), y[n]) for c in range(last + 1) for n in cols[c]}
    L.pos = {n: at[n] for n in order}
    L.pins = {s: at[p] for s, p in pin.items()}
    L.wires = [(a[0] if isinstance(a, _Trunk) else a, at[a], at[b]) for a in right for b in right[a]]
    L.level, L.depth, L.crossings = lvl, depth, best_x
    return L


def draw_wires(svg, L, shade=None, levels=8, colour=None, sw=0.9):
    """The edges of a layout as smooth curves. `shade`: a function node -> 0..1; a wire is then
    drawn darker and a little heavier the larger the value it carries (the share of cases in which
    a signal is 1, an activation, a flow), which puts real data on the structure. Without it every
    wire has `colour` (default: a mid grey)."""
    groups = {}
    for sig, (xa, ya), (xb, yb) in L.wires:
        k = round(min(max(shade(sig), 0.0), 1.0) * levels) / levels if shade else None
        m = (xb - xa) * 0.5
        groups.setdefault(k, []).append(f"M{xa:.1f},{ya:.1f}C{xa + m:.1f},{ya:.1f} {xb - m:.1f},{yb:.1f} {xb:.1f},{yb:.1f}")
    for k in sorted(groups, key=lambda k: -1 if k is None else k):
        if k is None:
            svg.path("".join(groups[k]), stroke=colour or "#9a9a9a", sw=sw)
        else:
            v = int(round(198 - 172 * k))
            svg.path("".join(groups[k]), stroke=f"#{v:02x}{v:02x}{v:02x}", sw=0.75 + 0.35 * k)


def _selftest():
    state = 12345

    def rnd(n):
        nonlocal state
        state = (state * 6364136223846793005 + 1442695040888963407) % 2 ** 64
        return (state >> 33) % n

    preds = {}
    names = [f"in{i}" for i in range(8)]
    for i in range(120):
        a, b = names[rnd(len(names))], names[max(0, len(names) - 1 - rnd(12))]
        preds[f"g{i}"] = [a, b] if a != b else [a]
        names.append(f"g{i}")
    used = {p for ps in preds.values() for p in ps}
    sinks = [n for n in preds if n not in used]
    in_y = {f"in{i}": 20.0 + 30 * i for i in range(8)}
    out_y = {s: 30.0 + 20 * i for i, s in enumerate(sinks)}
    for kw in (dict(), dict(in_y=in_y), dict(in_y=in_y, out_y=out_y)):
        L = layered(preds, 0, 800, 0, 400, **kw)
        assert set(L.pos) == set(preds) | {p for ps in preds.values() for p in ps}, "a node is missing"
        assert all(0 <= x <= 800 and -1e-6 <= y <= 400 + 1e-6 for x, y in L.pos.values()), "a node lies outside the box"
        assert all(L.level[n] > max(L.level[p] for p in ps) for n, ps in preds.items()), "an edge runs backwards"
        assert all(abs(b[0] - a[0] - L.dx) < 1e-6 for _, a, b in L.wires), "a wire skips a column"
        cols = {}
        for n, (x, y) in L.pos.items():
            cols.setdefault(round(x, 3), []).append(y)
        if not kw:
            assert all(b - a >= 5.39 for ys in cols.values() for a, b in zip(sorted(ys), sorted(ys)[1:])), "nodes closer than node_gap"
        if "out_y" in kw:
            assert {s: y for s, (_, y) in L.pins.items()} == out_y
        print(f"layered({', '.join(kw) or 'free'}): {len(names)} nodes, {L.depth + 1} columns, {len(L.wires)} wire segments, {L.crossings} crossings")
    try:
        layered({"a": ["b"], "b": ["a"]}, 0, 1, 0, 1)
        raise AssertionError("a cycle was accepted")
    except ValueError:
        pass
    print("ddgraph self-test: ok")


if __name__ == "__main__":
    _selftest()
