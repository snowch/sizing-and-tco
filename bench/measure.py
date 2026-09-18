"""How a measured constant is actually taken.

Every ``measured`` node in a model points at a file this module's runners produced. This is the
shared part: the corpora, the codecs, and the repeat-and-summarise that turns a single number
into a number with a standard error beside it.

## Why the corpora are generated rather than downloaded

A measured constant is only as meaningful as the body of data it was measured over, and a
corpus nobody can obtain is a measurement nobody can repeat. So the corpora here are produced by
the code below, deterministically, from a stated seed: anybody with this repository gets exactly
the same bytes, and the stamped result records the generator and the seed that made them.

That buys reproducibility and it costs realism, and the chapters say so in as many words. A
compression ratio measured over a synthetic corpus is a fact about *this corpus and this codec*,
and the book's claim about it goes no further than that. What transfers is the **method**: point
the same runner at a sample of your own data and you get the number that belongs in your model.
Every chapter that quotes one of these says exactly that, which is the difference between a
figure with conditions and a figure with authority.

## Why a standard error, not a single run

One measurement is a number; the interesting question is how much it would move if you did it
again. So each constant is measured over several independent shards of corpus and reported as a
mean with the standard error of that mean. That standard error is what becomes the measurement
uncertainty of a ``measured`` node, and it is what ch13 propagates through the model. A constant
stamped without one is claiming to have been measured exactly.
"""

from __future__ import annotations

import lzma
import math
import random
import statistics
import struct
import zlib
from dataclasses import dataclass

#: Corpus sizes are chosen so that every constant in the book re-derives in seconds. That is not
#: tidiness: CI re-derives all of them on every push, and a check that takes five minutes is a
#: check somebody eventually moves to a nightly job and then stops reading.
#:
#: Shards per measurement. Small on purpose: the standard error of a mean falls as one over the
#: square root of the count, so the seventh shard buys very little, and a runner nobody waits for
#: is a runner nobody runs. ch14's convergence argument applies to measurements as well as to
#: sampling, and this is the same arithmetic used the other way round.
SHARDS = 8


@dataclass(frozen=True)
class Shard:
    """One independently generated piece of corpus, and what it was made of."""

    seed: int
    payload: bytes
    items: int


# -- codecs ---------------------------------------------------------------------------------
#
# Named, versioned, and from the standard library, so a reader can re-run this without installing
# anything. Naming the level matters as much as naming the codec: DEFLATE at level 1 and level 9
# are different experiments and their ratios differ by more than most of the inputs in a model.


def deflate(data: bytes, level: int = 6) -> bytes:
    return zlib.compress(data, level)


def xz(data: bytes, preset: int = 1) -> bytes:
    return lzma.compress(data, preset=preset)


CODECS = {
    "deflate-6": (deflate, f"zlib {zlib.ZLIB_VERSION}, DEFLATE level 6"),
    "xz-1": (xz, "liblzma via python lzma, XZ preset 1"),
}


# -- corpora --------------------------------------------------------------------------------


def log_lines(seed: int, count: int = 20_000) -> Shard:
    """Structured application logs, of the shape a service actually emits.

    Deliberately not random text. What makes logs compress is that they are mostly the same line
    over and over with a few fields changing, and a corpus of random characters would measure a
    codec's behaviour on noise — which is the one case no real log resembles. So: a small set of
    templates, a realistic spread of levels, a handful of service and endpoint names, and
    identifiers with the cardinality those actually have.
    """
    rng = random.Random(seed)
    services = [f"svc-{name}" for name in ("api", "auth", "billing", "search", "ingest", "web")]
    endpoints = ["/v1/orders", "/v1/users/{id}", "/v1/search", "/healthz", "/v1/sessions"]
    levels = ["INFO"] * 88 + ["WARN"] * 9 + ["ERROR"] * 3
    out = []
    timestamp = 1_780_000_000.0
    for _ in range(count):
        timestamp += rng.expovariate(40.0)
        out.append(
            '{{"ts":"{ts:.3f}","level":"{level}","service":"{service}","trace":"{trace:032x}",'
            '"endpoint":"{endpoint}","status":{status},"ms":{ms:.1f},"msg":"{msg}"}}'.format(
                ts=timestamp,
                level=rng.choice(levels),
                service=rng.choice(services),
                trace=rng.getrandbits(128),
                endpoint=rng.choice(endpoints),
                status=rng.choices([200, 201, 304, 400, 404, 500], [70, 8, 6, 6, 7, 3])[0],
                ms=rng.lognormvariate(2.6, 0.8),
                msg=rng.choice(
                    [
                        "request completed",
                        "cache miss",
                        "upstream retry",
                        "validation failed",
                        "token refreshed",
                    ]
                ),
            )
        )
    return Shard(seed=seed, payload=("\n".join(out) + "\n").encode(), items=count)


def mixed_objects(seed: int, count: int = 250) -> Shard:
    """A general-purpose object store's contents, as a mixture rather than as one thing.

    The mixture is the measurement. A cluster holding nothing but text compresses beautifully and
    one holding nothing but video does not compress at all, and neither number is useful for
    sizing a cluster that holds some of each. The proportions below are an **assumption**, stated
    here and in the stamped result, and they are the first thing to change when using this against
    a real estate.
    """
    rng = random.Random(seed)
    parts: list[bytes] = []
    for _ in range(count):
        roll = rng.random()
        size = int(rng.lognormvariate(9.2, 1.0))
        if roll < 0.38:  # text-ish: documents, JSON, source, config
            words = ["alpha", "beta", "gamma", "delta", "epsilon", "record", "value", "field"]
            body = " ".join(rng.choice(words) for _ in range(size // 6))
            parts.append(body.encode())
        elif roll < 0.62:  # columnar-ish: repeated fixed-width records
            parts.append(
                b"".join(
                    struct.pack("<qd", rng.randint(0, 5000), rng.gauss(50, 3))
                    for _ in range(size // 16)
                )
            )
        elif roll < 0.80:  # already compressed: media, archives
            parts.append(rng.randbytes(size))
        else:  # sparse: partly-written blocks
            body = bytearray(size)
            for _ in range(size // 64):
                body[rng.randrange(size)] = rng.randrange(256)
            parts.append(bytes(body))
    payload = b"".join(parts)
    return Shard(seed=seed, payload=payload, items=count)


def metric_samples(seed: int, series: int = 300, points: int = 400) -> Shard:
    """Time series of the shape a monitoring agent scrapes: regular, and slow-moving.

    Two properties do all the work, and both are why a general-purpose codec is the wrong tool
    for metrics. Timestamps arrive at a near-constant interval, so the difference between
    successive gaps is almost always zero. Values drift rather than jump, so successive floats
    share most of their bits. :func:`encode_series` exploits exactly those two facts and nothing
    else.
    """
    rng = random.Random(seed)
    encoded = bytearray()
    for _ in range(series):
        timestamp = 1_780_000_000
        interval = rng.choice([15, 30, 60])
        value = rng.lognormvariate(3.0, 1.0)
        stream = []
        for _ in range(points):
            timestamp += interval + rng.choice([0, 0, 0, 0, 1, -1])
            value = max(0.0, value * math.exp(rng.gauss(0, 0.02)))
            stream.append((timestamp, value))
        encoded += encode_series(stream)
    return Shard(seed=seed, payload=bytes(encoded), items=series * points)


def trace_spans(seed: int, count: int = 30_000) -> Shard:
    """Spans as a tracing backend stores them: a small envelope and a bag of attributes.

    What makes a span expensive is rarely the span. It is the attributes hung off it — an HTTP
    route, a database statement, a user id somebody added during an incident and nobody removed —
    and the spread of attribute counts here matters more to the answer than anything else in the
    generator. It is an assumption, stated in the stamped result.
    """
    rng = random.Random(seed)
    operations = [
        "http.server",
        "http.client",
        "db.query",
        "cache.get",
        "rpc.call",
        "queue.publish",
    ]
    keys = [
        "http.route",
        "http.method",
        "db.system",
        "db.statement",
        "net.peer.name",
        "rpc.service",
        "messaging.destination",
        "user.id",
        "deployment.env",
        "k8s.pod",
    ]
    out = []
    for _ in range(count):
        attributes = {
            rng.choice(keys): rng.choice(
                [
                    "/v1/orders",
                    "GET",
                    "postgresql",
                    "SELECT * FROM orders WHERE id = $1",
                    "db-primary.internal",
                    "orders.v1",
                    "events.orders",
                    f"{rng.getrandbits(40):010x}",
                    "production",
                    f"api-{rng.getrandbits(24):06x}",
                ]
            )
            for _ in range(rng.choices([2, 4, 6, 9, 14], [20, 35, 25, 15, 5])[0])
        }
        body = ",".join(f'"{k}":"{v}"' for k, v in sorted(attributes.items()))
        out.append(
            f'{{"trace":"{rng.getrandbits(128):032x}","span":"{rng.getrandbits(64):016x}",'
            f'"parent":"{rng.getrandbits(64):016x}","name":"{rng.choice(operations)}",'
            f'"start":{1_780_000_000_000_000 + rng.getrandbits(40)},'
            f'"dur":{int(rng.lognormvariate(9.0, 1.2))},"attr":{{{body}}}}}'
        )
    return Shard(seed=seed, payload=("\n".join(out) + "\n").encode(), items=count)


# -- the metrics encoder --------------------------------------------------------------------


def encode_series(stream: list[tuple[int, float]]) -> bytes:
    """Delta-of-delta timestamps, XOR-of-previous values.

    The two ideas behind every time-series store's on-disk format, implemented here because a
    ``measured`` constant taken with a codec nobody can read is not a measurement anybody can
    check. Both ideas are published — Facebook's Gorilla paper @pelkonen2015gorilla is the usual
    citation — and neither is complicated:

    *Timestamps.* Scrapes arrive every fifteen seconds. The gap between them is almost always the
    same gap as last time, so store the change in the gap. It is nearly always zero, and a zero
    costs one byte here rather than eight.

    *Values.* A gauge that was 41.2 is now 41.3. Two float64s that close share their sign,
    exponent and most of their mantissa, so their XOR is mostly leading zeros: store how many
    leading and trailing zero bytes there are, then only the bytes in between.

    A byte-aligned arrangement rather than a bit-packed one, which costs perhaps a third of the
    space a production format achieves and makes the code legible. The stamped result says so,
    and ch03's whole point is that a measured constant belongs to the implementation that
    produced it — this implementation included.
    """
    out = bytearray()
    previous_timestamp = 0
    previous_delta = 0
    previous_bits = 0
    for i, (timestamp, value) in enumerate(stream):
        if i == 0:
            out += struct.pack("<qd", timestamp, value)
            previous_timestamp, previous_bits = (
                timestamp,
                struct.unpack("<Q", struct.pack("<d", value))[0],
            )
            continue
        delta = timestamp - previous_timestamp
        delta_of_delta = delta - previous_delta
        if -128 <= delta_of_delta < 128:
            out += struct.pack("<b", delta_of_delta)
        else:
            out += struct.pack("<bq", -128, delta_of_delta)
        previous_timestamp, previous_delta = timestamp, delta

        bits = struct.unpack("<Q", struct.pack("<d", value))[0]
        xor = bits ^ previous_bits
        previous_bits = bits
        if xor == 0:
            out += b"\x00"
            continue
        raw = xor.to_bytes(8, "big")
        lead = len(raw) - len(raw.lstrip(b"\x00"))
        trail = len(raw) - len(raw.rstrip(b"\x00"))
        meaningful = raw[lead : 8 - trail]
        out += struct.pack("<BB", lead + 1, len(meaningful)) + meaningful
    return bytes(out)


# -- repeat and summarise ---------------------------------------------------------------------


def over_shards(generator, shards: int = SHARDS, **kwargs) -> list[Shard]:
    """The same corpus generated several times, independently.

    Seeds are consecutive from zero and recorded in the result, so "re-run it" is a complete
    instruction rather than an invitation to get different numbers.
    """
    return [generator(seed=seed, **kwargs) for seed in range(shards)]


def with_error(values: list[float]) -> dict:
    """A mean and how far it would move if the measurement were taken again.

    The standard error of the mean — the spread of the individual shards divided by the square
    root of how many there were. It is the same one-over-root-n that ch14 spends a section on,
    used here in the direction people find less intuitive: not "how many samples do I need" but
    "given the ones I took, how much do I know".
    """
    mean = statistics.fmean(values)
    if len(values) < 2:
        return {"value": mean, "sd": 0.0, "shards": len(values)}
    spread = statistics.stdev(values)
    return {
        "value": mean,
        "sd": spread / math.sqrt(len(values)),
        "shard_spread": spread,
        "shards": len(values),
        "low": min(values),
        "high": max(values),
    }
