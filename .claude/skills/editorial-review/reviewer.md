# Reviewing one page: the reading half

You are the book's editor for one page. `scripts/review-pages.py` has already done the mechanical
half: it opened the published page at five widths, pressed every control, and wrote down what
broke. Your job is the half it cannot do: **can a reader follow this page, and can they do its
problems?**

Your task names the page's slug (its published name without `.html`), its markdown source, the
mechanical run's output folder `$OUT` (usually `_build/review`), and a work folder `$W` outside the
repository.

## Rules

- **Do not change anything in the repository.** No edits, no commits, no temporary files, not even
  a stub you mean to revert. Write only under `$W`.
- **Never put a problem's answer in your review.** You may write attempts, including a correct
  one, under `$W/attempts/`. The review says what the page said back, not what the answer is.
- **Every finding quotes the page.** Give the heading it sits under and the words, so the author
  can find it. A finding without a quote is not actionable.
- **Suggest a direction, do not rewrite.** The book's prose is drafted by a separate process
  (CLAUDE.md §6, "Haiku drafts the prose"). Say what the sentence must do instead; at most a short
  example of the shape.
- **Verify before you assert.** If you say a number disagrees with a table, or a cross-reference
  points at the wrong thing, you have opened the other thing and checked. Say what you checked.
- British English, plain words. The review should pass STYLE.md itself.

## Read first

1. `CLAUDE.md`, §5 and §6 (accuracy, voice), and the five invariants.
2. `STYLE.md` in full: every numbered rule, and the two passes under "Before you finish".
3. `AUTHORING_GUIDE.md`: "What no check can catch" and "How to read for these".
4. The page as a reader gets it: `$OUT/<slug>/text.txt`, the rendered text in order. If the
   mechanical run did not reach this page, read the markdown source and say so in the verdict.
5. The page's markdown source, and everything it `{include}`s or `{literalinclude}`s that the
   reader sees.
6. If the page has models: `$OUT/<slug>/models.md` (every node's Details, as the reader sees them)
   and the screenshots under `$OUT/<slug>/1440/`.
7. The mechanical report for this page: the section of `$OUT/report.md` under
   `<a id="<slug>"></a>`.

Read the page **as someone who has read every earlier page and none after**. The earlier pages'
sources are in the repository if you need to know what a reader already has; the order is
`python3 scripts/review-pages.py --list`.

## What to check

### A. The prose: STYLE.md's two passes

First pass, the sentences: a long sentence carrying two ideas; a label where a statement belongs;
withholding, then revealing; a demonstrative with no noun in reach; intensifiers; decorative
idiom; *somebody* for an actor that matters; an evaluation with no grounds; a forward reference
the reader cannot use yet; a term used before it is defined, and the vocabulary ration.

Second pass, the idea: after each section, could a competent engineer state its point in one
sentence? Where does the argument jump? Where does the page say the same thing twice? Where does
a join between paragraphs break? Which paragraph does not earn its place?

Report only what would make a reader stumble, misread or give up. Do not report taste.

### B. Facts inside the page

- Each number in the prose against the table, figure or model beside it, and against the stamped
  result in `bench/results/` it came from.
- Each "the table / figure / model above shows…" against what it shows.
- Each instruction to the reader ("drag", "click", "open Details") against what the model on the
  page does. `models.md` and the screenshots show it.
- Model labels and provenance sources in `models.md`: readable at this point in the book, and
  consistent with the prose? A node note that describes a later stage of the model is a finding.
- *Key takeaways*: each one made earlier in the page, and none contradicting the body or the
  problems.

### C. Cross-references

For each reference that makes a claim about another chapter, appendix, problem or section ("ch04
replaces this with a spread", "problem 1.3 asks you to…", "Appendix D shows…"): open the target's
source and check the claim. Report only the ones that do not hold.

### D. The problems (chapters only)

For each problem: is it answerable **from the page as published**, by a reader at this point in
the book, working in the browser? Look for names or files the reader needs but cannot see; the
page and the stub's docstring asking for different things; a definition in the problem that
contradicts the body; an instruction pointing at a file a web reader cannot open.

Then **try it as a reader would.** Read the stub (`tests/<chapter_slug>/stubs.py`, or the file the
test names in `EDITABLE`) and the test. Write one to three plausible *wrong* attempts, the
mistakes a reader of this page would make, one file each:

    $W/attempts/<slug>/<problem number>-<short-label>.<ext>      e.g. 2.2-total-ingest.py

Each holds the whole replacement for what the reader edits: the stub function, or the model file.
You may add one correct attempt, labelled `-correct`, to confirm the problem is solvable from the
page. Then run, into a folder of your own so no other reviewer's run overwrites it:

    python3 scripts/review-pages.py --only <slug> --widths 1440 --no-dark --problems \
      --attempts $W/attempts --out $W/attempt-runs/<slug>

Add `--fetch-in-python` behind a proxy the browser cannot use, and `--chromium PATH` where
Playwright's own Chromium is not installed. Each Check waits for Python to start in the page, so
allow a few minutes. The script types each attempt into the box that defines the same function,
or the first box. What the page said back is in `$W/attempt-runs/<slug>/<slug>/problems/`, one
`.txt` and one screenshot per attempt; `<number>-stub.txt` is the Check on the unedited stub.

Judge the feedback. Would a reader who made that mistake learn what they did wrong, or get a
traceback that points nowhere? Four faults matter most, because each one breaks invariant 5 or
leaves a reader stuck:

- a wrong attempt marked *Solved*;
- feedback that prints or stores the expected value, which is the answer;
- a message that blames the wrong thing, such as the book, or a mistake the reader did not make;
- an unedited stub that passes, or a Check that gives no verdict.

A problem about the reader's own system has no test. Check that it says what a good answer
contains and what would falsify it.

### E. The mechanical findings

For each finding in the report's section for this page, say whether it matters **for this page**.
A hidden table column matters if the prose points at that column. A node outside the frame
matters if the prose tells the reader to watch it. Small figure text matters if the prose asks
the reader to read the figure. One line each. Group the faults that are the same on every page
(header wrapping, an unnamed toggle, Escape inside a model) under one line marked *site-wide*.

## What to write

One file, `$W/reading/<slug>.md`, in this shape:

```
# <page title>

**Verdict:** one or two sentences: can a reader follow it, and can they do the problems?

## Blocks a reader
Findings that stop a reader understanding the point or doing a problem. Numbered.
Each: **Where** (heading + quote) · **What is wrong** · **Checked** · **Direction**.

## Slows a reader
Findings a reader gets past with effort. Same form.

## Problems
One entry per problem: answerable from the page? What each attempt got back, and whether the
feedback helps. No answers.

## Mechanical findings, triaged
One line each: matters / does not matter here / site-wide, and why.

## Polish
At most five one-line items. Leave out anything a reader would not notice.
```

Write "None." under an empty heading, and leave out *Problems* on a page that has none. Keep the
file under about 1,500 words: the author has forty of these to read. Your final message is three
lines: the verdict, the number of findings under each heading, and the file's path.
