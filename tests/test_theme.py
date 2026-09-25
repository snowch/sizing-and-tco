"""One choice of colours, reaching four documents that share nothing else.

A chapter with a model in it is four documents: the page, and up to three frames, each with its
own `:root` and its own stylesheet. While all four asked the operating system the same question
they agreed for free. A button ends that, and these are what keep them in step.

The one that matters most is `test_a_dark_block_that_cannot_be_overruled_fails_the_build`. Adding
a colour to a dark palette is a small edit somebody will make without reading any of this, and
the failure it causes -- a frame stuck on the machine's preference inside a page following the
reader's -- looks like a rendering bug rather than a missing rewrite.
"""

from __future__ import annotations

import re

import pytest

from bench.render import FRAME_KINDS
from bench.stamp import ROOT
from bench.theme import BUTTON, CHOICES, FRAME, FRAME_SELECTOR, KEY, PARENT, both_ways

#: A rule: a selector list, then a body with no braces in it.
RULE = re.compile(r"([^{}]+)\{([^{}]*)\}")

DARK_AT = "@media (prefers-color-scheme: dark) {"


def dark_blocks(css: str) -> list[str]:
    """Every `prefers-color-scheme: dark` block in a stylesheet, brace-matched."""
    out, at = [], 0
    while (start := css.find(DARK_AT, at)) != -1:
        depth, i = 1, start + len(DARK_AT)
        while depth and i < len(css):
            depth += {"{": 1, "}": -1}.get(css[i], 0)
            i += 1
        assert not depth, "unclosed prefers-color-scheme block"
        out.append(css[start + len(DARK_AT) : i - 1])
        at = i
    return out


def test_a_dark_block_is_written_once_and_lands_twice():
    """The palette stays in the stylesheet; the second copy is made rather than typed.

    `:root` is *narrowed* by the override and everything else becomes a descendant of it. Written
    the other way round, `:root[data-theme="dark"] :root body` matches nothing, and a reader who
    chose dark would get the palette without the background.
    """
    out = both_ways(
        ":root { --ink: #111; }\n"
        f"{DARK_AT}\n  :root {{ --ink: #eee; }}\n  body {{ background: #000; }}\n}}\n"
    )
    assert ':root:not([data-theme="light"]) { --ink: #eee; }' in out
    assert ':root:not([data-theme="light"]) body { background: #000; }' in out
    assert ':root[data-theme="dark"] { --ink: #eee; }' in out
    assert ':root[data-theme="dark"] body { background: #000; }' in out
    # The light `:root` above the query is untouched: an override is an override, not a rewrite
    # of the whole sheet.
    assert ":root { --ink: #111; }" in out


def test_the_reader_can_have_the_light_book_on_a_dark_machine():
    """`:not([data-theme="light"])` is the half that is easy to leave out.

    Without it the media query keeps winning and the button works in one direction only. That
    failure is invisible to anybody developing in daylight, which is most people.
    """
    out = both_ways(f"{DARK_AT}\n  :root {{ --ink: #eee; }}\n}}\n")
    inside = dark_blocks(out)[0]
    assert ':not([data-theme="light"])' in inside, (
        "a dark block that applies to every reader cannot be overruled by one of them"
    )


@pytest.mark.parametrize(
    "css",
    [
        # An at-rule inside the block: the rewriter cannot prefix that, and half a pair is
        # worse than none, because the page would look right until somebody pressed the button.
        f"{DARK_AT}\n  @media (min-width: 40rem) {{ :root {{ --ink: #eee; }} }}\n}}\n",
        # A block nobody closed.
        f"{DARK_AT}\n  :root {{ --ink: #eee; }}\n",
        # A block with nothing in it, which means somebody meant something else.
        f"{DARK_AT}\n}}\n",
    ],
)
def test_both_ways_refuses_what_it_cannot_rewrite(css):
    with pytest.raises(ValueError):
        both_ways(css)


def shipped() -> dict[str, str]:
    """Every stylesheet the build ships, as the reader receives it."""
    from importlib import util

    def load(name):
        spec = util.spec_from_file_location(name.replace("-", "_"), ROOT / "scripts" / f"{name}.py")
        module = util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    viewer = ROOT / "sizing" / "viewer"
    return {
        "the page": load("build-site").CSS,
        "the model viewer": both_ways((viewer / "style.css").read_text()),
        "the futures widget": both_ways((viewer / "futures.css").read_text()),
    }


@pytest.mark.parametrize("which", ["the page", "the model viewer", "the futures widget"])
def test_a_dark_block_that_cannot_be_overruled_fails_the_build(which):
    """Nothing goes dark for the machine that does not also go dark for the reader who asked.

    Stated over the shipped stylesheet rather than over `both_ways`, because the way this breaks
    is a stylesheet reaching the reader without going through it -- a fifth document, or a
    builder that inlines a file it forgot to rewrite.
    """
    css = shipped()[which]
    blocks = dark_blocks(css)
    assert blocks, f"{which} has no dark palette at all"
    for block in blocks:
        for selectors, body in RULE.findall(block):
            assert ':not([data-theme="light"])' in selectors, (
                f"{which}: `{selectors.strip()}` follows the machine and nothing else"
            )
            twin = selectors.replace(':root:not([data-theme="light"])', ':root[data-theme="dark"]')
            assert f"{twin.strip()} {{{body}}}" in css, (
                f"{which}: `{selectors.strip()}` has no counterpart for a reader who chose dark"
            )


def test_the_page_tells_every_kind_of_frame_it_can_hold():
    """A fourth kind of frame is exactly the thing somebody adds and forgets to tell.

    So the selector is derived from the renderer's own table rather than written out beside it.
    """
    for kind in set(FRAME_KINDS.values()):
        assert f"iframe.{kind}" in FRAME_SELECTOR, kind
    assert FRAME_SELECTOR in PARENT


def test_both_halves_accept_the_same_three_words_and_no_others():
    """The page sends and the frame accepts. Neither may drift from `CHOICES`."""
    import json

    assert f"const ORDER = {json.dumps(list(CHOICES))};" in PARENT
    for choice in CHOICES:
        assert f'"{choice}"' in PARENT, choice
        assert f'"{choice}"' in FRAME, choice
    # `system` is stored by removing the key, so a reader who never pressed the button and one
    # who cycled back round are the same reader.
    assert f'localStorage.removeItem("{KEY}")' in PARENT
    assert f'localStorage.getItem("{KEY}")' in PARENT


def test_the_frame_takes_a_theme_only_from_the_page_it_is_in():
    """Nothing else in a frame reads a message, so this check is the whole of the trust."""
    assert "e.source !== window.parent" in FRAME


def test_the_frame_asks_because_it_may_arrive_after_the_reader_chose():
    """Frames are `loading="lazy"`: most load long after the button was last pressed.

    A page that only broadcast on change would leave every late frame on the machine's
    preference, which is the common case rather than the corner one.
    """
    assert 'iframe class="{kind_class}" src="{src}" loading="lazy"' in (
        (ROOT / "bench" / "render.py").read_text().replace("html.escape(src)", "src")
    )
    assert 'postMessage({ sizingTheme: "?" }' in FRAME
    assert 'e.data.sizingTheme === "?"' in PARENT


def test_the_control_does_nothing_without_a_script_so_it_is_not_shown():
    """Like Search and the offline control: written `hidden`, revealed by the script."""
    assert " hidden " in BUTTON, "the attribute, not aria-hidden on a drawing inside it"
    assert "button.hidden = false" in PARENT
