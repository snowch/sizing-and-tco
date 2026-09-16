/*
 * The model evaluator, in the browser.
 *
 * This is the second implementation of the arithmetic in sizing/evaluate.py, and a second
 * implementation is a liability unless something checks it. Something does: every exported model
 * carries a set of slider positions together with the values Python computed at each of them, and
 * tests/test_viewer.py runs this file over exactly those and fails on any disagreement. A browser
 * quietly showing different numbers from the build would be the precise failure this repository
 * exists to prevent.
 *
 * It computes point values only. Moving a slider recomputes the whole graph instantly, because a
 * point is arithmetic; it does not resample, because the distributions came from a seeded,
 * stamped sampler and a second sampler here would be a second answer nobody had verified. The
 * page says so when a slider moves off the scenario.
 */

const FUNCTIONS = {
  min: Math.min,
  max: Math.max,
  ceil: Math.ceil,
  floor: Math.floor,
  sqrt: Math.sqrt,
  log: Math.log,
  exp: Math.exp,
};

export function walk(tree, values) {
  switch (tree.op) {
    case "const":
      return tree.value;
    case "ref": {
      const value = values[tree.name];
      if (value === undefined) throw new Error(`${tree.name} has no value`);
      return value;
    }
    case "neg":
      return -walk(tree.args[0], values);
    case "call":
      return FUNCTIONS[tree.fn](...tree.args.map((arg) => walk(arg, values)));
    case "+":
      return walk(tree.args[0], values) + walk(tree.args[1], values);
    case "-":
      return walk(tree.args[0], values) - walk(tree.args[1], values);
    case "*":
      return walk(tree.args[0], values) * walk(tree.args[1], values);
    case "/":
      return walk(tree.args[0], values) / walk(tree.args[1], values);
    case "**":
      return walk(tree.args[0], values) ** walk(tree.args[1], values);
    default:
      throw new Error(`unknown operator ${tree.op}`);
  }
}

/*
 * Every node's value, given the inputs the sliders are currently at.
 *
 * `payload.order` is the topological order the build computed, so a single forward pass is
 * enough and the browser never has to know how to sort a graph. `payload.factors` are the unit
 * conversions Pint worked out at build time — the reason a node declared in kW can be computed
 * from a formula that produces watts, and the reason this file needs no unit library at all.
 */
export function evaluatePoint(payload, overrides) {
  const values = {};
  const blocked = new Set();
  for (const name of payload.order) {
    const node = payload.nodes[name];
    if (node.blocked_by) {
      blocked.add(name);
      continue;
    }
    if (Object.prototype.hasOwnProperty.call(overrides, name)) {
      values[name] = overrides[name];
      continue;
    }
    if (node.kind === "input" || node.kind === "measured") {
      values[name] = node.point;
      continue;
    }
    try {
      values[name] = walk(node.ast, values) * (payload.factors[name] ?? 1);
    } catch (error) {
      blocked.add(name);
    }
  }
  return { values, blocked };
}

/*
 * Where a ceiling sits, given the current sliders.
 *
 * Recomputed here rather than read from the export, because the whole point of the sliders is to
 * let a reader find a configuration that clears the ceilings — and a verdict that did not move
 * when they did would be worse than not showing one.
 */
export function ceilingState(payload, name, values) {
  const node = payload.nodes[name];
  const stamped = node.ceiling;
  if (!stamped || values[name] === undefined) return null;
  const value = values[name];
  const limit = stamped.limit;
  const allowed = stamped.allowed;
  let verdict = "ok";
  if (value > limit) verdict = "over";
  else if (value > allowed) verdict = "inside headroom";
  return { value, limit, allowed, verdict, headroom: stamped.headroom, because: stamped.because };
}
