#!/usr/bin/env sh
# Assemble a self-contained ER diagram page from a model file.
#
#   sh build.sh MODEL.js OUT.html [--title "Title"] [--intro "One paragraph"] [--standalone]
#
# MODEL.js must define `var MODEL = { ... };` (see references/model-format.md).
# Without --standalone the page is in Artifact form (starts with <title>; the Artifact host adds the
# document skeleton). With --standalone it gets <!doctype html>, <head> and <body> so it opens from disk.
set -eu
DIR=$(cd "$(dirname "$0")/.." && pwd)
if [ $# -lt 2 ]; then
  echo "usage: sh build.sh MODEL.js OUT.html [--title T] [--intro TEXT] [--standalone]" >&2
  exit 2
fi
MODEL=$1; OUT=$2; shift 2
TITLE="Entity-relationship diagram"; INTRO=""; STANDALONE=0
while [ $# -gt 0 ]; do
  case "$1" in
    --title) TITLE=$2; shift 2 ;;
    --intro) INTRO=$2; shift 2 ;;
    --standalone) STANDALONE=1; shift ;;
    *) echo "unknown option: $1" >&2; exit 2 ;;
  esac
done
[ -f "$MODEL" ] || { echo "model file not found: $MODEL" >&2; exit 1; }
grep -q "MODEL" "$MODEL" || { echo "warning: $MODEL does not mention MODEL; the page calls ERDiagram.render(..., MODEL)" >&2; }

awk -v css="$DIR/assets/er-diagram.css" -v js="$DIR/assets/er-diagram.js" -v model="$MODEL" \
    -v title="$TITLE" -v intro="$INTRO" -v standalone="$STANDALONE" '
function cat(f,   l) { while ((getline l < f) > 0) print l; close(f) }
function repl(s, from, to,   i, out) { out = ""; while ((i = index(s, from)) > 0) { out = out substr(s, 1, i - 1) to; s = substr(s, i + length(from)) } return out s }
function html(s) { s = repl(s, "&", "\001"); s = repl(s, "<", "&lt;"); s = repl(s, ">", "&gt;"); s = repl(s, "\"", "&quot;"); return repl(s, "\001", "&amp;") }
BEGIN {
  t = html(title); i = html(intro); inhead = 0
  if (standalone == 1) {
    print "<!doctype html>"; print "<html lang=\"en\">"; print "<head>"
    print "<meta charset=\"utf-8\">"; print "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1, viewport-fit=cover\">"
    inhead = 1
  }
}
index($0, "@@ERD_CSS@@") { cat(css); next }
index($0, "@@ERD_ENGINE@@") { cat(js); next }
index($0, "@@ERD_MODEL@@") { cat(model); next }
inhead && /^<main / { print "</head>"; print "<body>"; inhead = 0 }
{ line = repl($0, "@@TITLE@@", t); line = repl(line, "@@INTRO@@", i); print line }
END { if (standalone == 1) { print "</body>"; print "</html>" } }
' "$DIR/assets/template.html" > "$OUT"
echo "wrote $OUT ($(wc -c < "$OUT" | tr -d ' ') bytes)"
