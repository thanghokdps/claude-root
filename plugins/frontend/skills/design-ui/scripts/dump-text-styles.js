// dump-text-styles.js — the computed type style of each selector, for check-text-styles.py.
// Evaluate in the page with the state's selectors and save the result as design/actual/<state>.styles.json:
//   const styles = await page.evaluate(dumpTextStyles, ["h1", "[data-role=answer] p"]);
// A selector that matches nothing is left out, so the check reports it missing.
function dumpTextStyles(selectors) {
  const props = ["font-family", "font-size", "font-weight", "line-height", "letter-spacing", "color"];
  const out = {};
  for (const sel of selectors) {
    const el = document.querySelector(sel);
    if (!el) continue;
    const cs = getComputedStyle(el);
    out[sel] = Object.fromEntries(props.map((p) => [p, cs.getPropertyValue(p)]));
  }
  return out;
}

if (typeof module !== "undefined") module.exports = { dumpTextStyles };
