---
name: editorial-review
description: Review the published book, or some of its pages, as its editor. Runs the browser pass (make review), then one reader per page for the prose, the facts, the cross-references and the problems, and merges both into one report. Use when asked for an editorial review, or whether a page is easy to follow and its problems can be done.
---

# Editorial review of *Sizing and TCO*

A review has two halves, and `make check` does neither.

- **The mechanical half** is `scripts/review-pages.py` (`make review`). It opens every published
  page in Chromium at five widths and in the dark theme, presses every control and model, and
  writes down what broke. Its report says at the top what it cannot see.
- **The reading half** is this skill. It covers what needs a reader: whether each sentence lands,
  whether each number matches the table beside it, and whether each cross-reference delivers what
  it promises. It also asks whether each problem can be done from the page, and whether a reader
  who gets it wrong learns why. `reviewer.md`, beside this file, is the brief for one page.

Scope is the whole book unless the request names pages. Give pages by published name (the slug),
as `python3 scripts/review-pages.py --list` prints them. That list is `myst.yml`'s order, which is
the reading order: the preface, the part pages, every chapter and every appendix.

## 1. Choose a work folder outside the repository

Call it `$W`: the session's scratchpad if there is one, otherwise a temporary directory. Attempts
at the problems go there, and a correct attempt is an answer, which CLAUDE.md forbids anywhere in
the repository. The reviews and the merged report go there too: they are working documents, not
pages.

## 2. Run the mechanical half

```bash
python3 -m pip install -r requirements-review.txt       # Playwright, once
make review ARGS="--problems"                           # or: --only <slug> ... --problems
```

It walks the published site. Pass `--base http://localhost:3000/` to review the site `make book`
serves instead, which is how to review a change before it deploys. Behind a proxy the browser
cannot use, add `--fetch-in-python`. Where Playwright's own Chromium is not installed, add
`--chromium PATH` or set `$CHROMIUM`. A run over the whole book takes a long time, so run it in
the background.

It writes `_build/review/` (`$OUT` below):

- `report.md`, page by page, and `findings.json`, the same findings as data;
- `<slug>/text.txt`, the page's rendered text in order;
- `<slug>/models.md`, every model node's Details as a reader sees them;
- `<slug>/<width>/`, the screenshots;
- `<slug>/problems/`, what each Check said.

Its severities are about the page, not the reader's understanding: *blocks* (a reader cannot go
on), *hides* (the content is there, and a reader cannot see or reach it) and *look*. Deciding which
of them matter is part of the reading half.

## 3. Read every page: one reviewer each

Give each page to its own subagent. Its prompt is `reviewer.md` plus four facts: the slug, the
markdown source (second column of `--list`), `$OUT`, and `$W`. One page per agent keeps each
review a first reading, by someone who has read the earlier pages and not the later ones. Run as
many at once as the session allows, in batches in reading order.

The reviewers run the problem Checks again with their own attempts. Each writes to
`$W/attempt-runs/<slug>`, never to `$OUT`, so concurrent runs cannot overwrite one another.

When a review comes back, read it before merging it:

- **every finding quotes the page** and says what was checked;
- **no answer appears in it**, not even in an attempt's feedback;
- **its facts hold**: re-check any finding you will present as a cause of faults on other pages,
  against the code or the live page.

A review that fails one of these goes back to its reviewer with a note.

## 4. Merge into one report

Write `$W/review.md`, in this order:

1. **A table of pages**, in reading order: findings under *Blocks a reader* and *Slows a reader*,
   the problems' state, and the mechanical *hides* and *look* counts after triage.
2. **Fix first.** Faults that recur across pages or live in the toolkit, the site or a shared
   test helper, where one fix clears many findings. Group them by kind, and name every page each
   one reaches. The kinds the last review found are the place to start looking:
   - Checks that break, or give no verdict;
   - tests that store or print the expected value;
   - tests that pass a wrong answer;
   - feedback that blames the wrong thing;
   - problems that cannot be done from the page;
   - bugs in the toolkit or the site found while checking a page's claims;
   - a prose habit from STYLE.md that recurs on many pages.

   Mark each item you re-checked yourself; the rest stand on their reviewer's word.
3. **Page by page**, each page's review as its reviewer wrote it.
4. **What neither half covered**: the offline install, which the browser pass blocks; browsers
   other than Chromium; and, when the site was not rebuilt first, any difference between the
   branch and what is deployed.

The merged report is a deliverable with an audience. If the session can publish an artifact,
publish it as a page, and tell the user the counts and the *Fix first* items in the reply.

## 5. After the review

Fixing the findings is a separate job, and CLAUDE.md governs it: the invariants, and §6's rule
that reader-facing prose is drafted by Haiku from a list of facts and checked by you for facts
only. What worked last time:

1. **Fix the *Fix first* items in code first**, since page fixes build on them. Where a fix edits
   `sizing/mc.py`, `evaluate.py`, `units.py` or `dsl.py`, run `make models`.
2. **Per page**, write fact briefs for each finding, have Haiku draft the words, check the drafts
   against the briefs and the repository, and apply them. Then read the whole page once more:
   that is where two drafts repeat each other.
3. **Figures last**, once the prose around them has settled.
4. **Run `./scripts/ci-check.sh`**, then `make review` again. Compare the blocks, hides and look
   counts before and after, and put them in the final report.
