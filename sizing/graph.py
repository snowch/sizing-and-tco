"""Where each node sits, worked out here rather than in the browser.

The dependency graph is the book's main figure and it has to be *checkable*: committed, diffable,
and identical on every machine, so that ``render-figures --check`` can tell a stale picture from a
current one. A layout computed in the browser by a force-directed library is none of those — it
settles somewhere slightly different every time it runs, which makes "has this figure gone stale"
an unanswerable question.

So the arrangement is computed here, deterministically, and shipped as coordinates. This is the
same argument *Systems From Scratch* makes for drawing its diagrams as SVG by hand rather than
with a plotting library, and it is the reason both books can put a picture under a staleness check
at all.

The algorithm is the standard layered one, in the two parts anybody would write:

1. **Layers.** A node sits one column to the right of the furthest-right thing it depends on. So
   inputs are all on the left, outputs on the right, and every arrow points forwards.
2. **Order within a layer.** Sort each column by the average height of the nodes it connects to,
   sweeping forwards and backwards a few times. It is a heuristic and it does not minimise
   crossings; it makes a graph of sixty nodes legible, which is the requirement.
"""

from __future__ import annotations

from sizing.dsl import Model

#: Sweeps of the barycentre heuristic. Four is where it stops improving on both reference models;
#: more is cheap and changes nothing, which is its own kind of evidence that this is enough.
SWEEPS = 4


def layers(model: Model) -> dict[str, int]:
    """Which column each node belongs in.

    Two passes, and the second one is what makes the picture readable.

    **Earliest.** The longest path from a root, not the shortest: a node must sit to the right of
    *everything* it depends on, and taking the shortest path would send an arrow backwards the
    first time two chains of different lengths reconverged. Both reference models do that
    constantly, which is what makes them models rather than columns of a spreadsheet.

    **Then as late as possible.** Earliest alone puts every input in column zero, and the storage
    model has twenty-three of them: a tower of boxes on the left, four nearly empty columns on the
    right, and half the page blank. So each node is then pushed right until it sits immediately
    before the first thing that consumes it. An electricity price now appears next to the energy
    cost it feeds rather than a metre away from it, which is both shorter and truer — the distance
    between two boxes on this figure should mean how far apart they are in the model.
    """
    earliest: dict[str, int] = {}
    for name in model.order:
        parents = model.nodes[name].depends_on()
        earliest[name] = 1 + max((earliest[p] for p in parents), default=-1)

    children: dict[str, list[str]] = {name: [] for name in model.nodes}
    for name, node in model.nodes.items():
        for parent in node.depends_on():
            children[parent].append(name)

    latest = dict(earliest)
    for name in reversed(model.order):
        if children[name]:
            latest[name] = max(earliest[name], min(latest[child] for child in children[name]) - 1)
    return latest


def place(model: Model) -> dict[str, dict]:
    """A column and a row for every node."""
    depth = layers(model)
    columns: dict[int, list[str]] = {}
    for name in sorted(model.nodes):
        columns.setdefault(depth[name], []).append(name)

    children: dict[str, list[str]] = {name: [] for name in model.nodes}
    for name, node in model.nodes.items():
        for parent in node.depends_on():
            children[parent].append(name)

    row = {name: float(i) for column in columns.values() for i, name in enumerate(column)}

    for sweep in range(SWEEPS):
        forwards = sweep % 2 == 0
        for level in sorted(columns, reverse=not forwards):
            for name in columns[level]:
                neighbours = (
                    sorted(model.nodes[name].depends_on()) if forwards else sorted(children[name])
                )
                if neighbours:
                    row[name] = sum(row[n] for n in neighbours) / len(neighbours)
        for level, names in columns.items():
            # Re-space to whole rows after each sweep, breaking ties by name so the result does
            # not depend on dictionary order and therefore on the Python version.
            for i, name in enumerate(sorted(names, key=lambda n: (row[n], n))):
                row[name] = float(i)
            columns[level] = sorted(names, key=lambda n: (row[n], n))

    return {name: {"layer": depth[name], "row": int(row[name])} for name in sorted(model.nodes)}


def extent(placement: dict[str, dict]) -> tuple[int, int]:
    """How many columns and how many rows the widest one has."""
    if not placement:
        return (0, 0)
    return (
        max(p["layer"] for p in placement.values()) + 1,
        max(p["row"] for p in placement.values()) + 1,
    )
