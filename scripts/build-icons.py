#!/usr/bin/env python3
"""The site icon, drawn from the same palette as the figures.

    python3 scripts/build-icons.py                  # into public/
    python3 scripts/build-icons.py --out DIR        # somewhere else
    python3 scripts/build-icons.py --check          # fail if what is committed is stale

What a reader saves to a home screen should say what the book is about, and the book is about
one number against the spread it does not mention. So the icon is an interval with the single
answer marked on it, off-centre, where this book's running example actually puts it.

A histogram was tried first and does not survive being 48 pixels wide: the bars stop reading as
one distribution and the marker reads as a gap between two of them. An interval is four
rectangles and is legible in a browser tab.

Drawn by code for the same reason every figure is. The colours are imported from
:mod:`bench.diagrams`, so the icon cannot drift away from the palette the chapters use, and the
geometry is declared once as fractions of the square and rasterised at whatever size each
platform asks for.

There is no image library in the dependencies and this does not add one. Every shape is an
axis-aligned rectangle, so a pixel's coverage is the overlap of two rectangles — exact, which
makes the anti-aliasing exact too — and a PNG is a zlib stream with four headers around it.
Both are in the standard library.
"""

from __future__ import annotations

import argparse
import re
import struct
import sys
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from bench.diagrams import KIND_FILL  # noqa: E402
from bench.stamp import load_result, shown  # noqa: E402

DEFAULT_OUT = ROOT / "public"

#: The slate the diagrams write their labels in, as a background: dark enough to hold a light
#: histogram, and neutral enough not to fight whatever wallpaper it lands on.
BACKGROUND = "#263238"

#: The bars are an `input` node's fill and the marker is a `ceiling`'s stroke, lightened so that
#: it reads against the slate. Nothing here is a new colour.
BARS = KIND_FILL["input"]
MARKER = "#e8756c"

#: Which stamped figure the icon is a picture of, and which node in it.
MARKED_FROM = ("web_service-reference", "tco")


def marked_at() -> float:
    """Where the answer sits inside its interval, as a fraction of the way along.

    Read off the stamped result rather than chosen, because a picture of a point estimate sitting
    off-centre in its own interval should sit where this book's actually does. The five-year total
    is the figure the introduction plots, and the dot is that plot's red line.

    Clamped well inside the ends: a model that put its point estimate outside its own 90%
    interval would otherwise draw the dot on top of a cap, and an icon is not the place to
    discover that. `make check` is.
    """
    node = load_result(MARKED_FROM[0])["summary"]["nodes"][MARKED_FROM[1]]
    low, high = node["summary"]["p5"], node["summary"]["p95"]
    return min(0.82, max(0.18, (node["point"] - low) / (high - low)))


#: How much of the square the drawing leaves empty at each side, and why there are two answers.
#: A maskable icon may be cropped to a circle of four fifths of the width, so a home-screen icon
#: has to keep its end caps well inside. A favicon is never cropped, and at sixteen pixels that
#: same margin is three pixels of nothing on each side — so the tab icon is drawn tighter.
INSET = {"masked": 0.175, "tight": 0.090}

#: Every stroke is a fraction of the width actually drawn on, not of the square, so the tighter
#: icon comes out proportionally bolder rather than just bigger.
BAR = 0.062  # the interval's own thickness
CAP = 0.646  # how tall the end caps stand
DOT = 0.162  # the answer's radius


def rectangles(inset: float) -> list[tuple[float, float, float, float, str]]:
    """The interval as ``(x0, y0, x1, y1, colour)`` in fractions of the square."""
    left, right, mid = inset, 1.0 - inset, 0.5
    span = right - left
    bar, cap = BAR * span, CAP * span
    return [
        # The interval.
        (left, mid - bar / 2, right, mid + bar / 2, BARS),
        # Its ends, which are what stop it reading as a progress bar.
        (left, mid - cap / 2, left + bar, mid + cap / 2, BARS),
        (right - bar, mid - cap / 2, right, mid + cap / 2, BARS),
    ]


def dot(inset: float) -> tuple[float, float, float, str]:
    """The answer somebody would have given, as ``(x, y, radius, colour)``.

    A disc rather than a fourth bar: three vertical strokes and a horizontal one read as a
    letter, and the point estimate is not one more feature of the interval. It is the thing the
    interval is an argument with.
    """
    left, right = inset, 1.0 - inset
    span = right - left
    return (left + marked_at() * span, 0.5, DOT * span, MARKER)


def rgb(colour: str) -> tuple[int, int, int]:
    value = colour.lstrip("#")
    return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]


def overlap(a0: float, a1: float, b0: float, b1: float) -> float:
    return max(0.0, min(a1, b1) - max(a0, b0))


def render(size: int, inset: float) -> bytes:
    """The icon at ``size`` × ``size``, as PNG bytes."""
    shapes = [(x0, y0, x1, y1, rgb(c)) for x0, y0, x1, y1, c in rectangles(inset)]
    cx, cy, radius, disc = dot(inset)
    disc = rgb(disc)
    base = rgb(BACKGROUND)
    pixel = 1.0 / size
    rows = []
    for y in range(size):
        py0, py1 = y / size, (y + 1) / size
        row = bytearray([0])  # filter 0: no prediction, so the bytes are the pixels
        for x in range(size):
            px0, px1 = x / size, (x + 1) / size
            r, g, b = base
            for x0, y0, x1, y1, (sr, sg, sb) in shapes:
                # Exact area of the pixel the shape covers. Both are axis-aligned, so this is
                # the product of two one-dimensional overlaps and needs no sampling.
                cover = overlap(px0, px1, x0, x1) * overlap(py0, py1, y0, y1) * size * size
                if cover > 0:
                    r = round(r + (sr - r) * cover)
                    g = round(g + (sg - g) * cover)
                    b = round(b + (sb - b) * cover)
            # A circle has no exact answer here, so the edge is taken from how far the pixel's
            # centre sits outside it, in pixels. That is the standard trick and at these sizes
            # it is indistinguishable from supersampling, for one calculation instead of
            # sixteen.
            away = (((px0 + px1) / 2 - cx) ** 2 + ((py0 + py1) / 2 - cy) ** 2) ** 0.5
            cover = min(1.0, max(0.0, 0.5 + (radius - away) / pixel))
            if cover > 0:
                r = round(r + (disc[0] - r) * cover)
                g = round(g + (disc[1] - g) * cover)
                b = round(b + (disc[2] - b) * cover)
            row += bytes((r, g, b, 255))
        rows.append(bytes(row))

    def chunk(tag: bytes, payload: bytes) -> bytes:
        return (
            struct.pack(">I", len(payload))
            + tag
            + payload
            + struct.pack(">I", zlib.crc32(tag + payload) & 0xFFFFFFFF)
        )

    header = struct.pack(">2I5B", size, size, 8, 6, 0, 0, 0)  # 8-bit, RGBA, no interlace
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", header)
        + chunk(b"IDAT", zlib.compress(b"".join(rows), 9))
        + chunk(b"IEND", b"")
    )


def svg(inset: float) -> str:
    """The same geometry as vector, for the browsers that will take it."""
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" role="img" '
        'aria-label="An interval with a single estimate marked on it, left of centre">',
        f'<rect width="64" height="64" fill="{BACKGROUND}"/>',
    ]
    for x0, y0, x1, y1, colour in rectangles(inset):
        parts.append(
            f'<rect x="{x0 * 64:.2f}" y="{y0 * 64:.2f}" width="{(x1 - x0) * 64:.2f}" '
            f'height="{(y1 - y0) * 64:.2f}" fill="{colour}"/>'
        )
    cx, cy, radius, colour = dot(inset)
    parts.append(
        f'<circle cx="{cx * 64:.2f}" cy="{cy * 64:.2f}" r="{radius * 64:.2f}" fill="{colour}"/>'
    )
    return "\n".join(parts) + "\n</svg>\n"


#: What each platform asks for. 180 is what iOS wants for a home screen, 192 and 512 are what a
#: web manifest has to offer Android, and the small pair is the browser tab.
PNG_SIZES = {
    "icon-512.png": (512, "masked"),
    "icon-192.png": (192, "masked"),
    "apple-touch-icon.png": (180, "masked"),
    "favicon-32.png": (32, "tight"),
    "favicon-16.png": (16, "tight"),
}

#: Every URL here is relative to the manifest's own, which is what makes this file correct at
#: the site root and correct under /sizing-and-tco/ without being generated per deployment.
#: An absolute path would need BASE_URL, and a committed file that needs BASE_URL is a file
#: that is wrong in the repository.
MANIFEST = """{
  "name": "Sizing and TCO",
  "short_name": "Sizing & TCO",
  "description": "How to size a system, cost it, and know how much to trust the answer.",
  "start_url": "./",
  "scope": "./",
  "display": "minimal-ui",
  "background_color": "%(background)s",
  "theme_color": "%(background)s",
  "icons": [
    {"src": "icon-192.png", "sizes": "192x192", "type": "image/png"},
    {"src": "icon-512.png", "sizes": "512x512", "type": "image/png"},
    {"src": "icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"}
  ]
}
"""

#: What goes in the head of every built page. The favicon a theme may set for itself; the other
#: two it will not, and they are what a phone reads when somebody saves the page.
HEAD = """<link rel="icon" href="{base}favicon.svg" type="image/svg+xml">
<link rel="icon" href="{base}favicon-32.png" sizes="32x32" type="image/png">
<link rel="apple-touch-icon" href="{base}apple-touch-icon.png">
<link rel="manifest" href="{base}site.webmanifest">
<meta name="theme-color" content="{background}">"""

#: How a page says it has already been through this. Matching on the manifest rather than the
#: favicon, because a theme may well have put a favicon there itself.
LINKED = 'rel="manifest"'


def files() -> dict[str, bytes]:
    out: dict[str, bytes] = {
        name: render(size, INSET[fit]) for name, (size, fit) in PNG_SIZES.items()
    }
    out["favicon.svg"] = svg(INSET["tight"]).encode()
    out["site.webmanifest"] = (MANIFEST % {"background": BACKGROUND}).encode()
    return out


#: A root-relative URL the theme emitted without the site's base path. MyST rewrites `href` on a
#: project site and does not rewrite an `{iframe}` directive's `src`, so a panel embedded in a
#: chapter asks the wrong address and gets a 404. Narrow on purpose: it matches the directories
#: this repository publishes beside the book, not every absolute URL on the page.
UNBASED = re.compile(r'(src|href)="/((?:playground|models)/[^"]*)"')


def rebase(html: Path, base: str) -> bool:
    """Give the theme's un-rewritten URLs the base path. True if the file changed."""
    text = html.read_text()
    fixed = UNBASED.sub(lambda m: f'{m.group(1)}="{base}{m.group(2)}"', text)
    if fixed == text:
        return False
    html.write_text(fixed)
    return True


def inject(html: Path, base: str) -> bool:
    """Put the icon links in one built page's head. True if the file changed.

    The theme owns the rest of the head and this adds to it rather than rewriting it, so a theme
    upgrade cannot be broken by this script. Idempotent, because the deploy may run twice and a
    page with two manifests is a page with none.
    """
    text = html.read_text()
    if LINKED in text or "</head>" not in text:
        return False
    head = HEAD.format(base=base, background=BACKGROUND)
    html.write_text(text.replace("</head>", head + "\n</head>", 1))
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument(
        "--check", action="store_true", help="fail if what is committed is out of date"
    )
    parser.add_argument(
        "--inject",
        type=Path,
        metavar="DIR",
        help="a built site: copy the icons in and add the links to every page's head",
    )
    parser.add_argument(
        "--base",
        default="/",
        help="the path the site is served from, for the links injected into each page",
    )
    args = parser.parse_args()

    wanted = files()

    if args.inject:
        if not args.inject.is_dir():
            print(f"build-icons: {args.inject} is not a directory")
            return 1
        for name, payload in wanted.items():
            (args.inject / name).write_bytes(payload)
        base = args.base if args.base.endswith("/") else args.base + "/"
        pages = sorted(args.inject.rglob("*.html"))
        added = sum(inject(page, base) for page in pages)
        rebased = sum(rebase(page, base) for page in pages)
        # A page that already carried the links is fine; the deploy may run this twice. A build
        # where no page carries them means the head was not what this script expects, and
        # publishing a site whose icons silently did not land is the failure worth catching.
        linked = sum(LINKED in page.read_text() for page in pages)
        print(
            f"build-icons: {len(wanted)} file(s) copied, {added} page(s) edited, "
            f"{linked} of {len(pages)} page(s) linked, {rebased} page(s) rebased"
        )
        if pages and not linked:
            print("build-icons: no page's head was found \u2014 nothing was linked")
            return 1
        return 0

    if args.check:
        stale = [
            name
            for name, payload in wanted.items()
            if not (args.out / name).exists() or (args.out / name).read_bytes() != payload
        ]
        if stale:
            print("build-icons: STALE \u2014 these are not what the script now draws:")
            for name in stale:
                print(f"  {shown(args.out)}/{name}")
            print("Run `python3 scripts/build-icons.py` and commit what changes.")
            return 1
        print(f"build-icons: OK ({len(wanted)} file(s))")
        return 0

    args.out.mkdir(parents=True, exist_ok=True)
    for name, payload in wanted.items():
        (args.out / name).write_bytes(payload)
        print(f"  wrote {shown(args.out / name)} ({len(payload):,} bytes)")
    return 0


if __name__ == "__main__":  # pragma: no cover - a thin wrapper around main()
    raise SystemExit(main())
