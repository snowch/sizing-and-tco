"""The size of the reading text, and the one thing that must not move with it.

The whole of this is one rule: the control moves the prose and the code, and nothing else. The
rails, the breakpoints and the page padding are all in `rem`, so a control that moved the root
font would widen both rails and narrow the chapter -- pressing *larger* would make the book
smaller. That is not a hypothetical; it is exactly what a reader's own browser text setting did
to this layout, which is the defect this arrived alongside.
"""

from __future__ import annotations

import json
import re

from bench.reading import BUTTON, CODE_RATIO, DEFAULT, KEY, PARENT, SIZES
from bench.stamp import ROOT


def site():
    from importlib import util

    spec = util.spec_from_file_location("build_site", ROOT / "scripts" / "build-site.py")
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def declarations(css: str, name: str) -> list[str]:
    """Every property that reads a custom property, by name.

    Comments first, or a paragraph above a declaration comes back as the property's name and
    the failure reads as nonsense -- which is what it did.
    """
    bare = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    return [
        line.split(":")[0].strip().split(";")[-1].strip()
        for line in re.findall(rf"[^;{{}}]*var\({re.escape(name)}[^;{{}}]*", bare)
    ]


def test_only_the_reading_text_moves():
    """`--reading` reaches the prose and the code, and nothing that lays the page out.

    A rail, a breakpoint or the page padding reading this would undo the control: the reader
    presses `larger`, the furniture grows with it, and the chapter -- the thing they wanted more
    of -- gets less room than before.
    """
    css = site().CSS
    assert set(declarations(css, "--reading")) <= {"font", "font-size"}, (
        "something other than a font size reads the reading size; if it lays the page out, "
        "pressing `larger` makes the chapter narrower"
    )
    for name in ("--nav", "--toc", "--rails", "--top"):
        written = re.search(rf"{re.escape(name)}: ([^;]+);", css)
        assert written, name
        assert "--reading" not in written.group(1), (
            f"{name} grows with the reading text, so the rails eat the chapter as the reader "
            f"asks for bigger text"
        )


def test_the_code_keeps_its_proportion_to_the_prose():
    """13.5 over 18 is what the book was set in, and a reader who never presses this sees it."""
    css = site().CSS
    assert f"calc(var(--reading, 18px) * {CODE_RATIO})" in css, (
        "the code is sized apart from the prose, so one of the two stops following the control"
    )
    assert abs(CODE_RATIO - 13.5 / 18) < 1e-12
    assert "font: var(--reading, 18px)/1.62" in css
    # The fallback is the size the book has always been, so a browser that drops the custom
    # property renders exactly the old page rather than an unstyled one.
    steps = {name: px for name, px, _ in SIZES}
    assert steps[DEFAULT] == 18.0, "the default step is not what the book was already set in"


def test_the_steps_run_one_way_and_the_default_is_an_absence():
    """The cycle wraps, so it has to be monotonic or a reader cannot predict the next press.

    It also has to reach *below* the default, which the first version did not: the list ran
    upwards from 18px, so the smaller step a reader might want did not exist at all.
    """
    sizes = [px for _, px, _ in SIZES]
    assert sizes == sorted(sizes), "the cycle is not monotonic, so a press is unpredictable"
    names = [name for name, _, _ in SIZES]
    assert DEFAULT in names
    assert names.index(DEFAULT) > 0, "there is no step smaller than the default"
    assert names.index(DEFAULT) < len(names) - 1, "there is no step larger than the default"
    assert f'let text = "{DEFAULT}"' in PARENT, (
        "the script starts somewhere other than the default, so a reader who has pressed "
        "nothing is not on the size the book is set in"
    )
    assert f'localStorage.removeItem("{KEY}")' in PARENT, (
        "`default` is stored by writing the word rather than by removing the key, so a reader "
        "who never pressed the button and one who cycled back round are told apart for nothing"
    )
    assert f'localStorage.getItem("{KEY}")' in PARENT
    assert json.dumps([[n, px, label] for n, px, label in SIZES]) in PARENT, (
        "the script carries its own copy of the steps, which will drift from SIZES"
    )


def test_the_control_is_drawn_rather_than_typeset():
    """A glyph in the button is a different size on every device -- and is real text.

    The first version set two `<text>` elements, and the button's own accessible name came back
    as "A A Default" to anything reading it. The provenance marks are drawn for the first of
    those reasons already.
    """
    assert "<text" not in BUTTON, "the icon is typeset, so it is a different size per device"
    assert "<path" in BUTTON
    assert " hidden " in BUTTON, "the attribute, not aria-hidden on the drawing inside it"
    assert "button.hidden = false" in PARENT


def test_the_chapter_keeps_what_it_needs_when_the_reader_presses_larger():
    """Pressing the control changes how much room the code wants, so the outline reconsiders.

    The two scripts do not know about each other. A resize event is what joins them, and without
    it a reader could press `larger` into a chapter that had already decided it had room.
    """
    css = site().CSS
    assert 'dispatchEvent(new Event("resize"))' in PARENT
    assert 'addEventListener("resize", reflectOutline)' in site().MENU
    # The rule and the stylesheet agree on which state hides the rail, and on the number.
    assert "html.toc-cramped .toc { display: none; }" in css.replace(
        "html.toc-closed .toc, ", ""
    ), "the stylesheet has no rule for the state the script sets"
    assert "const MODEL_NEEDS = 860;" in site().MENU
    assert "toc-cramped" in site().MENU
