/*
 * The interactive model page.
 *
 * Four of the book's six outputs live here: the dependency graph coloured by kind and provenance,
 * the input UI generated from each node's declared range, the distribution on *any* node rather
 * than only the outputs, and the tornado. The other two — unit checking and the reference-scenario
 * tests — happen in the build, which is the only place they could.
 *
 * What this page will not do is resample. See evaluate.js.
 */
import { evaluatePoint, ceilingState } from "./evaluate.js";

// What the build stamped, kept as it came; PAYLOAD is what the page shows, and after a
// resample it is a fresh payload from the same sampler with some inputs held.
const STAMPED = window.__MODEL__;
let PAYLOAD = STAMPED;
//: The toolkit the page carries for a resample, or undefined on a page built without one.
const TOOLKIT = window.__TOOLKIT__;
const BOX = { w: 154, h: 32, col: 188, row: 46, margin: 16 };

// A box is a box. What does not fit says so, rather than stopping mid-word and leaving the
// reader to guess whether "installed read throughpu" was the whole name. The full label is in
// the panel on the right, and the node's identifier is in the tooltip.
const LABEL_CHARS = 28;
const fit = (text) => (text.length > LABEL_CHARS ? text.slice(0, LABEL_CHARS - 1) + "\u2026" : text);

let overrides = {};
//: The input the reader last moved. The outputs it cannot reach go quiet while it is
//: held, because "I dragged this and nothing happened" is the question this page kept
//: leaving people to answer for themselves.
let touched = null;
//: Inputs held at a value by the last resample: name -> value. Shown against their sliders.
let fixed = {};
//: The node the graph is cut down to, and which way: what feeds it, or what it feeds.
let focus = null;
let direction = "up";
let selected = null;
let pyodide = null, booting = null, agreement = null;

const $ = (id) => document.getElementById(id);

function fmt(value, unit) {
  if (value === undefined || value === null || Number.isNaN(value)) return "—";
  const money = /USD|\$/.test(unit || "");
  const abs = Math.abs(value);
  if (money) return "$" + value.toLocaleString(undefined, { maximumFractionDigits: abs >= 1000 ? 0 : 2 });
  if (abs >= 1000) return value.toLocaleString(undefined, { maximumFractionDigits: 0 });
  return value.toLocaleString(undefined, { maximumSignificantDigits: 3 });
}

const isStale = () => Object.keys(overrides).length > 0;

/* -- the graph ------------------------------------------------------------------- */

// Everything upstream of a node, itself included: the nodes whose values reach it.
function ancestors(name) {
  const seen = new Set([name]);
  const stack = [name];
  while (stack.length) {
    for (const parent of PAYLOAD.nodes[stack.pop()].depends_on) {
      if (!seen.has(parent)) { seen.add(parent); stack.push(parent); }
    }
  }
  return seen;
}

// name -> the nodes whose formulas use it. Built per call because PAYLOAD can be replaced.
function childrenOf() {
  const kids = {};
  for (const name of Object.keys(PAYLOAD.nodes)) kids[name] = [];
  for (const [name, node] of Object.entries(PAYLOAD.nodes)) {
    for (const parent of node.depends_on) kids[parent].push(name);
  }
  return kids;
}

// Whether somebody chose this. The model says so itself, because nothing here can work it out:
// the nearest signal is whether the input was given a shape, and by that rule the records a
// service's users uploaded read as a decision and so does a year in seconds. ch02 is a whole
// section on how poor that proxy is.
const isDecision = (node) => node.decided === "you";

// Everything downstream of a node, itself included: how far its value reaches.
function descendants(name) {
  const kids = childrenOf();
  const seen = new Set([name]);
  const stack = [name];
  while (stack.length) {
    for (const child of kids[stack.pop()]) {
      if (!seen.has(child)) { seen.add(child); stack.push(child); }
    }
  }
  return seen;
}

const related = (name) => (direction === "down" ? descendants(name) : ancestors(name));

// Where each shown node sits. With nothing in focus, where the build placed it. With a focus,
// the same columns with the empty ones closed up and the rows packed, so that a dozen nodes
// take a dozen boxes' worth of canvas rather than the whole graph's. Columns keep their order,
// so every line still runs left to right, from what feeds to what is fed.
function layout(shown, compact) {
  const names = [...shown];
  const place = {};
  if (!compact) {
    for (const name of names) place[name] = { col: PAYLOAD.nodes[name].layer, row: PAYLOAD.nodes[name].row };
    return place;
  }
  const layers = [...new Set(names.map((n) => PAYLOAD.nodes[n].layer))].sort((a, b) => a - b);
  const column = new Map(layers.map((layer, i) => [layer, i]));
  const filled = {};
  names.sort((a, b) => PAYLOAD.nodes[a].row - PAYLOAD.nodes[b].row || a.localeCompare(b));
  for (const name of names) {
    const col = column.get(PAYLOAD.nodes[name].layer);
    filled[col] = (filled[col] ?? -1) + 1;
    place[name] = { col, row: filled[col] };
  }
  return place;
}

function centre(place) {
  return [BOX.margin + place.col * BOX.col + BOX.w / 2, BOX.margin + place.row * BOX.row + BOX.h / 2];
}

// Light a node's own lines and neighbours while the pointer is on it, so a path can be followed
// one hop at a time without cutting the graph down.
function hot(name, on) {
  const graph = $("graph");
  for (const edge of graph.querySelectorAll(`.edge[data-from="${name}"], .edge[data-to="${name}"]`)) {
    edge.classList.toggle("hot", on);
  }
  const kids = childrenOf();
  for (const other of [...PAYLOAD.nodes[name].depends_on, ...kids[name]]) {
    const box = graph.querySelector(`.node[data-node="${other}"]`);
    if (box) box.classList.toggle("hot", on);
  }
}

function drawGraph(values, blocked) {
  const names = Object.keys(PAYLOAD.nodes);
  const shown = focus ? related(focus) : new Set(names);
  const place = layout(shown, Boolean(focus));
  const cols = Math.max(...Object.values(place).map((p) => p.col)) + 1;
  const rows = Math.max(...Object.values(place).map((p) => p.row)) + 1;
  const w = BOX.margin * 2 + cols * BOX.col;
  const h = BOX.margin * 2 + rows * BOX.row;

  const edges = [];
  const boxes = [];
  for (const name of shown) {
    const node = PAYLOAD.nodes[name];
    for (const parent of node.depends_on) {
      if (!shown.has(parent)) continue;
      const [x1, y1] = centre(place[parent]);
      const [x2, y2] = centre(place[name]);
      const a = x1 + BOX.w / 2, b = x2 - BOX.w / 2, mid = (a + b) / 2;
      edges.push(`<path class="edge" data-from="${parent}" data-to="${name}" d="M${a},${y1} C${mid},${y1} ${mid},${y2} ${b},${y2}"/>`);
    }
  }
  for (const name of shown) {
    const node = PAYLOAD.nodes[name];
    const x = BOX.margin + place[name].col * BOX.col;
    const y = BOX.margin + place[name].row * BOX.row;
    const unmeasured = node.kind === "measured" && !node.measured;
    const ceiling = node.kind === "ceiling" ? ceilingState(PAYLOAD, name, values) : null;
    let fill = `var(--${node.kind})`, edge = `var(--${node.kind}-edge)`;
    // Nothing here yet, so the box is the page showing through: white on a white page,
    // dark on a dark one. A literal white would be a slab in the dark -- and, since the
    // label follows the palette, white text on it.
    if (unmeasured || blocked.has(name)) fill = "var(--bg)";
    if (ceiling && ceiling.verdict === "over") fill = "var(--ceiling)";
    const dash = unmeasured || blocked.has(name) ? ' stroke-dasharray="3 3"' : "";
    const value = blocked.has(name) ? "—" : fmt(values[name], node.unit);
    boxes.push(
      `<g class="node" data-node="${name}"><title>${name}</title>` +
      `<rect x="${x}" y="${y}" width="${BOX.w}" height="${BOX.h}" rx="3" fill="${fill}" stroke="${edge}" stroke-width="${selected === name ? 2.2 : 1.2}"${dash}/>` +
      // A bar down the left edge, which composes with the fill (kind) and the dash (measured
      // or not) rather than competing with either for the same channel.
      (isDecision(node) ? `<rect x="${x}" y="${y + 3}" width="3" height="${BOX.h - 6}" rx="1.5" fill="${edge}"/>` : "") +
      `<text x="${x + 6}" y="${y + 13}" fill="var(--ink)">${fit(node.label)}</text>` +
      `<text x="${x + BOX.w - 6}" y="${y + 26}" text-anchor="end" fill="var(--muted)" font-size="9">${value}</text>` +
      `</g>`
    );
  }
  $("graph").setAttribute("viewBox", `0 0 ${w} ${h}`);
  $("graph").setAttribute("width", w);
  $("graph").setAttribute("height", h);
  $("graph").innerHTML = edges.join("") + boxes.join("");
  for (const g of $("graph").querySelectorAll(".node")) {
    g.addEventListener("click", () => {
      const name = g.dataset.node;
      selected = name;
      focus = focus === name ? null : name;
      render();
    });
    g.addEventListener("mouseenter", () => hot(g.dataset.node, true));
    g.addEventListener("mouseleave", () => hot(g.dataset.node, false));
  }
}

// The line under the graph: what is shown, and the two ways out of it.
function focusNote() {
  const note = $("focus-note");
  if (!focus) {
    note.innerHTML = "Click a node to show only what feeds it. Rest the pointer on one to light its own lines.";
    return;
  }
  const count = related(focus).size - 1;
  const label = `<strong>${PAYLOAD.nodes[focus].label}</strong>`;
  const nodes = `${count} node${count === 1 ? "" : "s"}`;
  note.innerHTML =
    (direction === "down" ? `Showing the ${nodes} that ${label} feeds. ` : `Showing the ${nodes} that feed ${label}. `) +
    `<button class="link" id="flip">${direction === "down" ? "Show what feeds it" : "Show what it feeds"}</button>` +
    ` \u00b7 <button class="link" id="everything">Show everything</button>`;
  $("flip").addEventListener("click", () => { direction = direction === "down" ? "up" : "down"; render(); });
  $("everything").addEventListener("click", () => { focus = null; render(); });
}

// Go to a node from anywhere it is named: select it and cut the graph down to what feeds it.
function goTo(name) {
  selected = name;
  focus = name;
  direction = "up";
  render();
}

/* -- sliders --------------------------------------------------------------------- */

function buildControls() {
  const sliders = Object.entries(PAYLOAD.nodes)
    .filter(([, node]) => node.slider)
    .sort(([a], [b]) => a.localeCompare(b));
  $("sliders").innerHTML = sliders
    .map(([name, node]) => {
      const counted = ["node", "drive", "core", "host"].includes(node.unit);
      const step = counted ? 1 : "any";
      return `<div class="slider"><label for="s-${name}"><span>${node.label}</span>` +
        `<span id="v-${name}"></span></label>` +
        `<input type="range" id="s-${name}" data-node="${name}" min="${node.slider.min}" ` +
        `max="${node.slider.max}" step="${step}" value="${node.point}">` +
        `<div class="state" id="st-${name}"></div></div>`;
    })
    .join("");
  for (const input of $("sliders").querySelectorAll("input")) {
    input.addEventListener("input", () => {
      overrides[input.dataset.node] = parseFloat(input.value);
      touched = input.dataset.node;
      render();
    });
  }
}

/* -- panels ---------------------------------------------------------------------- */

function outputsTable(values, blocked) {
  // Whatever the reader last moved, and what it cannot reach. Greying those rows says the
  // number did not fail to update -- it cannot.
  const reach = touched ? descendants(touched) : null;
  const rows = PAYLOAD.outputs.map((name) => {
    const node = PAYLOAD.nodes[name];
    const inert = reach && name !== touched && !reach.has(name);
    const classes = [focus === name ? "focused" : "", inert ? "inert" : ""].filter(Boolean);
    const open = `<tr data-node="${name}"${classes.length ? ` class="${classes.join(" ")}"` : ""}`
      + ` title="Show what feeds ${name}">`;
    if (blocked.has(name)) return `${open}<td>${node.label}</td><td class="n">not measured</td></tr>`;
    const ceiling = node.kind === "ceiling" ? ceilingState(PAYLOAD, name, values) : null;
    const cell = ceiling
      ? `<span class="badge ${ceiling.verdict === "ok" ? "ok" : ceiling.verdict === "over" ? "over" : "headroom"}">${fmt(values[name], "")}</span>`
      : fmt(values[name], node.unit);
    return `${open}<td>${node.label}</td><td class="n">${cell}</td></tr>`;
  });
  const why = touched
    ? `<p class="note">Greyed rows cannot be moved by <strong>${PAYLOAD.nodes[touched].label}</strong>,`
      + ` however far you drag it.</p>`
    : "";
  $("outputs").innerHTML = why + `<table>${rows.join("")}</table>`;
  for (const row of $("outputs").querySelectorAll("tr")) {
    row.addEventListener("click", () => goTo(row.dataset.node));
  }
}

// A node's neighbours, each a link that goes there.
function neighbours(names) {
  return names.map((n) => `<button class="link" data-goto="${n}">${PAYLOAD.nodes[n].label}</button>`).join(", ");
}

function histogram(node) {
  if (!node.histogram) return "";
  const { counts, edges } = node.histogram;
  const tallest = Math.max(...counts) || 1;
  const bars = counts
    .map((c, i) => {
      const x = (i / counts.length) * 100;
      const w = 100 / counts.length;
      const h = (c / tallest) * 100;
      return `<rect x="${x}%" y="${100 - h}%" width="${w}%" height="${h}%" fill="var(--hist)"/>`;
    })
    .join("");
  return `<svg class="hist" preserveAspectRatio="none" viewBox="0 0 100 100">${bars}</svg>` +
    `<div class="note">${fmt(edges[0], node.unit)} to ${fmt(edges[edges.length - 1], node.unit)}</div>`;
}

function detail(values, blocked) {
  const name = selected;
  if (!name) {
    $("detail-body").innerHTML = `<p class="note">Click any node to see what fed it, what it is worth, and how uncertain it is.</p>`;
    return;
  }
  const node = PAYLOAD.nodes[name];
  const parts = [`<h2>${node.label}</h2>`, `<p class="note"><code>${name}</code> · ${node.kind} · ${node.unit}</p>`];
  if (blocked.has(name)) {
    parts.push(`<div class="blocked"><strong>Not yet measured.</strong> This depends on ${node.blocked_by.map((b) => `<code>${b}</code>`).join(", ")}, which nobody has measured. Nothing is estimated in its place.</div>`);
  } else {
    parts.push(`<table><tr><td>Value here</td><td class="n">${fmt(values[name], node.unit)}</td></tr>` +
      (node.point !== undefined ? `<tr><td>At the scenario</td><td class="n">${fmt(node.point, node.unit)}</td></tr>` : "") + `</table>`);
  }
  if (node.formula) parts.push(`<h2>Formula</h2><p><code>${node.formula}</code></p>`);
  const fed = childrenOf()[name];
  if (node.depends_on.length) parts.push(`<h2>Fed by</h2><p class="note">${neighbours(node.depends_on)}</p>`);
  if (fed.length) parts.push(`<h2>Feeds</h2><p class="note">${neighbours(fed)}</p>`);
  // One hop cannot answer the question a reader actually has at a slider, which is whether
  // this changes the answer. Records held feeds four things and reaches the fleet the model
  // recommends without ever reaching what the fleet costs, because the fleet is a decision and
  // the cost is of the fleet decided on. Naming the outputs it cannot move is the point: a
  // short list of what it does move reads as a summary, not as a dead end.
  const reach = descendants(name);
  const moves = PAYLOAD.outputs.filter((o) => o !== name && reach.has(o));
  const stuck = PAYLOAD.outputs.filter((o) => o !== name && !reach.has(o));
  if (moves.length || stuck.length) {
    parts.push(`<h2>Reaches</h2>`
      + `<p class="note">Moves <strong>${moves.length} of ${moves.length + stuck.length}</strong>`
      + ` outputs: ${moves.length ? neighbours(moves) : "none of them"}.</p>`
      + (stuck.length
          ? `<p class="note dead">Cannot move: ${neighbours(stuck)}.</p>`
          : ""));
  }
  if (node.provenance && node.provenance.kind) {
    parts.push(`<h2>Provenance</h2><p class="note"><strong>${node.provenance.kind.replace("_", " ")}</strong> — ${node.provenance.source}</p>`);
  }
  if (node.measured) {
    parts.push(`<h2>Measured</h2><p class="note">${fmt(node.measured.value, node.unit)} ± ${fmt(node.measured.sd, node.unit)}<br>${node.measured.stack}<br><code>bench/results/${node.result}.json</code></p>`);
  }
  if (node.ceiling) {
    const c = ceilingState(PAYLOAD, name, values);
    parts.push(`<h2>Ceiling</h2><table><tr><td>Limit</td><td class="n">${fmt(c.limit, "")}</td></tr>` +
      `<tr><td>Headroom</td><td class="n">${(c.headroom * 100).toFixed(0)}%</td></tr>` +
      `<tr><td>Allowed</td><td class="n">${fmt(c.allowed, "")}</td></tr></table>` +
      `<p class="note">${c.because}</p>` +
      (isStale() ? "" : `<p class="note">At the scenario, over its limit in <strong>${((node.ceiling.p_over_limit ?? 0) * 100).toFixed(0)}%</strong> of samples.</p>`));
  }
  if (node.histogram) {
    parts.push(`<h2>Distribution${isStale() ? " (at the scenario)" : ""}</h2>` + histogram(node));
    const s = node.summary;
    parts.push(`<table><tr><td>p5</td><td class="n">${fmt(s.p5, node.unit)}</td></tr>` +
      `<tr><td>median</td><td class="n">${fmt(s.p50, node.unit)}</td></tr>` +
      `<tr><td>p95</td><td class="n">${fmt(s.p95, node.unit)}</td></tr></table>`);
  }
  if (node.note) parts.push(`<h2>Note</h2><p class="note">${node.note}</p>`);
  $("detail-body").innerHTML = parts.join("");
  for (const link of $("detail-body").querySelectorAll("[data-goto]")) {
    link.addEventListener("click", () => goTo(link.dataset.goto));
  }
}

function render() {
  const { values, blocked } = evaluatePoint(PAYLOAD, overrides);
  for (const input of $("sliders").querySelectorAll("input")) {
    const name = input.dataset.node;
    if (!(name in overrides)) input.value = PAYLOAD.nodes[name].point;
    $(`v-${name}`).textContent = fmt(parseFloat(input.value), PAYLOAD.nodes[name].unit);
  }
  for (const input of $("sliders").querySelectorAll("input")) {
    const name = input.dataset.node;
    const state = $(`st-${name}`);
    if (name in overrides) {
      state.textContent = "held here \u2014 resample to see what that leaves";
      state.className = "state fixed";
    } else if (name in fixed) {
      state.textContent = `fixed at ${fmt(fixed[name], PAYLOAD.nodes[name].unit)}`;
      state.className = "state fixed";
    } else {
      state.textContent = shape(PAYLOAD.nodes[name]);
      state.className = "state";
    }
  }
  $("stale").style.display = isStale() ? "block" : "none";
  $("resample").style.display = TOOLKIT ? "block" : "none";
  $("reset").style.display = isStale() || Object.keys(fixed).length ? "inline-block" : "none";
  drawGraph(values, blocked);
  focusNote();
  outputsTable(values, blocked);
  detail(values, blocked);
}

$("reset").addEventListener("click", () => {
  overrides = {}; fixed = {}; touched = null; PAYLOAD = STAMPED;
  $("banner").style.display = "none";
  render();
});

/* -- resampling -------------------------------------------------------------------- */

// A declared shape, said the way the model file says it.
function shape(node) {
  const d = node.distribution;
  if (!d) return "a single value";
  const u = node.unit;
  if (d.lognormal) return `lognormal, p10 ${fmt(d.lognormal.p10, u)} to p90 ${fmt(d.lognormal.p90, u)}`;
  if (d.triangular) return `triangular, ${fmt(d.triangular.minimum, u)} / ${fmt(d.triangular.likely, u)} / ${fmt(d.triangular.maximum, u)}`;
  if (d.uniform) return `uniform, ${fmt(d.uniform.minimum, u)} to ${fmt(d.uniform.maximum, u)}`;
  return Object.keys(d)[0];
}

function banner(text, cls) {
  const b = $("banner");
  b.textContent = text;
  b.className = "banner" + (cls ? " " + cls : "");
  b.style.display = "block";
}

async function resampleWith(held) {
  pyodide.globals.set("_model", TOOLKIT.model);
  pyodide.globals.set("_scenario", TOOLKIT.scenario);
  pyodide.globals.set("_held", JSON.stringify(held));
  const text = await pyodide.runPythonAsync(
    "import json\nresample(_model, _scenario, json.loads(_held))");
  return JSON.parse(text);
}

// Before the page shows a resampled interval it shows that this sampler, in this browser, gives
// back the stamped one: every node's point and its p5, median and p95, at the scenario.
function agree(fresh) {
  let checked = 0;
  const off = [];
  const close = (a, b) => Math.abs(a - b) <= 1e-9 * Math.max(1, Math.abs(b));
  for (const [name, node] of Object.entries(STAMPED.nodes)) {
    const got = fresh.nodes[name] || {};
    if (node.point !== undefined) { checked += 1; if (!close(got.point, node.point)) off.push(name); }
    if (node.summary) {
      for (const k of ["p5", "p50", "p95"]) {
        checked += 1;
        if (!got.summary || !close(got.summary[k], node.summary[k])) { off.push(`${name}.${k}`); break; }
      }
    }
  }
  return off.length
    ? `This browser does not agree with the build at the scenario (${off.slice(0, 4).join(", ")}${off.length > 4 ? "\u2026" : ""}). Trust the stamped result, not this page.`
    : `At the scenario this browser reproduces the stamped result on all ${checked} checked figures.`;
}

async function resample() {
  const held = { ...fixed, ...overrides };
  const button = $("resample");
  button.disabled = true;
  try {
    booting = booting || bootToolkit({
      pyodideUrl: TOOLKIT.pyodide, modules: TOOLKIT.modules, results: TOOLKIT.results,
      wheels: TOOLKIT.wheels,
      status: (text) => banner(text, "pending"),
    });
    pyodide = await booting;
    if (agreement === null) {
      banner("Checking this browser against the build\u2026", "pending");
      agreement = agree(await resampleWith({}));
    }
    banner(`Sampling with ${Object.keys(held).length} input(s) held\u2026`, "pending");
    const fresh = await resampleWith(held);
    PAYLOAD = fresh;
    fixed = held;
    overrides = {};
    const s = fresh.scenario;
    const heldText = Object.entries(held)
      .map(([n, v]) => `${STAMPED.nodes[n].label} at ${fmt(v, STAMPED.nodes[n].unit)}`).join(", ");
    banner(`Resampled: ${s.samples.toLocaleString()} samples, seed ${s.seed}` +
      (heldText ? `, with ${heldText} held. ` : ". ") +
      "The intervals and the histograms below are for these settings. " + agreement,
      agreement.startsWith("At the scenario") ? "" : "bad");
  } catch (error) {
    banner("The sampler did not run here: " + error + " \u2014 the stamped intervals stand.", "bad");
  } finally {
    button.disabled = false;
    render();
  }
}

if (TOOLKIT) $("resample").addEventListener("click", resample);

// Shown only when the columns have stacked. Inside a chapter that is the embed's width, and
// Expand, over this panel's corner, gives it the whole window without reloading it, so every
// slider stays where it was put. Opening it on its own page is the other way, and starts over.
// On a phone the embed is the screen already, and the sliders still work.
{
  const note = $("narrow-note");
  const graphOnly = new URLSearchParams(location.search).get("graphOnly") === "true";
  // Auto-apply graph-only mode for progressive viewer stages in ch02
  const progressiveStages = [
    "demand_inputs_initial",
    "demand_inputs_all",
    "demand_horizon_exponent"
  ];
  const modelName = STAMPED?.model || "";
  const isProgressiveStage = progressiveStages.some(stage => modelName.includes(stage));

  if (window.self !== window.top) {
    // The chapter floats its Expand button over this panel's top right corner, so the header
    // keeps a space clear for it. On a phone the title wrapped under the button without it.
    document.documentElement.classList.add("embedded");
    if (graphOnly || isProgressiveStage) {
      // Graph-only mode: hide controls and detail, expand canvas to full width
      document.documentElement.classList.add("graph-only");
      $("controls").style.display = "none";
      $("detail").style.display = "none";
      note.textContent = "Click Expand to interact with this model.";
    } else {
      note.textContent = "Embedded at the chapter\u2019s width. Press Expand, at the top right, "
        + "for the whole window \u2014 or ";
      const open = document.createElement("a");
      open.href = location.href;
      open.target = "_blank";
      open.rel = "noopener";
      open.textContent = "open this model on its own";
      note.appendChild(open);
      note.appendChild(document.createTextNode(" for the full layout."));
      // Set up collapsible panels in embedded mode
      const toggleControls = $("toggle-controls");
      const toggleDetail = $("toggle-detail");
      const controlsContent = $("controls-content");
      const detailContent = $("detail-content");
      if (toggleControls && controlsContent) {
        const isExpanded = toggleControls.getAttribute("aria-expanded") === "true";
        // Initialize maxHeight based on initial aria-expanded state
        controlsContent.style.maxHeight = isExpanded ? "100vh" : "0";
        // Mark section as collapsed to remove padding
        const controlsSection = $("controls");
        if (!isExpanded) controlsSection.setAttribute("data-collapsed", "true");

        toggleControls.addEventListener("click", () => {
          const nowExpanded = toggleControls.getAttribute("aria-expanded") === "true";
          toggleControls.setAttribute("aria-expanded", String(!nowExpanded));
          toggleControls.textContent = nowExpanded ? "\u25b6" : "\u25bc";
          controlsContent.style.maxHeight = nowExpanded ? "0" : "100vh";
          if (nowExpanded) {
            controlsSection.setAttribute("data-collapsed", "true");
          } else {
            controlsSection.removeAttribute("data-collapsed");
          }
        });
      }
      if (toggleDetail && detailContent) {
        const isExpanded = toggleDetail.getAttribute("aria-expanded") === "true";
        // Initialize maxHeight based on initial aria-expanded state
        detailContent.style.maxHeight = isExpanded ? "100vh" : "0";
        // Mark section as collapsed to remove padding
        const detailSection = $("detail");
        if (!isExpanded) detailSection.setAttribute("data-collapsed", "true");

        toggleDetail.addEventListener("click", () => {
          const nowExpanded = toggleDetail.getAttribute("aria-expanded") === "true";
          toggleDetail.setAttribute("aria-expanded", String(!nowExpanded));
          toggleDetail.textContent = nowExpanded ? "\u25b6" : "\u25bc";
          detailContent.style.maxHeight = nowExpanded ? "0" : "100vh";
          if (nowExpanded) {
            detailSection.setAttribute("data-collapsed", "true");
          } else {
            detailSection.removeAttribute("data-collapsed");
          }
        });
      }
    }
    // The chapter sizes the frame to whatever this page reports. Not scrollHeight: that is never
    // less than the frame's current height, so a frame that grew when a panel opened would never
    // shrink when it closed. The observer fires through a panel's transition and on a resize.
    new ResizeObserver(() => {
      window.parent.postMessage({ sizing: Math.ceil(document.body.getBoundingClientRect().height) }, "*");
    }).observe(document.body);
  } else {
    note.textContent = "This graph wants a wider screen \u2014 a tablet held sideways, or larger. " +
      "The sliders below still work here.";
  }
}

buildControls();
render();
