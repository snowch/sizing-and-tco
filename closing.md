---
title: "Your own model"
short_title: "Your own model"
---

(your-own-model)=
# Your own model

This book teaches from the bottom up. Each idea rests on the one before it: you cannot grow a
figure until you know what a rate is.

Building a model of your own system works the other way. You start from the answer you have been
asked for and work back to the numbers it needs.

[The model builder](https://snowch.github.io/sizing-and-tco-builder/) is a companion tool that
walks you through that order, from question to inputs, one step at a time.

## What it asks, and where the book teaches it

The builder prompts you for the same decisions the chapters cover. Here is where the book answers
each one.

| The builder asks | Where the book teaches it |
|---|---|
| What answer you have been asked for, and in what unit | [ch01](#point-estimates), [ch02](#what-a-workload-is) |
| What decision the answer feeds | [ch01](#point-estimates), [ch21](#a-tco-for-finance) |
| What horizon the answer is for | [ch02](#what-a-workload-is), [ch04](#peak-mean-and-growth) |
| For each number: given, measured, or worked out from others | [ch02](#what-a-workload-is), [ch09](#capacity) |
| Who decides each input, and where it came from | [ch02](#what-a-workload-is), [ch03](#where-the-numbers-come-from) |
| Where the arithmetic stops working, and what margin to keep | [ch06](#queueing-and-the-knee), [ch11](#headroom-and-failure-domains) |
| How sure you are of each input outside your control | [ch04](#peak-mean-and-growth), [ch13](#monte-carlo) |
| Which input to measure first | [ch19](#which-input-is-the-answer) |
| A second case to compare | [ch21](#a-tco-for-finance), [ch22](#comparing-two-tcos) |

It asks one question at a time. The refining steps come only after every number the answer needs
has a place.

## What you can rely on

**It writes this book's model file.** What it produces is the YAML
[Appendix A](#appendix-a-dsl-reference) describes. The toolkit, the model viewer and the build's
checks read what you built. You can move on to editing the file by hand.

**It never fills in a number.** An input you do not have yet is *not yet measured*, and so is
everything worked out from it. That is how the book treats an unknown number.

**It is held to this book's rules.** The book publishes a conformance suite in `conformance/` in
the repository. That suite shows what the book's toolkit says about a set of model files. It is
checked on every change to the book. The builder may not release while any case gets a different
answer from the book's toolkit.

**Your own measurements go beside your model.** A measured constant you took yourself goes in a
`results/` folder next to the model file. It is held to the disclosure rules
[Appendix A](#appendix-a-dsl-reference) describes.

## Check what it wrote

The builder is a separate project with its own releases. The first line of every model file names
the format version it was written for. If that differs from the version this book's toolkit reads,
the toolkit refuses the file and says which versions they are.

Before you rely on a model the builder wrote, ask the book's own toolkit about it. From a copy of
the book's repository, run the command below. It reports every rule the file breaks, or says it is
fine.

```bash
python3 scripts/verify-models.py path/to/your/model.yaml
```

## Where to use it

The problems in this book that ask about your own system have no test, because only you have the
numbers. Problem 2.5 asks you to write your own workload down. Problem 12.3 asks for your own model
as far as it goes. The builder is a place to work them.

A model you can defend is one where every number says where it came from. The builder will not let
you leave one out.
