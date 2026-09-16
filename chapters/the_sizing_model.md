---
title: "The sizing model [DRAFT]"
short_title: "ch12 The sizing model"
---

(the-sizing-model)=
# ch12 · The sizing model [DRAFT]

:::{note} Chapter header
:class: dropdown

| | |
|---|---|
| **Prerequisites** | [ch09](#capacity), [ch10](#bandwidth-and-the-binding-constraint), [ch11](#headroom-and-failure-domains) |
| **What it produces** | The storage model end to end, and the node count it recommends. |
| **Built from** | `storage_cluster-reference`, `storage_cluster-sized_for_growth` |
:::

## The question

What does the whole chain produce, and how much of it would you defend?

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

[To write: each problem is a stub under `tests/the_sizing_model/` with a test that passes only when
it is solved. There is no answer key — the test is the answer key, and it cannot be wrong about
whether it passes.]

## Where to go next

[To write: primary sources via `@citekey` against `references.bib`. Textbooks may appear here as
further reading and nowhere else — never as a source for this chapter's content.]
