/*
 * The interactive model page.
 *
 * Four of the book's six outputs live here: the dependency graph coloured by kind and provenance,
 * the input UI generated from each node's declared range, the distribution on *any* node rather
 * than only the outputs, and the tornado. The other two \u2014 unit checking and the reference-scenario
 * tests \u2014 happen in the build, which is the only place they could.
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
//: Words the chapter around the page decides between: sizing/viewer/words.json holds the plain
//: ones, for a chapter before the one that teaches sampling, and the ones it teaches.
const WORDS = window.__WORDS__;
const UNTAUGHT = new URLSearchParams(location.search).has("before");
const say = (key, fill = {}) =>
  (UNTAUGHT ? WORDS.plain : WORDS.taught)[key].replace(/\{(\w+)\}/g, (_, name) => fill[name]);
//: Whether anything here was drawn rather than stated. Before ch04 nothing is: there is no band
//: to go stale, and nothing a resample could change.
const SAMPLED = Object.values(STAMPED.nodes).some((node) => node.histogram);
const CAN_RESAMPLE = Boolean(TOOLKIT) && SAMPLED && !UNTAUGHT;
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
  if (value === undefined || value === null || Number.isNaN(value)) return "\u2014";
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
    const value = blocked.has(name) ? "\u2014" : fmt(values[name], node.unit);
    boxes.push(
      `<g class="node" data-node="${name}"><title>${name}</title>` +
      `<rect x="${x}" y="${y}" width="${BOX.w}" height="${BOX.h}" rx="3" fill="${fill}" stroke="${edge}" stroke-width="${selected === name ? 2.2 : 1.2}"${dash}/>` +
      // A bar down the left edge, which composes with the fill (kind) and the dash (measured
      // or not) rather than competing with either for the same channel.
      (isDecision(node) ? `<rect x="${x}" y="${y + 3}" width="3" height="${BOX.h - 6}" rx="1.5" fill="${edge}"/>` : "") +
      // A vendor's claim carries the tables' half-filled mark, so it is told apart here too
      // (invariant 4): by fill it is an input like any other.
      (node.provenance && node.provenance.kind === "vendor_claim" ? vendorMark(x + BOX.w - 9, y + 9) : "") +
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
    // A click picks a node to read about. It does not cut the graph down: that is a choice of
    // its own, one link under the graph, because a reader told to click a node to see where it
    // came from did not expect the rest of the model to vanish.
    g.addEventListener("click", () => {
      const name = g.dataset.node;
      selected = selected === name ? null : name;
      if (selected) reveal();
      render();
    });
    g.addEventListener("mouseenter", () => hot(g.dataset.node, true));
    g.addEventListener("mouseleave", () => { hot(g.dataset.node, false); lit(); });
  }
  lit();
  scrollNote();
}

// On a narrow screen the graph scrolls sideways, and a box the chapter tells the reader to watch
// can sit out of sight with nothing saying it is there. Count them and say so.
function scrollNote() {
  const note = $("scroll-note");
  if (!note) return;
  const box = $("graph-scroll").getBoundingClientRect();
  const hidden = box.width
    ? [...$("graph").querySelectorAll(".node")].filter((g) => g.getBoundingClientRect().right > box.right + 1).length
    : 0;
  note.hidden = hidden === 0;
  // Expand is the chapter's button; an expanded model, or this page on its own, has none to tap.
  const root = document.documentElement;
  const expand = root.classList.contains("embedded") && !root.classList.contains("expanded")
    ? ", or tap Expand above to give the model the whole screen" : "";
  note.textContent = hidden === 1
    ? `Scroll sideways to see the box out of sight to the right${expand}.`
    : `Scroll sideways to see the ${hidden} boxes out of sight to the right${expand}.`;
}

// ◐, drawn: a ring with its left half filled, the mark the book's tables give a vendor's claim.
function vendorMark(cx, cy) {
  const r = 3.6;
  return `<g class="vendor-mark"><circle cx="${cx}" cy="${cy}" r="${r}" fill="none" stroke="var(--ink)" stroke-width="1.1"/>` +
    `<path d="M${cx},${cy - r} A${r},${r} 0 0 0 ${cx},${cy + r} Z" fill="var(--ink)"/></g>`;
}

// The picked node keeps its own lines lit, so it stays findable once the pointer moves on.
function lit() {
  if (selected && $("graph").querySelector(`.node[data-node="${selected}"]`)) hot(selected, true);
}

// The line above the graph: what is picked, what is shown, and the ways in and out of each.
function focusNote() {
  const note = $("focus-note");
  const link = (id, text) => `<button class="link" id="${id}">${text}</button>`;
  const feeds = (name) => PAYLOAD.nodes[name].depends_on.length > 0;
  const fed = (name) => childrenOf()[name].length > 0;
  if (focus) {
    const count = related(focus).size - 1;
    const label = `<strong>${PAYLOAD.nodes[focus].label}</strong>`;
    const nodes = `${count} node${count === 1 ? "" : "s"}`;
    const other = direction === "down" ? feeds(focus) : fed(focus);
    note.innerHTML =
      (direction === "down" ? `Showing the ${nodes} that ${label} feeds. ` : `Showing the ${nodes} that feed ${label}. `) +
      (other ? link("flip", direction === "down" ? "Show what feeds it" : "Show what it feeds") + " · " : "") +
      link("everything", "Show everything");
  } else if (selected) {
    const offers = [];
    if (feeds(selected)) offers.push(link("upstream", "Show only what feeds it"));
    if (fed(selected)) offers.push(link("downstream", "Show only what it feeds"));
    note.innerHTML = `<strong>${PAYLOAD.nodes[selected].label}</strong> is picked. ` + offers.join(" · ");
  } else {
    // A phone has no pointer to rest, so the note says what a tap does instead.
    note.innerHTML = matchMedia("(hover: none)").matches
      ? "Tap a node to read about it under Details and to highlight its connections."
      : "Click a node to read about it under Details. Rest the pointer on a node to light its own lines.";
  }
  const on = (id, act) => { if ($(id)) $(id).addEventListener("click", () => { act(); render(); }); };
  on("flip", () => { direction = direction === "down" ? "up" : "down"; });
  on("everything", () => { focus = null; });
  on("upstream", () => { focus = selected; direction = "up"; });
  on("downstream", () => { focus = selected; direction = "down"; });
}

// Go to a node from anywhere it is named: pick it, and bring it back into view if a cut-down
// graph had left it out.
function goTo(name) {
  selected = name;
  if (focus && !related(focus).has(name)) focus = null;
  reveal();
  render();
}

//: How to open a closed panel by its toggle's id. Filled in only where panels can close.
const panels = {};
// A node the reader picks is shown under Details, so a closed Details opens: a click that
// changed nothing on screen is what the chapter would otherwise be asking them to make.
const reveal = () => panels["toggle-detail"]?.(true);

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
    const classes = [selected === name ? "focused" : "", inert ? "inert" : ""].filter(Boolean);
    const open = `<tr data-node="${name}"${classes.length ? ` class="${classes.join(" ")}"` : ""}`
      + ` title="Read about ${name} under Details">`;
    if (blocked.has(name)) return `${open}<td>${node.label}</td><td class="n">not measured</td></tr>`;
    const ceiling = node.kind === "ceiling" ? ceilingState(PAYLOAD, name, values) : null;
    const cell = ceiling
      ? `<span class="badge ${ceiling.verdict === "ok" ? "ok" : ceiling.verdict === "over" ? "over" : "headroom"}">${fmt(values[name], "")}</span>`
      : fmt(values[name], node.unit);
    return `${open}<td>${node.label}</td><td class="n">${cell}</td></tr>`;
  });
  // Only when a row is grey: with every row moving, a note about greyed rows describes nothing
  // on screen and sends the reader looking for it.
  const greyed = touched && PAYLOAD.outputs.some((name) => name !== touched && !reach.has(name));
  const why = greyed
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
  const { counts, edges, spacing } = node.histogram;
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
    `<div class="note">${fmt(edges[0], node.unit)} to ${fmt(edges[edges.length - 1], node.unit)}` +
    `${spacing === "log" ? say("log_bins") : ""}</div>`;
}

/* -- the file ------------------------------------------------------------------- */

//: The model file this page was built from, as the chapter quotes it: the stage's own file for a
//: stage, so the lines shown are the lines the chapter is about.
const FILE = TOOLKIT ? TOOLKIT.model.split("\n") : null;
//: Whether the reader has opened "In the file" under Details, kept across redraws.
let inFileOpen = false;
//: The node the file view last showed: it is redrawn when the pick changes, not on every slider
//: move, so the file does not jump under a reader who is reading it.
let fileAt;

const esc = (text) => text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

// A node's lines in the file: its key, two spaces in under `nodes:`, and everything indented
// further below it. [first, last) as line numbers, or null.
function nodeLines(name) {
  if (!FILE) return null;
  const top = FILE.indexOf("nodes:");
  const first = FILE.findIndex((line, i) => i > top && line === `  ${name}:`);
  if (top < 0 || first < 0) return null;
  let last = first + 1;
  while (last < FILE.length && (FILE[last].trim() === "" || FILE[last].startsWith("    "))) last += 1;
  while (FILE[last - 1].trim() === "") last -= 1;
  return [first, last];
}

// The whole file, with the picked node's lines marked so the view can scroll to them.
function drawFile() {
  fileAt = selected;
  const span = selected ? nodeLines(selected) : null;
  const text = (from, to) => esc(FILE.slice(from, to).join("\n"));
  $("file-view").innerHTML = span
    ? text(0, span[0]) + "\n" + `<mark id="file-node">${text(span[0], span[1])}</mark>` + "\n" + text(span[1])
    : text(0);
  // Scroll the pane, not the page: scrollIntoView would move the chapter around an embed too.
  if (span) {
    // Whichever of the two scrolls: the file itself where it is capped, the pane where it is not.
    const view = $("file-view");
    const pane = view.scrollHeight > view.clientHeight ? view : $("canvas");
    const mark = $("file-node").getBoundingClientRect();
    pane.scrollTop += mark.top - pane.getBoundingClientRect().top - (pane.clientHeight - mark.height) / 2;
  }
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
      (node.point !== undefined ? `<tr><td>${say("book_value")}</td><td class="n">${fmt(node.point, node.unit)}</td></tr>` : "") + `</table>`);
  }
  const span = nodeLines(name);
  if (span) {
    parts.push(`<details class="in-file"${inFileOpen ? " open" : ""}><summary>In the file</summary>` +
      `<pre>${esc(FILE.slice(span[0], span[1]).join("\n"))}</pre></details>`);
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
  // Only worked-out outputs count. An output that is itself an input moves with its own slider
  // and nothing else, so listing it as "cannot move" tells the reader nothing, and on a model
  // with no arithmetic yet it was the whole section.
  const reach = descendants(name);
  const worked = PAYLOAD.outputs.filter((o) => o !== name && PAYLOAD.nodes[o].depends_on.length);
  const moves = worked.filter((o) => reach.has(o));
  const stuck = worked.filter((o) => !reach.has(o));
  // A node that is itself an output is told about the others, rather than "moves none of
  // them" as though it reached nothing at all.
  const isOutput = PAYLOAD.outputs.includes(name);
  if (moves.length || stuck.length) {
    const says = isOutput
      ? (moves.length
          ? `This output changes <strong>${moves.length}</strong> of the other outputs: ${neighbours(moves)}.`
          : "This output doesn't change any of the other outputs.")
      : `Moves <strong>${moves.length} of ${moves.length + stuck.length}</strong>`
        + ` outputs: ${moves.length ? neighbours(moves) : "none of them"}.`;
    parts.push(`<h2>Reaches</h2><p class="note">${says}</p>`
      + (stuck.length && !isOutput
          ? `<p class="note dead">Cannot move: ${neighbours(stuck)}.</p>`
          : ""));
  }
  if (node.provenance && node.provenance.kind) {
    parts.push(`<h2>Provenance</h2><p class="note"><strong>${node.provenance.kind.replace("_", " ")}</strong> \u2014 ${node.provenance.source}</p>`);
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
      (isStale() ? "" : `<p class="note">${say("over_limit", { share: `<strong>${((node.ceiling.p_over_limit ?? 0) * 100).toFixed(0)}%</strong>` })}</p>`));
  }
  if (node.histogram) {
    parts.push(`<h2>${say("band")}${isStale() ? say("at_book") : ""}</h2>` + histogram(node));
    const s = node.summary;
    parts.push(`<table><tr><td>${say("low")}</td><td class="n">${fmt(s.p5, node.unit)}</td></tr>` +
      `<tr><td>${say("middle")}</td><td class="n">${fmt(s.p50, node.unit)}</td></tr>` +
      `<tr><td>${say("high")}</td><td class="n">${fmt(s.p95, node.unit)}</td></tr></table>`);
  }
  if (node.note) parts.push(`<h2>Note</h2><p class="note">${node.note}</p>`);
  $("detail-body").innerHTML = parts.join("");
  const inFile = $("detail-body").querySelector(".in-file");
  if (inFile) inFile.addEventListener("toggle", () => { inFileOpen = inFile.open; });
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
      state.textContent = CAN_RESAMPLE ? say("resample_held") : say("moved");
      state.className = "state fixed";
    } else if (name in fixed) {
      state.textContent = `fixed at ${fmt(fixed[name], PAYLOAD.nodes[name].unit)}`;
      state.className = "state fixed";
    } else {
      state.textContent = shape(PAYLOAD.nodes[name]);
      state.className = "state";
    }
  }
  $("stale").style.display = isStale() && SAMPLED ? "block" : "none";
  $("reset").style.display = isStale() || Object.keys(fixed).length ? "inline-block" : "none";
  drawGraph(values, blocked);
  focusNote();
  outputsTable(values, blocked);
  detail(values, blocked);
  if (FILE && $("canvas").classList.contains("showing-file") && fileAt !== selected) drawFile();
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
  if (!d) return say("single");
  const u = node.unit;
  if (d.lognormal) return say("lognormal", { p10: fmt(d.lognormal.p10, u), p90: fmt(d.lognormal.p90, u) });
  if (d.triangular) {
    const t = d.triangular;
    return say("triangular", { minimum: fmt(t.minimum, u), likely: fmt(t.likely, u), maximum: fmt(t.maximum, u) });
  }
  if (d.uniform) return say("uniform", { minimum: fmt(d.uniform.minimum, u), maximum: fmt(d.uniform.maximum, u) });
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
      banner(say("resample_checking"), "pending");
      agreement = agree(await resampleWith({}));
    }
    banner(say("resample_running", { count: Object.keys(held).length }), "pending");
    const fresh = await resampleWith(held);
    PAYLOAD = fresh;
    fixed = held;
    overrides = {};
    const s = fresh.scenario;
    const heldText = Object.entries(held)
      .map(([n, v]) => `${STAMPED.nodes[n].label} at ${fmt(v, STAMPED.nodes[n].unit)}`).join(", ");
    banner(say("resample_done", { samples: s.samples.toLocaleString(), seed: s.seed }) +
      (heldText ? say("resample_with", { held: heldText }) : ". ") +
      say("resample_after") + agreement,
      agreement.startsWith("At the scenario") ? "" : "bad");
  } catch (error) {
    banner(say("resample_failed", { error }), "bad");
  } finally {
    button.disabled = false;
    render();
  }
}

if (CAN_RESAMPLE) $("resample").addEventListener("click", resample);

{
  const note = $("narrow-note");
  // What the chapter around the page has not taught yet comes out, and so does a resample with
  // nothing to change or no toolkit to do it with.
  if (UNTAUGHT) for (const el of document.querySelectorAll("[data-once-taught]")) el.remove();
  if (!CAN_RESAMPLE) for (const el of document.querySelectorAll("[data-resample]")) el.remove();
  $("stale-text").textContent = say("stale");
  // The whole file, beside the graph where there is room for both: shown only when the page is
  // wide, which is what Expand gives a chapter's embed on a desktop. style.css hides the switch
  // below that, and shows the graph whatever was chosen.
  if (FILE) {
    const view = (file) => {
      $("canvas").classList.toggle("showing-file", file);
      $("view-graph").setAttribute("aria-pressed", String(!file));
      $("view-file").setAttribute("aria-pressed", String(file));
      if (file) drawFile();
    };
    $("view-graph").addEventListener("click", () => view(false));
    $("view-file").addEventListener("click", () => view(true));
  } else {
    $("views").remove();
  }
  $("reset").textContent = say("reset");
  if (window.self !== window.top) {
    // The chapter floats its Expand button over this panel's top right corner, so the header
    // keeps a space clear for it. On a phone the title wrapped under the button without it.
    document.documentElement.classList.add("embedded");
    // The button says what it does, so a note explaining it only pushed the graph down. Removed
    // rather than hidden: the stacked layout's rule shows the note, and would beat `hidden`.
    note.remove();
    // Inputs and Details start closed, so a chapter shows the graph and the reader opens the rest.
    for (const [button, content] of [["toggle-controls", "controls-content"], ["toggle-detail", "detail-content"]]) {
      const toggle = $(button), body = $(content), section = body.closest("section");
      const show = (open) => {
        toggle.setAttribute("aria-expanded", String(open));
        toggle.textContent = open ? "\u25bc" : "\u25b6";
        body.style.maxHeight = open ? "100vh" : "0";
        section.toggleAttribute("data-collapsed", !open);
      };
      panels[button] = show;
      show(toggle.getAttribute("aria-expanded") === "true");
      toggle.addEventListener("click", () => show(toggle.getAttribute("aria-expanded") !== "true"));
    }
    // The chapter sizes the frame to whatever this page reports. Not scrollHeight: that is never
    // less than the frame's current height, so a frame that grew when a panel opened would never
    // shrink when it closed. The observer fires through a panel's transition and on a resize.
    // Embedded, every layout sizes itself to what it shows (style.css), so the height reported
    // here does not depend on the frame and cannot come back as the next one. Expanded to the
    // window, the three columns take the window's height and scroll on their own, and the
    // chapter's stylesheet decides the frame; null says so.
    const report = () => {
      const expanded = document.documentElement.classList.contains("expanded");
      const height = Math.ceil(document.body.getBoundingClientRect().height);
      window.parent.postMessage({ sizing: expanded ? null : height }, "*");
    };
    // Escape closes an expanded model, but once the reader has clicked a node or a slider the
    // keyboard is in this page, where the chapter cannot hear it. Pass the key up.
    addEventListener("keydown", (e) => {
      if (e.key === "Escape" && document.documentElement.classList.contains("expanded")) {
        window.parent.postMessage({ close: true }, "*");
      }
    });
    addEventListener("message", (e) => {
      if (e.source === window.parent && e.data && typeof e.data.expanded === "boolean") {
        document.documentElement.classList.toggle("expanded", e.data.expanded);
        report();
        scrollNote();
      }
    });
    new ResizeObserver(report).observe(document.body);
  } else {
    note.textContent = "This graph wants a wider screen \u2014 a tablet held sideways, or larger. " +
      "The sliders below still work here.";
  }
}

buildControls();
render();
$("graph-scroll").addEventListener("scroll", scrollNote, { passive: true });
addEventListener("resize", scrollNote);
