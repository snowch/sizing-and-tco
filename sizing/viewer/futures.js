/* One future at a time.
 *
 * ch01 tells a reader that the honest answer to *how big* is a range, and that you get it by
 * running the arithmetic again and again. Told and not shown, that sentence needs the reader to
 * already know what sampling is — repeating a sum gives the same sum, so why would you. This is
 * the showing. Press the button: every input jumps to the value that future brought, the fleet is
 * worked through once, and the answer drops onto the pile.
 *
 * The clustering is the lesson, and it is drawn rather than asserted. Nothing here says "in
 * proportion to how likely it is" in words. The ticks accumulating under each input say it, and
 * the prose beside the frame only has to name what the reader is watching.
 */

const $ = (id) => document.getElementById(id);

//: How many recent draws leave a tick under each input. Enough that the shape appears within a
//: dozen presses, few enough that a reader can still see one draw arrive.
const TRAIL = 60;

//: The silhouette under each input is its own percentile function, walked in even steps.
const STEPS = 64;

//: The band a spread is drawn across. Wide enough to show the tail, not so wide it is all tail.
const EDGE = 0.005;

//: The pile, in its own coordinates. The plot, a gap, then the column that holds everything off
//: the right-hand edge — which is a column rather than a clamp so that a reader can see there is
//: something out there, and how little of it there is. How many bins and how wide comes from the
//: payload, because this answer is a whole number of hosts and a bin that catches eight of them
//: beside one that catches nine draws a sawtooth nothing in the model put there.
const W = 620, H = 346, PLOT = 552, OVER_X = 580, FLOOR = 310;

//: What has been drawn so far, as counts rather than a list of every answer. A reader who holds
//: down *Draw 100* is not storing a hundred thousand numbers to re-bin on every press.
const state = { counts: [], over: 0, above: 0, drawn: 0, trails: {}, next: null, last: null };

/* -- numbers ----------------------------------------------------------------------------- */

/** Three significant figures, grouped, with no trailing zeros left behind. */
function sig(value) {
  if (!Number.isFinite(value)) return "—";
  const magnitude = Math.abs(value);
  const places =
    magnitude >= 100 ? 0 : magnitude >= 1 ? 2 : 2 - Math.floor(Math.log10(magnitude));
  return value.toLocaleString(undefined, { maximumFractionDigits: Math.min(Math.max(places, 0), 6) });
}

const whole = (value) => Math.round(value).toLocaleString();

/** The answer's unit, agreeing with its count. Left alone if it is a compound like `W/host`. */
function units(count) {
  const unit = PAYLOAD.answer_unit;
  if (!unit || unit === "dimensionless") return "";
  const plain = /^[a-z]+$/.test(unit) && !unit.endsWith("s");
  return ` ${plain && Math.round(count) !== 1 ? `${unit}s` : unit}`;
}

/* -- the inputs ---------------------------------------------------------------------------- */

const band = (spec) => [SAMPLE.at(spec, EDGE), SAMPLE.at(spec, 1 - EDGE)];

/**
 * The spread's own shape, as a filled silhouette.
 *
 * Taken from the percentile function rather than by sampling: even steps in percentile are uneven
 * steps in value, and how uneven is exactly the density. So nothing on this page is drawn from
 * draws except the pile itself, and the shape a reader compares the ticks against was not itself
 * a guess made from sixty of them.
 */
function silhouette(spec, lo, hi, w, h) {
  const xs = [];
  for (let i = 0; i <= STEPS; i++) xs.push(SAMPLE.at(spec, EDGE + ((1 - 2 * EDGE) * i) / STEPS));
  const gaps = xs.slice(1).map((x, i) => Math.max(x - xs[i], 1e-12));
  const tallest = Math.max(...gaps.map((gap) => 1 / gap));
  const at = (v) => (((v - lo) / (hi - lo)) * w).toFixed(1);
  let d = `M0,${h}`;
  for (let i = 0; i < gaps.length; i++) {
    d += ` L${at((xs[i] + xs[i + 1]) / 2)},${(h - (1 / gaps[i] / tallest) * (h - 3)).toFixed(1)}`;
  }
  return `${d} L${w},${h} Z`;
}

function inputRow(name) {
  const node = PAYLOAD.nodes[name];
  const [lo, hi] = band(node.distribution);
  const w = 200, h = 21;
  // The unit goes on the scale below rather than beside the label: six labels the model wrote
  // and a unit each is more than a narrow column holds, and every one of them wrapped.
  const unit = node.unit && node.unit !== "dimensionless" ? node.unit : "";
  return (
    `<div class="draw">` +
    `<div class="what"><span class="label">${node.label}</span>` +
    `<span class="value" id="v-${name}">—</span></div>` +
    `<svg class="spread" viewBox="0 0 ${w} ${h + 7}" preserveAspectRatio="none" aria-hidden="true">` +
    `<path class="shape" d="${silhouette(node.distribution, lo, hi, w, h)}"/>` +
    `<g class="trail" id="t-${name}"></g>` +
    `<line class="marker" id="m-${name}" y1="0" y2="${h}" x1="-10" x2="-10"/>` +
    `</svg>` +
    `<div class="ends"><span>${sig(lo)}</span><span class="unit">${unit}</span>` +
    `<span>${sig(hi)}</span></div></div>`
  );
}

function placeInput(name, value) {
  const [lo, hi] = band(PAYLOAD.nodes[name].distribution);
  const x = Math.min(Math.max(((value - lo) / (hi - lo)) * 200, 0), 200).toFixed(1);
  $(`m-${name}`).setAttribute("x1", x);
  $(`m-${name}`).setAttribute("x2", x);
  $(`v-${name}`).textContent = sig(value);

  const trail = (state.trails[name] = state.trails[name] || []);
  trail.push(x);
  if (trail.length > TRAIL) trail.shift();
  // Older ticks fade, so the newest draw is findable in a crowd of sixty without the crowd
  // disappearing. The crowd is the point.
  $(`t-${name}`).innerHTML = trail
    .map((tx, i) => {
      const age = ((i + 1) / trail.length).toFixed(3);
      return `<line x1="${tx}" x2="${tx}" y1="22" y2="28" opacity="${(0.2 + age * 0.55).toFixed(2)}"/>`;
    })
    .join("");
}

/* -- the pile ------------------------------------------------------------------------------- */

function drawPile() {
  const [lo, hi] = PAYLOAD.band;
  const counts = state.counts;
  const tallest = Math.max(...counts, state.over, 1);
  const bw = PLOT / counts.length;
  const tall = (count) => (count / tallest) * (FLOOR - 12);
  const bars = counts
    .map((count, i) =>
      count
        ? `<rect x="${(i * bw).toFixed(1)}" y="${(FLOOR - tall(count)).toFixed(1)}" ` +
          `width="${(bw - 1).toFixed(1)}" height="${tall(count).toFixed(1)}"/>`
        : "",
    )
    .join("");
  const over = state.over
    ? `<rect x="${OVER_X}" y="${(FLOOR - tall(state.over)).toFixed(1)}" width="${W - OVER_X}" ` +
      `height="${tall(state.over).toFixed(1)}"/>`
    : "";
  const at = (v) => (((v - lo) / (hi - lo)) * PLOT).toFixed(1);
  const landed =
    state.last === null
      ? ""
      : state.last > hi
        ? `<line class="landed" x1="${OVER_X + (W - OVER_X) / 2}" x2="${OVER_X + (W - OVER_X) / 2}" y1="4" y2="${FLOOR}"/>`
        : `<line class="behind" x1="${at(state.last)}" x2="${at(state.last)}" y1="4" y2="${FLOOR}"/>` +
          `<line class="landed" x1="${at(state.last)}" x2="${at(state.last)}" y1="4" y2="${FLOOR}"/>`;

  $("pile").innerHTML =
    `<rect class="paper" x="0" y="0" width="${PLOT}" height="${FLOOR}"/>` +
    `<rect class="paper" x="${OVER_X}" y="0" width="${W - OVER_X}" height="${FLOOR}"/>` +
    `<g class="bars">${bars}</g><g class="over">${over}</g>` +
    // A backing line in the paper colour, so the mark stays legible where it crosses the bars.
    // Red dashes over blue bars were the one thing on this page a reader could not find.
    `<line class="behind" x1="${at(PAYLOAD.point)}" x2="${at(PAYLOAD.point)}" y1="0" y2="${FLOOR}"/>` +
    `<line class="point" x1="${at(PAYLOAD.point)}" x2="${at(PAYLOAD.point)}" y1="0" y2="${FLOOR}"/>` +
    landed +
    `<text x="0" y="${FLOOR + 15}">${whole(lo)}</text>` +
    `<text class="mid" x="${at(PAYLOAD.point)}" y="${FLOOR + 15}">${whole(PAYLOAD.point)}</text>` +
    `<text class="right" x="${PLOT}" y="${FLOOR + 15}">${whole(hi)}</text>` +
    `<text class="mid" x="${(OVER_X + W) / 2}" y="${FLOOR + 15}">more</text>` +
    `<text class="mid" x="${(OVER_X + W) / 2}" y="${FLOOR + 28}">${state.over || ""}</text>`;

  $("count").textContent =
    state.drawn === 0 ? "" : `${state.drawn.toLocaleString()} future${state.drawn === 1 ? "" : "s"} drawn`;
  $("verdict").innerHTML = verdict();
}

/** What the reader is looking at, in the words the count currently earns. */
function verdict() {
  const mark = `<b>${whole(PAYLOAD.point)}${units(PAYLOAD.point)}</b>`;
  if (state.drawn === 0) {
    return `The dashed line is the single number: one value for every input, the arithmetic done
      once. Press <b>Draw one future</b>.`;
  }
  const last = `This future needed <b>${whole(state.last)}${units(state.last)}</b>.`;
  if (state.drawn === 1) {
    return `${last} That is not the answer — it is one of the answers, and by itself it tells you
      no more than ${mark} did.`;
  }
  if (state.drawn < 12) {
    return `${last} Too few yet to see anything. Every press asks the same model a different
      what-if, and one what-if is not a range.`;
  }
  const share = Math.round((100 * state.above) / state.drawn);
  return `${last} Of the <b>${state.drawn.toLocaleString()}</b> so far, <b>${share} in every
    hundred</b> needed more than ${mark}. The answers are not spread evenly, and the shape they
    make is what the repetition is for.`;
}

/* -- drawing ---------------------------------------------------------------------------------- */

function drawFutures(n) {
  const [lo, hi] = PAYLOAD.band;
  const bins = state.counts.length;
  for (let i = 0; i < n; i++) {
    const overrides = {};
    for (const [name, spec] of Object.entries(PAYLOAD.spreads)) {
      overrides[name] = SAMPLE.at(spec, state.next());
    }
    const answer = EVALUATE.evaluatePoint(PAYLOAD, overrides).values[PAYLOAD.answer];
    if (!Number.isFinite(answer)) continue;
    state.drawn++;
    state.last = answer;
    if (answer > PAYLOAD.point) state.above++;
    if (answer > hi) state.over++;
    else state.counts[Math.min(Math.floor(((answer - lo) / (hi - lo)) * bins), bins - 1)]++;
    // A hundred markers in one frame is a blur, and the trail underneath is where a hundred draws
    // are meant to show up anyway. So a batch moves the markers a few times and lands on its last.
    if (n <= 12 || i === n - 1 || i % 12 === 0) {
      for (const name of PAYLOAD.shown) placeInput(name, overrides[name]);
    }
  }
  drawPile();
}

function reset() {
  state.counts = new Array(PAYLOAD.bins).fill(0);
  state.trails = {};
  state.drawn = 0;
  state.over = 0;
  state.above = 0;
  state.last = null;
  // Not numpy's stream and not seeded from the book: two readers on this page are meant to get
  // different futures, and the stamped figures were never computed here. `sample.js` says so.
  state.next = SAMPLE.stream((Date.now() ^ (Math.random() * 1e9)) >>> 0);
  for (const name of PAYLOAD.shown) {
    $(`t-${name}`).innerHTML = "";
    $(`m-${name}`).setAttribute("x1", -10);
    $(`m-${name}`).setAttribute("x2", -10);
    $(`v-${name}`).textContent = "—";
  }
  drawPile();
}

function start() {
  // The chapter floats its Expand button over this frame's top right corner, so the header keeps
  // a space clear for it. Same arrangement as the model viewer's.
  if (window.self !== window.top) document.documentElement.classList.add("embedded");
  // Set here rather than in the page, so the pile's height lives in one file: the constants above
  // moved once and left the axis labels outside the frame, which is a silent way to lose them.
  $("pile").setAttribute("viewBox", `0 0 ${W} ${H}`);
  $("inputs").innerHTML = PAYLOAD.shown.map(inputRow).join("");
  $("one").addEventListener("click", () => drawFutures(1));
  $("many").addEventListener("click", () => drawFutures(100));
  $("again").addEventListener("click", reset);
  reset();
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", start);
} else {
  start();
}
