#!/usr/bin/env bash
# Exactly what CI runs. Run it before pushing.
#
# CI invokes this same script, so the two cannot drift. Nothing here needs the reference machine:
# `rig` measurements are refused on any other computer and the figures that would come from them
# render as "not measured yet" instead.
#
# Nothing here needs the network either. The book is parsed by MyST and rendered by this
# repository, and only the parse was ever MyST's — so what this builds is the site that deploys,
# rather than a preview of one that could only be built by a runner with a template registry in
# reach. What it cannot check is what only a reader's browser can answer: whether Python starts
# in their tab, and what a page looks like.
set -euo pipefail

cd "$(dirname "$0")/.."

PY_PATHS=(bench sizing scripts tests)

echo "== ruff lint =="
python3 -m ruff check "${PY_PATHS[@]}"

echo "== ruff format =="
python3 -m ruff format --check "${PY_PATHS[@]}"

echo "== which commit this build is =="
# Not one of the committed figures: it names the commit being built, so it is written here rather
# than checked. The pages include it, so MyST needs it to exist before it parses anything.
python3 scripts/build-stamp.py

echo "== myst content build (strict) =="
# Before pytest: the page tests render every chapter from this parse and skip without one, and
# a check that CI never ran is not a check. The build itself is unchanged.
if ! command -v myst >/dev/null 2>&1; then
  if [ -n "${CI:-}" ]; then
    # A check that silently skips itself is not a check. CI installs myst, so its absence here
    # means the workflow is misconfigured; fail loudly rather than publish a broken link.
    echo "ERROR: myst is not installed and CI must not skip the book build." >&2
    exit 1
  fi
  echo "  myst not installed; skipping the content build, and every check that reads the parse."
  echo "  install with: npm install -g \"mystmd@$(node -p "require('./package.json').devDependencies.mystmd")\""
  myst_built=0
  log=""
else

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
  myst_built=1
fi

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
# or a ceiling in it is a conditional model, and a conditional model must declare its headroom.
python3 scripts/verify-models.py

echo "== the running example, as each chapter leaves it =="
# The book builds this model a few nodes at a time, so the intermediate models have to be real:
# they are derived from the finished file by bench/stages.py and held to the same rules above.
# tests/test_stages.py is where the invariants live — every node introduced by some chapter, no
# stage taking a node away, and the change from a definitional model to a conditional one happening in the
# chapter that claims it.
python3 -m bench.stages --check

echo "== the corpus constants still say what the book prints =="
# The one class of measurement CI can re-derive rather than trust: a codec is deterministic, so
# pointing the same code at the same bytes must give the same answer here as it did on the
# machine that stamped it. A change to a generator, an encoder or the interpreter fails here
# instead of quietly restating the book's figures.
python3 -m bench.run_corpus --check

echo "== the models still compute what the book publishes =="
python3 -m bench.run_models --check

echo "== the sampler still behaves the way ch13 says it does =="
python3 -m bench.run_uncertainty --check

echo "== what a measurement would buy is still what the book says it would =="
# ch18's ceiling on every measurement anybody could commission. Re-derived rather than trusted,
# for the same reason as everything else here: it is a claim about what this book's models say.
python3 -m bench.run_information --check

echo "== the two quotes still differ by what the book says they differ by =="
# ch22: both quotes on the same draws, subtracted future by future, with the break-evens that
# say what would flip the ordering. Re-derived rather than trusted, like everything else here.
python3 -m bench.run_comparison --check

echo "== the post-mortem still attributes what the book says it attributes =="
# ch23, and the half of it that matters: the same method on a model with a known hole in it,
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

echo "== the site icon is what the script draws =="
# Its proportions come from a stamped result, so a model change moves it. Same contract as the
# figures: regenerate and commit, rather than let the repository and the site disagree.
python3 scripts/build-icons.py --check

echo "== the interactive pages assemble =="
# Into the site's own tree, where deploy.yml puts them, because every model table's *Source* line
# links to one. Built anywhere else and nothing checks that those links resolve.
python3 scripts/build-viewers.py --out _build/static/models > /dev/null
echo "  OK"

echo "== the one-future-at-a-time page assembles =="
# Into the site's own tree for the same reason: ch01 embeds it by a `/futures/...` URL, and
# nothing else checks that the URL resolves to a file.
python3 scripts/build-futures.py --out _build/static/futures > /dev/null
echo "  OK"

rm -f "$log"

if [ "$myst_built" = 1 ]; then
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

echo "== the book renders =="
# This is the published site, not a preview of it: the deploy runs this same script against the
# same parse. The renderer raises on a node type it does not handle rather than dropping the
# content, so rendering every page on every push is what stops a new directive from silently
# disappearing from the site.
python3 scripts/build-site.py --out _build/static > /dev/null
python3 scripts/check-built-links.py _build/static
echo "  OK"

echo "== every link still resolves under the base path =="
# The check above runs at the site root, where a URL missing the base path is indistinguishable
# from one that has it. This book publishes at /sizing-and-tco/, and a root-relative `src` that
# nothing rebased 404s there and nowhere else -- which is why it can only be caught after the
# site is assembled *under* a base path. It has taken the deploy down twice: once when the
# playground was added, once when `/futures/` was, and on both days this script was green.
#
# The base here is a stand-in, not the real one. What matters is that it is non-empty.
rm -rf _build/based
mkdir -p _build/based/book
cp -r _build/static/. _build/based/book/
python3 scripts/build-icons.py --inject _build/based/book --base /book/ > /dev/null
python3 scripts/check-built-links.py _build/based/book /book
echo "  OK"

echo "== the book installs for offline use =="
# After every page and viewer is in the tree, because the worker lists them all and
# a list that names a file the build did not produce fails the install in the reader's browser.
python3 scripts/build-offline.py --inject _build/static --base /
fi

echo
echo "All checks passed."
