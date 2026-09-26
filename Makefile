# Sizing and TCO — the commands the book tells you to run.
#
# Three kinds of number, and the split runs through everything here:
#
#   corpus  — a codec or an encoder over a declared body of data. Deterministic, so `make measure`
#             runs anywhere and CI re-derives every one of them on every push.
#   rig     — a throughput or a latency, on the declared reference machine. `make measure-rig`
#             refuses to run anywhere else rather than quietly producing a number about a laptop.
#   model   — what a model file says, worked out by `make models` and stamped like a measurement.

PYTHON ?= python3
SHELL  := /bin/bash

.DEFAULT_GOAL := help

.PHONY: help
help:  ## Show this list
	@grep -hE '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
	  | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

# -- setup ---------------------------------------------------------------------------------

.PHONY: install
install:  ## Install everything the book and the toolkit need
	$(PYTHON) -m pip install -r requirements.txt -r requirements-dev.txt
	npm install -g "mystmd@$$(node -p "require('./package.json').devDependencies.mystmd")"

.PHONY: machine
machine:  ## Say what this computer is, and whether it may take a rig measurement
	$(PYTHON) -m bench.stamp

# -- measuring -----------------------------------------------------------------------------

.PHONY: measure
measure:  ## Re-take every corpus constant. Runs anywhere; CI re-derives these too.
	$(PYTHON) -m bench.run_corpus

.PHONY: measure-rig
measure-rig:  ## Re-take every rig figure. ON THE REFERENCE MACHINE ONLY.
	@$(PYTHON) -c 'import sys; sys.path.insert(0, "."); from bench.stamp import classify_machine; \
	  k = classify_machine(); sys.exit(0) if k == "rig" else (print( \
	  "Refusing to run: this is a %r machine, not the rig.\n" \
	  "A throughput measured on the wrong computer is indistinguishable from a real one once it\n" \
	  "is a number in a table. Declare the reference machine in rig/machine.yml (ch03)." % k, \
	  file=sys.stderr) or sys.exit(1))'
	@echo "No rig runners are written yet — see NEXT_STEPS.md."

# -- the models ----------------------------------------------------------------------------

.PHONY: models
models:  ## Evaluate and sample every model, and stamp what each one said
	$(PYTHON) -m bench.run_models
	$(PYTHON) -m bench.run_uncertainty
	$(PYTHON) -m bench.run_curves
	@echo
	@echo "Now re-render and commit:"
	@echo "  $(PYTHON) scripts/render-figures.py && git add bench/results chapters/_generated chapters/_figures"

.PHONY: information
information:  ## What knowing each uncertain input exactly would buy (ch19)
	$(PYTHON) -m bench.run_information

.PHONY: comparison
comparison:  ## Subtract two quotes for one workload, future by future (ch22)
	$(PYTHON) -m bench.run_comparison

.PHONY: postmortem
postmortem:  ## Attribute the running example's own failures (ch23)
	$(PYTHON) -m bench.run_postmortem

.PHONY: verify
verify:  ## Units, provenance, ceilings and shape, for every model
	$(PYTHON) scripts/verify-models.py

.PHONY: figures
figures:  ## Re-render every table and diagram from committed results
	$(PYTHON) scripts/render-figures.py

.PHONY: icons
icons:  ## Redraw the favicon and home-screen icons into public/
	$(PYTHON) scripts/build-icons.py

.PHONY: viewers
viewers:  ## Build the interactive model pages into _build/viewers/
	$(PYTHON) scripts/build-viewers.py

.PHONY: futures
futures:  ## Build ch01's draw-one-future page into _build/futures/
	$(PYTHON) scripts/build-futures.py

# -- the book ------------------------------------------------------------------------------

.PHONY: book
book:  ## Build the site and serve it at localhost:3000 (re-run to pick up an edit)
	$(PYTHON) scripts/build-stamp.py
	myst build --strict
	$(PYTHON) scripts/build-site.py --out _build/html
	@echo
	@echo '  http://localhost:3000 — this is the published site, not a preview of one.'
	@echo '  An edit needs "make book" again; the whole build takes about three seconds.'
	@echo
	@cd _build/html && $(PYTHON) -m http.server 3000

.PHONY: review
review:  ## Walk every published page in a browser at five widths, press everything, and report
	@echo '  ARGS passes options, for instance ARGS="--base http://localhost:3000/ --only point-estimates".'
	@echo '  The report is the mechanical half of a review, and says at its top what it cannot see.'
	$(PYTHON) scripts/review-pages.py $(ARGS)

.PHONY: chapter
chapter:  ## Regenerate any missing chapter stubs (never touches written prose)
	$(PYTHON) scripts/new-chapter.py --all

.PHONY: test
test:  ## Run the test suite (the reader's problems are deselected, as in CI)
	$(PYTHON) -m pytest tests/ -q -m "not problem"

.PHONY: problems
problems:  ## Run the chapter problems. They fail until you solve them; that is the point.
	$(PYTHON) -m pytest tests/ -m "problem"

.PHONY: check
check:  ## Everything CI runs
	./scripts/ci-check.sh

.PHONY: clean
clean:  ## Remove build output; committed results and figures are kept
	rm -rf _build models/_out
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
