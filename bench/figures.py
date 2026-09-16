"""Every figure the book contains, declared in one place.

One entry per table and per diagram, so that a chapter cannot quietly cite a different run from
the one its prose discusses. ``scripts/render-figures.py`` turns these into files under
``chapters/_generated/`` and ``chapters/_figures/``, which pages pull in with ``{include}`` and
``{image}``; ``scripts/verify-numbers.py`` fails the build when a committed fragment no longer
matches what the results say.

## Figures that are waiting on a measurement

This book inherits ``pending=`` from the template it was built on, and then mostly does not need
it — because a missing measurement here is a *node*, not a figure, and the state propagates down
the graph on its own (``Model.blocked``). A table whose model has an unmeasured constant renders
the affected rows as *not yet measured* without anybody marking anything, and the accompanying
box names the constants and the runner that would take them.

``pending=`` remains for the case the graph cannot see: a figure whose whole result file does not
exist yet, because the experiment it comes from has not been run on the machine it needs.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from bench import diagrams, tables


@dataclass(frozen=True)
class Table:
    """A markdown fragment rendered from one committed result."""

    render: Callable[..., str]
    result: str
    args: tuple = ()
    #: None means "take the conditions line from `result`"; a name overrides it.
    conditions_from: str | None = None
    #: Why this has not been produced, and what to run. None means it has been.
    pending: str | None = None

    @property
    def sources(self) -> tuple[str, ...]:
        return (self.result,) if self.pending is None else ()


@dataclass(frozen=True)
class Diagram:
    """An SVG drawn by :mod:`bench.diagrams`, deterministically."""

    draw: Callable[..., str]
    alt: str
    result: str
    args: tuple = ()
    pending: str | None = None

    @property
    def sources(self) -> tuple[str, ...]:
        return (self.result,) if self.pending is None else ()

    def render(self) -> str:
        return self.draw(self.result, *self.args)


#: The reference machine runs the `rig` measurements, and nobody has one attached to CI.
RIG = "take it on the reference machine (`make measure-rig`) and commit the result"

FIGURES: dict[str, Table | Diagram] = {
    # -- the preface ---------------------------------------------------------------------
    "preface-storage-outputs": Table(
        render=tables.outputs_table, result="storage_cluster-reference"
    ),
    "preface-tco-distribution": Diagram(
        draw=diagrams.distribution,
        result="storage_cluster-reference",
        args=("tco",),
        alt="The five-year total cost as a distribution, with the point estimate marked on it",
    ),
    # -- ch13 Monte Carlo ----------------------------------------------------------------
    "monte-carlo-outputs": Table(render=tables.outputs_table, result="storage_cluster-reference"),
    "monte-carlo-nodes-distribution": Diagram(
        draw=diagrams.distribution,
        result="storage_cluster-reference",
        args=("nodes_recommended",),
        alt="The recommended node count as a distribution",
    ),
    "monte-carlo-tco-distribution": Diagram(
        draw=diagrams.distribution,
        result="storage_cluster-reference",
        args=("tco",),
        alt="The five-year total as a distribution, with the point estimate marked on it",
    ),
    "monte-carlo-ceilings": Table(render=tables.ceilings_table, result="storage_cluster-reference"),
    "monte-carlo-ceilings-resized": Table(
        render=tables.ceilings_table, result="storage_cluster-sized_for_growth"
    ),
    "monte-carlo-provenance": Table(
        render=tables.provenance_table, result="storage_cluster-reference"
    ),
    "monte-carlo-graph": Diagram(
        draw=diagrams.dependency_graph,
        result="storage_cluster-reference",
        args=("tco",),
        alt="The sub-graph that feeds the five-year total",
    ),
    # -- ch14 Correlation and convergence ------------------------------------------------
    "correlation-and-convergence-table": Table(
        render=tables.convergence_table, result="convergence-storage-tco"
    ),
    "correlation-and-convergence-curve": Diagram(
        draw=diagrams.convergence,
        result="convergence-storage-tco",
        alt="Run-to-run spread against sample count, with the one-over-root-n law beside it",
    ),
    "correlation-and-convergence-effect": Table(
        render=tables.correlation_table, result="correlation-effect"
    ),
    "correlation-and-convergence-declared": Table(
        render=tables.declared_correlations, result="observability-reference"
    ),
    # -- appendix E: the storage model ---------------------------------------------------
    "appendix-e-storage-model-graph": Diagram(
        draw=diagrams.dependency_graph,
        result="storage_cluster-reference",
        alt="The storage cluster model as a dependency graph, coloured by node kind",
    ),
    "appendix-e-storage-model-outputs": Table(
        render=tables.outputs_table, result="storage_cluster-reference"
    ),
    "appendix-e-storage-model-ceilings": Table(
        render=tables.ceilings_table, result="storage_cluster-reference"
    ),
    "appendix-e-storage-model-measured": Table(
        render=tables.measured_table, result="storage_cluster-reference"
    ),
    "appendix-e-storage-model-provenance": Table(
        render=tables.provenance_table, result="storage_cluster-reference"
    ),
    "appendix-e-storage-model-tornado": Table(
        render=tables.tornado_table, result="storage_cluster-reference", args=("tco",)
    ),
    "appendix-e-storage-model-tornado-chart": Diagram(
        draw=diagrams.tornado_chart,
        result="storage_cluster-reference",
        args=("tco",),
        alt="Which input moves the five-year total most",
    ),
    "appendix-e-storage-model-distribution": Diagram(
        draw=diagrams.distribution,
        result="storage_cluster-reference",
        args=("cost_per_usable_tb_month",),
        alt="Cost per usable TB per month, as a distribution",
    ),
    "appendix-e-storage-model-scenarios": Table(
        render=tables.scenario_comparison,
        result="storage_cluster-reference",
        args=("storage_cluster-sized_for_growth",),
    ),
    # -- appendix F: the observability model ----------------------------------------------
    "appendix-f-observability-model-graph": Diagram(
        draw=diagrams.dependency_graph,
        result="observability-reference",
        alt="The observability model as a dependency graph, with the unmeasured chain marked",
    ),
    "appendix-f-observability-model-outputs": Table(
        render=tables.outputs_table, result="observability-reference"
    ),
    "appendix-f-observability-model-unmeasured": Table(
        render=tables.not_yet_measured, result="observability-reference"
    ),
    "appendix-f-observability-model-ceilings": Table(
        render=tables.ceilings_table, result="observability-reference"
    ),
    "appendix-f-observability-model-measured": Table(
        render=tables.measured_table, result="observability-reference"
    ),
    "appendix-f-observability-model-provenance": Table(
        render=tables.provenance_table, result="observability-reference"
    ),
    "appendix-f-observability-model-tornado": Table(
        render=tables.tornado_table, result="observability-reference", args=("active_series",)
    ),
    "appendix-f-observability-model-tornado-chart": Diagram(
        draw=diagrams.tornado_chart,
        result="observability-reference",
        args=("active_series",),
        alt="Which input moves the active series count most",
    ),
    "appendix-f-observability-model-cardinality": Diagram(
        draw=diagrams.distribution,
        result="observability-reference",
        args=("label_cardinality",),
        alt="Label cardinality as a distribution: a product of uncertain counts",
    ),
    "appendix-f-observability-model-scenarios": Table(
        render=tables.scenario_comparison,
        result="observability-reference",
        args=("observability-knobs_turned_down",),
    ),
    # -- ch03: the measured constants ------------------------------------------------------
    "where-the-numbers-come-from-constants": Table(
        render=tables.constants_index, result="logs-line-bytes"
    ),
    "where-the-numbers-come-from-rig": Table(
        render=tables.constant_table,
        result="collector-throughput-per-core",
        pending=f"Collector throughput per core is a timing: {RIG}.",
    ),
}


def cited_results() -> set[str]:
    return {result for figure in FIGURES.values() for result in figure.sources}


def pending_results() -> dict[str, str]:
    return {
        figure.result: figure.pending for figure in FIGURES.values() if figure.pending is not None
    }
