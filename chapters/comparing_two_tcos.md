---
title: "Comparing two TCOs"
short_title: "ch22 Comparing two TCOs"
---

(comparing-two-tcos)=
# ch22 · Comparing two TCOs

:::{note}
**Draft.** Content drafted. This chapter is undergoing final review and polish.
:::

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

Read the marks in the quotes table first. Almost every line on both sides is marked as a
vendor's claim, whichever vendor it is. The three kinds of claim are the ones
[ch03](#where-the-numbers-come-from) introduced. Everywhere else in the book the model gives the
host price a wide band, because a host is a configuration rather than a commodity. A quote names
one configuration and one price for it. So the band goes and the quoted number stays: every line
of each quote is pinned. What is left uncertain is what no quote fixes: the workload, its growth,
the electricity, the people.

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

### Every line on both sides

The challenger licenses per host. The incumbent's quote has no such line. A line that one side
does not have is a cost that side never pays, and a comparison with a line missing from one
column is won by omission.

You have met both lines before. The full web service model carries a per-host licence and a
one-off cost of moving, and [ch21](#a-tco-for-finance)'s provenance table lists both, with their
sources. On the single design earlier chapters priced, both lines were zero and moved nothing.
This chapter is the first in which either carries a figure. On the incumbent's side both are
still zero. The zero is declared, with a source, rather than left out:

```{literalinclude} ../models/web_service/model.yaml
:language: yaml
:start-at: licence_per_host:
:end-before: annual_licences:
```

The second line is the cost of the move. Neither side's own figures carry it:

```{literalinclude} ../models/web_service/model.yaml
:language: yaml
:start-at: migration_cost:
:end-before: tco:
```

With both lines on both sides, the two totals contain the same things and can be subtracted line
by line:

```{include} _generated/comparing-two-tcos-lines.md
```

Read down the last column of the lines table. The challenger wins on licences, on energy and on
network, and loses on the move. The hosts cost about the same in total, because fewer of them
cost more each. Support is a share of capital on both quotes, and the challenger's rate is
higher. Yet the challenger's capital, hosts plus network, is lower than the incumbent's, mostly
because its *Network* line is much smaller. A higher rate on less capital leaves the *Support*
line barely changed.

The largest line in either total is people, and it does not appear in the difference at all.
Both designs are run by the same engineers at the same cost, so the line is the same on both
sides and cancels. That is the general rule. **What both designs pay alike drops out of the
comparison, however large it is.** A comparison is about the lines that differ. The total is
only where they are added up.

The last row is the whole comparison at the point estimate. The challenger is cheaper, by a
sliver of either total. That is the number a spreadsheet stops at.

The challenger's quote runs below as a model you can change. Drag *hosts in the fleet* up by one
host and watch the five-year total pass the incumbent's figure in the last row of the lines table
above.

```{iframe} /models/web_service-challenger.html
:width: 100%
The challenger's quote, running. An input has a slider when the model file gives it a range:
*hosts in the fleet*, *licence per host* and *one-off cost of moving to this design* among them.
The other quoted prices, including host price and support rate, are pinned by the scenario and
have no slider. Each line's Details show the note and source from the model file, written for
the design the plan was built on. The challenger's own reasons are in its scenario file, quoted
in the previous section. The incumbent's quote has a model of its own, linked under the quotes
table and the ceilings table.
```

### Subtract futures, not intervals

Each total has an interval of its own. The totals table below shows both: each five-year total
at the point estimate and as a middle nine in ten. The two intervals are nearly the same.

That is not a coincidence. Most of what either total is uncertain about is shared. The
electricity price, the building's overhead, what an engineer costs and how many are needed are
the same inputs on both sides, and the same draw of each reaches both designs. When the
electricity price comes out high, it comes out high for both fleets. When an engineer costs more,
both totals rise together.

So the difference between the totals is far less uncertain than either total. The toolkit takes
it one future at a time: the same future, both fleets, subtract. Both scenarios pin the same
inputs and share a seed. So every input neither quote fixes is drawn once, and the same draw
reaches both designs. Before it subtracts anything, the toolkit checks that each shared input
came out identical on both sides, and it refuses to subtract if one did not.

```{image} _figures/comparing-two-tcos-difference.svg
:alt: The difference between the two five-year totals, future by future, with the tie marked and the share of futures either side of it
:width: 100%
```

The interval on the difference is a fraction of the interval on either total. The challenger is
cheaper in most of the futures the model thinks plausible, and dearer in a large minority of
them. Both of those shares are the answer. A comparison that reports only the share in which the
challenger wins is the one the challenger's vendor would show you. A spreadsheet reports neither
share. It shows one difference, at the point estimate: the first row of the table below.

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

One row differs clearly: *utilisation, counting coordination*. The challenger is over that
ceiling much less often, because it has fewer hosts and they spend less of their capacity
agreeing with each other ([ch07](#when-adding-servers-stops-helping)).

A mechanism pulls the other way on *utilisation with one host down*: losing one host of a small
fleet removes a larger share of the fleet than losing one host of a large fleet
([ch11](#headroom-and-failure-domains)). On this pair the effect is small. The row barely
differs, by less than the working-set and busy-hour rows that the paragraph above calls about
equal. The challenger's fleet starts with more cores in total than the incumbent's, so after
losing its larger share it is left with about as many cores as the incumbent. You can check this
from the quotes table: cores per host times hosts in the fleet. Neither difference shows up in
the money. Both are part of what is being bought.

### What would flip it

The difference is small, so the next question is what would reverse it. For each line the
challenger could argue about, and for each input both designs share, the toolkit finds the value
at which the two totals tie, with everything else at its point estimate.

```{include} _generated/comparing-two-tcos-break-even.md
```

Read the first four rows first: the lines on the challenger's side. Each ties within a few per
cent of the figure the comparison uses. Two of the four are the vendor's quote: the host price
and the licence per host. Two are assumptions: the cost of the move is the team's estimate, and
the host count is the model's sizing rule. The *Whose* column marks which. The move can cost a
little more than the team estimated, the host price and the licence can each rise a little, and
the fleet can grow by less than one host before the ordering reverses. Take the *hosts in the
fleet* row into the meeting. The challenger's host count comes from the sizing rule applied to
two things: its spec sheet, and the CPU time per request. The CPU time per request belongs on a
rig, and it has not been measured on either design's hosts
([ch03](#where-the-numbers-come-from)). The comparison turns on a fraction of one host.

The row about people is a different kind of claim. Both quotes hold the engineers equal, because
a vendor's figure for how many people *you* will need is a claim about your organisation and
not about their product. If the challenger cost a little more of an engineer's time, the totals
would tie. If it claimed to save some, the comparison would rest on that claim and on nothing
else, since the people line is larger than every line the quotes differ on. A comparison that
turns on a headcount the vendor supplied has a thumb on the scale, and this model refuses to
take that number from a quote.

The shared inputs are next. Cheaper electricity favours the incumbent, because the challenger's
advantage on energy shrinks with the price. The tie sits inside the middle eighty per cent of
what the price could be. The tie on the network price per host is inside its middle eighty per
cent too. The building's overhead, the PUE, would have to be better than every value the model
draws for it before it flipped anything. Growth cannot flip the comparison at all, because it
reaches neither total. The host count is a decision each quote pins, and the cost chain starts
there, so nothing upstream of the fleet reaches the money. [ch19](#which-input-is-the-answer)
found the same thing for the five-year total: growth is not on its tornado at all. Growth still
moves how often each fleet copes, which is the ceilings table's business.

```{image} _figures/comparing-two-tcos-tornado.svg
:alt: Which shared input moves the difference between the two totals, and how many do not move it at all
:width: 100%
```

The chart has three bars and a count of inputs with no bar. The three bars are the shared inputs
that reach the lines the quotes differ on: the network price per host, charged per host; the
electricity price and the PUE, which together set the energy line. Growth, the busy hour and the CPU
time per request reach neither total because the fleet is pinned, as the paragraph above explains.
The lines the quotes argue about (host price, licences, support rate) are pinned by the quotes and
have no bar on this chart; the break-even table shows where they appear. The salary and the head
count reach both totals equally through the people line, which cancels. So on this pair the
difference is sensitive to the quoted lines and to three shared inputs, and to nothing else.

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
| The cost of the move, on the side that has to move | this chapter | the challenger's vendor does not quote it, because the buyer pays for it; a plan built on the incumbent has nothing to move |
| The difference as an interval over shared futures, and the share of futures in which it flips | this chapter | two intervals side by side, which say nothing, or one number, which says too much |
| Each design's ceilings, as how often it fails to cope | [ch11](#headroom-and-failure-domains), [ch21](#a-tco-for-finance) | cheaper because it copes less often |
| The break-evens, and whether each lies inside a range anybody would defend | this chapter, [ch19](#which-input-is-the-answer) | a comparison that turns on an input nobody measured |
| The people line held equal unless there is evidence, and marked as a claim if not | this chapter | a headcount the vendor supplied |
| Unit costs on the same denominator and the same period | [ch17](#unit-economics) | per terabyte-month against per terabyte-year, the busy hour against the mean |
| What was left out, named | [ch20](#the-missing-node) | a line neither total has, which favours whichever side it would have hurt |
| Capital, yearly running cost, one-off move cost and horizon, undiscounted, to let finance place them in years and apply its own rate | [ch15](#capex-opex-and-lifecycle), [ch21](#a-tco-for-finance) | a discount rate chosen to flatter the side that spends later |
| A file that re-runs, so the reader can change an input and watch | [the introduction](#preface) | a bar chart, with nothing in it to change |

Check the first item twice. Two quotes that were sized differently are not two
prices for the same thing, and no amount of care over the lines below it repairs that.

## What this cannot tell you

**What either vendor would charge.** Both quotes are held exactly. A quote is a number,
and this chapter takes it as one. What you would pay after negotiation is a different number on
both sides, and a discount that is the same percentage on both is not the same money, because
the two capital lines differ.

**What the move will cost.** The migration line is the team's estimate, marked as an
assumption. No quote, invoice or measurement stands behind it, and nothing in the model checks
it. The break-even says how wrong it can be before the ordering flips. Nothing here says how
wrong it is.

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
and the checklist above is the same whoever built it. What the checklist cannot supply is one
number: the share of futures in which the presenter's own design loses. That share is how often
the choice turns out wrong, which is the risk the buyer takes on. Only a model of both designs
over shared futures produces it, so the presenter has to run one and show the result. A
checklist held against a finished document cannot.

## Key takeaways

:::{div}
:class: takeaways

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
- **Find what would flip it.** The break-evens say how far each line and each shared input can
  move before the ordering reverses. On this pair, each line on the challenger's side ties
  within a few per cent of the figure the comparison uses. Growth and the people line move
  nothing: growth reaches neither total, and the people line is the same on both sides.
- **A comparison somebody else built arrives with one column already won.** The checklist says what
  it has to show, and the item to check twice is whether both designs were sized by the same rule to
  the same margins.
:::

## Problems

Three, in `tests/comparing_two_tcos/`. The first two have tests. The last does not, and says why.

**22.1 — Subtract futures, not intervals.**
The test evaluates both quotes on the same draws and hands you the two five-year totals, one
entry per future. Subtract them sample by sample. Return the interval on the difference and the
share of futures in which the challenger is cheaper. The test runs your function twice: once on
every future, whose answer the paired table above prints, and once on a subset of the same
futures, whose answer the page does not print. So a figure copied from the table does not pass.

When an answer is wrong, the test names the mistake:

- two independent draws subtracted (much wider);
- the opposite ends of the two intervals (much wider);
- one total's percentile minus the other's, each on its own (narrower);
- the subtraction the wrong way round (incumbent minus challenger).

```bash
python3 -m pytest tests/comparing_two_tcos/test_problem_1_paired_difference.py -m problem
```

**22.2 — How expensive can the move be?**
The test hands you the difference between the two totals at the point estimate, as a function of
the one-off cost of moving. Find the cost at which the difference is zero. The break-even table
prints the tie for the fleet the incumbent runs. The test grades that fleet and two the page does
not print, with a function for each. An answer that moves when the fleet does cannot have been
copied off the page. The total is linear in the cost of the move, so two evaluations fix the
line.

```bash
python3 -m pytest tests/comparing_two_tcos/test_problem_2_break_even.py -m problem
```

**22.3 — A comparison somebody showed you.** No test: the comparison is theirs, and nothing here
has seen it.

Take a comparison that was put in front of you, by a vendor or by a colleague, and hold it
against the checklist above. Write down which items it has and which it lacks. Then repair the
one that matters most and see what it does to the ordering: put the missing line on the side
that lacked it, size both designs by the same rule, or hold the people line equal.

A good answer names the items the comparison failed, says which repair you judged to matter most
and why, and says what the difference did once that repair was made. That judgement is falsified
if a repair you ranked lower moves the difference more than the one you chose, or flips the
ordering when yours did not. You find out by making the next repair too. A comparison that passes
every item, or whose ordering survives every repair, is a sound comparison. The answer should say
so. If the ordering flipped on the first repair, you have found what the comparison was for.

## Where to go next

Kahn and Marshall @kahnmarshall1953 set out the trick this chapter rests on, in the paper that
first treated Monte Carlo as a problem in experimental design: sample two things you mean to
compare on the same draws, so that what they share cancels. Wright and Ramsay @wrightramsay1979
show when it fails. The shared draws have to reach both designs the same way, and a design that
responds to a draw in the opposite direction gets a wider difference, not a narrower one.

[ch23](#what-the-model-got-wrong) is what happens after one of the two quotes is chosen, and the
future that arrives is one of the ones in which it was the wrong choice.
