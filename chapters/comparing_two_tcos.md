---
title: "Comparing two TCOs"
short_title: "ch22 Comparing two TCOs"
---

(comparing-two-tcos)=
# ch22 · Comparing two TCOs

## The question

Two quotes for the same workload, each with an interval on it. Which is cheaper, and how often
would that turn out to be wrong?

[ch21](#a-tco-for-finance) put two designs side by side and called the difference between them
a decision. This chapter is about the difference itself. Two totals with intervals on them
overlap, and a reader shown the overlap concludes that nothing can be said. Something can. The
two designs face the same future, and a difference taken future by future is far narrower than
the totals it came from.

It is also the chapter for a comparison somebody else built. A vendor's comparison arrives with
one column already won. The last section says what such a comparison has to show before you
believe it, and each item points at the chapter that says why.

## The material

### Two quotes for one workload

The incumbent is the design the plan was built on: the platform the team already runs, on the
hosts [ch12](#the-sizing-model) sized and [ch18](#the-five-year-model) priced. The challenger is
a second quote for the same workload. Its hosts are denser and cost more each, it licenses per
host rather than per core, its support rate is higher, and moving to it costs something the
incumbent does not pay.

Both are scenarios of the running example, and both hold every line of the quote exactly.

```{include} _generated/comparing-two-tcos-quotes.md
```

Read the marks first. Almost every line on both sides is a vendor's claim, whichever vendor it
is. The model gave the host price a band because nobody had quoted one
([ch03](#where-the-numbers-come-from)). A quote is a number, so the band goes and the number
stays. What is left uncertain is what no quote fixes: the workload, its growth, the electricity,
the people.

Two lines are not the vendor's. The host count is the model's own sizing rule, applied to each
host at the point estimate, so both designs are sized to the same margins by the same rule
([ch12](#the-sizing-model)). The cost of the move is the team's estimate, marked as an
assumption, because the challenger did not quote it and the incumbent has nothing to move.

Here is the challenger's quote as the toolkit holds it. A comparison starts from a file like
this one, and the file is where the reasons for its numbers live.

```{literalinclude} ../models/web_service/scenarios/challenger.yaml
:language: yaml
:start-at: scenario:
```

And here it is running. Drag *hosts in the fleet* up by one and watch the five-year total pass
the incumbent's.

```{iframe} /models/web_service-challenger.html
:width: 100%
The challenger's quote, with every input on a slider. The incumbent's is linked under every
table on this page.
```

### Every line on both sides

The challenger licenses per host. The incumbent's quote has no such line, and until this chapter
the model had no such node. A line that one side does not have is a cost that side never pays,
and a comparison with a line missing from one column is won by omission.

So the model carries two lines it did not need before, and both are zero on the incumbent's
side. The zero is declared, with a source, rather than left out:

```{literalinclude} ../models/web_service/model.yaml
:language: yaml
:start-at: licence_per_host:
:end-before: annual_licences:
```

The second is the cost of the move. It is the line an incumbent's comparison never shows and a
challenger's never includes:

```{literalinclude} ../models/web_service/model.yaml
:language: yaml
:start-at: migration_cost:
:end-before: tco:
```

With both lines on both sides, the two totals contain the same things and can be subtracted line
by line:

```{include} _generated/comparing-two-tcos-lines.md
```

Read down the last column. The challenger wins on licences, on energy and on network, and loses
on the move. The hosts cost about the same in total, because fewer of them cost more each.
Support is a share of capital on both quotes and the capital is about equal, so it barely moves.

The largest line in either total is people, and it does not appear in the difference at all.
Both designs are run by the same engineers at the same cost, so the line is the same on both
sides and cancels. That is the general rule. **What both designs pay alike drops out of the
comparison, however large it is.** A comparison is about the lines that differ. The total is
only where they are added up.

The last row is the whole comparison at the point estimate. The challenger is cheaper, by a
sliver of either total. That is the number a spreadsheet stops at.

### Subtract futures, not intervals

Both totals have intervals, and the two intervals are nearly the same interval.

That is not a coincidence. Most of what either total is uncertain about is shared. The
electricity price, the building's overhead, what an engineer costs and how many are needed are
the same inputs on both sides, and the same draw of each reaches both designs. When the
electricity price comes out high, it comes out high for both fleets. When an engineer costs more,
both totals rise together.

So the difference between the totals is far less uncertain than either total. The toolkit takes
it the only honest way: the same future, both fleets, subtract. Both scenarios pin the same
inputs and share a seed, so every input neither quote fixes is drawn once and reaches both
designs, and the toolkit checks that before it subtracts anything.

```{image} _figures/comparing-two-tcos-difference.svg
:alt: The difference between the two five-year totals, future by future, with the tie marked and the share of futures either side of it
:width: 100%
```

The interval on the difference is a fraction of the interval on either total. The challenger is
cheaper in most of the futures the model thinks plausible, and dearer in a large minority of
them. Both of those are the answer. A comparison that reports only the first is the one the
challenger would show you. A comparison that reports neither is the one a spreadsheet shows you.

```{include} _generated/comparing-two-tcos-paired.md
```

The third and fourth rows are what goes wrong when the futures are not shared. Draw each design
in a future of its own and subtract, and the interval on the difference is many times wider,
because the shared uncertainty is counted twice, once with each sign. Subtract the ends of the
two intervals, which is what two totals side by side invite a reader to do, and it is wider
still. Neither is a statement about the decision. Both are statements about how the arithmetic
was done.

[ch14](#correlation-and-convergence) made the same point from the other side. Two inputs that
move together, drawn independently, understate the width of a total. Two totals that move
together, subtracted independently, overstate the width of their difference. It is one fact about
shared uncertainty, and which way it cuts depends on which side of the subtraction it sits.

Problem 22.1 is that subtraction, and its test can tell which way you did it.

### Cheaper at what risk

A total is the price of a fleet that works. Two fleets that cope different amounts of the time
are not the same purchase at two prices, so a comparison carries the ceilings as well as the
money.

```{include} _generated/comparing-two-tcos-ceilings.md
```

They cope about equally often, and that is by construction. Both were sized by the same rule to
the same margins, so both are over the knee at the busy hour in about the same share of futures.
A comparison that sized one design to the daily mean and the other to the busy hour would show a
cheaper fleet that copes less often, and would not say so.

Two rows differ, in opposite directions. The challenger's hosts spend less of their capacity
agreeing with each other, because there are fewer of them
([ch07](#when-adding-servers-stops-helping)), so it is over the coordination ceiling less often.
And losing one host of a small fleet costs more of the fleet than losing one of a large one, so
the challenger is over the one-host-down ceiling slightly more often
([ch11](#headroom-and-failure-domains)). Neither shows up in the money. Both are part of what
is being bought.

### What would flip it

The difference is small, so the next question is what would reverse it. For each line the
challenger could argue about, and for each input both designs share, the toolkit finds the value
at which the two totals tie, with everything else at its point estimate.

```{include} _generated/comparing-two-tcos-break-even.md
```

Read the challenger's lines first. Every one of them ties within a few per cent of the quote.
The move can cost a little more than the team estimated, the host price and the licence can each
rise a little, and the fleet can grow by less than one host before the ordering reverses. Carry
that last row into the meeting. How many hosts a workload needs on hardware nobody has run it on
is the kind of number [ch03](#where-the-numbers-come-from) says to distrust, and this comparison
turns on a fraction of one.

The row about people is a different kind of claim. Both quotes hold the engineers equal, because
a vendor's figure for how many people *you* will need is a claim about your organisation and
not about their product. If the challenger cost a little more of an engineer's time, the totals
would tie. If it claimed to save some, the comparison would rest on that claim and on nothing
else, since the people line is larger than every line the quotes differ on. A comparison that
turns on a headcount the vendor supplied has a thumb on the scale, and this model refuses to
take that number from a quote.

The shared inputs are next. Cheaper electricity favours the incumbent, because the challenger's
advantage on energy shrinks with the price, and the tie sits inside the middle eighty per cent
of what the price could be. So does the tie on the network price. The building's overhead would
have to be better than the model thinks plausible before it flipped anything. And growth cannot
flip it at all. Both fleets were bought before the growth arrived, so the input that dominates
every other tornado in this book does not move the difference by a dollar.

```{image} _figures/comparing-two-tcos-tornado.svg
:alt: Which shared input moves the difference between the two totals, and how many do not move it at all
:width: 100%
```

The chart is a few bars and a count. Everything the two designs pay alike has a bar of no length,
and that includes the growth, the busy hour, the salary and the head count. The comparison is
sensitive to the two prices that scale with the host count and to almost nothing else. That is what
a comparison between two quotes for one workload is usually sensitive to, and it is rarely what the
argument in the room is about.

Problem 22.2 finds one of those break-evens by hand.

### What a competitive comparison has to show

A comparison somebody else built arrives with one column already won. This is what it has to
contain before you believe it, where the book covers each item, and how the comparison is tilted
when the item is missing.

| What to look for | Where it is taught | How the comparison is tilted without it |
|---|---|---|
| The workload it was sized for, stated, and both designs sized by the same rule to the same margins | [ch02](#what-a-workload-is), [ch12](#the-sizing-model) | one design sized to the daily mean and the other to the busy hour |
| The same horizon and the same refresh convention on both sides | [ch15](#capex-opex-and-lifecycle) | a three-year quote against a five-year one |
| Every line on both sides, with a declared zero where a quote has no such line | this chapter | hardware only on one side, fully loaded on the other |
| Whose number each line is, marked on both sides, the presenter's own included | [ch03](#where-the-numbers-come-from) | list price for the other side, the negotiated price for yours |
| The cost of the move, on the side that has to move | this chapter | the incumbent never shows it; the challenger never includes it |
| The difference as an interval over shared futures, and the share of futures in which it flips | this chapter | two intervals side by side, which say nothing, or one number, which says too much |
| Each design's ceilings, as how often it fails to cope | [ch11](#headroom-and-failure-domains), [ch21](#a-tco-for-finance) | cheaper because it copes less often |
| The break-evens, and whether each lies inside a range anybody would defend | this chapter, [ch19](#which-input-is-the-answer) | a comparison that turns on an input nobody measured |
| The people line held equal unless there is evidence, and marked as a claim if not | this chapter | a headcount the vendor supplied |
| Unit costs on the same denominator and the same period | [ch17](#unit-economics) | per terabyte-month against per terabyte-year, the busy hour against the mean |
| What was left out, named | [ch20](#the-missing-node) | a line neither total has, which favours whichever side it would have hurt |
| Cash by year, undiscounted, so that finance can apply its own rate | [ch15](#capex-opex-and-lifecycle), [ch21](#a-tco-for-finance) | a discount rate chosen to flatter the side that spends later |
| A file that re-runs, so the reader can change an input and watch | [the introduction](#preface) | a bar chart, with nothing in it to change |

Check the first item twice. Two quotes that were sized differently are not two
prices for the same thing, and no amount of care over the lines below it repairs that.

:::{note} Key takeaways
- **A comparison is about the lines that differ.** What both designs pay alike drops out of the
  difference however large it is, so every line goes on both sides, with a declared zero where a
  quote has no such line.
- **Subtract futures, not intervals.** The two totals share most of their uncertainty, so the
  difference taken future by future is far narrower than either total. Subtracting independent
  draws, or the ends of two intervals, says how the arithmetic was done and nothing about the
  decision.
- **A total is the price of a fleet that works.** Two fleets that cope different amounts of the time
  are not the same purchase at two prices, so the comparison carries the ceilings as well as the
  money.
- **Find what would flip it.** The break-evens say how far each line and each shared input can move
  before the ordering reverses. Usually that is a few per cent on the prices that scale with the
  host count, and nothing on the inputs the argument in the room is about.
- **A comparison somebody else built arrives with one column already won.** The checklist says what
  it has to show, and the item to check twice is whether both designs were sized by the same rule to
  the same margins.
:::

## What this cannot tell you

**What either vendor would charge.** Both quotes are held exactly. A quote is a number,
and this chapter takes it as one. What you would pay after negotiation is a different number on
both sides, and a discount that is the same percentage on both is not the same money, because
the two capital lines differ.

**What the move will cost.** The migration line is the team's estimate, marked as an
assumption, and it is the kind of number that is usually low. The break-even says how wrong it
can be before the ordering flips. Nothing here says how wrong it is.

**Anything about performance.** Both quotes share one CPU time per request, because it is the
same software on different hosts. A quote for a different platform would carry a different
service demand, and that number is a rig measurement ([ch03](#where-the-numbers-come-from))
which no vendor's benchmark replaces. The host-count break-even is the hedge. It says how much
slower than the spec sheet the challenger's hosts could be before the comparison reverses, and on
this pair the answer is not much.

**What the structure omits.** Both totals come from one model, so a line neither quote has is a
line neither total has ([ch20](#the-missing-node)). Rack space, the second environment, the cost
of running both platforms during the move, the exit cost at the end of the horizon and the price
at renewal are in neither column. A missing line favours whichever side it would have hurt, and
the comparison cannot say which side that is.

**Whether the futures are shared.** They are here by construction, because both designs
are scenarios of one model. Two quotes built as two models and joined by figures in documents
lose that ([ch18](#the-five-year-model)), and the interval on their difference comes back as
wide as the independent one above.

**Which side you are on.** A comparison built by the party that wins it is still a comparison,
and the checklist above is the same whoever built it. What the checklist cannot supply is the
number a prospect is entitled to and rarely gets: the share of futures in which the presenter's
own design loses.

## Problems

Three, in `tests/comparing_two_tcos/`. The first two have tests. The last does not, and says why.

**22.1 — Subtract futures, not intervals.**
Evaluate both quotes and subtract the totals sample by sample. Return the interval on the
difference and the share of futures in which the challenger is cheaper. The test can tell whether
you subtracted two independent draws instead, because that answer is several times wider.

```bash
python3 -m pytest tests/comparing_two_tcos/test_problem_1_paired_difference.py
```

**22.2 — How expensive can the move be?**
Take the incumbent's fleet as an input. For an incumbent of that many hosts, find the one-off
cost of moving at which the two totals tie at the point estimate. Use the model's own point
evaluation rather than arithmetic of your own. The break-even table prints the tie for the fleet
the incumbent runs. The test grades that fleet and two the page does not print. An answer that
moves when the fleet does cannot have been copied off the page. The total is linear in the cost
of the move, so two evaluations fix the line.

```bash
python3 -m pytest tests/comparing_two_tcos/test_problem_2_break_even.py
```

**22.3 — A comparison somebody showed you.** No test: the comparison is theirs, and nothing here
has seen it.

Take a comparison that was put in front of you, by a vendor or by a colleague, and hold it
against the checklist above. Write down which items it has and which it lacks. Then repair the
one that matters most and see what it does to the ordering: put the missing line on the side
that lacked it, size both designs by the same rule, or hold the people line equal.

A good answer names the items the comparison failed and says what the difference did once the
worst of them was fixed. It would be falsified by a comparison that passed every item and whose
ordering survived every repair. That happens, and then you know the comparison was sound. If the
ordering flipped on the first repair, you have found what the comparison was for.

## Where to go next

Kahn and Marshall @kahnmarshall1953 set out the trick this chapter rests on, in the paper that
first treated Monte Carlo as a problem in experimental design: sample two things you mean to
compare on the same draws, so that what they share cancels. Wright and Ramsay @wrightramsay1979
show when it fails. The shared draws have to reach both designs the same way, and a design that
responds to a draw in the opposite direction gets a wider difference, not a narrower one.

[ch23](#what-the-model-got-wrong) is what happens after one of the two quotes is chosen, and the
future that arrives is one of the ones in which it was the wrong choice.
