// The growth explorer in ch02: the horizon sets how many times the annual growth factor is applied.
//
// Inlined into the page by bench/tables.py, beside the markup it drives. Its defaults, the growth
// factor and the horizon, are the model's own point values, read from the stamped result into the
// figure's data attributes; nothing here is a figure the book claims. The starting demand of one
// hundred and the slider bounds are teaching choices, chosen so the arithmetic can be done in the
// head, and the figure says so where the reader sees them.
(() => {
  for (const root of document.querySelectorAll(".explorer.growth")) {
    const d = root.dataset;
    const START = Number(d.start);
    const factor = root.querySelector(".ge-factor");
    const horizon = root.querySelector(".ge-horizon");
    const linear = root.querySelector(".ge-linear");
    const svg = root.querySelector(".ge-chart");
    const NS = "http://www.w3.org/2000/svg";
    const $ = (name) => root.querySelector(`[data-show="${name}"]`);
    const el = (name, attrs, text) => {
      const node = document.createElementNS(NS, name);
      for (const [k, v] of Object.entries(attrs)) node.setAttribute(k, v);
      if (text !== undefined) node.textContent = text;
      return node;
    };
    const whole = (x) => Math.round(x).toLocaleString("en-GB");
    const years = (n) => `${n} year${n === 1 ? "" : "s"}`;

    const draw = () => {
      const g = Number(factor.value);
      const n = Number(horizon.value);
      const f = g.toFixed(2);
      const values = Array.from({ length: n + 1 }, (_, i) => START * g ** i);
      const rise = START * (g - 1);
      const adding = Array.from({ length: n + 1 }, (_, i) => START + i * rise);
      const top = Math.max(...values);
      // Drawn at its real width, so its text stays readable on a phone.
      const W = Math.max(300, Math.round(svg.getBoundingClientRect().width) || 560);
      svg.setAttribute("viewBox", `0 0 ${W} 246`);
      const left = 12;
      const right = W - 8;
      const base = 180;
      const height = 150;
      const slot = (right - left) / (n + 1);
      const bar = Math.min(34, slot * 0.62);
      svg.replaceChildren();
      svg.append(el("line", { class: "axis", x1: left, x2: right, y1: base, y2: base }));
      values.forEach((v, i) => {
        const cx = left + slot * (i + 0.5);
        const h = (v / top) * height;
        svg.append(el("rect", { class: i ? "bar" : "bar start", x: cx - bar / 2, y: base - h,
          width: bar, height: h, rx: 3 }));
        if (slot > 30 || i === n || i === 0) {
          svg.append(el("text", { class: "value", x: cx, y: base - h - 5,
            "text-anchor": "middle" }, whole(v)));
        }
        svg.append(el("text", { class: "year", x: cx, y: base + 14, "text-anchor": "middle" },
          i ? (slot > 44 ? `Year ${i}` : `${i}`) : (slot > 44 ? "Today" : "0")));
        if (!i) return;
        if (linear.open) {
          const ay = base - (adding[i] / top) * height;
          svg.append(el("line", { class: "adding", x1: cx - bar / 2 - 3, x2: cx + bar / 2 + 3,
            y1: ay, y2: ay }));
        }
        // One chip per application of the factor, under the year it produced.
        const chip = el("g", { class: "step" });
        const w = Math.min(slot - 4, 44);
        chip.append(el("rect", { x: cx - w / 2, y: base + 22, width: w, height: 18, rx: 4 }));
        chip.append(el("text", { x: cx, y: base + 35, "text-anchor": "middle" },
          slot > 40 ? `×${f}` : "×"));
        svg.append(chip);
        // What this year added: it grows, because the factor applies to the grown number.
        if (slot > 40) {
          svg.append(el("text", { class: "rise", x: cx, y: base + 54, "text-anchor": "middle" },
            `+${whole(values[i] - values[i - 1])}`));
        }
      });

      const end = values[n];
      $("factor").textContent = `${f}×`;
      $("horizon").textContent = years(n);
      $("chain-horizon").textContent = years(n);
      $("chain-divide").textContent = `${years(n)} ÷ 1 year`;
      $("chain-count").textContent = n;
      $("chain-power").innerHTML = `${f}<sup>${n}</sup>`;
      $("chain-growth").textContent = `= ×${(g ** n).toFixed(2)}`;
      $("chain-demand").textContent = whole(end);
      $("start").textContent = `from ${whole(START)} today`;
      $("caption").textContent =
        `One ×${f} chip per year: ${n} in all, the same ${n} as the exponent. ` +
        "The figure under each chip is what that year added.";
      $("adding").textContent = `${whole(START)} + ${n} × ${whole(rise)} = ${whole(adding[n])}`;
      $("compounding").innerHTML = `${whole(START)} × ${f}<sup>${n}</sup> = ${whole(end)}`;
    };
    addEventListener("resize", draw);
    factor.addEventListener("input", draw);
    horizon.addEventListener("input", draw);
    linear.addEventListener("toggle", draw);
    draw();
  }
})();
