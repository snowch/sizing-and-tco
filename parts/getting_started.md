---
title: "Getting started"
short_title: "Getting started"
---

(part-getting-started)=
# Getting started

> What is a model here, and how do you check that a number in this book is still true?

Neither chapter sizes anything. Both are here because everything after them is a model file and a
stamped number, and neither of those should be unfamiliar the first time it decides an answer. A
reader who would rather start on the subject can go straight to [ch02](#what-a-workload-is) and
come back when a model file appears in front of them.

[ch00](#prerequisites-and-setup) is the toolchain and one command. The command matters more than
the toolchain: a book of numbers you cannot re-derive is a book of assertions, and the difference
between the two is `make check`. It also establishes what your machine may and may not be asked
to produce, a rule the rest of the book keeps.

[ch01](#reading-a-model) is a model file. Four node kinds, what declaring each one commits you to,
and the classification that the whole book turns on — a model with a measured constant or a
declared ceiling in it is a sizing model, and the build works that out rather than being told.
