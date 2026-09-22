/* Drawing one future, in the browser.
 *
 * A port of `sizing/mc.py`'s percentile functions and `sizing/normal.py`'s inverse normal CDF,
 * so that a page can draw from a model's declared spreads without fetching a Python runtime to
 * do it. ch01's widget presses a button and wants an answer in the same frame; ten megabytes of
 * Pyodide is the right price for running the reader's own code and the wrong price for this.
 *
 * What this deliberately does NOT do is reproduce a seeded Python run. numpy's PCG64 stream
 * cannot be had here without porting PCG64 as well, so a seeded draw in this file and a seeded
 * draw in `mc.py` are different draws. They are drawn from the same distributions, which is the
 * claim `tests/test_sample.py` checks: every percentile function here agrees with its Python
 * original across the range, including the tails. The random stream is not part of that claim
 * and nothing in the book rests on it — a stamped result is always computed by Python.
 */

/* -- the inverse normal CDF -------------------------------------------------------------
 *
 * Acklam's coefficients, as in `sizing/normal.py`. Constants of a published algorithm; the
 * arrangement is this repository's own.
 */
const TAIL = 0.02425;

const CENTRAL_NUM = [
  -3.969683028665376e01, 2.209460984245205e02, -2.759285104469687e02,
  1.383577518672690e02, -3.066479806614716e01, 2.506628277459239e00,
];
const CENTRAL_DEN = [
  -5.447609879822406e01, 1.615858368580409e02, -1.556989798598866e02,
  6.680131188771972e01, -1.328068155288572e01,
];
const TAIL_NUM = [
  -7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e00,
  -2.549732539343734e00, 4.374664141464968e00, 2.938163982698783e00,
];
const TAIL_DEN = [
  7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e00,
  3.754408661907416e00,
];

/** Horner's rule. `poly([a, b, c], x)` is `a*x**2 + b*x + c`. */
function poly(coefficients, x) {
  let out = 0;
  for (const coefficient of coefficients) out = out * x + coefficient;
  return out;
}

/** The value below which a fraction `u` of a standard normal lies. */
export function normalPpf(u) {
  if (!(u > 0 && u < 1)) {
    throw new RangeError("normalPpf needs a percentile strictly between 0 and 1");
  }
  if (u >= TAIL && u <= 1 - TAIL) {
    const q = u - 0.5;
    const r = q * q;
    return (poly(CENTRAL_NUM, r) * q) / (poly(CENTRAL_DEN, r) * r + 1.0);
  }
  // Both tails, in the variable that makes them well behaved: the upper is the lower reflected.
  const lower = u < TAIL;
  const tailU = lower ? u : 1 - u;
  const q = Math.sqrt(-2.0 * Math.log(tailU));
  const value = poly(TAIL_NUM, q) / (poly(TAIL_DEN, q) * q + 1.0);
  return lower ? value : -value;
}

/** The percentile the `p10`/`p90` form of a lognormal is pinned at, as a z-score. */
const Z90 = normalPpf(0.9);

/* -- the four shapes --------------------------------------------------------------------
 *
 * Each takes a percentile and returns the value at it. That is the whole interface, here as in
 * `mc.py`: draw a percentile uniformly at random, and ask the distribution what sits at it.
 */

export function uniformPpf(u, minimum, maximum) {
  return minimum + u * (maximum - minimum);
}

export function triangularPpf(u, minimum, likely, maximum) {
  if (!(minimum <= likely && likely <= maximum)) {
    throw new RangeError(
      `triangular needs min <= likely <= max, got ${minimum}, ${likely}, ${maximum}`,
    );
  }
  if (maximum === minimum) return minimum;
  const width = maximum - minimum;
  const atMode = (likely - minimum) / width;
  return u < atMode
    ? minimum + Math.sqrt(u * width * (likely - minimum))
    : maximum - Math.sqrt((1.0 - u) * width * (maximum - likely));
}

export function lognormalPpf(u, p10, p90) {
  if (!(p10 > 0 && p10 < p90)) {
    throw new RangeError(`lognormal needs 0 < p10 < p90, got p10=${p10}, p90=${p90}`);
  }
  const logMedian = (Math.log(p10) + Math.log(p90)) / 2.0;
  const logSpread = (Math.log(p90) - Math.log(p10)) / (2.0 * Z90);
  return Math.exp(logMedian + logSpread * normalPpf(u));
}

export function normalPpfScaled(u, mean, sd) {
  if (sd < 0) throw new RangeError(`normal needs sd >= 0, got ${sd}`);
  return mean + sd * normalPpf(u);
}

//: Keyed by the name a model file declares the shape under, as `mc.SHAPES` is.
export const SHAPES = {
  uniform: (u, d) => uniformPpf(u, d.minimum, d.maximum),
  triangular: (u, d) => triangularPpf(u, d.minimum, d.likely, d.maximum),
  lognormal: (u, d) => lognormalPpf(u, d.p10, d.p90),
  normal: (u, d) => normalPpfScaled(u, d.mean, d.sd),
};

/** The one shape a spec declares, as `(name, parameters)`. Raises on none and on several. */
export function oneShape(spec) {
  const named = Object.keys(spec || {}).filter((key) => key in SHAPES);
  if (named.length !== 1) {
    throw new RangeError(`a distribution declares exactly one shape, got ${named.length}`);
  }
  return [named[0], spec[named[0]]];
}

/** The value this spec's distribution has at percentile `u`. */
export function at(spec, u) {
  const [name, parameters] = oneShape(spec);
  return SHAPES[name](u, parameters);
}

/* -- the stream -------------------------------------------------------------------------
 *
 * Not numpy's. A small counter-based generator, so that a page can offer the reader a repeatable
 * sequence without pretending it is the one a stamped result came from.
 */
export function stream(seed) {
  let state = (seed >>> 0) || 1;
  return () => {
    // mulberry32: short, well distributed, and its whole state is one number a reader can print.
    state = (state + 0x6d2b79f5) >>> 0;
    let t = state;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    const u = ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    // `normalPpf` refuses 0 and 1, and a percentile of exactly either is a bug rather than a
    // draw. Nudge inside rather than rejecting, so a caller never has to loop.
    return Math.min(Math.max(u, Number.EPSILON), 1 - Number.EPSILON);
  };
}

/** One value for each named input: a future, as the spreads say futures arrive. */
export function drawOne(specs, next) {
  const out = {};
  for (const [name, spec] of Object.entries(specs)) out[name] = at(spec, next());
  return out;
}
