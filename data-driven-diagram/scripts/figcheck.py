"""Check a figure in a real browser, from the command line: headless Chrome, Chromium or Edge.

    python figcheck.py audit FIGURE.svg
        Lay the figure out with the browser's fonts and report text on text, text leaving the
        canvas, text on a picture without a halo and lines through text (exit status 1 if any),
        then what is worth a look: text that straddles the edge of a box, fonts below 9 px.

    python figcheck.py shoot FIGURE.svg OUTDIR [--zoom 2] [--tile 600x450]
        Write overview.png and enlarged tiles that cover the figure, to be looked at one by one:
        an audit finds collisions, not a label on the wrong curve or a cramped corner.

    python figcheck.py shoot FIGURE.svg OUTDIR --region X,Y,W,H [--zoom 3]
        One enlarged cut, in figure coordinates.

The browser is found in the usual places; name another with --browser or the environment variable
DDFIG_BROWSER. No third-party packages.
"""
import argparse
import html
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent


def find_browser(given=None):
    names = ["chrome", "google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "msedge", "microsoft-edge"]
    places = []
    for root in (os.environ.get("PROGRAMFILES"), os.environ.get("PROGRAMFILES(X86)"), os.environ.get("LOCALAPPDATA")):
        if root:
            places += [Path(root) / "Google/Chrome/Application/chrome.exe", Path(root) / "Microsoft/Edge/Application/msedge.exe",
                       Path(root) / "Chromium/Application/chrome.exe"]
    places += [Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"), Path("/Applications/Chromium.app/Contents/MacOS/Chromium"),
               Path("/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge")]
    for cand in (given, os.environ.get("DDFIG_BROWSER")):
        if cand:
            found = shutil.which(cand) or (cand if Path(cand).is_file() else None)
            if not found:
                raise SystemExit(f"browser not found: {cand}")
            return found
    for n in names:
        if shutil.which(n):
            return shutil.which(n)
    for p in places:
        if p.is_file():
            return str(p)
    raise SystemExit("No Chrome, Chromium or Edge found. Name one with --browser or DDFIG_BROWSER, or open the figure in any\n"
                     f"browser and run {HERE / 'audit_svg.js'} in its console. (ddfig's own audit ran when the figure was written.)")


class Browser:
    def __init__(self, given=None):
        self.exe = find_browser(given)
        self.tmp = Path(tempfile.mkdtemp(prefix="figcheck-"))

    def run(self, *args, timeout=120):
        cmd = [self.exe, "--headless", "--disable-gpu", "--no-first-run", "--no-default-browser-check", "--disable-extensions",
               "--hide-scrollbars", "--force-device-scale-factor=1", f"--user-data-dir={self.tmp / 'profile'}", *args]
        return subprocess.run(cmd, capture_output=True, timeout=timeout)

    def page(self, name, body):
        p = self.tmp / name
        p.write_text("<!doctype html><html><head><meta charset=\"utf-8\"></head><body style=\"margin:0;background:#fff;overflow:hidden\">"
                     + body + "</body></html>", encoding="utf-8")
        return p.as_uri()

    def close(self):
        shutil.rmtree(self.tmp, ignore_errors=True)


def size_of(svg_text):
    m = re.search(r'viewBox="\s*[-\d.]+[ ,]+[-\d.]+[ ,]+([\d.]+)[ ,]+([\d.]+)', svg_text)
    if m:
        return float(m.group(1)), float(m.group(2))
    w, h = re.search(r'<svg[^>]*\swidth="([\d.]+)', svg_text), re.search(r'<svg[^>]*\sheight="([\d.]+)', svg_text)
    if not (w and h):
        raise SystemExit("the SVG has neither a viewBox nor a width and height")
    return float(w.group(1)), float(h.group(1))


def audit(path, browser=None, as_json=False):
    text = Path(path).read_text(encoding="utf-8")
    inline = re.sub(r"^\s*<\?xml[^>]*\?>", "", text)
    js = (HERE / "audit_svg.js").read_text(encoding="utf-8")
    b = Browser(browser)
    try:
        url = b.page("audit.html", inline + '<pre id="ddfig-audit"></pre><script>document.getElementById("ddfig-audit").textContent = ' + js.strip() + ";</script>")
        dom = b.run("--dump-dom", url).stdout.decode("utf-8", "replace")
    finally:
        b.close()
    m = re.search(r'<pre id="ddfig-audit">(.*?)</pre>', dom, re.S)
    if not m or not m.group(1).strip():
        raise SystemExit("the browser returned no audit; is the file a well-formed SVG?")
    r = json.loads(html.unescape(m.group(1)))
    fatal = len(r["overlaps"]) + len(r["off"]) + len(r["onimg"]) + len(r["lines"])
    if as_json:
        print(json.dumps(r, ensure_ascii=False, indent=1))
        return 1 if fatal else 0
    print(f"{path}: {r['width']:.0f} x {r['height']:.0f} px, {r['texts']} texts, {r['images']} pictures")
    for key, what in (("overlaps", "texts overlap"), ("off", "text leaves the canvas"), ("onimg", "text on a picture without a halo"), ("lines", "a line runs through text")):
        print(f"  {what}: {len(r[key])}")
        for e in r[key][:25]:
            print("      " + (f"{e['a']!r} and {e['b']!r}" if "a" in e else repr(e["text"])) + f"  at {tuple(e['at'])}")
    for key, what in (("review", "to look at: text straddling the edge of a box or mark"), ("small", "to look at: font below 9 px")):
        if r[key]:
            print(f"  {what}: {len(r[key])}")
            for e in r[key][:12]:
                print(f"      {e['text']!r}  at {tuple(e['at'])}" + (f"  ({e['shape']})" if "shape" in e else f"  ({e['size']} px)"))
    print("  " + ("FAILED" if fatal else "passed") + f": {fatal} problem(s) a reader would trip over")
    return 1 if fatal else 0


def shoot(path, outdir, zoom=2.0, tile=(600, 450), region=None, browser=None):
    src = Path(path).resolve()
    w, h = size_of(src.read_text(encoding="utf-8"))
    out = Path(outdir).resolve()          # the browser resolves a relative path against its own folder
    out.mkdir(parents=True, exist_ok=True)
    b = Browser(browser)

    def shot(name, x, y, vw, vh, z):
        url = b.page("shot.html", f'<img src="{src.as_uri()}" style="position:absolute;left:{-x * z:.2f}px;top:{-y * z:.2f}px;width:{w * z:.2f}px;height:{h * z:.2f}px">')
        target = out / name
        b.run(f"--window-size={round(vw * z)},{round(vh * z)}", f"--screenshot={target}", url)
        if not target.is_file():
            raise SystemExit(f"the browser wrote no screenshot for {name}")
        print(f"  {target}   x {x:.0f}..{x + vw:.0f}, y {y:.0f}..{y + vh:.0f}")

    try:
        if region:
            x, y, rw, rh = region
            print(f"{path}: one region at {zoom:g}x")
            shot(f"region_{x:.0f}_{y:.0f}_{rw:.0f}_{rh:.0f}.png", x, y, rw, rh, zoom)
            return 0
        fit = min(1.0, 1200 / w, 1500 / h)
        print(f"{path}: {w:.0f} x {h:.0f} px; the whole at {fit:.2f}x, then tiles of {tile[0]} x {tile[1]} px at {zoom:g}x")
        shot("overview.png", 0, 0, w, h, fit)
        cols, rows = max(1, -(-int(w) // tile[0])), max(1, -(-int(h) // tile[1]))
        for r in range(rows):
            for c in range(cols):
                x = min(c * tile[0], max(0, w - tile[0]))
                y = min(r * tile[1], max(0, h - tile[1]))
                shot(f"tile_r{r + 1}_c{c + 1}.png", x, y, min(tile[0], w), min(tile[1], h), zoom)
        print(f"  {cols * rows} tiles: look at every one")
    finally:
        b.close()
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("audit")
    a.add_argument("figure")
    a.add_argument("--json", action="store_true", help="print the browser's full report as JSON")
    a.add_argument("--browser")
    s = sub.add_parser("shoot")
    s.add_argument("figure")
    s.add_argument("outdir")
    s.add_argument("--zoom", type=float, default=2.0)
    s.add_argument("--tile", default="600x450", help="tile size in figure px, WxH")
    s.add_argument("--region", help="X,Y,W,H in figure px: one cut instead of the tiles")
    s.add_argument("--browser")
    args = ap.parse_args()
    if not Path(args.figure).is_file():
        raise SystemExit(f"no such file: {args.figure}")
    if args.cmd == "audit":
        sys.exit(audit(args.figure, args.browser, args.json))
    tile = tuple(int(v) for v in args.tile.lower().split("x"))
    region = tuple(float(v) for v in args.region.split(",")) if args.region else None
    sys.exit(shoot(args.figure, args.outdir, args.zoom, tile, region, args.browser))


if __name__ == "__main__":
    main()
