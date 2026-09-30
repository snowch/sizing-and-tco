"""The seller's TCO, set beside the buyer's.

    python3 -m bench.run_seller            # run it and write the result
    python3 -m bench.run_seller --check    # re-run and fail if a published figure moved

``models/sellers_tco/`` is a top-down TCO: the customer's spend per host, scaled by a benchmark.
``make models`` stamps what each of its scenarios says. This runner asks the question the
scenarios cannot ask on their own: **how far does the seller's model land from the bottom-up
comparison of the same customer, and which of its assumptions put it there?**

## One customer, four answers

ch22 compared two quotes for the web service bottom up: every line of both, future by future.
The seller's model is run on that same customer, with the two figures a seller could learn by
asking pinned (``ch22_customer.yaml``), and then again with its two hidden assumptions set three
ways: as a brochure sets them, as the bottom-up comparison implies them, and as the seller guessed
them. The fourth answer is ch22's own, read from ``comparison.json``.

The bottom-up comparison's share of spend that scales is not typed anywhere. It is worked out here
from the incumbent's stamped result: everything but the people, as a share of the total. So is the
check that the model's pinned figures are the ones ch22's quotes imply; if the web service model
moves, this runner refuses to stamp until the seller's model is brought back in line.

## What it cannot see

The seller's model is linear in hosts and has no ceilings. ch22's bottom-up comparison found the
challenger over its limits in a share of its futures; nothing here can, and the page says so.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import replace

from bench.stamp import build_result, load_result, numeric_differences, result_exists
from sizing.dsl import load_model, load_scenario
from sizing.evaluate import evaluate, point

SOURCES = ["bench/run_seller.py"]

MODEL = "models/sellers_tco/model.yaml"
SCENARIOS = "models/sellers_tco/scenarios"

#: How close the model's pinned figures must be to what ch22's stamped quotes imply.
PINNED_TOLERANCE = 1e-6

#: The transfer factors the figure draws the saving at.
TRANSFERS = tuple(round(0.4 + 0.02 * i, 2) for i in range(31))


def ch22_figures() -> dict:
    """What ch22's two stamped quotes say per host-year, and the incumbent's scaling share."""

    def of(scenario: str) -> dict:
        nodes = load_result(f"web_service-{scenario}")["summary"]["nodes"]
        horizon, hosts = nodes["horizon"]["point"], nodes["hosts"]["point"]
        total = nodes["tco"]["point"]
        people = nodes["annual_staff_cost"]["point"] * horizon
        move = nodes["migration_cost"]["point"]
        return {
            "hosts": hosts,
            "per_host_year": total / (hosts * horizon),
            "per_host_year_without_people_or_move": (total - people - move) / (hosts * horizon),
            "share_without_people": (total - people - move) / total,
            "move": move,
        }

    return {"incumbent": of("incumbent"), "challenger": of("challenger")}


def pinned_problems(model, customer, figures: dict) -> list[str]:
    """Where the seller's model has drifted from the quotes it was pinned to."""
    checks = (
        ("usage_hosts", customer.overrides["usage_hosts"], figures["incumbent"]["hosts"]),
        (
            "current_cost_per_host",
            customer.overrides["current_cost_per_host"],
            figures["incumbent"]["per_host_year"],
        ),
        (
            "proposed_cost_per_host",
            model.nodes["proposed_cost_per_host"].value,
            figures["challenger"]["per_host_year_without_people_or_move"],
        ),
        ("move_cost", model.nodes["move_cost"].value, figures["challenger"]["move"]),
    )
    return [
        f"{name} is {pinned!r}; ch22's quotes imply {implied!r}"
        for name, pinned, implied in checks
        if abs(pinned - implied) > PINNED_TOLERANCE * max(1.0, abs(implied))
    ]


def shares(model, scenario) -> dict:
    """In how many of the model's futures the product saves money, and in how many it could."""
    evaluation = evaluate(model, scenario)
    saving = evaluation.samples["saving"]
    margin = evaluation.samples["margin_per_host_year"]
    return {
        "saving_positive": float((saving > 0).mean()),
        "margin_positive": float((margin > 0).mean()),
    }


def seller(write: bool = True) -> dict:
    model = load_model(MODEL)
    customer = load_scenario(f"{SCENARIOS}/ch22_customer.yaml")
    reference = load_scenario(f"{SCENARIOS}/reference.yaml")
    brochure = load_scenario(f"{SCENARIOS}/brochure.yaml")
    figures = ch22_figures()
    drifted = pinned_problems(model, customer, figures)
    if drifted:
        raise ValueError("the seller's model no longer matches ch22: " + "; ".join(drifted))

    guessed = point(model, customer)
    bottom_up_share = figures["incumbent"]["share_without_people"]

    def at(transfer: float, share: float) -> dict:
        overrides = {**customer.overrides, "transfer_factor": transfer, "scaling_share": share}
        return point(model, replace(customer, overrides=overrides))

    as_brochure = at(1.0, 1.0)
    as_bottom_up = at(1.0, bottom_up_share)
    customer_run = load_result("sellers_tco-ch22_customer")["summary"]["nodes"]["saving"]

    comparison = load_result("comparison")["summary"]
    difference = comparison["nodes"]["difference"]
    # ch22 subtracts the incumbent from the challenger; a saving is the other way round.
    ladder = [
        {
            "key": "brochure",
            "label": "the brochure: the benchmark carries over whole, and every dollar scales",
            "transfer_factor": 1.0,
            "scaling_share": 1.0,
            "proposed_hosts": as_brochure["proposed_hosts"],
            "point": as_brochure["saving"],
        },
        {
            "key": "bottom_up_assumptions",
            "label": "the seller's model, with the two assumptions ch22's comparison implies",
            "transfer_factor": 1.0,
            "scaling_share": bottom_up_share,
            "proposed_hosts": as_bottom_up["proposed_hosts"],
            "point": as_bottom_up["saving"],
        },
        {
            "key": "sellers_guesses",
            "label": "the seller's model, with the seller's own guesses",
            "transfer_factor": guessed["transfer_factor"],
            "scaling_share": guessed["scaling_share"],
            "proposed_hosts": guessed["proposed_hosts"],
            "point": guessed["saving"],
            "p5": customer_run["summary"]["p5"],
            "p95": customer_run["summary"]["p95"],
            "share_positive": shares(model, customer)["saving_positive"],
        },
        {
            "key": "bottom_up",
            "label": "ch22's bottom-up comparison, line by line",
            "transfer_factor": None,
            "scaling_share": None,
            "proposed_hosts": figures["challenger"]["hosts"],
            "point": -difference["point"],
            "p5": -difference["summary"]["p95"],
            "p95": -difference["summary"]["p5"],
            "share_positive": comparison["paired"]["share_challenger_cheaper"],
        },
    ]

    curves = []
    for key, share in (
        ("brochure", 1.0),
        ("bottom_up_assumptions", bottom_up_share),
        ("sellers_guesses", guessed["scaling_share"]),
    ):
        savings = [at(t, share)["saving"] for t in TRANSFERS]
        curves.append(
            {
                "key": key,
                "scaling_share": share,
                "saving": savings,
                "break_even_transfer": at(1.0, share)["break_even_transfer"],
            }
        )

    scenarios = {}
    for scenario in (reference, brochure, customer):
        values = point(model, scenario)
        scenarios[scenario.name] = {
            "title": scenario.title,
            "saving": values["saving"],
            "break_even_transfer": values["break_even_transfer"],
            "break_even_usage": values["break_even_usage"],
            "margin_per_host_year": values["margin_per_host_year"],
            **shares(model, scenario),
        }

    units: dict[str, str] = {
        "ch22.incumbent.hosts": "host",
        "ch22.incumbent.per_host_year": "USD/host/year",
        "ch22.incumbent.per_host_year_without_people_or_move": "USD/host/year",
        "ch22.incumbent.share_without_people": "dimensionless",
        "ch22.incumbent.move": "USD",
        "ch22.challenger.hosts": "host",
        "ch22.challenger.per_host_year": "USD/host/year",
        "ch22.challenger.per_host_year_without_people_or_move": "USD/host/year",
        "ch22.challenger.share_without_people": "dimensionless",
        "ch22.challenger.move": "USD",
        "transfers": "dimensionless",
    }
    ladder_units = {
        "point": "USD",
        "p5": "USD",
        "p95": "USD",
        "transfer_factor": "dimensionless",
        "scaling_share": "dimensionless",
        "proposed_hosts": "host",
        "share_positive": "dimensionless",
    }
    for i, row in enumerate(ladder):
        for field, unit in ladder_units.items():
            if row.get(field) is not None:
                units[f"ladder[{i}].{field}"] = unit
    for i, _ in enumerate(curves):
        units[f"curves[{i}].scaling_share"] = "dimensionless"
        units[f"curves[{i}].saving"] = "USD"
        units[f"curves[{i}].break_even_transfer"] = "dimensionless"
    for name in scenarios:
        units[f"scenarios.{name}.saving"] = "USD"
        units[f"scenarios.{name}.break_even_transfer"] = "dimensionless"
        units[f"scenarios.{name}.break_even_usage"] = "host"
        units[f"scenarios.{name}.margin_per_host_year"] = "USD/host/year"
        units[f"scenarios.{name}.saving_positive"] = "dimensionless"
        units[f"scenarios.{name}.margin_positive"] = "dimensionless"

    return build_result(
        "seller",
        target="model",
        kind="measurement",
        produced_by={
            "method": "the seller's top-down model at its point estimates, with its two hidden "
            "assumptions set three ways, beside ch22's paired bottom-up difference",
            "model": model.name,
            "scenario": f"{customer.name}, {reference.name} and {brochure.name}",
            "seed": customer.seed,
            "samples": customer.samples,
            "stack": "sizing.evaluate",
        },
        summary={
            "ch22": figures,
            "ladder": ladder,
            "transfers": list(TRANSFERS),
            "curves": curves,
            "scenarios": scenarios,
        },
        units=units,
        conditions={
            "one_customer": "every row of the ladder is ch22's incumbent: its hosts and its spend "
            "per host-year are pinned from the stamped quote, not guessed",
            "pinned_from_ch22": "the proposed spend per host-year and the move are the "
            "challenger's quote in ch22, and the runner refuses to stamp if they drift",
            "no_ceilings": "the seller's model is linear in hosts and has no ceilings, so nothing "
            "in it can say the proposed fleet is too small (ch23)",
            "one_model": "ch22's bottom-up row is as complete as the web service model, and no "
            "more (ch20)",
        },
        code_sources=[
            *SOURCES,
            MODEL,
            f"{SCENARIOS}/ch22_customer.yaml",
            f"{SCENARIOS}/reference.yaml",
            f"{SCENARIOS}/brochure.yaml",
        ],
        write=write,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="re-run and diff against the stamp")
    arguments = parser.parse_args(argv)

    fresh = seller(write=not arguments.check)
    if not arguments.check:
        print("  wrote bench/results/seller.json")
        print("\nrun_seller: OK")
        return 0

    if not result_exists("seller"):
        print("seller has never been run", file=sys.stderr)
        return 1
    differences = numeric_differences(load_result("seller")["summary"], fresh["summary"])
    if differences:
        print("seller moved:", file=sys.stderr)
        for line in differences:
            print(f"  {line}", file=sys.stderr)
        return 1
    print("  ok: seller")
    print("\nrun_seller: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
