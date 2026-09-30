---
title: "Preface"
short_title: Preface
---

(preface)=
# Preface

*How to size a system, cost it, and know how much to trust the answer.*

## What this book is about

Someone asks how big the system needs to be. How many machines, how much storage, and what it
will cost to run for as long as they keep it. They will spend real money on whatever you tell
them.

**How big, how much, and how wrong could I be?**

The first question, how big, is sizing; the second, how much, is total cost of ownership.

:::{div}
:class: definition

**Sizing** means working out how much hardware a stated workload needs, and where that hardware
stops coping.
:::

:::{div}
:class: definition

**Total cost of ownership** (TCO) means what that hardware costs over the years you keep it. That
is not the same as what it costs to buy.
:::

Most of the work in both is multiplication and addition: a request rate times the work each
request needs, a number of hosts times a price, a yearly cost times the years. One part of sizing
is not multiplication: finding where the hardware stops coping. As a machine gets busier, response
time climbs steeply well before the machine is fully busy. A chain of multiplications cannot show
that climb.

## The question this book answers

The third question is how far you can trust your answer: how wrong it could be. This book teaches
you to answer it.

To answer it you need to know:

- which input your answer rests on;
- how far the answer moves when that input moves; and
- what it would cost to find out.

[ch19](#which-input-is-the-answer) answers all three.

## How the models work

:::{div}
:class: definition

**Model** — a YAML file containing numbers with their units and sources, plus formulas connecting them.
:::

Each number in a model file has a name, a unit, and a note saying where its value came from. Each
computed number has a formula that refers to the other numbers by name. A model file is written
this way so you can see which numbers matter and how they connect. You can then see what happens
to the answer when one of them changes.

Two models run through the book. In both, the structure is what the book teaches, and the numbers
are yours to replace.

- The first is a web service and its data, on a fleet of Linux hosts. It is sized and costed end
  to end. How it behaves under load is not a chain of multiplications at all.
- The second is an observability platform, which has a hole in it where a measurement should be.

The web service model grows through the book. [ch02 · What a workload is](#what-a-workload-is)
writes its first numbers: what arrives (the busy-hour request rate) and what accumulates (the
records held). Later chapters add where each number came from, what the hardware can hold, where
it stops coping, and what it costs. [ch12 · The sizing model](#the-sizing-model) produces a host
count. [ch18 · The five-year model](#the-five-year-model) produces a cost.

Each chapter that adds to the web service model shows it as it stands at the end of that chapter,
in a viewer where you can drag its inputs. Some pages show the finished model before the book has
built it. ch01 does, to show what the whole model produces. Every figure is produced by the
build from the repository's files. The build fails when a figure no longer matches the code that
made it.

## Why a file, and not a spreadsheet

A spreadsheet cell holds a value and nothing about it. It doesn't tell you the unit, where it came from, or how certain it is. Everything this book does depends on those three things being written down beside the number.

- **Unit.** A spreadsheet multiplies a rate by a plain number and produces identical digits
  regardless of whether the result is a rate or an amount. The toolkit enforces units on every
  formula and refuses any that do not match the declared unit: requests per second times seconds
  gives requests, but requests per second times a plain number stays requests per second.
- **Source.** A spreadsheet has no required place to write where a number came from, so that
  knowledge stays with whoever built the sheet. The model file requires every input to declare its
  kind (fact, vendor's claim, or assumption) and its source; the build refuses any without both,
  and a fact must cite something.
- **Certainty.** A cell holds one number however unsure you are of it. An input in a model file
  can say how unsure you are: a low value you would be surprised to see it fall below and a high
  value you would be surprised to see it rise above. A number nobody has measured is left empty,
  and so is everything computed from it — the page prints "not yet measured" instead of a guess.

## Who this book is for

This is a self-study text and a toolkit. It is for an engineer who has been asked how big
something needs to be, or what it will cost, and who wants to give an answer they would still
defend a year later.

You should be comfortable with code and with arithmetic. You are assumed to know **nothing**
about statistics. This book introduces statistical terms as it needs them, in plain English first.
All terms are defined in the chapter where they first matter.

Every chapter ends with problems. Most are implemented as Python tests that fail until you have solved them.

The last problem in every chapter is different. It asks about a system you run, and no test can
check your answer, because only you have the system. Instead, the problem tells you what a good
answer looks like, and what would show that yours is wrong.

## What you need

You install nothing to read the book or run its models. The book is a website where the models
are things you drag and run in your browser. The prose reads on any screen, but the models need a
tablet held sideways or a larger screen.

The problems run in the page. Under each one that has a test sits the code it grades, yours to
edit. **Check** runs the tests in your browser. Nothing leaves your machine.

Once you open the book, it works offline. If you press a problem's **Check** once while online,
the Python runtime is kept. **Keep offline** in the header fetches it ahead of need.

To work the problems at a desk with an editor and shell, clone the repository:

```bash
git clone https://github.com/snowch/sizing-and-tco.git
cd sizing-and-tco
python3 -m pip install -r requirements.txt -r requirements-dev.txt
python3 -m pytest tests/point_estimates/ -m problem
```

Nothing in this book needs a datacentre, a cloud account, or a licence.

## How this book was made

Chris Snow wrote this book in collaboration with Claude, an AI model made by Anthropic. Claude drafted much of the
prose, the models and the toolkit. The author set the book's rules, chose what it covers, and
decided what stays.

No number in this book comes from Claude's own knowledge. Every figure is a stamped result that the
build computes again on every change, every quoted line of code is read from its file, and a figure
nobody has measured is shown as not yet measured. The rules that hold the models to evidence hold
the writing too. The build refuses a page with a number typed into its prose, and a quote that no
longer matches its file fails the build.

Claude also ran the editorial reviews. One reader checked each page's claims against the code, and a
script opened every page in a browser and pressed every control. You can check any number the same
way the build does: each table's *Source* line names the result it came from.

Each chapter page opens with a short video summary. Gemini Notebook, an AI tool, created these
summaries one chapter at a time directly from each chapter's text. The instructions told it to use
only the chapter's text, to state no number that the chapter does not state, and to name no
product. The build checks every number on the pages; it does not check the videos, so where a
video and its page disagree, the page is right.

## Where to start

Read [ch01](#point-estimates) first. It shows what a single number leaves out when you answer
"how big" or "how much" with one figure. The chapter draws the line the rest of the book is built
on: between a model that is right whenever every input is right, and a model that can be wrong
even then. It can be wrong when it rests on a number measured on one piece of software,
or when it runs into a limit.

### If you only need the seller's TCO

Some readers only need to build or judge a sales TCO: the one a seller builds to show a customer what its product saves. You can read six chapters instead of the whole book.

Start with [ch01](#point-estimates), which teaches the distinction the rest of the book relies on. Then read [ch02](#what-a-workload-is), which shows how a model file reads. Next, [ch03](#where-the-numbers-come-from) covers where each number comes from, and how to mark a vendor's claim, an assumption and a figure observed on a running system. [ch04](#peak-mean-and-growth) teaches you to run a model through futures and to read a tornado chart. [ch22](#comparing-two-tcos) shows two quotes compared line by line and the checklist a buyer uses. Finally, [ch23](#the-sellers-tco) teaches the seller's model itself.

The chapters between these six size the fleet: queueing, capacity, headroom, where a fleet hits limits. The seller's TCO leaves all of that out. You will know that blind spot exists, but not what is inside it.

### If you need to present a TCO to finance

Some readers need a TCO for a finance audience: to present one, or to read one as the person who approves the spend. You can read nine chapters instead of the whole book.

Start with [ch01](#point-estimates), which teaches the difference between a model that is right whenever its inputs are right and one that can be wrong even then. Then read [ch02](#what-a-workload-is), which shows how a model file reads. Next, [ch03](#where-the-numbers-come-from) covers where each number comes from, and how each is marked. [ch04](#peak-mean-and-growth) teaches you the busy hour, and the futures a model runs through. [ch13](#monte-carlo) shows how the model runs through many futures at once, and the range of totals that comes out. [ch15](#capex-opex-and-lifecycle) explains what is bought once and what is paid every year, and over what horizon. [ch18](#the-five-year-model) presents the five-year model the finance chapter uses. [ch19](#which-input-is-the-answer) names which input the answer rests on. Finally, [ch21](#a-tco-for-finance) teaches which number to put in front of the room, and the sentence that goes beside it.

Most of the chapters between these nine size the fleet: queueing, capacity, headroom, where a fleet hits limits. The finance chapter takes that fleet as given. If someone in the room asks why the fleet is that size, those chapters are where the answer is.
