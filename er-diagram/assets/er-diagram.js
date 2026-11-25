/*!
 * er-diagram engine (er-diagram skill). No dependencies.
 *
 * Draws a zoomable entity-relationship diagram: tables grouped into annotated module boxes on a grid,
 * header colors by table kind, field icons, and right-angled lines routed (A* on an 8 px grid) from each
 * foreign-key field to the key it references, with crow's-foot ends. Hover cards explain tables, fields
 * and lines.
 *
 *   var view = ERDiagram.render(rootElement, MODEL);   // rootElement contains the [data-erd] parts
 *   view.ready.then(...)                               // resolves once every line is routed and drawn
 *   view.check().then(console.log)                     // layout quality metrics
 *   view.fit(); view.zoomTo("Order");                  // navigation helpers
 *
 * The MODEL format is documented in references/model-format.md.
 */
(function (global) {
  "use strict";

  var KINDS = { core: "Core entity", dep: "Owned detail", link: "Link table", ref: "Reference data", log: "Log or ledger" };
  var PCARD = { "1": "exactly one", "01": "zero or one" };
  var CCARD = { "0n": "zero or more", "1n": "one or more" };
  var HEAD = 28, ROW = 18, GHEAD = 72, STUB = 24, S = 8;

  function esc(s) { return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;"); }
  function r1(n) { return Math.round(n * 10) / 10; }
  function natural(a, b) {
    var ra = /^(\D*)(\d*)/.exec(a), rb = /^(\D*)(\d*)/.exec(b);
    if (ra[1] !== rb[1]) return ra[1] < rb[1] ? -1 : 1;
    return parseInt(ra[2] || "0", 10) - parseInt(rb[2] || "0", 10);
  }

  // ---- icons and line ends ----
  function keyIcon(x, cy, cls) {
    return '<g class="' + cls + '"><circle cx="' + r1(x + 3.4) + '" cy="' + r1(cy) + '" r="3.1"/><circle class="hole" cx="' + r1(x + 3.4) + '" cy="' + r1(cy) + '" r="1.1"/>' +
      '<path class="shaft" d="M' + r1(x + 6) + ',' + r1(cy) + ' H' + r1(x + 12.5) + ' M' + r1(x + 10.4) + ',' + r1(cy) + ' V' + r1(cy + 3) + ' M' + r1(x + 12.5) + ',' + r1(cy) + ' V' + r1(cy + 2.4) + '"/></g>';
  }
  function icon(fl, x, cy) {
    var P = fl.indexOf("P") >= 0, F = fl.indexOf("F") >= 0;
    if (P && F) return keyIcon(x, cy, "ic-pk") + '<circle class="ic-fkdot" cx="' + r1(x + 11) + '" cy="' + r1(cy - 4) + '" r="2.6"/>';
    if (P) return keyIcon(x, cy, "ic-pk");
    if (F) return keyIcon(x, cy, "ic-fk");
    if (fl.indexOf("U") >= 0) return '<rect class="ic-uk" x="' + r1(x + 1) + '" y="' + r1(cy - 5) + '" width="10" height="10" rx="2"/><text class="ic-ukt" x="' + r1(x + 6) + '" y="' + r1(cy + 3.2) + '" text-anchor="middle">U</text>';
    if (fl.indexOf("D") >= 0) return '<path class="ic-der" d="M' + r1(x + 7) + ',' + r1(cy - 5.5) + ' L' + r1(x + 2.5) + ',' + r1(cy + 0.8) + ' L' + r1(x + 5.6) + ',' + r1(cy + 0.8) + ' L' + r1(x + 4.6) + ',' + r1(cy + 5.5) + ' L' + r1(x + 9.6) + ',' + r1(cy - 1.2) + ' L' + r1(x + 6.5) + ',' + r1(cy - 1.2) + ' Z"/>';
    if (fl.indexOf("I") >= 0) return '<g class="ic-ix"><rect x="' + r1(x + 1) + '" y="' + r1(cy - 4.4) + '" width="10" height="2"/><rect x="' + r1(x + 1) + '" y="' + r1(cy - 1) + '" width="7" height="2"/><rect x="' + r1(x + 1) + '" y="' + r1(cy + 2.4) + '" width="4.5" height="2"/></g>';
    return '<rect class="ic-col" x="' + r1(x + 3) + '" y="' + r1(cy - 3) + '" width="6" height="6" rx="1"/>';
  }
  // crow's-foot end at the box edge (x, y); d = +1 when the line leaves to the right; n = lines sharing the row
  function glyph(x, y, d, card, n) {
    var hh = n > 1 ? 3 : 5.5, rr = n > 1 ? 2.4 : 3.6, s = "";
    function bar(o) { s += '<path class="er-glyph" d="M' + r1(x + d * o) + ',' + r1(y - hh) + ' V' + r1(y + hh) + '"/>'; }
    function circ(o) { s += '<circle class="er-circ" cx="' + r1(x + d * o) + '" cy="' + r1(y) + '" r="' + rr + '"/>'; }
    if (card === "1") { bar(6); bar(10); }
    else if (card === "01") { bar(6); circ(13); }
    else {
      s += '<path class="er-glyph" d="M' + r1(x) + ',' + r1(y - hh) + ' L' + r1(x + d * 10) + ',' + r1(y) + ' L' + r1(x) + ',' + r1(y + hh) + '"/>';
      if (card === "1n") bar(14); else circ(17);
    }
    return s;
  }

  function legendHtml(kinds) {
    function sv(w, inner) { return '<svg class="er-lsvg" width="' + w + '" height="16" viewBox="0 0 ' + w + ' 16" aria-hidden="true">' + inner + "</svg>"; }
    var h = '<div class="er-lgroup"><span class="er-lhead">Table kinds</span>';
    Object.keys(kinds).forEach(function (k) {
      h += '<span class="er-li">' + sv(22, '<g class="k-' + k + '"><rect class="er-swatch" x="1" y="2" width="20" height="12" rx="2"/></g>') + esc(kinds[k]) + "</span>";
    });
    h += '<span class="er-li">' + sv(22, '<rect class="er-group-box" x="1" y="2" width="20" height="12" rx="3"/>') + "Module group</span>";
    h += '</div><div class="er-lgroup"><span class="er-lhead">Fields</span>';
    [["P", "Primary key"], ["F", "Foreign key"], ["PF", "Primary and foreign key"], ["U", "Unique"], ["I", "Indexed"], ["D", "Derived, kept in sync"], ["", "Column"]].forEach(function (it) {
      h += '<span class="er-li">' + sv(16, icon(it[0], 1, 8)) + it[1] + "</span>";
    });
    h += '<span class="er-li">' + sv(26, '<rect class="er-tag" x="1" y="1.5" width="24" height="13" rx="3"/><text class="er-tagt" x="13" y="11.2" text-anchor="middle">P2</text>') + "Added or changed in that phase</span>";
    h += '</div><div class="er-lgroup"><span class="er-lhead">Relationships</span>';
    h += '<span class="er-li">' + sv(40, '<path class="er-path" d="M2,8 H38"/>') + "Identifying</span>";
    h += '<span class="er-li">' + sv(40, '<g class="nonid"><path class="er-path" d="M2,8 H38"/></g>') + "Non-identifying</span>";
    [["1", "Exactly one"], ["01", "Zero or one"], ["0n", "Zero or more"], ["1n", "One or more"]].forEach(function (it) {
      h += '<span class="er-li">' + sv(40, '<rect class="er-edge" x="0" y="1" width="3" height="14"/><path class="er-path" d="M3,8 H38"/>' + glyph(3, 8, 1, it[0], 1)) + it[1] + "</span>";
    });
    return h + "</div>";
  }

  // Accepts the documented long keys and the short keys used by earlier pages (k, s, p, ru, sum, f, g).
  function normalize(model) {
    var ents = {};
    Object.keys(model.entities || {}).forEach(function (name) {
      var e = model.entities[name], status = e.status || e.s || null, phase = e.phase || e.p || "";
      if (status === "v2") { status = "future"; phase = phase || "V2"; }
      ents[name] = {
        name: name, kind: e.kind || e.k || "core", status: status, phase: phase,
        alt: e.alt || e.ru || "", summary: e.summary || e.sum || "", badge: e.badge,
        fields: (e.fields || e.f || []).map(function (f) { return [f[0], f[1] || "", f[2] || "", f[3] || "", f[4] || "", f[5] || ""]; })
      };
    });
    var groups = (model.groups || []).map(function (g) {
      return { id: g.id, short: g.short || g.title, title: g.title || g.id, note: g.note || "", at: g.at || g.g || [0, 0], gap: g.gap, cols: g.cols || [] };
    });
    var kinds = {}, k;
    for (k in KINDS) kinds[k] = KINDS[k];
    for (k in (model.kinds || {})) kinds[k] = model.kinds[k];
    return {
      entities: ents, relations: model.relations || [], groups: groups, kinds: kinds,
      altLang: model.altLang || "", sourceLabel: model.sourceLabel || "Source", title: model.title || "Entity-relationship diagram",
      layout: model.layout || {}
    };
  }

  function badgeOf(e) {
    if (e.badge != null) return String(e.badge).toUpperCase();
    switch (e.status) {
      case "changed": return "CHANGED";
      case "new": return ("new " + e.phase).trim().toUpperCase();
      case "future": return (e.phase || "future").toUpperCase();
      case "later": return "NOT PLANNED";
      default: return "";
    }
  }
  function statusText(e, f) {
    if (!e.status) return "";
    if (e.status === "future") return e.phase ? "Planned for " + e.phase : "Planned";
    if (e.status === "later") return "Not planned yet";
    if (e.status === "new") return e.phase ? "New in " + e.phase : "New";
    if (!f) {
      if (e.status === "current") return "Exists today, unchanged";
      var tags = [];
      e.fields.forEach(function (x) { if (x[3] && tags.indexOf(x[3]) < 0) tags.push(x[3]); });
      tags.sort(natural);
      return tags.length ? "Exists today; changes in " + tags.join(", ") : "Exists today; changes planned";
    }
    if (!f[3]) return "Exists today";
    return (f[5] ? "Changes in " : "New in ") + f[3];
  }
  function autoDesc(name) {
    var n = name.toLowerCase().replace(/_/g, "");
    if (n === "id") return "Primary key.";
    if (n === "createdat") return "When the row was created (UTC).";
    if (n === "updatedat") return "When the row last changed (UTC).";
    if (n === "deletedat") return "Soft delete: when set, the row is hidden from normal queries but kept so history stays intact.";
    if (n === "slug") return "URL-friendly name used in page addresses; unique.";
    if (n === "sortorder" || n === "position") return "Display order; lower numbers come first.";
    return "";
  }

  function render(root, rawModel) {
    var M = normalize(rawModel);
    function part(name) { return root.querySelector('[data-erd="' + name + '"]'); }
    var canvas = part("canvas");
    var view = { root: root, model: M, failedRoutes: [], routeMs: 0 };
    var resolveReady;
    view.ready = new Promise(function (res) { resolveReady = res; });
    view.check = function () { return view.ready.then(function () { return measure(view); }); };
    view.fit = function () {}; view.zoomTo = function () {};
    ERDiagram.instances.push(view);
    if (!canvas) { resolveReady(view); throw new Error('ERDiagram: no [data-erd="canvas"] inside the root element'); }
    var legend = part("legend");
    if (legend) legend.innerHTML = legendHtml(M.kinds);
    try { build(root, canvas, M, view, part, resolveReady); }
    catch (err) {
      canvas.textContent = "Diagram failed to draw: " + err.message;
      if (global.console) console.error(err);
      view.error = err.message; resolveReady(view);
    }
    return view;
  }

  function build(root, canvas, M, view, part, resolveReady) {
    var L = M.layout, VGAP = L.rowGap || 30, CGAP = L.colGap || 96, GPAD = L.groupPad || 30, GGAP = L.groupGap || 150, MARGIN = L.margin || 60;
    var CAT = M.entities;

    // ---- tables and relationships ----
    var boxes = {}, list = [], groups = [];
    M.groups.forEach(function (gd) {
      var g = { def: gd, cols: [] };
      gd.cols.forEach(function (col, ci) {
        g.cols.push(col.map(function (nm) {
          var def = CAT[nm];
          if (!def) throw new Error("Unknown table " + nm + " in group " + gd.id);
          if (boxes[nm]) throw new Error("Table " + nm + " is placed twice");
          var b = { name: nm, def: def, g: g, ci: ci };
          b.rows = def.fields.map(function (f) { return { f: f, n: { L: 0, R: 0 } }; });
          b.row = {}; b.rows.forEach(function (rw) { b.row[rw.f[0]] = rw; });
          boxes[nm] = b; list.push(b); return b;
        }));
      });
      groups.push(g);
    });
    var missing = Object.keys(CAT).filter(function (n) { return !boxes[n]; });
    if (missing.length) throw new Error("Tables not placed in any group: " + missing.join(", "));
    var rels = M.relations.map(function (r, i) {
      var o = { i: i, c: boxes[r[0]], cf: r[1], p: boxes[r[2]], pf: r[3], pc: r[4] || "1", cc: r[5] || "0n", ident: !!r[6], label: r[7] || "" };
      if (!o.c || !o.p || !o.c.row[o.cf] || !o.p.row[o.pf]) throw new Error("Bad relationship " + r.slice(0, 4).join(" "));
      return o;
    });
    var fkOf = {}, refsTo = {};
    rels.forEach(function (r) { fkOf[r.c.name + "." + r.cf] = r; (refsTo[r.p.name + "." + r.pf] = refsTo[r.p.name + "." + r.pf] || []).push(r); });
    var hasStatus = list.some(function (b) { return !!b.def.status; });

    // ---- sizes: every table in a group column shares the column's width ----
    list.forEach(function (b) {
      var nMax = 0, tMax = 0, tag = false;
      b.rows.forEach(function (rw) { nMax = Math.max(nMax, rw.f[0].length); tMax = Math.max(tMax, rw.f[1].length); if (rw.f[3]) tag = true; });
      b.badge = badgeOf(b.def);
      var rowW = 8 + 18 + nMax * 6.7 + 16 + tMax * 6.1 + (tag ? 30 : 0) + 8;
      var headW = 10 + b.name.length * 7.6 + (b.badge ? 16 + b.badge.length * 6.2 : 0) + 10;
      b.minW = Math.ceil(Math.max(rowW, headW, 160));
    });
    groups.forEach(function (g) {
      g.colW = g.cols.map(function (col) { return Math.max.apply(null, col.map(function (b) { return b.minW; })); });
      g.cols.forEach(function (col, ci) { col.forEach(function (b) { b.w = g.colW[ci]; }); });
    });
    var nGX = 1, nGY = 1;
    groups.forEach(function (g) { nGX = Math.max(nGX, g.def.at[0] + 1); nGY = Math.max(nGY, g.def.at[1] + 1); });

    var W = 0, H = 0;
    function layout() {
      list.forEach(function (b) {
        b.h = HEAD + 4;
        b.rows.forEach(function (rw) { var k = Math.max(rw.n.L, rw.n.R); rw.h = Math.max(ROW, k * 7 + 4); b.h += rw.h; });
      });
      groups.forEach(function (g) {
        var x = 0, hMax = 0, gap = g.def.gap || CGAP;
        g.cols.forEach(function (col, ci) {
          var y = 0;
          col.forEach(function (b) { b.lx = x; b.ly = y; y += b.h + VGAP; });
          hMax = Math.max(hMax, y - VGAP);
          x += g.colW[ci] + gap;
        });
        g.w = Math.max(GPAD * 2 + x - gap, 360);
        g.h = GHEAD + hMax + GPAD;
      });
      var colW = [], rowH = [], i;
      for (i = 0; i < nGX; i++) colW.push(0);
      for (i = 0; i < nGY; i++) rowH.push(0);
      groups.forEach(function (g) { colW[g.def.at[0]] = Math.max(colW[g.def.at[0]], g.w); rowH[g.def.at[1]] = Math.max(rowH[g.def.at[1]], g.h); });
      var gx = [MARGIN], gy = [MARGIN];
      for (i = 1; i < nGX; i++) gx[i] = gx[i - 1] + colW[i - 1] + GGAP;
      for (i = 1; i < nGY; i++) gy[i] = gy[i - 1] + rowH[i - 1] + GGAP;
      W = gx[nGX - 1] + colW[nGX - 1] + MARGIN; H = gy[nGY - 1] + rowH[nGY - 1] + MARGIN;
      groups.forEach(function (g) {
        g.x = Math.round(gx[g.def.at[0]] + (colW[g.def.at[0]] - g.w) / 2); g.y = gy[g.def.at[1]];
        g.cols.forEach(function (col) {
          col.forEach(function (b) {
            b.x = g.x + GPAD + b.lx; b.y = g.y + GHEAD + b.ly;
            var yy = b.y + HEAD; b.rows.forEach(function (rw) { rw.y = yy; rw.cy = yy + rw.h / 2; yy += rw.h; });
          });
        });
      });
    }
    function decideSides() {
      list.forEach(function (b) { b.rows.forEach(function (rw) { rw.n.L = 0; rw.n.R = 0; }); });
      rels.forEach(function (r) {
        var c = r.c, p = r.p;
        if (c === p) { r.cs = "R"; r.ps = "R"; }
        else if (p.x >= c.x + c.w + 20) { r.cs = "R"; r.ps = "L"; }
        else if (p.x + p.w + 20 <= c.x) { r.cs = "L"; r.ps = "R"; }
        else { var s = (p.x + p.w / 2) >= (c.x + c.w / 2) ? "R" : "L"; r.cs = s; r.ps = s; }
        c.row[r.cf].n[r.cs]++; p.row[r.pf].n[r.ps]++;
      });
    }
    layout(); decideSides(); layout(); decideSides(); layout();

    // lines sharing a row and side fan out, ordered by where they come from
    var ports = {};
    rels.forEach(function (r) {
      var kc = r.c.name + "|" + r.cf + "|" + r.cs, kp = r.p.name + "|" + r.pf + "|" + r.ps;
      (ports[kc] = ports[kc] || []).push({ r: r, end: "c" });
      (ports[kp] = ports[kp] || []).push({ r: r, end: "p" });
    });
    Object.keys(ports).forEach(function (k) {
      var g = ports[k];
      g.forEach(function (e) { e.o = e.end === "c" ? e.r.p.row[e.r.pf].cy : e.r.c.row[e.r.cf].cy; });
      g.sort(function (a, b) { return a.o - b.o; });
      g.forEach(function (e, i) {
        var rw = e.end === "c" ? e.r.c.row[e.r.cf] : e.r.p.row[e.r.pf];
        var sp = g.length > 1 ? Math.min(7, (rw.h - 6) / (g.length - 1)) : 0;
        var y = rw.cy + (i - (g.length - 1) / 2) * sp;
        if (e.end === "c") { e.r.cy = y; e.r.cn = g.length; } else { e.r.py = y; e.r.pn = g.length; }
      });
    });

    // ---- hover cards ----
    function sourceLabel(name) { return esc(M.sourceLabel.replace(/\{entity\}/g, name)).replace(/`([^`]+)`/g, "<code>$1</code>"); }
    function tipHtml(key) {
      var a = key.split("|");
      if (a[0] === "e") {
        var b = boxes[a[1]], d = b.def, refs = 0, st = statusText(d);
        rels.forEach(function (r) { if (r.p === b && r.c !== b) refs++; });
        return (d.alt ? '<div class="tip-alt"' + (M.altLang ? ' lang="' + esc(M.altLang) + '"' : "") + ">" + esc(d.alt) + "</div>" : "") +
          '<div class="tip-head"><span class="tip-name">' + esc(b.name) + '</span><span class="tip-kind"><span class="kind-sw k-' + esc(d.kind) + '"></span>' + esc(M.kinds[d.kind] || d.kind) + "</span></div>" +
          (st ? '<div class="tip-chips"><span class="tip-chip ph">' + esc(st) + "</span></div>" : "") +
          (d.summary ? '<p class="tip-desc">' + esc(d.summary) + "</p>" : "") +
          '<div class="tip-meta">' + esc(b.g.def.title) + " · " + d.fields.length + " fields" + (refs ? " · referenced by " + refs + " field" + (refs > 1 ? "s" : "") : "") + "</div>";
      }
      if (a[0] === "f") {
        var bx = boxes[a[1]], f = bx.row[a.slice(2).join("|")].f, fl = f[2], chips = "";
        if (fl.indexOf("P") >= 0) chips += '<span class="tip-chip pk">Primary key</span>';
        var fk = fkOf[bx.name + "." + f[0]];
        if (fk) chips += '<span class="tip-chip fk">Foreign key → ' + esc(fk.p.name + "." + fk.pf) + "</span>";
        if (fl.indexOf("U") >= 0) chips += '<span class="tip-chip">Unique</span>';
        if (fl.indexOf("I") >= 0) chips += '<span class="tip-chip">Indexed</span>';
        if (fl.indexOf("D") >= 0) chips += '<span class="tip-chip">Derived, kept in sync</span>';
        var st2 = statusText(bx.def, f);
        if (st2) chips += '<span class="tip-chip ph">' + esc(st2) + "</span>";
        var out = '<div class="tip-head"><span class="tip-name mono">' + esc(bx.name + "." + f[0]) + '</span><span class="tip-type">' + esc(f[1]) + "</span></div>" +
          (chips ? '<div class="tip-chips">' + chips + "</div>" : "");
        var desc = f[4] || autoDesc(f[0]);
        if (desc) out += '<p class="tip-desc">' + esc(desc) + "</p>";
        if (f[5]) out += '<div class="tip-code">' + sourceLabel(bx.name) + ": “" + esc(f[5]) + "”</div>";
        var inc = refsTo[bx.name + "." + f[0]];
        if (inc && inc.length) {
          var names = inc.map(function (r) { return r.c.name + "." + r.cf; });
          out += '<div class="tip-meta">Referenced by ' + names.length + ": " + esc(names.slice(0, 8).join(", ")) + (names.length > 8 ? " and " + (names.length - 8) + " more" : "") + "</div>";
        }
        return out;
      }
      var r = rels[+a[1]];
      return '<div class="tip-head"><span class="tip-name mono">' + esc(r.c.name + "." + r.cf) + " → " + esc(r.p.name + "." + r.pf) + "</span></div>" +
        '<div class="tip-chips"><span class="tip-chip">' + (r.ident ? "Identifying" : "Non-identifying") + "</span>" + (r.label ? '<span class="tip-chip">' + esc(r.label) + "</span>" : "") + "</div>" +
        '<p class="tip-desc">Each ' + esc(r.c.name) + " has " + PCARD[r.pc] + " " + esc(r.p.name) + "; each " + esc(r.p.name) + " has " + CCARD[r.cc] + " " + esc(r.c.name) + ".</p>";
    }

    // ---- drawing ----
    function drawGroup(g) {
      var d = g.def, n = 0, nNew = 0, nCh = 0;
      g.cols.forEach(function (c) { c.forEach(function (b) { n++; if (b.def.status === "new") nNew++; if (b.def.status === "changed") nCh++; }); });
      var counts = n + (n === 1 ? " table" : " tables") + (hasStatus && nCh ? " · " + nCh + " changed" : "") + (hasStatus && nNew ? " · " + nNew + " new" : "");
      return '<g class="er-group"><rect class="er-group-box" x="' + g.x + '" y="' + g.y + '" width="' + g.w + '" height="' + g.h + '" rx="16"/>' +
        '<text class="er-group-title" x="' + (g.x + GPAD) + '" y="' + (g.y + 36) + '">' + esc(d.title) + "</text>" +
        '<text class="er-group-note" x="' + (g.x + GPAD) + '" y="' + (g.y + 58) + '">' + esc(d.note) + "</text>" +
        '<text class="er-group-count" x="' + (g.x + g.w - GPAD) + '" y="' + (g.y + 36) + '" text-anchor="end">' + esc(counts) + "</text></g>";
    }
    function drawBox(b) {
      var x = b.x, y = b.y, w = b.w, s = "";
      s += '<g class="er-ent k-' + esc(b.def.kind) + '" data-table="' + esc(b.name) + '">';
      s += '<rect class="er-fill" x="' + x + '" y="' + y + '" width="' + w + '" height="' + b.h + '" rx="5"/>';
      s += '<g class="er-hd" data-tip="e|' + esc(b.name) + '"><path class="er-head" d="M' + x + ',' + (y + HEAD) + ' V' + (y + 5) + ' Q' + x + ',' + y + ' ' + (x + 5) + ',' + y + ' H' + (x + w - 5) + ' Q' + (x + w) + ',' + y + ' ' + (x + w) + ',' + (y + 5) + ' V' + (y + HEAD) + ' Z"/>';
      s += '<text class="er-name" x="' + (x + 10) + '" y="' + (y + 18.5) + '">' + esc(b.name) + "</text>";
      if (b.badge) s += '<text class="er-badge" x="' + (x + w - 10) + '" y="' + (y + 18) + '" text-anchor="end">' + esc(b.badge) + "</text>";
      s += "</g>";
      s += '<line class="er-sep" x1="' + x + '" x2="' + (x + w) + '" y1="' + (y + HEAD) + '" y2="' + (y + HEAD) + '"/>';
      var lastPk = -1;
      b.rows.forEach(function (rw, i) { if (rw.f[2].indexOf("P") >= 0) lastPk = i; });
      b.rows.forEach(function (rw, i) {
        var f = rw.f, fl = f[2], cy = rw.cy, right = x + w - 9;
        s += '<g class="er-row" data-tip="f|' + esc(b.name) + "|" + esc(f[0]) + '">';
        s += '<rect class="er-rowbg" x="' + (x + 1) + '" y="' + r1(rw.y) + '" width="' + (w - 2) + '" height="' + rw.h + '"/>';
        s += icon(fl, x + 9, cy);
        s += '<text class="er-field' + (fl.indexOf("P") >= 0 ? " pk" : "") + (fl.indexOf("D") >= 0 ? " derived" : "") + '" x="' + (x + 27) + '" y="' + r1(cy + 3.8) + '">' + esc(f[0]) + "</text>";
        if (f[3]) {
          s += '<rect class="er-tag" x="' + (right - 24) + '" y="' + r1(cy - 6.5) + '" width="24" height="13" rx="3"/><text class="er-tagt" x="' + (right - 12) + '" y="' + r1(cy + 3.2) + '" text-anchor="middle">' + esc(f[3]) + "</text>";
          right -= 30;
        }
        s += '<text class="er-type" x="' + right + '" y="' + r1(cy + 3.5) + '" text-anchor="end">' + esc(f[1]) + "</text></g>";
        if (i === lastPk && i < b.rows.length - 1) { var ly = r1(rw.y + rw.h); s += '<line class="er-sep" x1="' + x + '" x2="' + (x + w) + '" y1="' + ly + '" y2="' + ly + '"/>'; }
      });
      s += '<rect class="er-outline" x="' + x + '" y="' + y + '" width="' + w + '" height="' + b.h + '" rx="5"/></g>';
      return s;
    }

    var parts = [];
    groups.forEach(function (g) { parts.push(drawGroup(g)); });
    list.forEach(function (b) { parts.push(drawBox(b)); });
    canvas.innerHTML = '<svg class="erd-svg" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="' + esc(M.title + ": " + list.length + " tables grouped into " + groups.length + " modules") + '"><g class="erd-world">' +
      parts.join("") + '<g class="erd-lines"></g></g></svg><div class="er-tip" hidden></div><div class="erd-status">Drawing ' + rels.length + " relationships…</div>";
    var world = canvas.querySelector(".erd-world"), linesG = canvas.querySelector(".erd-lines");
    var tip = canvas.querySelector(".er-tip"), status = canvas.querySelector(".erd-status");
    var scaleLabel = part("scale"), fig = part("figure") || root;

    // ---- zoom and pan ----
    var s = 1, tx = 0, ty = 0, touched = false, MINS = 0.05, MAXS = 3;
    function clampS(v) { return Math.max(MINS, Math.min(MAXS, v)); }
    function apply() { world.setAttribute("transform", "translate(" + r1(tx) + "," + r1(ty) + ") scale(" + s.toFixed(4) + ")"); if (scaleLabel) scaleLabel.textContent = Math.round(s * 100) + "%"; }
    function fitRect(x, y, w, h, maxS) {
      var cw = canvas.clientWidth || 800, ch = canvas.clientHeight || 600;
      s = clampS(Math.min(cw / w, ch / h) * 0.94); if (maxS) s = Math.min(s, maxS);
      tx = (cw - w * s) / 2 - x * s; ty = (ch - h * s) / 2 - y * s; apply();
    }
    function fitAll() { fitRect(0, 0, W, H); }
    function zoomAt(f, px, py) { var ns = clampS(s * f); tx = px - (px - tx) * (ns / s); ty = py - (py - ty) * (ns / s); s = ns; apply(); }
    function local(e) { var rc = canvas.getBoundingClientRect(); return { x: e.clientX - rc.left, y: e.clientY - rc.top }; }
    fitAll();
    if (global.ResizeObserver) new ResizeObserver(function () { if (!touched) fitAll(); }).observe(canvas);
    view.fit = function () { touched = false; fitAll(); };
    view.zoomTo = function (name) {
      var b = boxes[name]; if (!b) return false;
      touched = true; fitRect(b.x - 160, b.y - 80, b.w + 320, b.h + 160, 1.5);
      var el = canvas.querySelector('[data-table="' + name + '"]');
      if (el) { el.classList.add("er-flash"); setTimeout(function () { el.classList.remove("er-flash"); }, 1800); }
      return true;
    };

    canvas.addEventListener("wheel", function (e) {
      if (!(e.ctrlKey || e.metaKey)) return;
      e.preventDefault(); touched = true;
      var p = local(e); zoomAt(Math.exp(-e.deltaY * 0.0022), p.x, p.y);
    }, { passive: false });
    canvas.addEventListener("dblclick", function (e) { touched = true; var p = local(e); zoomAt(1.6, p.x, p.y); });
    var pointers = new Map(), moved = false, pinch = null;
    function pinchInfo() { var pts = Array.from(pointers.values()), rc = canvas.getBoundingClientRect(); return { d: Math.hypot(pts[0].x - pts[1].x, pts[0].y - pts[1].y) || 1, x: (pts[0].x + pts[1].x) / 2 - rc.left, y: (pts[0].y + pts[1].y) / 2 - rc.top }; }
    canvas.addEventListener("pointerdown", function (e) {
      if (e.pointerType === "mouse" && e.button !== 0) return;
      try { canvas.setPointerCapture(e.pointerId); } catch (err) { /* ignore */ }
      pointers.set(e.pointerId, { x: e.clientX, y: e.clientY });
      if (pointers.size === 1) moved = false;
      if (pointers.size === 2) pinch = pinchInfo();
    });
    canvas.addEventListener("pointermove", function (e) {
      var p = pointers.get(e.pointerId);
      if (!p) { hover(e); return; }
      if (pointers.size === 1) {
        var dx = e.clientX - p.x, dy = e.clientY - p.y;
        if (!moved && Math.abs(dx) + Math.abs(dy) > 3) { moved = true; touched = true; canvas.classList.add("dragging"); hideTip(); }
        if (moved) { tx += dx; ty += dy; apply(); }
      }
      p.x = e.clientX; p.y = e.clientY;
      if (pointers.size === 2) {
        var now = pinchInfo();
        if (pinch) { zoomAt(now.d / pinch.d, now.x, now.y); tx += now.x - pinch.x; ty += now.y - pinch.y; apply(); }
        pinch = now; moved = true; touched = true;
      }
    });
    function endPointer(e) {
      var had = pointers.delete(e.pointerId);
      if (pointers.size < 2) pinch = null;
      if (!pointers.size) { canvas.classList.remove("dragging"); if (had && !moved && e.type === "pointerup") tapAt(e); }
    }
    canvas.addEventListener("pointerup", endPointer);
    canvas.addEventListener("pointercancel", endPointer);
    canvas.addEventListener("pointerleave", function () { if (!pointers.size) hideTip(); });
    canvas.addEventListener("keydown", function (e) {
      var k = e.key, c = { x: canvas.clientWidth / 2, y: canvas.clientHeight / 2 };
      if (k === "+" || k === "=") zoomAt(1.25, c.x, c.y);
      else if (k === "-" || k === "_") zoomAt(0.8, c.x, c.y);
      else if (k === "0") fitAll();
      else if (k === "ArrowLeft") { tx += 80; apply(); }
      else if (k === "ArrowRight") { tx -= 80; apply(); }
      else if (k === "ArrowUp") { ty += 80; apply(); }
      else if (k === "ArrowDown") { ty -= 80; apply(); }
      else return;
      touched = true; e.preventDefault();
    });
    Array.prototype.forEach.call(root.querySelectorAll("[data-z]"), function (btn) {
      btn.addEventListener("click", function () {
        var z = btn.getAttribute("data-z"), c = { x: canvas.clientWidth / 2, y: canvas.clientHeight / 2 };
        touched = true;
        if (z === "in") zoomAt(1.4, c.x, c.y);
        else if (z === "out") zoomAt(1 / 1.4, c.x, c.y);
        else if (z === "fit") fitAll();
        else if (z === "one") zoomAt(1 / s, c.x, c.y);
        else if (z === "full") {
          var req = fig.requestFullscreen || fig.webkitRequestFullscreen;
          if (document.fullscreenElement) document.exitFullscreen().catch(function () {});
          else if (req) { try { var pr = req.call(fig); if (pr && pr.catch) pr.catch(function () {}); } catch (err) { /* not allowed here */ } }
        }
      });
    });
    document.addEventListener("fullscreenchange", function () { setTimeout(fitAll, 60); });
    var jump = part("jump");
    if (jump) {
      jump.innerHTML = "";
      groups.forEach(function (g) {
        var bt = document.createElement("button"); bt.type = "button"; bt.className = "erd-btn"; bt.textContent = g.def.short;
        bt.addEventListener("click", function () { touched = true; fitRect(g.x - 20, g.y - 20, g.w + 40, g.h + 40, 1.4); });
        jump.appendChild(bt);
      });
    }
    var find = part("find");
    if (find) {
      list.map(function (b) { return b.name; }).sort().forEach(function (n) {
        var o = document.createElement("option"); o.value = n; o.textContent = CAT[n].alt ? n + " — " + CAT[n].alt : n; find.appendChild(o);
      });
      find.addEventListener("change", function () { view.zoomTo(find.value); });
    }

    var curTip = null;
    function hideTip() { tip.hidden = true; curTip = null; }
    function placeTip(cx, cy) {
      var cw = canvas.clientWidth, ch = canvas.clientHeight, tw = tip.offsetWidth, th = tip.offsetHeight;
      var x = cx + 16, y = cy + 16;
      if (x + tw > cw - 8) x = Math.max(8, cx - tw - 16);
      if (y + th > ch - 8) y = Math.max(8, cy - th - 16);
      tip.style.left = x + "px"; tip.style.top = y + "px";
    }
    function showFor(el, p) {
      var key = el.getAttribute("data-tip");
      if (key !== curTip) { curTip = key; tip.innerHTML = tipHtml(key); tip.hidden = false; }
      placeTip(p.x, p.y);
    }
    function hover(e) {
      var el = e.target && e.target.closest ? e.target.closest("[data-tip]") : null;
      if (!el) { hideTip(); return; }
      showFor(el, local(e));
    }
    function tapAt(e) {
      var hit = document.elementFromPoint(e.clientX, e.clientY);
      var el = hit && hit.closest ? hit.closest("[data-tip]") : null;
      if (el && canvas.contains(el)) showFor(el, local(e)); else hideTip();
    }

    // ---- orthogonal routing: A* on an 8 px grid with bend, proximity and overlap costs ----
    var GW = Math.ceil(W / S) + 2, GH = Math.ceil(H / S) + 2, N = GW * GH;
    var blocked = new Uint8Array(N), near = new Uint8Array(N), occH = new Uint16Array(N), occV = new Uint16Array(N);
    function mark(arr, x0, y0, x1, y1) {
      var a = Math.max(0, Math.floor(x0 / S)), b = Math.min(GW - 1, Math.ceil(x1 / S)), c = Math.max(0, Math.floor(y0 / S)), d = Math.min(GH - 1, Math.ceil(y1 / S));
      for (var gy = c; gy <= d; gy++) for (var gx = a; gx <= b; gx++) arr[gy * GW + gx] = 1;
    }
    list.forEach(function (b) { mark(blocked, b.x - 6, b.y - 6, b.x + b.w + 6, b.y + b.h + 6); mark(near, b.x - 16, b.y - 16, b.x + b.w + 16, b.y + b.h + 16); });
    groups.forEach(function (g) { mark(blocked, g.x + 10, g.y + 10, g.x + g.w - 10, g.y + GHEAD - 12); });
    var gScore = new Float32Array(N * 4), seen = new Uint32Array(N * 4), closed = new Uint32Array(N * 4), from = new Int32Array(N * 4), stamp = 0;
    var hF = new Float64Array(1 << 15), hS = new Int32Array(1 << 15), hN = 0;
    function hpush(f, st) {
      if (hN >= hF.length) { var nf = new Float64Array(hF.length * 2), ns = new Int32Array(hF.length * 2); nf.set(hF); ns.set(hS); hF = nf; hS = ns; }
      var i = hN++;
      while (i > 0) { var pi = (i - 1) >> 1; if (hF[pi] <= f) break; hF[i] = hF[pi]; hS[i] = hS[pi]; i = pi; }
      hF[i] = f; hS[i] = st;
    }
    function hpop() {
      var top = hS[0]; hN--;
      if (hN > 0) {
        var f = hF[hN], st = hS[hN], i = 0;
        while (true) { var l = 2 * i + 1; if (l >= hN) break; var m = (l + 1 < hN && hF[l + 1] < hF[l]) ? l + 1 : l; if (hF[m] >= f) break; hF[i] = hF[m]; hS[i] = hS[m]; i = m; }
        hF[i] = f; hS[i] = st;
      }
      return top;
    }
    var DX = [1, -1, 0, 0], DY = [0, 0, 1, -1], BEND = 6;
    // directions: 0 right, 1 left, 2 down, 3 up; sdir = way out of the start, tin = way into the target box
    function astar(sx, sy, sdir, tgx, tgy, tin) {
      stamp++; hN = 0;
      var sCell = sy * GW + sx, tCell = tgy * GW + tgx, st0 = sCell * 4 + sdir;
      gScore[st0] = 0; seen[st0] = stamp; from[st0] = -1;
      hpush(Math.abs(sx - tgx) + Math.abs(sy - tgy), st0);
      var expanded = 0;
      while (hN) {
        var st = hpop();
        if (closed[st] === stamp) continue;
        closed[st] = stamp;
        var cell = st >> 2, dir = st & 3;
        if (cell === tCell) return st;
        if (++expanded > 2500000) return -1;
        var cx = cell % GW, cy = (cell - cx) / GW, g0 = gScore[st];
        for (var nd = 0; nd < 4; nd++) {
          if (nd === (dir ^ 1)) continue;
          var nx = cx + DX[nd], ny = cy + DY[nd];
          if (nx < 0 || ny < 0 || nx >= GW || ny >= GH) continue;
          var nc = ny * GW + nx;
          if (nc === tCell) { if (nd === (tin ^ 1)) continue; }
          else if (blocked[nc]) continue;
          var cost = 1 + (nd !== dir ? BEND : 0) + (near[nc] ? 0.5 : 0);
          cost += nd < 2 ? occH[nc] * 30 + occV[nc] * 1.5 : occV[nc] * 30 + occH[nc] * 1.5;
          if (nc === tCell && nd !== tin) cost += BEND;
          var ns2 = nc * 4 + nd, ng = g0 + cost;
          if (seen[ns2] !== stamp || ng < gScore[ns2]) { seen[ns2] = stamp; gScore[ns2] = ng; from[ns2] = st; hpush(ng + 1.1 * (Math.abs(nx - tgx) + Math.abs(ny - tgy)), ns2); }
        }
      }
      return -1;
    }
    function endInfo(b, side, y) {
      var edge = side === "R" ? b.x + b.w : b.x;
      var gx = side === "R" ? Math.ceil((edge + STUB) / S) : Math.floor((edge - STUB) / S);
      return { edge: edge, gx: gx, gy: Math.round(y / S), out: side === "R" ? 0 : 1 };
    }
    function routeRel(r) {
      var A = endInfo(r.c, r.cs, r.cy), B = endInfo(r.p, r.ps, r.py);
      var res = astar(A.gx, A.gy, A.out, B.gx, B.gy, r.ps === "R" ? 1 : 0), cells = [], pts;
      if (res >= 0) { var st = res; while (st >= 0) { cells.push(st >> 2); st = from[st]; } cells.reverse(); }
      if (cells.length) {
        pts = [];
        for (var i = 0; i < cells.length; i++) {
          var c = cells[i], x = (c % GW) * S, y = ((c - (c % GW)) / GW) * S;
          if (i > 0) { var pc = cells[i - 1]; if (Math.abs(c - pc) === 1) { occH[c]++; occH[pc]++; } else { occV[c]++; occV[pc]++; } }
          if (pts.length >= 2) {
            var a = pts[pts.length - 2], b2 = pts[pts.length - 1];
            if ((a[0] === b2[0] && b2[0] === x) || (a[1] === b2[1] && b2[1] === y)) { b2[0] = x; b2[1] = y; continue; }
          }
          pts.push([x, y]);
        }
        // keep the first and last runs at the exact row height so each line meets its field squarely
        var gy0 = pts[0][1];
        pts[0][1] = r.cy; if (pts.length > 1 && pts[1][1] === gy0) pts[1][1] = r.cy;
        var L2 = pts.length - 1, gy1 = pts[L2][1];
        pts[L2][1] = r.py; if (L2 > 0 && pts[L2 - 1][1] === gy1 && !(L2 - 1 === 0 && pts.length === 2)) pts[L2 - 1][1] = r.py;
      } else {
        view.failedRoutes.push(r.c.name + "." + r.cf + " → " + r.p.name + "." + r.pf);
        var mx = (A.gx + B.gx) / 2 * S;
        pts = [[A.gx * S, r.cy], [mx, r.cy], [mx, r.py], [B.gx * S, r.py]];
      }
      pts.unshift([A.edge, r.cy]); pts.push([B.edge, r.py]);
      // a straight run whose ends sit at slightly different heights gets a small square jog instead of a slant
      for (var q = 0; q < pts.length - 1; q++) {
        var u = pts[q], v = pts[q + 1];
        if (Math.abs(u[0] - v[0]) > 0.01 && Math.abs(u[1] - v[1]) > 0.01) {
          var jx = q === 0 ? v[0] : (q === pts.length - 2 ? u[0] : Math.round((u[0] + v[0]) / 2));
          pts.splice(q + 1, 0, [jx, u[1]], [jx, v[1]]);
          q += 2;
        }
      }
      var clean = [];
      pts.forEach(function (p) {
        if (clean.length && Math.abs(clean[clean.length - 1][0] - p[0]) < 0.01 && Math.abs(clean[clean.length - 1][1] - p[1]) < 0.01) return;
        if (clean.length >= 2) {
          var a2 = clean[clean.length - 2], b3 = clean[clean.length - 1];
          if ((Math.abs(a2[0] - b3[0]) < 0.01 && Math.abs(b3[0] - p[0]) < 0.01) || (Math.abs(a2[1] - b3[1]) < 0.01 && Math.abs(b3[1] - p[1]) < 0.01)) { b3[0] = p[0]; b3[1] = p[1]; return; }
        }
        clean.push([p[0], p[1]]);
      });
      r.pts = clean;
    }
    function drawRel(r) {
      var d = "M" + r.pts.map(function (p) { return r1(p[0]) + "," + r1(p[1]); }).join(" L");
      var ce = r.cs === "R" ? r.c.x + r.c.w : r.c.x, pe = r.ps === "R" ? r.p.x + r.p.w : r.p.x;
      return '<g class="er-rel' + (r.ident ? "" : " nonid") + '" data-tip="r|' + r.i + '"><path class="er-hit" d="' + d + '"/><path class="er-path" d="' + d + '"/>' +
        glyph(ce, r.cy, r.cs === "R" ? 1 : -1, r.cc, r.cn) + glyph(pe, r.py, r.ps === "R" ? 1 : -1, r.pc, r.pn) + "</g>";
    }

    view.geometry = { W: W, H: H, groups: groups, boxes: boxes, rels: rels };
    rels.forEach(function (r) { var A = endInfo(r.c, r.cs, r.cy), B = endInfo(r.p, r.ps, r.py); r.est = Math.abs(A.gx - B.gx) + Math.abs(A.gy - B.gy); });
    var order = rels.slice().sort(function (a, b) { return a.est - b.est; }), k = 0, started = Date.now();
    function step() {
      var t0 = Date.now();
      try { while (k < order.length && Date.now() - t0 < 40) routeRel(order[k++]); }
      catch (err) { status.textContent = "Some lines could not be drawn: " + err.message; view.error = err.message; if (global.console) console.error(err); resolveReady(view); return; }
      if (k < order.length) { status.textContent = "Drawing relationships… " + k + " of " + order.length; setTimeout(step, 0); return; }
      linesG.innerHTML = rels.map(drawRel).join("");
      status.remove();
      view.routeMs = Date.now() - started;
      resolveReady(view);
      try { root.dispatchEvent(new CustomEvent("erd:ready", { detail: view })); } catch (err) { /* old browsers */ }
    }
    setTimeout(step, 0);
  }

  // Layout quality: what to fix before shipping. Every number except tables/lines/avgBends/routeMs should be 0.
  function measure(view) {
    var G = view.geometry;
    if (!G) return { error: view.error || "not drawn" };
    var boxes = Object.keys(G.boxes).map(function (n) { return G.boxes[n]; });
    var segs = [], diag = 0, through = [], heads = 0, bends = 0;
    G.rels.forEach(function (r) {
      var pts = r.pts || [];
      bends += Math.max(0, pts.length - 2);
      for (var k = 0; k < pts.length - 1; k++) {
        var x1 = pts[k][0], y1 = pts[k][1], x2 = pts[k + 1][0], y2 = pts[k + 1][1];
        if (Math.abs(x1 - x2) > 0.05 && Math.abs(y1 - y2) > 0.05) diag++;
        segs.push({ r: r, x1: x1, y1: y1, x2: x2, y2: y2 });
        boxes.forEach(function (b) {
          if (Math.min(x1, x2) < b.x + b.w - 0.5 && Math.max(x1, x2) > b.x + 0.5 && Math.min(y1, y2) < b.y + b.h - 0.5 && Math.max(y1, y2) > b.y + 0.5) through.push(r.c.name + "." + r.cf + " through " + b.name);
        });
        G.groups.forEach(function (g) {
          if (Math.min(x1, x2) < g.x + g.w - 12 && Math.max(x1, x2) > g.x + 12 && Math.min(y1, y2) < g.y + GHEAD - 14 && Math.max(y1, y2) > g.y + 12) heads++;
        });
      }
    });
    function groupAt(x, y) {
      for (var i = 0; i < G.groups.length; i++) { var g = G.groups[i]; if (x >= g.x && x <= g.x + g.w && y >= g.y && y <= g.y + g.h) return g.def.id; }
      return "between groups";
    }
    var overlaps = 0, hotspots = {}, examples = [];
    for (var i = 0; i < segs.length; i++) for (var j = i + 1; j < segs.length; j++) {
      var a = segs[i], b = segs[j];
      if (a.r === b.r || (a.r.p === b.r.p && a.r.pf === b.r.pf)) continue;
      var o = 0, mx = 0, my = 0;
      if (a.y1 === a.y2 && b.y1 === b.y2 && Math.abs(a.y1 - b.y1) < 1) {
        var lo = Math.max(Math.min(a.x1, a.x2), Math.min(b.x1, b.x2)), hi = Math.min(Math.max(a.x1, a.x2), Math.max(b.x1, b.x2));
        o = hi - lo; mx = (lo + hi) / 2; my = a.y1;
      } else if (a.x1 === a.x2 && b.x1 === b.x2 && Math.abs(a.x1 - b.x1) < 1) {
        var lo2 = Math.max(Math.min(a.y1, a.y2), Math.min(b.y1, b.y2)), hi2 = Math.min(Math.max(a.y1, a.y2), Math.max(b.y1, b.y2));
        o = hi2 - lo2; mx = a.x1; my = (lo2 + hi2) / 2;
      }
      if (o > 16) {
        overlaps++;
        var where = groupAt(mx, my); hotspots[where] = (hotspots[where] || 0) + 1;
        if (examples.length < 6) examples.push(a.r.c.name + "." + a.r.cf + " / " + b.r.c.name + "." + b.r.cf + " (" + Math.round(o) + " px, " + where + ")");
      }
    }
    return {
      tables: boxes.length, lines: G.rels.length, size: [Math.round(G.W), Math.round(G.H)], routeMs: view.routeMs,
      avgBends: G.rels.length ? +(bends / G.rels.length).toFixed(1) : 0,
      failedRoutes: view.failedRoutes.slice(), throughTables: through.length, throughHeaders: heads, diagonal: diag,
      overlaps: overlaps, overlapHotspots: hotspots, overlapExamples: examples, throughExamples: through.slice(0, 6)
    };
  }

  var ERDiagram = { render: render, instances: [] };
  global.ERDiagram = ERDiagram;
})(window);
