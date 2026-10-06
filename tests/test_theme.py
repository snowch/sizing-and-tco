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


def test_a_dropdown_box_starts_closed():
    """`:class: dropdown` renders as a <details> with no `open`, its title as the summary.

    It used to render as a div, so a box the page offered as optional reading was always open.
    """
    from bench.render import render

    node = {
        "type": "admonition",
        "kind": "note",
        "class": "dropdown",
        "children": [
            {"type": "admonitionTitle", "children": [{"type": "text", "value": "Why?"}]},
            {"type": "paragraph", "children": [{"type": "text", "value": "Because."}]},
        ],
    }
    out = render(node)
    assert out.startswith('<details class="admonition note dropdown">'), out
    assert " open" not in out.split(">", 1)[0]
    assert '<summary class="admonition-title">Why?</summary>' in out
    assert "Because." in out and out.count("Why?") == 1


def test_an_explorer_box_is_replaced_by_its_generated_figure():
    """An empty ``{div}`` classed ``explorer`` and a figure's name becomes that figure's HTML; a
    box naming no generated explorer, or with content inside, fails rather than going blank."""
    from bench.render import EXPLORER, UnknownNodeError, render

    box = {"type": "div", "class": "explorer what-a-workload-is-growth", "children": []}
    assert render(box).startswith(EXPLORER)
    with pytest.raises(UnknownNodeError):
        render({"type": "div", "class": "explorer no-such-explorer", "children": []})
    with pytest.raises(UnknownNodeError):
        render(
            {
                "type": "div",
                "class": "explorer what-a-workload-is-growth",
                "children": [{"type": "text", "value": "typed inside"}],
            }
        )


def test_the_growth_explorer_starts_at_the_model_s_own_values():
    """Its defaults are the stage's point values, inside the sliders' bounds, and what it shows
    before its script runs is the model's arithmetic, not a typed figure."""
    import re as regex

    from bench.stamp import load_result
    from bench.tables import (
        GROWTH_EXPLORER_FACTOR,
        GROWTH_EXPLORER_HORIZON,
        GROWTH_EXPLORER_START,
        growth_explorer,
    )

    name = "web_service_demand_horizon_exponent-reference"
    nodes = load_result(name)["summary"]["nodes"]
    growth, horizon = nodes["annual_growth"]["point"], nodes["horizon"]["point"]
    page = growth_explorer(name)
    assert "\n\n" not in page, "a blank line would end MyST's HTML block early"
    assert f'class="ge-factor" type="range" min="{GROWTH_EXPLORER_FACTOR[0]}"' in page
    assert f'value="{growth}"' in page and f'value="{int(round(horizon))}"' in page
    assert GROWTH_EXPLORER_FACTOR[0] <= growth <= GROWTH_EXPLORER_FACTOR[1]
    assert GROWTH_EXPLORER_HORIZON[0] <= horizon <= GROWTH_EXPLORER_HORIZON[1]
    shown = regex.search(r'data-show="chain-demand">([\d,]+)<', page).group(1)
    assert shown == f"{GROWTH_EXPLORER_START * growth**horizon:,.0f}"


def test_the_shapes_calculator_uses_the_loader_s_formulas_and_the_model_s_values():
    """It carries `GROWTH_SHAPES` itself, starts at the stage's point values inside its sliders'
    bounds, and what it shows before its script runs is each formula worked out, not a typed
    figure."""
    import html as markup
    import json
    import re as regex

    from bench.stamp import load_result
    from bench.tables import (
        GROWTH_EXPLORER_FACTOR,
        GROWTH_EXPLORER_START,
        GROWTH_SHAPES_AMOUNT,
        GROWTH_SHAPES_CEILING,
        GROWTH_SHAPES_CEILING_RANGE,
        GROWTH_SHAPES_HORIZON,
        growth_shapes_explorer,
    )
    from sizing.dsl import GROWTH_SHAPES

    name = "web_service_demand_horizon_exponent-reference"
    nodes = load_result(name)["summary"]["nodes"]
    growth, horizon = nodes["annual_growth"]["point"], int(round(nodes["horizon"]["point"]))
    page = growth_shapes_explorer(name)
    assert "\n\n" not in page, "a blank line would end MyST's HTML block early"
    carried = regex.search(r'data-shapes="([^"]*)"', page).group(1)
    assert json.loads(markup.unescape(carried)) == GROWTH_SHAPES
    assert f'class="gs-factor" type="range" min="{GROWTH_EXPLORER_FACTOR[0]}"' in page
    assert GROWTH_EXPLORER_FACTOR[0] <= growth <= GROWTH_EXPLORER_FACTOR[1]
    assert GROWTH_SHAPES_HORIZON[0] <= horizon <= GROWTH_SHAPES_HORIZON[1]
    amount = round(GROWTH_EXPLORER_START * (growth - 1))
    assert GROWTH_SHAPES_AMOUNT[0] <= amount <= GROWTH_SHAPES_AMOUNT[1]
    assert GROWTH_SHAPES_CEILING_RANGE[0] <= GROWTH_SHAPES_CEILING <= GROWTH_SHAPES_CEILING_RANGE[1]
    start, ceiling = GROWTH_EXPLORER_START, GROWTH_SHAPES_CEILING
    expected = {
        "compound": start * growth**horizon,
        "linear": start + amount * horizon,
        "levelling": ceiling / (1 + (ceiling / start - 1) * growth**-horizon),
    }
    for shape, value in expected.items():
        shown = regex.search(rf'data-show="worked-{shape}">[^<]* = ([\d,]+)<', page).group(1)
        assert shown == f"{value:,.0f}", shape
    # The shapes keep their order against one another at the defaults: levelling below compound,
    # both above the start, which is what the calculator is there to show.
    assert start < expected["levelling"] < min(expected["compound"], ceiling)


def test_the_label_grid_starts_inside_its_sliders_and_counts_what_it_draws():
    """Its defaults sit inside its sliders, and the sum it shows before its script runs is the
    product of the three counts it draws."""
    from bench.tables import (
        LABEL_GRID_ACCIDENTAL,
        LABEL_GRID_ENDPOINT,
        LABEL_GRID_STATUS,
        label_grid_explorer,
    )

    page = label_grid_explorer("observability-reference")
    assert "\n\n" not in page, "a blank line would end MyST's HTML block early"
    counts = [LABEL_GRID_ENDPOINT, LABEL_GRID_STATUS, LABEL_GRID_ACCIDENTAL]
    for low, high, default in counts:
        assert low <= default <= high
    e, s, a = (default for _, _, default in counts)
    assert f"× {a} = {e * s * a} series" in page
