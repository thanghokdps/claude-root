// dump-ui-styles.js — colour, type, spacing and box of every visible element, for check-ui.py.
// Evaluate in the page in each state and save the result as design/actual/<state>.ui.json:
//   const ui = await page.evaluate(dumpUiStyles);            // or dumpUiStyles("main") for one region
// Colours go through a 1×1 canvas so oklch(), color-mix() and named colours all arrive as sRGB.
function dumpUiStyles(rootSelector) {
  const root = rootSelector ? document.querySelector(rootSelector) : document.body;
  const ctx = Object.assign(document.createElement("canvas"), { width: 1, height: 1 }).getContext("2d", { willReadFrequently: true });
  const INTERACTIVE = 'a[href], button, input:not([type=hidden]), select, textarea, summary, [role=button], [role=link], [role=checkbox], [role=radio], [role=switch], [role=tab], [role=menuitem], [tabindex]:not([tabindex="-1"])';

  const rgba = (c) => {
    ctx.clearRect(0, 0, 1, 1);
    ctx.fillStyle = "#000";
    ctx.fillStyle = c;
    ctx.fillRect(0, 0, 1, 1);
    const [r, g, b, a] = ctx.getImageData(0, 0, 1, 1).data;
    return [r, g, b, +(a / 255).toFixed(3)];
  };
  // The colour behind el: its own and its ancestors' backgrounds composited over the white canvas.
  const background = (el) => {
    const layers = [];
    let image = false;
    for (let n = el; n && n.nodeType === 1; n = n.parentElement) {
      const cs = getComputedStyle(n);
      if (cs.backgroundImage !== "none") image = true;
      const c = rgba(cs.backgroundColor);
      if (c[3] > 0) layers.push(c);
      if (c[3] === 1 || image) break;
    }
    let out = [255, 255, 255];
    for (const [r, g, b, a] of layers.reverse()) out = [r, g, b].map((v, i) => Math.round(v * a + out[i] * (1 - a)));
    return { background: `rgb(${out.join(", ")})`, bgImage: image };
  };
  const selector = (el) => {
    const parts = [];
    for (let n = el; n && n !== document.body && parts.length < 3; n = n.parentElement) {
      if (n.id) { parts.unshift(`#${n.id}`); break; }
      const cls = [...n.classList].slice(0, 2).map((c) => `.${CSS.escape(c)}`).join("");
      parts.unshift(n.tagName.toLowerCase() + cls);
    }
    return parts.join(" > ");
  };
  const px = (v) => (v.endsWith("px") ? parseFloat(v) : null);

  const elements = [];
  for (const el of root.querySelectorAll("*")) {
    const cs = getComputedStyle(el);
    const box = el.getBoundingClientRect();
    if (!box.width || !box.height || cs.visibility !== "visible" || +cs.opacity === 0) continue;
    const text = [...el.childNodes].filter((n) => n.nodeType === 3).map((n) => n.textContent).join(" ").trim();
    const [r, g, b, a] = rgba(cs.color);
    elements.push({
      selector: selector(el),
      tag: el.tagName.toLowerCase(),
      text: text.slice(0, 40),
      interactive: el.matches(INTERACTIVE),
      inline: cs.display === "inline",
      disabled: el.matches(':disabled, [aria-disabled="true"]'),
      color: `rgba(${r}, ${g}, ${b}, ${a})`,
      ...background(el),
      fontSize: parseFloat(cs.fontSize),
      fontWeight: parseInt(cs.fontWeight, 10),
      padding: ["Top", "Right", "Bottom", "Left"].map((s) => parseFloat(cs[`padding${s}`])),
      margin: ["Top", "Right", "Bottom", "Left"].map((s) => parseFloat(cs[`margin${s}`])),
      gap: [px(cs.rowGap), px(cs.columnGap)],
      box: [+box.width.toFixed(1), +box.height.toFixed(1)],
    });
  }
  return { viewport: [innerWidth, innerHeight], elements };
}

if (typeof module !== "undefined") module.exports = { dumpUiStyles };
