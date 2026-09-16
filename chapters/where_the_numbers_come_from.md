---
title: "Where the numbers come from [DRAFT]"
short_title: "ch03 Where the numbers come from"
---

(where-the-numbers-come-from)=
# ch03 · Where the numbers come from [DRAFT]

:::{note} Chapter header
:class: dropdown

| | |
|---|---|
| **Prerequisites** | [ch01](#reading-a-model) |
| **What it produces** | Every corpus constant in the book, with its corpus, codec and standard error; and the provenance census of both models. |
| **Built from** | `logs-line-bytes`, `metrics-sample-bytes`, `traces-span-bytes`, `storage-object-compression` |
:::

## The question

What is the difference between a number you measured, a number you were told and a number you decided?

[To write: one paragraph. State the question this chapter answers and why the previous chapter
leaves it open. No summary of what is to come — the reader can see the headings.]

## The material

[To write: the body. Short sections. Code is quoted from the working tree with
`{literalinclude}` and text anchors, never pasted; model files are quoted the same way. See
AUTHORING_GUIDE.md.]

## What the model says

[To write: `{include}` the generated fragments declared in `bench/figures.py`. No number is
ever typed here. A figure that depends on a constant nobody has measured renders as *not yet
measured* on its own — the state propagates down the graph, and nothing has to be marked by
hand.]

## What this cannot tell you

[To write. **Mandatory.** What the model, the measurement or the method could not show, and what
was done instead. For a chapter with a model in it this must name what the model's *structure*
omits, because that is the error no amount of sampling can see. This chapter is not finished
while this section is missing.]

## Problems

[To write: each problem is a stub under `tests/where_the_numbers_come_from/` with a test that passes only when
it is solved. There is no answer key — the test is the answer key, and it cannot be wrong about
whether it passes.]

## Where to go next

[To write: primary sources via `@citekey` against `references.bib`. Textbooks may appear here as
further reading and nowhere else — never as a source for this chapter's content.]
