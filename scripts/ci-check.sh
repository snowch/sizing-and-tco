#!/usr/bin/env bash
# Exactly what CI runs. Run it before pushing.
#
# CI invokes this same script, so the two cannot drift. Nothing here needs the reference machine:
# `rig` measurements are refused on any other computer and the figures that would come from them
# render as "not measured yet" instead.
set -euo pipefail

cd "$(dirname "$0")/.."

PY_PATHS=(bench sizing scripts tests)

echo "== ruff lint =="
python3 -m ruff check "${PY_PATHS[@]}"

echo "== ruff format =="
python3 -m ruff format --check "${PY_PATHS[@]}"

echo "== pytest =="
# `python3 -m pytest`, not bare `pytest`: the module form runs the tests under the interpreter
# that has the project's dependencies. A standalone pytest (pipx, uv tool) has its own isolated
# environment and cannot import `sizing`.
#
# -m "not problem" deselects the chapter problems. They are the reader's work and they fail until
# solved, which is the whole design — a suite that went red for an unsolved exercise would train
# everyone to ignore it. What CI does check is that each problem is *answerable*: the unmarked
# scaffolding tests beside them assert that the oracle is real and that the cases are not all the
# same case.
python3 -m pytest tests/ -q -m "not problem"

echo "== every model typechecks, and says where its numbers came from =="
# Units, provenance, measured constants, ceilings, graph shape — and the rule that makes the
# book's central distinction enforceable rather than rhetorical: a model with a measured constant
# or a ceiling in it is a sizing model, and a sizing model must declare its headroom.
python3 scripts/verify-models.py

echo "== the corpus constants still say what the book prints =="
# The one class of measurement CI can re-derive rather than trust: a codec is deterministic, so
# pointing the same code at the same bytes must give the same answer here as it did on the
# machine that stamped it. A change to a generator, an encoder or the interpreter fails here
# instead of quietly restating the book's figures.
python3 -m bench.run_corpus --check

echo "== the models still compute what the book publishes =="
python3 -m bench.run_models --check

echo "== the sampler still behaves the way ch14 says it does =="
python3 -m bench.run_uncertainty --check

echo "== what a measurement would buy is still what the book says it would =="
# ch19's ceiling on every measurement anybody could commission. Re-derived rather than trusted,
# for the same reason as everything else here: it is a claim about what this book's models say.
python3 -m bench.run_information --check

echo "== the post-mortem still attributes what the book says it attributes =="
# ch22, and the half of it that matters: the same method on a model with a known hole in it,
# which has to keep confidently blaming the inputs that are present.
python3 -m bench.run_postmortem --check

echo "== the curves Part II argues about still have the shape it claims =="
# A shape asserted in prose is a claim; a shape swept out of the model the chapter is about is
# evidence, and this is what stops the two drifting apart.
python3 -m bench.run_curves --check

echo "== result stamps and no numbers typed into prose =="
python3 scripts/verify-numbers.py

echo "== figures up to date =="
python3 scripts/render-figures.py --check

echo "== the interactive pages assemble =="
python3 scripts/build-viewers.py > /dev/null
echo "  OK"

echo "== myst content build (strict) =="
if ! command -v myst >/dev/null 2>&1; then
  if [ -n "${CI:-}" ]; then
    # A check that silently skips itself is not a check. CI installs myst, so its absence here
    # means the workflow is misconfigured; fail loudly rather than publish a broken link.
    echo "ERROR: myst is not installed and CI must not skip the book build." >&2
    exit 1
  fi
  echo "  myst not installed; skipping locally."
  echo "  install with: npm install -g \"mystmd@$(node -p "require('./package.json').devDependencies.mystmd")\""
  echo
  echo "All checks passed."
  exit 0
fi

# Content build WITHOUT --html. This matters: with --html, MyST downloads the site theme before it
# parses anything, so where the template registry is unreachable the build aborts having validated
# nothing at all. Without it, every page is parsed first and only the final site assembly fails —
# so the log still says whether the content is sound.
log=$(mktemp)
myst build --strict > "$log" 2>&1 || true

# Two conditions, both required. The page count proves parsing actually happened, so a build that
# died early can never be mistaken for a clean one; the warning check is the verdict.
if ! grep -qE "Built [0-9]+ pages" "$log"; then
  echo "ERROR: myst did not parse any pages — the build failed before validating content." >&2
  tail -25 "$log" >&2
  rm -f "$log"
  exit 1
fi
if grep -qE "⚠|⛔" "$log"; then
  echo "ERROR: content warnings (broken reference, citation or literalinclude anchor):" >&2
  grep -E "⚠|⛔" "$log" >&2
  rm -f "$log"
  exit 1
fi
echo "  $(grep -oE 'Built [0-9]+ pages' "$log" | tail -1), no warnings"
rm -f "$log"

echo "== no price has become an equation =="
# This book writes money as $4,150,036 and intervals as "$318,062 to $611,522". Two dollar signs
# on a line are a LaTeX span to MyST, so with dollar-maths on it sets the "to" as a pair of
# variables — and nothing warns, because the markup is valid. myst.yml turns the extension off
# (the book has no maths in it); this is the check that the setting is still doing its job, which
# an assertion about the config file cannot be: the key was in the wrong place once already.
# A check that cannot find the thing it inspects is a check that always passes.
if ! compgen -G "_build/site/content/*.json" > /dev/null; then
  echo "ERROR: no parsed content to inspect — the build wrote nothing to _build/site/content." >&2
  exit 1
fi
if grep -rq '"type":"inlineMath"' _build/site/content/ 2>/dev/null; then
  echo "ERROR: a figure is being parsed as maths. Currency between two dollar signs, almost" >&2
  echo "certainly — check project.settings.parser.dollarmath in myst.yml." >&2
  grep -rho '"type":"inlineMath","value":"[^"]*"' _build/site/content/ | sort -u | head -5 >&2
  exit 1
fi
echo "  no currency parsed as LaTeX"

echo "== the PDF renderer sees every page =="
# The mdast-to-HTML renderer is the one part of the pipeline that is not MyST's, and it raises on
# a node type it does not handle rather than dropping content. Running it over every page on every
# push is what stops a new directive from silently disappearing out of the PDF. No Chromium here
# on purpose: assembling the HTML is what touches every page, and printing it is the cheap part CI
# does not need to repeat.
python3 scripts/build-pdf.py --no-myst --html-only --out _build/pdf-check/book.pdf > /dev/null
echo "  every page rendered"

echo "== myst themed HTML build =="
# Needs the MyST template registry and GitHub. Mandatory in CI; locally a blocked host says
# nothing about the book, since the content build above already validated everything authored.
if [ -n "${CI:-}" ]; then
  myst build --html --strict
  echo "  themed build OK"
elif myst build --html --strict > /dev/null 2>&1; then
  echo "  themed build OK"
else
  echo "  SKIPPED: cannot reach the MyST template registry from this environment."
fi

echo
echo "All checks passed."
