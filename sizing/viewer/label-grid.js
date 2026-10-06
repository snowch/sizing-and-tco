// The label grid in ch02: one square per series, for one metric on one host.
//
// Inlined into the page by bench/tables.py. Endpoint values run across and status values down;
// each value of an accidental label is one more copy of the whole grid, drawn behind it. The
// counts are teaching choices declared beside LABEL_GRID_ENDPOINT, not figures the book claims.
(() => {
  const ENDPOINTS = ["/login", "/search", "/cart", "/pay", "/account", "/orders", "/help", "/admin"];
  const STATUSES = ["200", "301", "404", "500", "503"];
  for (const root of document.querySelectorAll(".explorer.labels")) {
    const endpoint = root.querySelector(".lg-endpoint");
    const status = root.querySelector(".lg-status");
    const accidental = root.querySelector(".lg-accidental");
    const svg = root.querySelector(".lg-chart");
    const NS = "http://www.w3.org/2000/svg";
    const $ = (name) => root.querySelector(`[data-show="${name}"]`);
    const el = (name, attrs, text) => {
      const node = document.createElementNS(NS, name);
      for (const [k, v] of Object.entries(attrs)) node.setAttribute(k, v);
      if (text !== undefined) node.textContent = text;
      return node;
    };

    const draw = () => {
      const e = Number(endpoint.value);
      const s = Number(status.value);
      const a = Number(accidental.value);
      const W = Math.max(300, Math.round(svg.getBoundingClientRect().width) || 560);
      // Squares sized for the widest grid the sliders allow, so a new value visibly adds a
      // column or a row instead of shrinking every square. The drawing grows to what it holds.
      const AMAX = Number(accidental.max);
      const left = 50;
      const cell = Math.max(16, Math.min(46, (W - left - 16) / (ENDPOINTS.length + 0.45 * (AMAX - 1))));
      const shift = Math.round(cell * 0.45);
      const top = 30 + shift * (a - 1);
      const H = top + s * cell + 8;
      svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
      svg.style.height = `${H}px`;
      svg.replaceChildren();
      // The copies an accidental label makes, back to front, each shifted up and to the right.
      for (let k = a - 1; k >= 0; k--) {
        const dx = left + k * shift;
        const dy = top - k * shift;
        for (let r = 0; r < s; r++) {
          for (let c = 0; c < e; c++) {
            svg.append(el("rect", {
              class: k ? "cell copy" : "cell", x: dx + c * cell + 1, y: dy + r * cell + 1,
              width: cell - 4, height: cell - 4, rx: 3,
            }));
          }
        }
      }
      const base = top;
      for (let c = 0; c < e; c++) {
        svg.append(el("text", {
          class: "axis", x: left + c * cell + cell / 2, y: base - 8 - (a - 1) * shift,
          "text-anchor": "middle",
        }, cell > 34 ? ENDPOINTS[c] : String(c + 1)));
      }
      for (let r = 0; r < s; r++) {
        svg.append(el("text", {
          class: "axis", x: left - 6, y: base + r * cell + cell / 2 + 4, "text-anchor": "end",
        }, STATUSES[r]));
      }
      $("endpoint").textContent = e;
      $("status").textContent = s;
      $("accidental").textContent = a;
      $("sum").textContent =
        `${e} endpoint value${e === 1 ? "" : "s"} × ${s} status value${s === 1 ? "" : "s"} × ` +
        `${a} = ${e * s * a} series`;
    };
    addEventListener("resize", draw);
    for (const control of [endpoint, status, accidental]) control.addEventListener("input", draw);
    draw();
  }
})();
