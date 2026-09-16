"""Take every corpus measurement the models use.

    python3 -m bench.run_corpus            # measure and write bench/results/*.json
    python3 -m bench.run_corpus --check    # re-derive and fail if anything moved

These are the constants a model can have because a codec is deterministic: point the same code at
the same bytes and you get the same answer on any machine. So CI re-derives all of them on every
push, exactly as *Systems From Scratch* re-captures its disassembly listings, and a change to the
generator, the encoder or the Python version fails the build instead of quietly restating the
book's figures.

What these are **not** is facts about your data. Every one of them is measured over a corpus this
repository generates, and every chapter that quotes one says so and says what to run against a
sample of your own. ch03 is about precisely that distinction.
"""

from __future__ import annotations

import argparse
import sys

from bench import measure
from bench.stamp import build_result, load_result, result_exists

#: Everything in this module's fingerprint, so editing a corpus generator or the metrics encoder
#: invalidates the constants taken with it.
SOURCES = ["bench/measure.py", "bench/run_corpus.py"]


def object_compression() -> dict:
    """How much smaller a general-purpose object store's contents get.

    The storage cluster's one measured constant, and the model is built so that it is the only
    one — that book-keeping is deliberate. ch17's argument is that a cost model's structure is
    accounting identities with uncertain prices hung off it, and a model stuffed with empirical
    constants would be quietly making the opposite case.
    """
    shards = measure.over_shards(measure.mixed_objects)
    codec, description = measure.CODECS["xz-1"]
    ratios = [len(shard.payload) / len(codec(shard.payload)) for shard in shards]
    stats = measure.with_error(ratios)
    return build_result(
        "storage-object-compression",
        target="corpus",
        produced_by={
            "corpus": "bench.measure.mixed_objects — synthetic mixture of text, columnar, "
            "already-compressed and sparse objects, seeds 0-7",
            "codec": description,
            "stack": "python lzma (XZ preset 1)",
            "mixture": "38% text, 24% fixed-width records, 18% incompressible, 20% sparse",
        },
        summary={
            **stats,
            "bytes_in": sum(len(shard.payload) for shard in shards),
            "objects": sum(shard.items for shard in shards),
        },
        units={
            "value": "dimensionless",
            "sd": "dimensionless",
            "shard_spread": "dimensionless",
            "low": "dimensionless",
            "high": "dimensionless",
            "shards": "dimensionless",
            "bytes_in": "byte",
            "objects": "dimensionless",
        },
        conditions={
            "what_this_is_about": "this corpus and this codec, and nothing else",
            "to_use_it": "re-run bench.measure.mixed_objects against a sample of your own "
            "estate, or replace the generator with one that reads it",
            "the_mixture_is_an_assumption": "the proportions were chosen, not observed; they are "
            "the first thing to change and the largest source of error here",
        },
        code_sources=SOURCES,
        write=True,
    )


def log_line_bytes() -> dict:
    """What one structured log line costs on disk after compression.

    The observability model's logs chain turns lines per second into bytes per second and this is
    the exchange rate. Measured after compression rather than before, because the number that
    sizes a retention store is the one that lands on a disk.
    """
    shards = measure.over_shards(measure.log_lines)
    codec, description = measure.CODECS["deflate-6"]
    per_line = [len(codec(shard.payload)) / shard.items for shard in shards]
    raw_per_line = [len(shard.payload) / shard.items for shard in shards]
    stats = measure.with_error(per_line)
    return build_result(
        "logs-line-bytes",
        target="corpus",
        produced_by={
            "corpus": "bench.measure.log_lines — JSON service logs, five templates, six services, "
            "128-bit trace ids, seeds 0-7",
            "codec": description,
            "stack": "python zlib (DEFLATE level 6)",
        },
        summary={
            **stats,
            "uncompressed": measure.with_error(raw_per_line)["value"],
            "lines": sum(shard.items for shard in shards),
        },
        units={
            "value": "byte/line",
            "sd": "byte/line",
            "shard_spread": "byte/line",
            "low": "byte/line",
            "high": "byte/line",
            "uncompressed": "byte/line",
            "shards": "dimensionless",
            "lines": "line",
        },
        conditions={
            "what_moves_it_most": "the width of the highest-cardinality field. The trace id here "
            "is 128 random bits and is nearly incompressible; a corpus without one is much "
            "cheaper per line",
            "what_this_is_about": "this corpus and this codec, and nothing else",
        },
        code_sources=SOURCES,
        write=True,
    )


def metric_sample_bytes() -> dict:
    """What one scraped metric sample costs after a time-series encoder has had it.

    The single most load-bearing constant in the observability model: it multiplies the whole
    metrics chain, and the metrics chain is where label cardinality lands.

    The encoder is ``bench.measure.encode_series``, in this repository, byte-aligned and therefore
    perhaps a third worse than a production format that packs bits. That is a *property of this
    measurement*, recorded here, and ch03's argument in one line: change the implementation and
    this constant is about something else.
    """
    shards = measure.over_shards(measure.metric_samples)
    per_sample = [len(shard.payload) / shard.items for shard in shards]
    stats = measure.with_error(per_sample)
    return build_result(
        "metrics-sample-bytes",
        target="corpus",
        produced_by={
            "corpus": "bench.measure.metric_samples — 400 series x 500 points, 15/30/60s scrape "
            "intervals with occasional jitter, lognormal random-walk values, seeds 0-7",
            "codec": "bench.measure.encode_series — delta-of-delta timestamps, XOR values, "
            "byte-aligned",
            "stack": "this repository's encoder, not any product's",
        },
        summary={**stats, "samples": sum(shard.items for shard in shards)},
        units={
            "value": "byte/sample",
            "sd": "byte/sample",
            "shard_spread": "byte/sample",
            "low": "byte/sample",
            "high": "byte/sample",
            "shards": "dimensionless",
            "samples": "sample",
        },
        conditions={
            "byte_aligned": "a bit-packed production format achieves materially less per sample; "
            "this figure belongs to this encoder",
            "what_moves_it_most": "how fast the values move. A flat gauge costs about a byte; a "
            "noisy one costs most of a float",
        },
        code_sources=SOURCES,
        write=True,
    )


def trace_span_bytes() -> dict:
    """What one span costs on disk after compression.

    The traces chain's byte-level constant. Its sibling — how many spans a request actually makes
    — is not here and cannot be: that is a property of somebody's instrumented application, not of
    any corpus, and the observability model leaves it unmeasured on purpose so that the reader
    meets a blocked chain on a published page rather than in a footnote (ch03).
    """
    shards = measure.over_shards(measure.trace_spans)
    codec, description = measure.CODECS["deflate-6"]
    per_span = [len(codec(shard.payload)) / shard.items for shard in shards]
    stats = measure.with_error(per_span)
    return build_result(
        "traces-span-bytes",
        target="corpus",
        produced_by={
            "corpus": "bench.measure.trace_spans — spans with 2-14 attributes drawn from a "
            "ten-key vocabulary, 128-bit trace ids, seeds 0-7",
            "codec": description,
            "stack": "python zlib (DEFLATE level 6)",
        },
        summary={**stats, "spans": sum(shard.items for shard in shards)},
        units={
            "value": "byte/span",
            "sd": "byte/span",
            "shard_spread": "byte/span",
            "low": "byte/span",
            "high": "byte/span",
            "shards": "dimensionless",
            "spans": "span",
        },
        conditions={
            "what_moves_it_most": "the attribute count distribution, which is an assumption here "
            "and is the first thing to replace with an observation of your own traces",
        },
        code_sources=SOURCES,
        write=True,
    )


#: Every corpus measurement, by the result name a model refers to.
RUNNERS = {
    "storage-object-compression": object_compression,
    "logs-line-bytes": log_line_bytes,
    "metrics-sample-bytes": metric_sample_bytes,
    "traces-span-bytes": trace_span_bytes,
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="re-derive every constant and fail if one no longer matches what is committed",
    )
    args = parser.parse_args()

    failures = []
    for name, runner in RUNNERS.items():
        if not args.check:
            runner()
            continue
        if not result_exists(name):
            print(f"  MISSING: bench/results/{name}.json — run `make measure`")
            failures.append(name)
            continue
        committed = load_result(name)
        fresh = runner.__wrapped__() if hasattr(runner, "__wrapped__") else _dry(runner)
        for figure in ("value", "sd"):
            was = committed["summary"].get(figure)
            now = fresh["summary"].get(figure)
            if was is None or now is None or abs(was - now) > 1e-9 * max(1.0, abs(was)):
                print(f"  MOVED: {name}.{figure}: committed {was!r}, now {now!r}")
                failures.append(name)
        if name not in failures:
            print(f"  ok: {name} = {committed['summary']['value']:.6g}")

    if failures:
        print(
            "\nrun_corpus: FAILED — these constants no longer match the code that took them.\n"
            "Either the generator, the encoder or the interpreter changed. Re-run "
            "`python3 -m bench.run_corpus` and read what moved before committing it."
        )
        return 1
    print(f"\nrun_corpus: OK ({len(RUNNERS)} constant(s))")
    return 0


def _dry(runner):
    """Re-derive a constant without writing it, for ``--check``."""
    import bench.stamp as stamp

    real, stamp.build_result = stamp.build_result, _capture
    try:
        globals_ = runner.__globals__
        saved = globals_.get("build_result")
        globals_["build_result"] = _capture
        try:
            return runner()
        finally:
            globals_["build_result"] = saved
    finally:
        stamp.build_result = real


def _capture(name, **kwargs):
    return {"name": name, **kwargs}


if __name__ == "__main__":
    sys.exit(main())
