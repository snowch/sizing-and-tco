---
title: "The seller's TCO"
short_title: "ch23 The seller's TCO"
---

(the-sellers-tco)=
# ch23 · The seller's TCO

## The question

You are selling a system too large to size in detail, to a customer whose workload you cannot see. What can a TCO built from a benchmark and an assumed usage honestly claim?

[ch22](#comparing-two-tcos) compared two quotes bottom up: every line of both, future by future. That comparison is the buyer's work. This chapter is the other side of it — the seller building the TCO.

A seller cannot build it bottom up, so the seller's model works top down: start from what the customer spends per host, and scale it by a benchmark and an assumed usage.

## The material

### What the seller cannot see

A bottom-up TCO needs the customer's workload ([ch02](#what-a-workload-is)), the processor time per request measured on a machine ([ch05](#littles-law), [ch03](#where-the-numbers-come-from)), a fleet sized by a rule ([ch12](#the-sizing-model)), and every line priced ([ch18](#the-five-year-model)). The seller has none of these for the customer: not the busy hour, not the processor time per request on the customer's software, not the bill.

The seller does have three things: its own benchmark, its own price list, and a picture of what customers in its market tend to look like. So the seller's model works per host: what the customer spends for each host it runs, how many hosts it runs, and ratios that scale that spend. The honest aim is not a saving for this customer. It is the conditions under which the product saves money, stated so the customer can check them against numbers only the customer has.

### Top down: start from the spend

The model is the file `models/sellers_tco/model.yaml`. It is a definitional model ([ch01](#point-estimates)): no measured constant, no ceiling. Every figure it gives is right if its inputs are right. The trouble is all in the inputs.

The customer's side has three inputs: the hosts the customer runs today; the customer's spend per host-year, everything in, staff included (the whole bill divided by the hosts); and the share of that spend that moves with the number of hosts. Hardware, power, licences and support move with the host count. Staff, and anything bought per site, largely do not.

The arithmetic, in words: the proposed fleet is the customer's hosts divided by the product's advantage on the customer's work. The customer's spend as it is equals hosts times spend per host-year times horizon. The spend with the product equals the part of today's spend that does not scale, which stays; plus the proposed hosts times the seller's price per host-year times horizon; plus the cost of the move. The saving is the first total minus the second. The proposed fleet is not rounded up. A top-down model counts capacity, not boxes.

```{literalinclude} ../models/sellers_tco/model.yaml
:language: yaml
:start-at: effective_advantage:
:end-before: margin_per_host_year:
```

The nodes above show the arithmetic just described: the effective advantage the product brings to the customer's work, the proposed fleet it needs, and the saving that results.

The share that scales is the assumption a brochure skips. A brochure that scales the whole bill has set the share to one without saying so. People are the largest line that does not move with the host count: in [ch22](#comparing-two-tcos) the people line was the same on both sides.

### A benchmark is two claims

The seller's benchmark says how much more work one proposed host did than one of the customer's current hosts, on the benchmark's workload. The model marks it a vendor's claim. In this model it stands in for a published result, and its value is the ratio of the two hosts' cores in ch22.

The second claim is how much of that advantage survives on the customer's own workload. The model calls it the transfer factor and marks it an assumption. One means the benchmark is the customer's workload.

:::{div}
:class: definition

**Transfer factor.** The share of a benchmark's advantage that carries over to the customer's own workload. One means the benchmark is the customer's workload.
:::

Why it is not one by default: [ch05](#littles-law) said the processor time per request belongs to one build of the software on one kind of machine. A benchmark is that fact about somebody else's software. The transfer factor is the same fact, applied to a benchmark.

Nobody has measured the transfer factor for any customer. Measuring it means running the customer's own workload on both hosts: a measurement on a machine ([ch03](#where-the-numbers-come-from)), which is exactly what the seller cannot do without the customer. A brochure that says the product does several times the work makes the first claim out loud and sets the second to one in silence.

The model multiplies the two, and keeps them as two inputs so that each can be argued separately: the vendor stands behind the first, and nobody can stand behind the second until the customer's workload has been run.

```{literalinclude} ../models/sellers_tco/model.yaml
:language: yaml
:start-at: benchmark_advantage:
:end-before: proposed_cost_per_host:
```

### Your usage figure or theirs

In the model's reference scenario, the customer's hosts and the customer's spend per host-year are the seller's assumptions: guesses about a customer in its market. The customer knows both. Once the customer supplies them, they are the customer's figures: an observation of a running system, which [ch03](#where-the-numbers-come-from) called an `estate` figure. [ch03](#where-the-numbers-come-from) holds such a figure to three disclosures: which system, over what window, and on what date. The seller should record them.

A sales TCO often shows both kinds of figure the same way: the seller's guess about a typical customer and this customer's own count. It should mark which is which. A guess shown as the customer's own figure is a claim the customer cannot check against anything.

For a customer the seller has not met, the input that moves the seller's saving most is the customer's spend per host-year. The transfer factor and the share of the spend that scales come next.

The chart below shows it: each bar is how far the saving moves when that one input runs across its range and the others stay where they are. This is a tornado—a chart you learned in an earlier chapter.

```{image} _figures/the-sellers-tco-tornado.svg
:alt: Which input moves the seller's saving most, for a customer the seller has not met
:width: 100%
```

The customer knows the top bar. Asking for it removes the widest bar. What is left are the two assumptions neither side can read off an invoice.

The scenario below pins the two figures to [ch22](#comparing-two-tcos)'s incumbent: the hosts it runs and its spend per host-year, everything in, both worked out from ch22's stamped quote. The share that scales and the transfer factor stay the seller's guesses. Neither is on an invoice: the share needs the bill broken into lines, and the transfer factor needs a measurement.

```{literalinclude} ../models/sellers_tco/scenarios/ch22_customer.yaml
:language: yaml
:start-at: scenario:
```

### Sell the break-even, not the saving

The table below sets two versions of the seller's model side by side, for a customer the seller has not met. The brochure sets the transfer factor to one and the share that scales to one. The honest model leaves both as the seller's ranges. Nothing else differs.

```{include} _generated/the-sellers-tco-scenarios.md
```

What the table shows: the brochure saves money in nearly every future, and a small customer already pays for the move. The honest model loses money at the point estimate and saves money in a minority of its futures. At its point estimate each host the customer runs loses money every year after the move, so no size of customer pays for the move. To break even, the benchmark would have to carry over more than whole.

The break-even customer size exists only while each host saves money a year after the move. When each host loses, the model's formula still returns a number, and it is negative. A negative number of hosts is not a customer; it means no customer pays.

The lesson: a seller cannot know the saving for a customer it has not met. It can state the break-even: the transfer factor, or the customer size, at which the product pays. That is a claim the customer can test: run their workload on both hosts, or count their hosts.

```{image} _figures/the-sellers-tco-transfer.svg
:alt: The five-year saving for one customer against the share of the benchmark that carries over, for three guesses at the share of the spend that scales, with the bottom-up answer marked
:width: 100%
```

About the figure: it is [ch22](#comparing-two-tcos)'s customer, from the previous section. It draws the saving against the transfer factor for three guesses at the share that scales: the brochure's (all of it), the share implied by ch22's comparison, and the seller's own guess. Where each line crosses no saving is that guess's break-even. The less of the bill moves with the hosts, the further right the crossing moves: more of the benchmark has to survive. For the seller's own guess the crossing is off the right-hand edge. The lines bend because the proposed fleet is the customer's hosts divided by the transfer factor, so a small transfer factor makes the proposed fleet grow fast. The dot is ch22's bottom-up answer, drawn at a transfer factor of one; the last section says why it sits there.

The figure below draws the same two assumptions as a plane, for the same customer: the transfer factor across, the share of the spend that scales up. The line is where the saving is zero. On the shaded side the product pays; on the other it loses.

```{image} _figures/the-sellers-tco-plane.svg
:alt: The transfer factor against the share of the spend that scales, split by the line where the saving is zero, with the seller's futures as dots and three settings marked
:width: 100%
```

The break-even is a line, not a number. Any pair of assumptions on it ties. A larger share that scales lets a smaller transfer factor pay.

The brochure sits on the top edge, deep in the paying side. [ch22](#comparing-two-tcos)'s two assumptions sit just on the paying side. The middle of the seller's own guesses sits well on the losing side.

The dots are a few hundred of the seller's own futures. The share of them on the paying side is how often the seller's guesses say the product pays, and it is a minority: the same share the table below gives as futures with a saving.

A seller can show this plane before the customer has given any number. The customer can then place themselves on it.

### The chart a sales TCO leads with

Most sales TCOs lead with one chart. It shows each option's spend added up year by year. The customer's own line starts at nothing. Each proposal's line starts at the cost of the move, and then climbs more slowly if the product saves money each year.

The point where a proposal's line crosses the customer's line is its payback. This is the year in which the savings add up to the cost of the move. It is a break-even in time, the same kind of claim as the break-evens above.

The model has a node for it, `payback`: the cost of the move divided by the saving a year.

```{image} _figures/the-sellers-tco-by-year.svg
:alt: Each option's spend added up year by year for one customer, starting from the cost of the move, with the year each proposal pays back marked
:width: 100%
```

The figure shows [ch22](#comparing-two-tcos)'s customer, drawn with three settings of the two hidden assumptions from the figure above: the brochure's, ch22's, and the seller's guesses. The brochure pays back early. With ch22's two assumptions, the proposal pays back just inside the horizon, so a horizon a little shorter would lose money. With the seller's guesses, the line never crosses: each year the proposal spends more than the customer does today, so the move is never paid back.

The same chart, drawn three ways, tells three stories. What decides which story a buyer sees is the same two numbers the chapter keeps returning to, and the chart does not show them. A seller's per-year chart should say which transfer factor and which share that scales drew it.

The payback row in the table above gives the same comparison for a customer the seller has not met. The brochure pays back quickly. The honest model never does.

The lines are straight because the model is linear in time. A real move has a period of running both systems, which puts a bend in the early years that this chart cannot show. The totals are undiscounted, as everywhere in the book ([ch15](#capex-opex-and-lifecycle)): a finance reader will place the years and apply their own rate.

### What the buyer will do with it

[ch22](#comparing-two-tcos) ended with a checklist for a comparison somebody else built. The buyer will hold the seller's TCO against it. A seller who expects that can answer each item before it is asked.

| What the buyer checks in ch22 | What the seller's TCO shows |
|---|---|
| The workload it was sized for | that the benchmark's workload is not the customer's, and the transfer factor as an input with a range |
| Every line on both sides | the share of the spend that does not scale, shown, not hidden inside a whole-bill scaling |
| Whose number each line is | the benchmark and the price marked as the vendor's claims; the customer's hosts and spend marked as the customer's `estate` figures once supplied; everything else as an assumption |
| The cost of the move, on the side that has to move | the move, as its own line |
| The difference over shared futures, and how often it flips | the share of futures with a saving, not only the saving at the point estimate |
| Each design's ceilings | that the model has none, said plainly |
| The break-evens | first, before the saving |
| A file that re-runs | the model itself, so the customer can put in their own numbers |

The seller's honest model runs below. The customer's hosts, the spend per host-year, the share that scales and the transfer factor each have a slider. Drag the transfer factor to one and the share to one and watch the model turn into the brochure.

```{iframe} /models/sellers_tco-reference.html
:width: 100%
The seller's model running on reference assumptions. Among its sliders: the hosts the customer runs today, the customer's spend per host-year, the share of that spend that moves with the host count, and the transfer factor — how much of the benchmark advantage carries over to the customer's own work. The customer supplies the first two once the seller asks. The last two are the seller's guesses about a market it does not yet know in detail. The horizon, the benchmark, the seller's price per host-year and the cost of the move have sliders too; the model file gives each one value.
```

### How far top down lands from bottom up

The table below runs the seller's model on [ch22](#comparing-two-tcos)'s customer four ways, and ends with ch22's own bottom-up answer.

```{include} _generated/the-sellers-tco-ladder.md
```

Row one, the brochure: the largest saving by far. It scales the people with the host count, and it assumes the benchmark carries over whole.

Row two sets the two hidden assumptions as [ch22](#comparing-two-tcos)'s comparison implies them: a transfer factor of one, and the share that scales worked out from ch22's stamped incumbent (everything except the people, as a share of its total). It lands close to ch22's answer. What gap remains is rounding: the top-down model counts capacity and needs a fraction of a host, while the bottom-up comparison buys whole hosts (see the proposed hosts column).

Why a transfer factor of one for [ch22](#comparing-two-tcos): ch22 sized the challenger by its cores, with one processor time per request on both hosts, because it is the same software on different hosts. So ch22's bottom-up comparison had the transfer assumption inside it too. ch22 said as much where it said its comparison could not speak to performance; here the assumption has a name and a value.

Row three, the seller's own guesses: a loss at the point estimate, and a saving in few of its futures. Its transfer factor is below one, so it needs more proposed hosts (the column shows it), and its share that scales is a little below [ch22](#comparing-two-tcos)'s. Its middle nine in ten is wide, much wider than the bottom-up row. That width is the seller's not knowing the transfer factor and the share that scales.

The figure below splits each proposal's five-year spend into three parts: the part of today's spend that stays, the proposed hosts, and the move. The dashed line is what the customer spends as it is, so the gap between a bar's top and the line is the saving, printed above each bar.

```{image} _figures/the-sellers-tco-breakdown.svg
:alt: Each proposal's five-year spend split into the part of today's spend that stays, the proposed hosts and the move, against the customer's own total
:width: 100%
```

The brochure's bar has no grey block. Scaling the whole bill assumes all of today's spend goes away with the hosts, the people included. That missing block is most of the brochure's saving.

With [ch22](#comparing-two-tcos)'s two assumptions, the grey block is the people, and the bar lands just under the line.

With the seller's guesses, the grey block is larger, because less of the spend scales, and the blue block is taller, because a smaller transfer factor needs more hosts. The bar ends above the line.

The conclusion: the top-down structure is not what makes a sales TCO wrong. Given the right two numbers, it reproduces the bottom-up answer to within rounding. What makes a sales TCO wrong is the two numbers it hides. The runner that builds this table (`bench/run_seller.py`) checks that the seller's model is still pinned to [ch22](#comparing-two-tcos)'s quotes, and refuses to stamp the table if it is not.

## What this cannot tell you

**Anything that does not scale in a straight line.** The model is linear in hosts: every host the customer runs saves or loses the same amount. There are no economies of scale and no costs that jump at a size. The proposed fleet can be a fraction of a host, because the model counts capacity, not boxes.

**Whether the proposed fleet copes.** The model has no ceilings, so nothing in it can say the proposed fleet is too small. [ch22](#comparing-two-tcos)'s bottom-up comparison found the challenger over its limits in a share of its futures; the seller's model cannot see any of that. Denser hosts also mean each host failing takes more of the fleet with it ([ch11](#headroom-and-failure-domains)).

**The move as it happens.** The model moves the customer all at once. It has no period of running both systems and no gradual migration. The move is one number.

**Whether the benchmark measured the right thing.** The transfer factor is one number for the whole workload. A workload limited by memory or storage rather than processor cores ([ch10](#bandwidth-and-the-binding-constraint)) gains differently from a denser host, and the model cannot say which limit decides.

**The customer's bill, line by line.** The share that scales is one number for the whole bill. The customer knows which of its lines move with hosts; the seller guesses.

**What the other vendor will do.** The model holds the customer's spend as it is. An incumbent who cuts its price to keep the customer changes the answer, and nothing in the model knows that.

**What is unmeasured.** Nothing in the model is a measured constant, so nothing is marked not yet measured: it is a definitional model. The input that most needs a measurement is the transfer factor, and the seller cannot take that measurement alone.

## Key takeaways

:::{div}
:class: takeaways

- **A top-down TCO hides two assumptions.** How much of the benchmark carries over to the customer's work, and how much of the customer's spend moves with the number of hosts. A brochure sets both to one.
- **A benchmark is two claims.** The vendor's result on the benchmark's workload, and its transfer to yours. The first is the vendor's to stand behind; nobody can stand behind the second until the customer's workload has been run.
- **Sell the break-even, not the saving.** A seller cannot know the saving for a customer it has not met. It can say at what transfer factor, or what customer size, the product pays, and the customer can test that.
- **The structure is not what makes it wrong.** Run on [ch22](#comparing-two-tcos)'s customer with the two assumptions ch22 implies, the top-down model lands on its bottom-up answer to within rounding.
- **Mark the customer's figures as theirs.** The customer's hosts and spend, once supplied, are observations of a running system, with the system, the window and the date written down. A guess about a typical customer is not one.

:::

## Problems

Four, in `tests/the_sellers_tco/`. The first two have tests. The last two do not, and say why.

**23.1 — How much of the benchmark has to carry over?**
The test hands you the seller's five-year saving on [ch22](#comparing-two-tcos)'s customer as a function of the transfer factor, with everything else pinned, including a share of the spend that scales that the test chooses. Return the transfer factor at which the saving is zero, to within a dollar of saving. The test grades three shares of the spend that scales, none of which the chapter prints a break-even for, so an answer copied off the page does not pass. The saving is not a straight line in the transfer factor, because the proposed fleet is the customer's hosts divided by it. Work the formula through, or search: the saving rises with the transfer factor, so bisection between a factor that loses money and one that saves it finds the zero.

```bash
python3 -m pytest tests/the_sellers_tco/test_problem_1_break_even_transfer.py -m problem
```

**23.2 — How small a customer can the seller take?**
The test hands you the saving as a function of the number of hosts the customer runs, with a share that scales and a transfer factor the test chooses. Return the number of hosts at which the saving is zero, or None when no number of hosts pays for the move. In some of the cases each host loses money every year after the move. There the larger the customer, the larger the loss, and the right answer is None. The model's own formula returns a negative number of hosts there, and a negative number of hosts is not a customer. The saving is a straight line in the number of hosts, so two evaluations fix it.

```bash
python3 -m pytest tests/the_sellers_tco/test_problem_2_smallest_customer.py -m problem
```

**23.3 — The seller's TCO for something you sell.** No test: the product is yours, and nothing here has seen it.
Take a product or system you sell, or one you would propose to a customer inside your own organisation. Build its top-down TCO in the model file's shape: the customer's hosts and spend per host-year, the share that scales, the benchmark advantage and the transfer factor, your price per host-year, and the move. A good answer gives each input a range and a source, marks the benchmark as your claim and the transfer factor as an assumption, states the break-even transfer factor and break-even customer size, and says what the customer would have to supply or measure to test them. It is falsified when a customer runs their own workload on both and the transfer factor lands outside your range, or when your break-even rests on an input the customer has no way to check.

**23.4 — The transfer factor nobody wrote down.** No test: the document is someone else's, and nothing here has seen it.
Take a sales TCO you have received. Find the saving it claims, the benchmark it rests on, and whatever it says about your usage. Put its figures into the seller's model and find the transfer factor and the share that scales that reproduce its saving. Neither will be written in the document. A good answer says which two values the document implied, whether you would defend them for your own workload, and which one you would measure first and how. It is falsified if those two values, with your own hosts and your own spend, do not give the saving the document claims, or if the document did state them and you missed it.

## Where to go next

Fleming and Wallace @flemingwallace1986 is about summarising a set of benchmark results with one number. They show that the arithmetic mean of results normalised to a reference machine can rank machines differently depending on which machine is the reference, and argue for the geometric mean. A benchmark advantage quoted as one ratio is a summary of that kind: ask what it summarises.

Jain's textbook @jain1991art is further reading: its chapter on ratio games shows how the choice of base system and of summary can make either of two systems look better.

[ch24](#what-the-model-got-wrong) is what happens after a design is chosen, when the future that arrives is one the model said was possible.
