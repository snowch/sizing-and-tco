# STYLE.md — how to make the writing clearer

Rewrite technical prose into clear, plain English without dumbing down the technical content.
The goal is to make the reader understand the idea on the first reading.

Every page is edited against this list. CLAUDE.md §6 sets the voice; this is the checklist that
gets a page there. Where rule 6 below meets the vocabulary ration in CLAUDE.md §6, the ration
wins: a statistics term is defined where a model first needs it, not before.

## 1. Shorten long sentences

If a sentence contains several separate ideas, split it into two or three sentences.

Prefer:

> The model records where each number came from. It also records how certain that number is.

over:

> The model records where each number came from and how certain that number is, so the reader
> can understand the basis for the result.

Do not be afraid of short sentences.

## 2. Put one main idea in each paragraph

A paragraph should normally answer one question or explain one idea.

If a paragraph moves from:

- what the model is,
- to why files are used,
- to how units work,
- to how the build system works,

split it into separate paragraphs.

## 3. State the important idea directly

Do not make the reader infer the point.

For example, instead of:

> One consequence of those rules shows up on the pages.

say:

> If a required number has not been measured, the model does not invent one.

Put the important conclusion first.

## 4. Use concrete examples

When explaining an abstract idea, give a small example.

For example:

> data per second × seconds = data

This is easier to understand than a paragraph explaining dimensional consistency.

## 5. Prefer ordinary words

Replace unnecessarily abstract or formal words with familiar ones.

Examples:

- "utilise" → "use"
- "commence" → "start"
- "subsequently" → "later"
- "quantities" → "numbers", when "numbers" is accurate
- "ascertain" → "find out"
- "constitutes" → "is"
- "demonstrates" → "shows"
- "in order to" → "to"

Keep technical terms when they are genuinely useful, but explain them in plain English.

## 6. Define technical terms immediately

When introducing a technical term, give the plain-English meaning first.

For example:

> Sizing means working out how much hardware a particular workload needs.

Then use "sizing" normally afterwards.

Do the same for TCO, distribution, percentile, correlation, convergence, and so on — at the
point the book first needs each one.

## 7. Use headings to expose the structure

Turn implicit structure into explicit headings.

For example:

- What this book is about
- How the model works
- Why use a file instead of a spreadsheet?
- Every number can be checked
- Unknown numbers stay unknown
- Who this book is for
- What you need

The reader should be able to skim the headings and understand the argument.

## 8. Use lists when the reader is being given several things

If a sentence contains a list of three or more items, consider using bullets.

For example:

> You need to know:
>
> - where the number came from;
> - how uncertain it is; and
> - how much the answer changes if it changes.

This is easier to scan than putting everything into one sentence.

## 9. Explain cause and effect explicitly

Do not make the reader work out why something matters.

Instead of:

> A spreadsheet cell holds a value and nothing about it.

follow immediately with the consequences:

> It does not tell you the unit. It does not tell you where the number came from. It does not
> tell you how certain the number is.

Then explain why those omissions matter.

## 10. Use contrast to make important ideas memorable

When there is a useful distinction, state it explicitly.

For example:

> A spreadsheet may accept an incorrect calculation without complaining. This model rejects it.

Or:

> The system does not know the number yet, so the model does not invent one.

Short contrasts are easier to remember.

## 11. Avoid unnecessary rhetorical complexity

Do not use phrases that sound sophisticated but make the reader work harder.

For example, prefer:

> How much should I trust the answer?

over:

> What degree of confidence should reasonably be attached to the resulting estimate?

The technical meaning can remain precise without making the sentence complicated.

## 12. Preserve technical precision

Clarity does not mean removing important qualifications.

Do not:

- remove important caveats;
- replace precise technical concepts with vague language;
- simplify away assumptions;
- change the meaning of formulas;
- invent facts;
- turn uncertainty into certainty.

The aim is: simpler language, not simpler thinking.

## 13. Make the argument progressive

Introduce ideas in the order the reader needs them.

A good sequence is:

1. What problem are we solving?
2. Why is the problem harder than it first appears?
3. What approach does the book use?
4. Why does that approach matter?
5. How does the reader use it?
6. What do they need to know?
7. What can they do next?

Do not introduce concepts before the reader has a reason to care about them.

## 14. Prefer "you" and active voice

Prefer:

> You can check where the number came from.

over:

> The provenance of the number can be verified.

Prefer:

> The build rejects the model.

over:

> The model is rejected by the build.

Use passive voice when it is genuinely clearer, but do not use it by default.

## 15. Make important sentences stand on their own

Important principles should work as standalone sentences.

For example:

> If a required number has not been measured, the model does not invent one.

This is stronger and clearer than burying the same idea inside a longer paragraph.

## 16. Do not overdo the simplification

The writing should still sound like an experienced engineer explaining something to another
engineer.

Avoid:

- childish language;
- excessive conversational filler;
- fake enthusiasm;
- marketing language;
- unnecessary metaphors;
- repeating the same point several times.

The desired style is: calm, precise, direct, technically serious, but easy to read.

## Final test

Before returning the rewrite, ask:

> Could a technically competent engineer understand this paragraph on the first reading without
> having to reread the sentence?

If not, simplify the sentence or split the paragraph.

The objective is not to make the subject easy. The objective is to make the writing stop getting
in the way of the subject.
