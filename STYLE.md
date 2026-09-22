# STYLE.md — how to make the writing clearer

Rewrite technical prose into clear, plain English without dumbing down the technical content.
The goal is to make the reader understand the idea on the first reading.

Every page is edited against this list: the chapters, the appendices, the part pages and the
introduction. CLAUDE.md §6 sets the voice; this is the checklist that gets a page there. Where
rule 6 below meets the vocabulary ration in CLAUDE.md §6, the ration wins: a statistics term is
defined where a model first needs it, not before.

Rules 1 to 16 were written before the chapters. Rules 17 to 22 were added after two outside
reviews of the finished book found the same faults on page after page, which is evidence about
the rules rather than about the pages: a fault that recurs under a rule is a fault the rule did
not name. Each of the new rules shows a sentence the book printed and the sentence the rule
produces. The two checklists at the end run every rule: the first pass over the sentences,
the second over whether the idea arrived.

## 1. Shorten long sentences

One idea per sentence, about twenty words. If a sentence contains several separate ideas, split
it into two or three sentences.

Prefer:

> The model records where each number came from. It also records how certain that number is.

over:

> The model records where each number came from and how certain that number is, so the reader
> can understand the basis for the result.

Three shapes hide a second sentence inside a first, and the book's longest sentences are made of
them:

- a pair of dashes in the middle, holding a clause the reader has to carry across the gap;
- a clause after *rather than*, *which is* or a second *and* that starts a new thought;
- a colon followed by a list of clauses rather than a list of things.

Before, from ch05:

> Nobody has declared one, so the model holds it as an assumption whose source says what would
> replace it, rather than as a measured constant with nothing behind it.

After:

> Nobody has declared one. So the model holds it as an assumption, and its source says what
> measurement would replace it. It does not pose as a measured constant, because no measurement
> is behind it.

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

Three habits make the reader work the point out instead of receiving it. CLAUDE.md §6 names them
under *Say the thing. Do not perform it.*; this is the checklist entry.

- **A label where a statement belongs.** *That is the whole motivation* names the paragraph
  instead of saying anything. Write what the motivation is.
- **Withholding, then revealing.** *The third part is the one that decides whether anybody
  should act on the answer* sets a small puzzle and makes the reader wait. Lead with the point:
  *This book teaches the third part: how to find which input your answer rests on.* The same
  shape hides in *the one that*, *the ones to carry* and *the one people do not compute*.
  Before, from ch10: *Neither is small here, and the second is the one people do not compute.*
  After: *Neither is small here, and people do not compute the second.*
- **A roundabout purpose.** *The line is there so that a reader who does not believe this table
  has somewhere to go* is *It is there so you can check the table instead of trusting it.*

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

And the phrases this book actually reaches for:

- "it is worth making again" → "again:" and then make it
- "it is worth noting that" → cut it, and state the thing
- "the whole of the discipline" → "the discipline"
- "the fact that" → "that"
- "a great many" → "many"

Keep technical terms when they are genuinely useful, but explain them in plain English.

## 6. Define technical terms immediately

When introducing a technical term, give the plain-English meaning first.

For example:

> Sizing means working out how much hardware a particular workload needs.

Then use "sizing" normally afterwards.

Do the same for TCO, distribution, percentile, correlation, convergence, and so on — at the
point the book first needs each one. A term the ration does not admit is not defined and not
used: say the plain thing instead.

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

The reader should be able to skim the headings and understand the argument. A heading names
what its section contains, in a few words. It is not a sentence, not a label with a colon on
the end, and not a question unless the section answers it: *Running it*, not *To run this model
yourself:*.

## 8. Use lists when the reader is being given several things

If a sentence contains a list of three or more items, consider using bullets.

For example:

> You need to know:
>
> - where the number came from;
> - how uncertain it is; and
> - how much the answer changes if it changes.

This is easier to scan than putting everything into one sentence.

Every item in a list, and every half of a pair, takes the same shape: all sentences or all
phrases, each starting the same way. *The model includes inputs, derived nodes, and it has
ceilings* has to be read twice; *inputs, derived nodes and ceilings* does not.

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

Short contrasts are easier to remember. A contrast is also where a very short sentence earns its
place (rule 17): *Not a verdict. A probability.*

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
- turn uncertainty into certainty;
- type a figure into the prose. Every number on a page comes from a stamped result (CLAUDE.md,
  invariant 1), so a rewrite never adds one, however much clearer *the fleet costs $5M* would
  look than the sentence it replaces.

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

Use passive voice when it is genuinely clearer, but do not use it by default. The test is
whether the reader can tell who did it. A passive whose actor is obvious and uninteresting is
fine: *`because` is required*. A passive that hides an actor the reader needs is not.

Before, from ch01:

> It happens because of what gets added to the file, and the toolkit works the rest out.

After:

> It happens when you add a measured constant or a ceiling to the file, and the toolkit works
> the rest out.

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

## 17. A very short sentence lands a point; it does not label one

The book uses sentences of two or three words, and the reviews found dozens. Some are its best
device: *It compounds it.* *So divide.* *Not a verdict. A probability.* Each lands a point the
sentence before it set up. Others are a heading in disguise, a label for what comes next: *Two
columns.* *Three marks.* *Then the shared inputs.* *This chapter.*

The test: cover the sentence after it. If the short sentence still says something, keep it. If
it only points at what follows, make it a sentence that says what follows.

Before, from ch21:

> Two columns. The left one buys what the model recommends at the point estimate.

After:

> The table has two columns. The left one buys what the model recommends at the point estimate.

Before, from ch20:

> **The model is the wrong shape.** This chapter. Not in the interval, not in a scenario, not
> anywhere, because nothing in the file knows the term is missing.

After:

> **The model is the wrong shape.** This is the error this chapter is about. It appears in no
> interval and no scenario, because nothing in the file knows the term is missing.

## 18. A demonstrative needs its noun

*That*, *this*, *it*, *all of that* and *the same* point back at something. If the reader has to
look back more than one sentence to find what, put the noun in the sentence. A sentence that is
nothing but a demonstrative and an adjective, *It is structural*, *This one is real*, is usually
a label for the sentence after it, and rule 17 applies as well.

Before, from ch01:

> Each belongs to one implementation at one version, each has a measurement error, and none is a
> fact about the world. A chain of multiplications built on them inherits all of that.

After:

> … A chain of multiplications built on them inherits their errors, their version, and their
> standing as measurements rather than facts.

Before, from ch04:

> That is not a quirk of these numbers. It is structural. A growth rate is the one input that is
> *raised to a power*; everything else is multiplied.

After:

> That is not a quirk of these numbers. A growth rate is the one input that is *raised to a
> power*; everything else is multiplied.

Before, from ch21:

> The failure mode of the first two is optical. This one is real. Half the futures cost more, and
> nothing has been said about what happens in them.

After:

> The first two fail in how they look. This one fails in what happens: half the futures cost
> more, and nothing has been said about them.

## 19. Cut intensifiers and hedges

*Actually*, *exactly*, *genuinely*, *really*, *entirely*, *quite*, *simply*. Almost none survives
a second reading, and the book's prose has *actually* and *exactly* on dozens of lines each. Keep
*exactly* where exactness is the claim, *exactly one function*, and cut it where it is emphasis:
*for exactly this reason* is *for this reason*.

Before, from ch04:

> what is a five-year growth rate actually a claim about?

After:

> what is a five-year growth rate a claim about?

Before, from Appendix C:

> the percentiles are something a person can actually state

After:

> the percentiles are something a person can state

## 20. An idiom must be the plain way to say it

British idiom is the book's register, and a figure of speech that is the shortest way to say a
thing stays: *a thumb on the scale*, *two decisions wearing one name*. One that decorates a
plain statement goes: *right up until* is *until*; *does most of the damage* is *moves the
answer most*; *worth carrying around* is *worth remembering*, and then rule 22 asks why. A
reader whose English is not British, or not their first, meets each of these as a small puzzle
in the middle of a sentence about something else.

Before, from ch02:

> That sounds like pedantry, right up until somebody sizes a retention store from a rate.

After:

> That sounds like pedantry until somebody sizes a retention store from a rate.

Before, from ch04:

> Growth does most of the damage in this book.

After:

> Growth moves the answer more than any other input in this book.

## 21. *Somebody* names an actor whose identity is the point

*Somebody*, *nobody* and *anybody* are how the book says that a decision was taken and the taker
is not on record, which is often the point: *a decision somebody took, and a decision has no
distribution*. Used for any actor at all, they become a tic, and a reviewer reads them as
evasion. Use one when who did it is unknown, or is the point. Where the actor is you, the
toolkit, the model, finance or a vendor, name them. Not twice in one sentence unless the
repetition is the device: *a figure nobody can repeat is a figure nobody can check* is the
device.

Before, from Appendix D:

> The distinction is invisible until somebody in finance does the reconciling, which is why the
> conversion appears in the table above rather than inside somebody's head.

After:

> The distinction is invisible until finance does the reconciling, which is why the conversion
> appears in the table above rather than in the modeller's head.

## 22. An evaluation says why

*Is worth*, *is the honest form*, *is the whole of*, *earns its place*, *is the one to carry*
judge a thing without saying on what grounds. Either give the grounds, or cut the sentence and
let the thing speak for itself. The grounds are usually in the next sentence already, and the
fix is to join them.

Before, from ch03:

> Writing that down is the whole of the discipline. The claim is recorded as a claim, and what is
> doubtful about it is recorded beside it.

After:

> Writing that down is the discipline: the claim is recorded as a claim, and what is doubtful
> about it is recorded beside it.

Before, from Appendix C:

> Correlated inputs push the same way at the same time, so the cancellation does not happen. That
> mechanism is worth carrying around.

After:

> Correlated inputs push the same way at the same time, so the cancellation does not happen.
> Keep that mechanism in mind: it is why leaving each of these correlations undeclared made the
> interval narrower.

## Before you finish: two passes

The first pass cleans the sentences. The second asks whether the idea arrived. They are separate
because they cost different things: the first is a scan, and a page can be run through it in
minutes; the second is reading, and it is slower because judgement is slow.

Keeping them apart is the point. For a long time this section ran twelve of the rules above and
called itself the whole list, and the ten it left out were, every one of them, the ones that ask
whether the reader understood — the example beside the abstract idea, the cause said rather than
implied, the paragraph that holds one thing. What was left was the half a person can run without
reading for sense. So pages came out clean and stayed abstract: short sentences, no intensifiers,
plain words, and nothing a reader could take hold of. A checklist that omits the slow half is a
checklist for the fast half, whatever it says at the top.

## 23. A turn of phrase is rationed like everything else

Rules 17 to 22 each ban a habit. This one bans a *density*. *Somebody's mood on a Tuesday*, *a
purchase order signed on Friday*, *the arithmetic is a morning's work* — each is a good line, and
three of them within a page make a reader parse the style instead of the meaning. A reader who is
enjoying the writing has stopped reading the argument.

One or two to a section. The test is not whether the phrase is good; it is whether the reader has
met one recently. Where two do the same job, keep the one nearer the point it is making, and
where two are the same *shape* — two arbitrary weekdays, two homely units of time — cut one
whatever their quality.

Before, from ch01, one section apart:

> If the growth rate's spread was somebody's mood on a Tuesday, the range inherits that…
>
> A narrow one on a purchase order signed on Friday might be.

After: the second stays, because the purchase order is the decision the paragraph is about. The
first becomes *a guess nobody checked*.

## 24. A forward reference is a debt the reader cannot call in

*[ch13] measures it*, *[ch19] is that subject*, *[Appendix E] shows the finished thing* each tell
a reader the answer is somewhere they are not. A few are a map. A dozen is being told, over and
over, that this page is not where the thing is explained — and most chapters are read on their
own, as a web page, by somebody who will not turn to ch19 today.

So: one to a paragraph, none in a sentence already doing two jobs, and where two point at the
same thing, put them in one sentence rather than two. *Where to go next* exists to carry the rest.
A chapter that has said what it has to say does not need to keep promising.

Before, from ch01:

> The smallest and the largest are a poor summary of the spread, because a handful of extreme
> answers set them. The chart below shows where the answers piled up. Every later table in this
> book reports a narrower band than this column, and [ch13](#monte-carlo) says which band and why.

After — three jobs become two, and the reference goes, because ch13 is named two paragraphs later
with something substantial to say:

> The smallest and the largest are a poor summary of the spread: a handful of extreme answers set
> them. The chart below shows where the answers piled up.

### First pass: the sentences

A scan. Each line names the rule.

- [ ] Any sentence much over twenty words: split it (1).
- [ ] Any sentence of three words or fewer: does it land a point, or label the next sentence? (17)
- [ ] A label, a withheld point, a roundabout purpose: state the thing (3).
- [ ] *That*, *this*, *it*, *all of that*: is the noun within one sentence? (18)
- [ ] *Actually*, *exactly*, *genuinely*, *really*, *entirely*: cut (19).
- [ ] A figure of speech: is it the plain way to say it? (20)
- [ ] *Somebody*, *nobody*: is who did it unknown, or the point? (21)
- [ ] *Is worth*, *is the whole of*, *earns its place*: where are the grounds? (22)
- [ ] A passive: can the reader tell who did it? (14)
- [ ] A long word where a short one says it: swap it (5).
- [ ] A sentence built to sound careful rather than to be read: straighten it (11).
- [ ] Items in a list: the same shape? (8)
- [ ] A term the ration does not admit: gone, and the plain thing said (6).
- [ ] A number typed into the prose: never (12).
- [ ] Two forward references in one sentence, or one in a sentence already busy: thin them (24).

### Second pass: the idea

Read the page through, once, for sense. These are questions, not searches, and a page can pass
every line above and fail every line here.

- [ ] An abstract idea with no small example beside it: give it one (4).
- [ ] A paragraph that answers more than one question: split it (2).
- [ ] A consequence the reader is left to work out: say it (9).
- [ ] A distinction worth remembering: is it set against what it is not? (10)
- [ ] The principle of the section: does that sentence stand up on its own, quoted out of the
      page? (15)
- [ ] The headings, read alone: do they carry the argument? (7)
- [ ] An idea arriving before the reader has a reason to want it: move it (13).
- [ ] Anything made simple enough to be wrong: put the difficulty back (16).
- [ ] Count the turns of phrase in each section. More than two: cut to the best (23).
- [ ] Count the forward references on the page. Is the reader being told the answer is
      elsewhere more often than they are being given one? (24)

## Final test

Before returning the rewrite, ask:

> Could a technically competent engineer understand this paragraph on the first reading without
> having to reread the sentence?

If not, simplify the sentence or split the paragraph.

The objective is not to make the subject easy. The objective is to make the writing stop getting
in the way of the subject.
