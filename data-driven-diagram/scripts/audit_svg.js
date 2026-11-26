/* The layout audit of a figure, with the browser's own fonts and text layout: the last word on
   whether text overlaps. One expression that returns JSON, so it runs
     - through figcheck.py audit (headless Chrome or Edge), or
     - in any browser tool or console, on a page that shows the SVG (as the document or inline).
   fatal: overlaps (text on text), off (text leaving the canvas), onimg (text on a picture without
          a halo), lines (a line through text that has no halo)
   to look at: review (text that straddles the edge of a box or a mark), small (font below 9 px) */
(() => {
  const svg = document.querySelector('svg') || document.documentElement;
  const vb = svg.viewBox && svg.viewBox.baseVal && svg.viewBox.baseVal.width ? svg.viewBox.baseVal : {width: svg.getBoundingClientRect().width, height: svg.getBoundingClientRect().height};
  const r0 = svg.getBoundingClientRect();
  const k = vb.width / r0.width;
  const box = el => { const r = el.getBoundingClientRect(); return {x: (r.left - r0.left) * k, y: (r.top - r0.top) * k, w: r.width * k, h: r.height * k}; };
  const cut = s => s.length > 48 ? s.slice(0, 45) + '...' : s;
  const texts = [...svg.querySelectorAll('text')].map(t => Object.assign({t, s: t.textContent, halo: !!t.getAttribute('paint-order'),
    upright: !/rotate\(\s*-?90/.test(t.getAttribute('transform') || ''), size: parseFloat(t.getAttribute('font-size') || getComputedStyle(t).fontSize)}, box(t)));
  for (const b of texts) {            // the ink of the text: the box without the room above capitals and below the baseline
    if (b.upright) { b.x0 = b.x + 0.5; b.x1 = b.x + b.w - 0.5; b.y0 = b.y + 0.22 * b.h; b.y1 = b.y + 0.84 * b.h; }
    else { b.x0 = b.x + 0.2 * b.w; b.x1 = b.x + 0.8 * b.w; b.y0 = b.y + 0.5; b.y1 = b.y + b.h - 0.5; }
  }
  const at = b => [Math.round(b.x), Math.round(b.y)];
  const out = {texts: texts.length, images: 0, width: vb.width, height: vb.height, overlaps: [], off: [], onimg: [], lines: [], review: [], small: []};
  for (let i = 0; i < texts.length; i++) for (let j = i + 1; j < texts.length; j++) {
    const a = texts[i], b = texts[j];
    const ox = Math.min(a.x1, b.x1) - Math.max(a.x0, b.x0), oy = Math.min(a.y1, b.y1) - Math.max(a.y0, b.y0);
    if (ox > 0.5 && oy > 0.5) out.overlaps.push({a: cut(a.s), b: cut(b.s), at: at(a)});
  }
  for (const b of texts) {
    if (b.x < 0 || b.y < 0 || b.x + b.w > vb.width || b.y + b.h > vb.height) out.off.push({text: cut(b.s), at: at(b)});
    if (b.size < 9) out.small.push({text: cut(b.s), size: b.size, at: at(b)});
  }
  const hit = (b, m) => Math.min(b.x1, m.x + m.w) - Math.max(b.x0, m.x) > 0.5 && Math.min(b.y1, m.y + m.h) - Math.max(b.y0, m.y) > 0.5;
  const inside = (b, m) => m.x <= b.x0 + 1 && m.y <= b.y0 + 1 && m.x + m.w >= b.x1 - 1 && m.y + m.h >= b.y1 - 1;
  // pictures: images, and the grounds of pictures drawn with shapes (ddfig: rect(picture=True))
  const images = [...svg.querySelectorAll('image, [data-ddfig="picture"]')].map(box);
  out.images = images.length;
  for (const b of texts) if (!b.halo && images.some(m => hit(b, m))) out.onimg.push({text: cut(b.s), at: at(b)});
  const crosses = (x1, y1, x2, y2, b) => {          // Liang-Barsky
    let t0 = 0, t1 = 1; const dx = x2 - x1, dy = y2 - y1;
    const p = [-dx, dx, -dy, dy], q = [x1 - b.x0, b.x1 - x1, y1 - b.y0, b.y1 - y1];
    for (let i = 0; i < 4; i++) {
      if (p[i] === 0) { if (q[i] < 0) return false; }
      else { const r = q[i] / p[i]; if (p[i] < 0) { if (r > t1) return false; if (r > t0) t0 = r; } else { if (r < t0) return false; if (r < t1) t1 = r; } }
    }
    return t1 - t0 > 0;
  };
  for (const l of svg.querySelectorAll('line')) {
    const m = l.getScreenCTM();
    const P = (x, y) => [(m.a * x + m.c * y + m.e - r0.left) * k, (m.b * x + m.d * y + m.f - r0.top) * k];
    const [x1, y1] = P(+l.getAttribute('x1'), +l.getAttribute('y1')), [x2, y2] = P(+l.getAttribute('x2'), +l.getAttribute('y2'));
    for (const b of texts) if (!b.halo && crosses(x1, y1, x2, y2, b)) out.lines.push({text: cut(b.s), at: at(b)});
  }
  const seen = new Set();
  for (const el of svg.querySelectorAll('rect, circle')) {
    const m = box(el);
    if (m.w >= vb.width - 1 || el.getAttribute('data-ddfig') === 'picture') continue;   // the background; a picture's ground
    for (const b of texts) if (!b.halo && hit(b, m) && !inside(b, m)) {
      const key = b.s + '|' + at(b);
      if (!seen.has(key)) { seen.add(key); out.review.push({text: cut(b.s), at: at(b), shape: el.tagName + ' ' + Math.round(m.w) + 'x' + Math.round(m.h)}); }
    }
  }
  return JSON.stringify(out);
})()
