"""How big the reader wants the text, and the one thing that must not scale with it.

The book already follows the browser's text size. This adds a control of its own, because most
readers never find the browser's, and because the two are not the same thing: a reader who wants
bigger *prose* does not want a bigger chapter list.

That distinction is the whole design. The obvious way to build this -- move the root font size --
is wrong here, and wrong in a way that is invisible until somebody presses the button twice. The
two rails are declared in `rem`, so they grow with the root: at 24px text they go from 272px and
224px to 408px and 336px, which is 744px of a 1440px window spent on the lists either side of
what the reader is reading. The chapter gets 696px, the code loses a third of its columns and an
embedded model drops to its stacked layout. Pressing *larger* makes the book smaller.

So this moves the reading text and nothing else: the prose, and the code in the same proportion.
`--prose` is `82ch` of the prose font, so the reading column follows without being told. The
rails, the breakpoints and the page padding stay where they are.

What it cannot do is help a reader who raised their *browser's* text rather than pressing this.
That reader gets the rails growing under them, and the fix for it is in the stylesheet rather
than here.
"""

from __future__ import annotations

import json

#: What the button cycles through: the prose size in pixels, and the name shown beside it. 18px is
#: what the book has always been. The steps are about a sixth each -- large enough to be worth a
#: press, small enough that the third step is still a book rather than a poster.
SIZES = (("default", 18.0, "Default"), ("large", 21.0, "Large"), ("larger", 24.0, "Larger"))

#: The key in `localStorage`, alongside `nav`, `toc` and `theme`. Per browser, not per page.
KEY = "text"

#: Code against prose. 13.5/18 is the ratio the book was set in, and it is kept rather than
#: recomputed so that a reader who never touches this sees exactly what they saw before.
CODE_RATIO = 13.5 / 18

_PARENT = r"""<script>
(() => {
  const root = document.documentElement;
  const SIZES = __SIZES__;
  const names = SIZES.map((s) => s[0]);
  let text = "default";
  try {
    const kept = localStorage.getItem("text");
    if (names.includes(kept)) text = kept;
  } catch (e) {}
  // Before the first paint, or a reader who chose `larger` watches the book set itself in 18px
  // on every page and then jump.
  const apply = () => {
    const px = SIZES[names.indexOf(text)][1];
    root.style.setProperty("--reading", px + "px");
  };
  apply();
  document.addEventListener("DOMContentLoaded", () => {
    const button = document.getElementById("text");
    const reflect = () => {
      const [, , label] = SIZES[names.indexOf(text)];
      button.dataset.state = text;
      button.querySelector("span").textContent = label;
      button.setAttribute("aria-label", `Text size: ${label}. Press for the next.`);
    };
    button.hidden = false;
    button.addEventListener("click", () => {
      text = names[(names.indexOf(text) + 1) % names.length];
      try {
        if (text === "default") localStorage.removeItem("text");
        else localStorage.setItem("text", text);
      } catch (e) {}
      apply();
      reflect();
      dispatchEvent(new Event("resize"));
    });
    reflect();
  });
})();
</script>"""

PARENT = _PARENT.replace("__SIZES__", json.dumps([[name, px, label] for name, px, label in SIZES]))

#: The control: two letter A's, a small one and a large one, drawn as paths rather than set as
#: `<text>`. A glyph would be a different size on every device, which is the reason the
#: provenance marks are drawn too -- and `<text>` is real text, so the button's own label came
#: back as "A A Default" to anything reading it. Written `hidden` and revealed by the script,
#: like every other control in this header: with scripts off it would cycle nothing.
BUTTON = (
    '<button id="text" class="text-size" type="button" hidden data-state="default"'
    ' title="How big the reading text is">'
    '<svg viewBox="0 0 22 16" width="20" height="14" aria-hidden="true" fill="none"'
    ' stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round">'
    '<path d="M1 12.4 4.1 5.2 7.2 12.4M2.1 9.9h4"/>'
    '<path d="M10.4 12.6 14.9 2.6 19.4 12.6M12 9.1h5.8"/>'
    "</svg><span>Default</span></button>"
)

BUTTON_CSS = """
.text-size { display: flex; align-items: center; gap: .45rem; font: 13.5px/1 var(--chrome);
             color: var(--muted); background: var(--panel); border: 1px solid var(--edge);
             border-radius: 6px; padding: .45rem .7rem; cursor: pointer; }
.text-size:hover { border-color: var(--accent); color: var(--accent); }
.text-size svg { flex: none; }
@media (max-width: 52rem) { .text-size span { display: none; }
                            .text-size { padding: .45rem .5rem; } }
"""
