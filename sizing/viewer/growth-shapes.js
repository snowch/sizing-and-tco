// The shapes calculator in ch04: compound, linear and levelling growth from the same start.
//
// Inlined into the page by bench/tables.py. Its formulas are not written here: the page carries
// sizing.dsl.GROWTH_SHAPES in a data attribute, and this turns each into a function, so the
// calculator computes what a `grown` node computes. Its defaults are the model's point values or
// teaching choices declared beside GROWTH_SHAPES_CEILING; nothing here is a figure the book claims.
(() => {
  for (const root of document.querySelectorAll(".explorer.shapes")) {
    const START = Number(root.dataset.start);
    const FORMULAS = JSON.parse(root.dataset.shapes);
    const SHAPES = Object.keys(FORMULAS);
    // The loader's formula, with each key's name standing for its value. Keys only, no input
    // from the page reaches it, and `**` is the same operator in both languages.
    const compiled = Object.fromEntries(SHAPES.map((s) => [s,
      new Function("start", "rate", "over", "ceiling", `return ${FORMULAS[s].replace(/[{}]/g, "")};`)]));
    const input = (name) => root.querySelector(`.gs-${name}`);
    const factor = input("factor");
    const amount = input("amount");
    const ceilingIn = input("ceiling");
    const horizon = input("horizon");
    const picks = [...root.querySelectorAll(".gs-pick input")];
    const svg = root.querySelector(".gs-chart");
    const tip = root.querySelector(".gs-tip");
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
    let state = null;

    const read = () => {
      const g = Number(factor.value);
      const a = Number(amount.value);
      const c = Number(ceilingIn.value);
      const n = Number(horizon.value);
      const rate = { compound: g, linear: a, levelling: g };
      const shown = picks.filter((p) => p.checked).map((p) => p.value);
      const series = Object.fromEntries(SHAPES.map((s) => [s,
        Array.from({ length: n + 1 }, (_, i) => compiled[s](START, rate[s], i, c))]));
      return { g, a, c, n, rate, shown, series };
    };

    const draw = () => {
      state = read();
      const { g, a, c, n, rate, shown, series } = state;
      const W = Math.max(300, Math.round(svg.getBoundingClientRect().width) || 560);
      const H = 260;
      svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
      const left = 40;
      // Room on the right for the longest end label this drawing will print.
      const longest = Math.max(...SHAPES.filter((s) => shown.includes(s))
        .map((s) => `${s} ${whole(series[s][n])}`.length), `ceiling ${whole(c)}`.length);
      const right = W - Math.max(96, longest * 8 + 18);
      const top = 14;
      const base = H - 28;
      const visible = shown.flatMap((s) => series[s]);
      if (shown.includes("levelling")) visible.push(c);
      const peak = Math.max(START, ...visible) * 1.06;
      const x = (i) => left + (n ? (i / n) * (right - left) : 0);
      const y = (v) => base - (v / peak) * (base - top);
      svg.replaceChildren();
      // A few round gridlines, so a reader can read a value off the chart.
      const step = 10 ** Math.floor(Math.log10(peak / 4));
      const tick = [1, 2, 5, 10].map((m) => m * step).find((t) => peak / t <= 5);
      for (let v = 0; v <= peak; v += tick) {
        svg.append(el("line", { class: "grid", x1: left, x2: right, y1: y(v), y2: y(v) }));
        svg.append(el("text", { class: "tick", x: left - 6, y: y(v) + 4, "text-anchor": "end" },
          whole(v)));
      }
      for (let i = 0; i <= n; i++) {
        if (n > 6 && i % 2 && i !== n) continue;
        svg.append(el("text", { class: "tick", x: x(i), y: base + 16, "text-anchor": "middle" },
          i ? `${i}` : "today"));
      }
      if (shown.includes("levelling")) {
        svg.append(el("line", { class: "ceiling", x1: left, x2: right, y1: y(c), y2: y(c) }));
      }
      const labels = [];
      for (const s of SHAPES) {
        if (!shown.includes(s)) continue;
        const points = series[s].map((v, i) => `${x(i)},${y(v)}`).join(" ");
        svg.append(el("polyline", { class: `line ${s}`, points }));
        series[s].forEach((v, i) => {
          svg.append(el("circle", { class: `dot ${s}`, cx: x(i), cy: y(v), r: 4 }));
        });
        labels.push({ s, v: series[s][n], at: y(series[s][n]) });
      }
      if (shown.includes("levelling")) labels.push({ s: "ceiling", v: c, at: y(c) });
      // End labels, pushed apart so two lines that finish close together stay readable.
      labels.sort((p, q) => p.at - q.at);
      for (let k = 1; k < labels.length; k++) {
        labels[k].at = Math.max(labels[k].at, labels[k - 1].at + 14);
      }
      for (const l of labels) {
        svg.append(el("text", { class: `end ${l.s}`, x: right + 8, y: l.at + 4 },
          `${l.s} ${whole(l.v)}`));
      }
      svg.append(el("rect", { class: "hit", x: left, y: top, width: right - left,
        height: base - top }));
      svg.append(el("line", { class: "cursor", x1: 0, x2: 0, y1: top, y2: base,
        visibility: "hidden" }));

      $("factor").textContent = `${g.toFixed(2)}×`;
      $("amount").textContent = `+${whole(a)}`;
      $("ceiling").textContent = whole(c);
      $("horizon").textContent = years(n);
      for (const s of SHAPES) {
        const r = s === "linear" ? whole(rate[s]) : rate[s].toFixed(2);
        const text = FORMULAS[s].replaceAll("{start}", START).replaceAll("{rate}", r)
          .replaceAll("{over}", n).replaceAll("{ceiling}", c);
        $(`worked-${s}`).textContent = `${text} = ${whole(series[s][n])}`;
        root.querySelector(`.gs-row.${s}`).classList.toggle("off", !shown.includes(s));
      }
      tip.hidden = true;
      svg.dataset.left = left;
      svg.dataset.right = right;
    };

    // Hover or touch: the year under the pointer, with each drawn shape's value that year.
    const point = (event) => {
      if (!state) return;
      const box = svg.getBoundingClientRect();
      const scale = box.width / Number(svg.viewBox.baseVal.width || box.width);
      const left = Number(svg.dataset.left);
      const right = Number(svg.dataset.right);
      const px = (event.clientX - box.left) / scale;
      const i = Math.max(0, Math.min(state.n, Math.round(((px - left) / (right - left)) * state.n)));
      const cx = left + (state.n ? (i / state.n) * (right - left) : 0);
      const cursor = svg.querySelector(".cursor");
      cursor.setAttribute("x1", cx);
      cursor.setAttribute("x2", cx);
      cursor.setAttribute("visibility", "visible");
      tip.replaceChildren();
      const head = document.createElement("b");
      head.textContent = i ? `Year ${i}` : "Today";
      tip.append(head);
      for (const s of SHAPES) {
        if (!state.shown.includes(s)) continue;
        const row = document.createElement("span");
        row.className = s;
        row.textContent = `${s}: ${whole(state.series[s][i])}`;
        tip.append(row);
      }
      tip.hidden = false;
      const room = box.width - tip.offsetWidth - 8;
      tip.style.left = `${Math.max(4, Math.min(room, cx * scale + 12))}px`;
    };
    const leave = () => {
      tip.hidden = true;
      svg.querySelector(".cursor")?.setAttribute("visibility", "hidden");
    };
    svg.addEventListener("pointermove", point);
    svg.addEventListener("pointerdown", point);
    svg.addEventListener("pointerleave", leave);

    addEventListener("resize", draw);
    for (const control of [factor, amount, ceilingIn, horizon, ...picks]) {
      control.addEventListener("input", draw);
    }
    draw();
  }
})();
