"""One theme across three documents, and a reader who may disagree with their machine.

A chapter is one page, but a chapter with a model in it is three: the page, the model viewer and
the futures widget each render in their own frame, with their own stylesheet and their own
`:root`. Nothing is shared between them but the colours, and until now the only thing keeping the
three in step was that all three asked the operating system the same question.

A button breaks that. A reader on a dark machine who presses it for the light book moves the page
and leaves the frames behind, so the chapter comes out light with dark panels cut into it. The
choice has to reach every frame, and a frame cannot read it for itself: they are separate
documents, and `localStorage` is shared but a frame that has already painted will not re-read it.
The page sends it. `postMessage` rather than a reload, because a reader who has moved six sliders
should not lose them to a change of colour.

Two rules come out of that, and this module is both of them:

- `both_ways` rewrites a stylesheet's dark block so it applies for the machine's preference
  *unless* the reader has said otherwise, and again for a reader who has chosen dark whatever the
  machine says. The palette is still written once, in the stylesheet, where somebody editing a
  colour will find it. Doubling it by hand is how one of the two ends up a shade out.
- `PARENT` and `FRAME` are the two halves of the conversation.

The book still goes dark with scripts switched off: the media query is untouched, and every
override hangs off an attribute that only a script sets.
"""

from __future__ import annotations

import json

from bench.render import FRAME_KINDS

#: What the button cycles through, in order. `system` is the absence of a choice, and is stored by
#: removing the key rather than by writing the word -- so a reader who has never pressed the button
#: and one who has cycled back round are the same reader.
CHOICES = ("system", "light", "dark")

#: The key in `localStorage`, alongside `nav` and `toc`. Per browser, not per page.
KEY = "theme"

#: Which frames to tell, derived from the kinds the renderer gives a class to. A fourth kind of
#: frame added there is told without anybody remembering to add it here -- and a fourth kind of
#: frame is exactly the thing somebody would forget.
FRAME_SELECTOR = ", ".join(f"iframe.{kind}" for kind in sorted(set(FRAME_KINDS.values())))

_DARK_AT = "@media (prefers-color-scheme: dark) {"

#: The two roots the pair is written under. Inside the query, every reader except the one who has
#: asked for light; outside it, only the reader who has asked for dark.
_UNLESS_LIGHT = ':root:not([data-theme="light"])'
_CHOSE_DARK = ':root[data-theme="dark"]'


def _prefixed(selectors: str, root: str) -> str:
    """Put one root selector in front of each selector in a list.

    A rule already rooted at `:root` is *narrowed* -- `:root` becomes `:root[data-theme="dark"]`,
    the same element with one more condition. Anything else is a descendant of it. Writing the
    second as the first would give `:root[...] :root body`, which matches nothing.
    """
    out = []
    for selector in selectors.split(","):
        selector = selector.strip()
        if not selector:
            continue
        out.append(
            root + selector[len(":root") :]
            if selector.startswith(":root")
            else f"{root} {selector}"
        )
    return ", ".join(out)


def _rules(block: str):
    """Walk a dark block a rule at a time, refusing anything that is not one.

    Scanned rather than matched with a regular expression, because the obvious expression --
    a selector, a brace, a body with no braces, a brace -- *skips* a nested at-rule and matches
    the rule inside it instead. The block would then come out with that rule hoisted clear of
    the query that was holding it, which is worse than either refusing or leaving it alone.
    """
    at = 0
    while at < len(block):
        while at < len(block):
            if block[at].isspace():
                at += 1
            elif block.startswith("/*", at):  # a comment between two rules
                end = block.find("*/", at)
                if end == -1:
                    raise ValueError("theme: unclosed comment in a dark block")
                at = end + 2
            else:
                break
        if at >= len(block):
            return
        opened = block.find("{", at)
        if opened == -1:
            raise ValueError(f"theme: not a rule in a dark block: {block[at : at + 40]!r}")
        closed = block.find("}", opened)
        if closed == -1:
            raise ValueError("theme: unclosed rule in a dark block")
        selectors, body = block[at:opened].strip(), block[opened + 1 : closed]
        if selectors.startswith("@") or "{" in body:
            raise ValueError(f"theme: cannot rewrite a nested block in a dark block: {selectors}")
        yield selectors, body
        at = closed + 1


def _rewrite(block: str, root: str) -> str:
    rules = [f"{_prefixed(selectors, root)} {{{body}}}" for selectors, body in _rules(block)]
    if not rules:
        raise ValueError("theme: a dark block with no rules in it")
    return "\n".join(rules)


def both_ways(css: str) -> str:
    """Rewrite every `prefers-color-scheme: dark` block so the reader can overrule the machine.

    Each block comes back as two: the original, narrowed to readers who have not asked for light,
    and a copy outside the query for readers who have asked for dark. `:not([data-theme="light"])`
    is the half that is easy to leave out, and leaving it out makes the button work in one
    direction only -- a reader on a dark machine could never get the light book.
    """
    out, at = [], 0
    while (start := css.find(_DARK_AT, at)) != -1:
        depth, i = 1, start + len(_DARK_AT)
        while depth and i < len(css):
            depth += {"{": 1, "}": -1}.get(css[i], 0)
            i += 1
        if depth:
            raise ValueError("theme: unclosed prefers-color-scheme block")
        block = css[start + len(_DARK_AT) : i - 1]
        out.append(css[at:start])
        follows_machine = _rewrite(block, _UNLESS_LIGHT)
        chose_dark = _rewrite(block, _CHOSE_DARK)
        out.append(f"{_DARK_AT}\n{follows_machine}\n}}\n{chose_dark}\n")
        at = i
    out.append(css[at:])
    return "".join(out)


#: The page's half: read the choice before anything paints, apply it, and answer any frame that
#: asks. The button itself is wired later, on `DOMContentLoaded`; this part cannot wait for that,
#: because a reader who chose light would watch the dark book paint first on every page.
#:
#: Frames are `loading="lazy"`, so most of them load long after the button was last pressed and
#: some never load at all. That is why the frame asks rather than the page announcing: whenever a
#: frame arrives, however late, its first act is to find out what colour the book is.
_PARENT = r"""<script>
(() => {
  const root = document.documentElement;
  const ORDER = __ORDER__;
  const NAMES = { system: "System", light: "Light", dark: "Dark" };
  let theme = "system";
  try {
    const kept = localStorage.getItem("theme");
    if (kept === "light" || kept === "dark") theme = kept;
  } catch (e) {}
  const apply = () => {
    if (theme === "system") root.removeAttribute("data-theme");
    else root.setAttribute("data-theme", theme);
    // Scrollbars, form controls and the space beyond the page are the browser's to draw, and it
    // draws them from this rather than from the palette.
    root.style.colorScheme = theme === "system" ? "light dark" : theme;
  };
  apply();
  const tell = (win) => { try { win.postMessage({ sizingTheme: theme }, "*"); } catch (e) {} };
  const frames = () => document.querySelectorAll("__FRAMES__");
  addEventListener("message", (e) => {
    if (e.data && e.data.sizingTheme === "?" && e.source) tell(e.source);
  });
  document.addEventListener("DOMContentLoaded", () => {
    const button = document.getElementById("theme");
    const reflect = () => {
      button.dataset.state = theme;
      button.querySelector("span").textContent = NAMES[theme];
      button.setAttribute("aria-label", `Colours: ${NAMES[theme]}. Press for the next.`);
    };
    button.hidden = false;
    button.addEventListener("click", () => {
      theme = ORDER[(ORDER.indexOf(theme) + 1) % ORDER.length];
      try {
        if (theme === "system") localStorage.removeItem("theme");
        else localStorage.setItem("theme", theme);
      } catch (e) {}
      apply();
      reflect();
      frames().forEach((f) => f.contentWindow && tell(f.contentWindow));
    });
    reflect();
  });
})();
</script>"""

PARENT = _PARENT.replace("__FRAMES__", FRAME_SELECTOR).replace(
    "__ORDER__", json.dumps(list(CHOICES))
)

#: A frame's half. It asks the page what colour the book is, and listens in case that changes
#: while it is open. A frame opened on its own -- these pages are single files and open from a
#: disk -- asks nobody, hears nothing, and follows the machine, which is what its stylesheet
#: already does.
FRAME = r"""<script>
(() => {
  const root = document.documentElement;
  addEventListener("message", (e) => {
    const theme = e.data && e.data.sizingTheme;
    // Only from the page this frame is in, and only one of three words. Nothing else here reads
    // a message, so the check is the whole of the trust.
    if (e.source !== window.parent) return;
    if (theme !== "system" && theme !== "light" && theme !== "dark") return;
    if (theme === "system") root.removeAttribute("data-theme");
    else root.setAttribute("data-theme", theme);
    root.style.colorScheme = theme === "system" ? "light dark" : theme;
  });
  if (window.self !== window.top) window.parent.postMessage({ sizingTheme: "?" }, "*");
})();
</script>"""

#: The control. Three drawings, one shown at a time: a sun, a moon, and the two halves together
#: for a reader who has not chosen. Written `hidden`, like Search and the offline control, and
#: revealed by the script -- with scripts off it would cycle nothing.
BUTTON = (
    '<button id="theme" class="theme" type="button" hidden data-state="system"'
    ' title="Follow the system, or choose light or dark">'
    '<svg class="t-system" viewBox="0 0 16 16" width="14" height="14" aria-hidden="true">'
    '<circle cx="8" cy="8" r="4.2" fill="none" stroke="currentColor" stroke-width="1.4"/>'
    '<path d="M8 3.8A4.2 4.2 0 0 1 8 12.2z" fill="currentColor"/>'
    '<path d="M8 .8v1.4M8 13.8v1.4M.8 8h1.4M13.8 8h1.4" stroke="currentColor" stroke-width="1.4"'
    ' stroke-linecap="round"/></svg>'
    '<svg class="t-light" viewBox="0 0 16 16" width="14" height="14" aria-hidden="true">'
    '<circle cx="8" cy="8" r="3.1" fill="none" stroke="currentColor" stroke-width="1.4"/>'
    '<path d="M8 .9v1.7M8 13.4v1.7M.9 8h1.7M13.4 8h1.7M2.9 2.9l1.2 1.2M11.9 11.9l1.2 1.2'
    'M13.1 2.9l-1.2 1.2M4.1 11.9l-1.2 1.2" stroke="currentColor" stroke-width="1.4"'
    ' stroke-linecap="round"/></svg>'
    '<svg class="t-dark" viewBox="0 0 16 16" width="14" height="14" aria-hidden="true">'
    '<path d="M13.2 9.8A5.6 5.6 0 0 1 6.2 2.8 5.6 5.6 0 1 0 13.2 9.8z" fill="none"'
    ' stroke="currentColor" stroke-width="1.4" stroke-linejoin="round"/></svg>'
    "<span>System</span></button>"
)

#: Which drawing is showing. The button carries the state rather than the root, because `system`
#: is an absence on the root and an absence cannot be selected for.
BUTTON_CSS = """
.theme { display: flex; align-items: center; gap: .45rem; font: 13.5px/1 var(--chrome);
         color: var(--muted); background: var(--panel); border: 1px solid var(--edge);
         border-radius: 6px; padding: .45rem .7rem; cursor: pointer; }
.theme:hover { border-color: var(--accent); color: var(--accent); }
.theme svg { display: none; }
.theme[data-state="system"] .t-system,
.theme[data-state="light"] .t-light,
.theme[data-state="dark"] .t-dark { display: block; }
@media (max-width: 46rem) { .theme span { display: none; } .theme { padding: .45rem .5rem; } }
"""
