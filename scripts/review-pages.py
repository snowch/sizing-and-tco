#!/usr/bin/env python3
"""Walk the published book in a browser, press everything on it, and write down what went wrong.

    python3 scripts/review-pages.py                                  # every page, the published site
    python3 scripts/review-pages.py --base http://localhost:3000/    # the site `make book` serves
    python3 scripts/review-pages.py --only what-a-workload-is        # one page, by its published name
    python3 scripts/review-pages.py --problems                       # also press every problem's Check
    python3 scripts/review-pages.py --attempts DIR                   # also type in a reader's attempts
    python3 scripts/review-pages.py --list                           # the pages it would walk

`make check` builds the site that deploys, and cannot say what a reader's browser does with it:
whether a table hides the column the prose points at on a phone, whether Escape closes an expanded
model, whether Python starts when a reader presses Check. This looks, at five widths and in the
dark theme, and writes a report to `_build/review/`.

It is the mechanical half of an editorial review, and only that half. It cannot say whether a
sentence lands, whether a cross-reference delivers what it promises, whether a problem is
answerable from the page, or whether a clipped table matters -- which depends on whether the prose
points at what is clipped. Those need a reader, working from the report, the page's text and
screenshots this writes, the markdown source and STYLE.md. The report says so at the top, so
nobody mistakes a clean run for a reviewed book.

What it does, on every page in `myst.yml`'s order -- the preface, the part pages, every chapter
and every appendix:

- **Layout, at each width:** sideways scrolling of the whole page; a header control pushed out of
  the header; each table column the reader cannot see without scrolling; code lines cut at the
  right edge, which matters most where a problem's instructions are a docstring; figure text
  rendered too small to read; each model graph node outside its frame.
- **Every control, at a phone width and a desktop width:** each Expand opened, then closed with
  Escape, after a click inside it where it holds a model, and with its own button if Escape fails.
- **Every model, once:** each slider at both ends of its range, each node clicked, looking for
  NaN, Infinity or undefined in what the reader sees. What each node's Details says is written
  out, because labels and provenance sources reach the reader through the models, not the
  markdown the build's prose checks read.
- **The page itself:** console errors, failed requests, broken links and anchors, images without
  alt text, controls with no accessible name, text below the contrast a reader needs in both
  themes, the icon font, and wording that assumes a mouse a phone does not have.
- **Problems, when asked:** each Check pressed with the stub unchanged, which should fail cleanly;
  and with ``--attempts``, a reader's attempts typed in and checked, with what the page said back.
  Attempts live outside the repository: a correct one is an answer, and CLAUDE.md forbids writing
  an answer anywhere in it.

Service workers are blocked so every run starts clean. The offline install is not exercised.

Needs Playwright and a Chromium it can drive: `requirements-review.txt`. CI does not install
either, and this needs the network, so it is not part of `make check`.
"""

from __future__ import annotations

import argparse
import contextlib
import json
import re
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import UTC, datetime
from importlib import util
from pathlib import Path
from urllib.parse import urldefrag, urljoin, urlparse

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from bench.render import page_order  # noqa: E402

PUBLISHED = "https://snowch.github.io/sizing-and-tco/"
DEFAULT_OUT = ROOT / "_build" / "review"
WIDTHS = (320, 375, 768, 1440, 1920)
HEIGHT = {320: 640, 375: 812, 768: 1024, 1440: 900, 1920: 1080}

#: What each severity asks of the person reading the report. Ordered: the report lists them so.
SEVERITY = {
    "blocks": "a reader cannot go on",
    "hides": "the content is there, and a reader cannot see or reach it",
    "look": "a person should judge whether it matters",
}

#: The verdicts a problem's Check can end on. Anything else is still running.
VERDICT = re.compile(r"Solved\.|\d+ of \d+ tests? pass|could not start|did not start")


def _site():
    """``scripts/build-site.py``, imported, so a page's name is the one the build gives it."""
    spec = util.spec_from_file_location("build_site", ROOT / "scripts" / "build-site.py")
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def pages() -> list[tuple[str, str]]:
    """Every page in reading order, as (source file, published name)."""
    href_for = _site().href_for
    return [(source, href_for(source)) for source in page_order()]


@dataclass
class Finding:
    """One fault in one place, with what was seen at each width it was seen at."""

    severity: str
    kind: str
    where: str
    seen: dict[str, str] = field(default_factory=dict)

    def describe(self) -> str:
        """The detail once where every width agrees, and width by width where they do not."""
        order = sorted(self.seen, key=lambda w: (int(w.split("-")[0]) if w[:1].isdigit() else 0, w))
        details = {self.seen[w] for w in order}
        if len(details) == 1:
            detail = details.pop()
            return (f" — {detail}" if detail else "") + f" ({', '.join(order)})"
        return " — " + "; ".join(f"at {w}: {self.seen[w]}" for w in order)


@dataclass
class Page:
    source: str
    name: str
    title: str = ""
    findings: dict[tuple[str, str, str], Finding] = field(default_factory=dict)
    checks: list[str] = field(default_factory=list)
    attempts: list[str] = field(default_factory=list)
    #: The same fault in several models, gathered so the report says it once: fault -> models.
    in_models: dict[tuple[str, str, str], list[str]] = field(default_factory=dict)

    def add(self, severity: str, kind: str, where: str, detail: str, width: str) -> None:
        found = self.findings.setdefault((severity, kind, where), Finding(severity, kind, where))
        found.seen.setdefault(width, detail)

    def add_in_model(self, severity: str, kind: str, detail: str, model: str) -> None:
        models = self.in_models.setdefault((severity, kind, detail), [])
        if model not in models:
            models.append(model)

    def settle(self, width: str) -> None:
        """Report each fault gathered across models once, naming the models it was in."""
        for (severity, kind, detail), models in self.in_models.items():
            which = ("model " if len(models) < 2 else "models ") + ", ".join(models)
            self.add(severity, kind, f"{detail}, in {which}", "", width)
        self.in_models.clear()

    @property
    def slug(self) -> str:
        return self.name.removesuffix(".html")


# -- what runs in the page ---------------------------------------------------------------------
#
# Raw strings: Python would otherwise eat every backslash in these, and a regular expression that
# no longer parses fails in the browser, where nothing on the Python side notices.

LAYOUT = r"""() => {
  const main = document.querySelector("#main") || document.body;
  const vw = document.documentElement.clientWidth;
  const headings = [...main.querySelectorAll("h1, h2, h3")];
  const where = (el) => {
    const top = el.getBoundingClientRect().top;
    let last = null;
    for (const h of headings) { if (h.getBoundingClientRect().top <= top + 1) last = h; else break; }
    return last ? last.textContent.trim().slice(0, 70) : "the top of the page";
  };
  const shown = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const edge = (el) => {
    for (let a = el.parentElement; a && a !== document.body; a = a.parentElement) {
      if (getComputedStyle(a).overflowX !== "visible") return a.getBoundingClientRect().right;
    }
    return vw;
  };
  const out = { overflow: document.documentElement.scrollWidth - vw, header: [], tables: [],
                code: [], images: [], figures: [] };

  const top = document.querySelector("header.top");
  if (top) {
    const box = top.getBoundingClientRect();
    for (const el of top.querySelectorAll("a, button")) {
      if (!shown(el)) continue;
      const r = el.getBoundingClientRect();
      if (r.top < box.top - 1 || r.bottom > box.bottom + 1 || r.right > vw + 1 || r.left < -1)
        out.header.push((el.getAttribute("aria-label") || el.textContent).trim().slice(0, 40));
    }
  }

  main.querySelectorAll("table").forEach((table, i) => {
    const row = table.querySelector("tr");
    if (!shown(table) || !row) return;
    const hidden = [], cut = [];
    [...row.children].forEach((cell, n) => {
      const r = cell.getBoundingClientRect(), right = edge(cell);
      const name = cell.textContent.trim().slice(0, 40) || `column ${n + 1}`;
      if (r.left >= right - 2) hidden.push(name);
      else if (r.right > right + 1) cut.push(name);
    });
    if (hidden.length || cut.length) out.tables.push({ index: i + 1, where: where(table), hidden, cut });
  });

  main.querySelectorAll("pre").forEach((pre, i) => {
    if (!shown(pre) || pre.scrollWidth <= pre.clientWidth + 1) return;
    const probe = document.createElement("span");
    probe.textContent = "0".repeat(20);
    pre.appendChild(probe);
    const ch = probe.getBoundingClientRect().width / 20;
    probe.remove();
    const s = getComputedStyle(pre);
    const room = Math.floor((pre.clientWidth - parseFloat(s.paddingLeft) - parseFloat(s.paddingRight)) / ch);
    const lines = pre.textContent.split("\n");
    out.code.push({ index: i + 1, where: where(pre), room, lines: lines.length,
                    long: lines.filter((l) => l.length > room).length,
                    problem: !!pre.closest(".problem") });
  });

  main.querySelectorAll("img").forEach((img) => {
    if (!(img.getAttribute("alt") || "").trim()) out.images.push(img.getAttribute("src"));
  });

  let n = 0;
  for (const svg of main.querySelectorAll("svg")) {
    const r = svg.getBoundingClientRect();
    if (r.width < 150 || svg.closest("button")) continue;
    n += 1;
    const box = svg.viewBox && svg.viewBox.baseVal;
    const scale = box && box.width ? r.width / box.width : 1;
    const sizes = [...svg.querySelectorAll("text")].filter((t) => t.textContent.trim())
      .map((t) => parseFloat(getComputedStyle(t).fontSize) * scale);
    if (!sizes.length) continue;
    const named = svg.querySelector("title") || svg.getAttribute("aria-label")
      || (svg.closest("figure") && svg.closest("figure").querySelector("figcaption"));
    out.figures.push({ index: n, where: where(svg), smallest: Math.round(Math.min(...sizes) * 10) / 10,
                       named: !!named });
  }
  return out;
}"""

NAMES = r"""() => {
  const out = [];
  for (const el of document.querySelectorAll("button, input, select, textarea, [role=button]")) {
    const r = el.getBoundingClientRect();
    if (el.hidden || !r.width || el.type === "hidden") continue;
    let name = el.getAttribute("aria-label") || el.getAttribute("title") || "";
    const by = el.getAttribute("aria-labelledby");
    if (!name && by) name = by.split(/\s+/).map((id) => (document.getElementById(id) || {}).textContent || "").join(" ");
    if (!name && el.labels && el.labels.length) name = [...el.labels].map((l) => l.textContent).join(" ");
    if (!name && el.tagName === "BUTTON") name = el.textContent;
    if (!/[A-Za-z0-9]/.test(name || "")) {
      const shown = (el.textContent || el.value || "").trim().slice(0, 12);
      out.push(`${el.tagName.toLowerCase()}${el.id ? "#" + el.id : ""}${shown ? ` "${shown}"` : ""}`);
    }
  }
  return [...new Set(out)];
}"""

CONTRAST = r"""() => {
  const parse = (c) => {
    const m = /rgba?\(([^)]+)\)/.exec(c);
    if (!m) return null;
    const p = m[1].split(/[\s,\/]+/).filter(Boolean).map(Number);
    return [p[0], p[1], p[2], p.length > 3 ? p[3] : 1];
  };
  const lum = (c) => {
    const f = (v) => { v /= 255; return v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4; };
    return 0.2126 * f(c[0]) + 0.7152 * f(c[1]) + 0.0722 * f(c[2]);
  };
  const behind = (el) => {
    const layers = [];
    for (let a = el; a; a = a.parentElement) {
      const s = getComputedStyle(a);
      if (s.backgroundImage !== "none") return null;
      const c = parse(s.backgroundColor);
      if (c && c[3] > 0) { layers.push(c); if (c[3] >= 1) break; }
    }
    let base = [255, 255, 255];
    for (const c of layers.reverse()) base = base.map((v, i) => v * (1 - c[3]) + c[i] * c[3]);
    return base;
  };
  const seen = new Map();
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  for (let t = walker.nextNode(); t; t = walker.nextNode()) {
    const el = t.parentElement;
    if (!t.textContent.trim() || !el || el.closest("script, style, svg, [hidden]")) continue;
    const r = el.getBoundingClientRect();
    if (!r.width || !r.height) continue;
    const s = getComputedStyle(el);
    if (s.visibility === "hidden" || parseFloat(s.opacity) === 0) continue;
    const fg = parse(s.color), bg = behind(el);
    // Transparent text is hidden on purpose: a mark drawn in CSS keeps its word for a screen reader.
    if (!fg || !bg || fg[3] === 0) continue;
    const ink = bg.map((v, i) => v * (1 - fg[3]) + fg[i] * fg[3]);
    const [a, b] = [lum(ink), lum(bg)];
    const ratio = (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05);
    const size = parseFloat(s.fontSize), bold = parseInt(s.fontWeight, 10) >= 700;
    const need = size >= 24 || (bold && size >= 18.66) ? 3 : 4.5;
    if (ratio >= need) continue;
    const key = `${s.color} on ${bg.map(Math.round).join(",")}`;
    if (!seen.has(key)) {
      const cls = typeof el.className === "string" && el.className ? "." + el.className.split(" ")[0] : "";
      seen.set(key, { ratio: Math.round(ratio * 100) / 100, need,
                      sample: t.textContent.trim().slice(0, 50), element: el.tagName.toLowerCase() + cls });
    }
  }
  return [...seen.values()];
}"""

#: Wording that only works with a mouse. A phone has no pointer to rest.
POINTER = r"""() => {
  const text = document.body.innerText;
  const found = text.match(/[^.\n]*\b(hover|rest the pointer|mouse|right-click|double-click)\b[^.\n]*[.\n]/gi);
  return [...new Set((found || []).map((s) => s.trim()))];
}"""

ICON_FONT = r"""async () => {
  await document.fonts.ready;
  // Only a box whose icon is a font's ligature depends on the font arriving.
  const uses = [...document.querySelectorAll(".admonition.note, .definition, .takeaways, .example")]
    .some((e) => getComputedStyle(e, "::before").fontFamily.includes("Material Icons"));
  if (!uses) return true;
  return [...document.fonts].some((f) => f.family.replace(/["']/g, "") === "Material Icons" && f.status === "loaded");
}"""

LINKS = r"""() => {
  const ids = new Set([...document.querySelectorAll("[id], a[name]")].map((e) => e.id || e.name));
  const here = location.href.split("#")[0];
  const out = [];
  for (const a of document.querySelectorAll("a[href]")) {
    const href = a.href;
    if (!/^https?:/.test(href)) continue;
    const [base, frag] = href.split("#");
    if (base === here && frag && !ids.has(decodeURIComponent(frag))) out.push({ href, missing: true, text: a.textContent.trim().slice(0, 40) });
    else out.push({ href, missing: false, text: a.textContent.trim().slice(0, 40) });
  }
  return out;
}"""

VIEWER_LAYOUT = r"""() => {
  const scroller = document.getElementById("graph-scroll");
  const title = ((document.querySelector("header h1") || {}).textContent || "").trim();
  if (!scroller) return { title, total: 0, outside: [], graph: false };
  const box = scroller.getBoundingClientRect();
  const nodes = [...document.querySelectorAll("g.node")];
  if (!box.width) return { title, total: nodes.length, outside: [], graph: false };
  const outside = nodes.filter((g) => {
    const r = g.getBoundingClientRect();
    return r.right > box.right + 1 || r.left < box.left - 1;
  }).map((g) => g.dataset.node);
  return { title, total: nodes.length, outside, graph: true };
}"""

VIEWER_PRESS = r"""() => {
  const bad = /\bNaN\b|\bInfinity\b|\bundefined\b|\[object Object\]/;
  // Only where a value is shown. A note may say "infinity" on purpose, to explain a clamp.
  const shown = (root) => [...root.querySelectorAll("td, svg text, [id^='v-'], .state, .badge, .banner")]
    .map((e) => e.textContent).join("\n");
  const $ = (id) => document.getElementById(id);
  const problems = [];
  for (const id of ["toggle-controls", "toggle-detail"]) {
    const t = $(id);
    if (t && t.getAttribute("aria-expanded") !== "true") t.click();
  }
  let emptyGrey = false;
  for (const input of document.querySelectorAll("input[type=range]")) {
    for (const v of [input.min, input.max]) {
      input.value = v;
      input.dispatchEvent(new Event("input", { bubbles: true }));
      const m = bad.exec(shown(document));
      if (m) problems.push(`${input.id.replace(/^s-/, "")} at ${v} shows "${m[0]}"`);
      const note = [...document.querySelectorAll("#outputs .note")].some((p) => p.textContent.startsWith("Greyed rows"));
      if (note && !document.querySelector("#outputs tr.inert")) emptyGrey = true;
    }
  }
  if ($("reset")) $("reset").click();
  const details = [];
  for (const g of document.querySelectorAll("g.node")) {
    g.dispatchEvent(new MouseEvent("click", { bubbles: true }));
    const body = ($("detail-body") || document.body).innerText.trim();
    const m = bad.exec(shown($("detail-body") || document.body));
    if (m) problems.push(`Details for ${g.dataset.node} shows "${m[0]}"`);
    details.push(`### ${g.dataset.node}\n\n${body}\n`);
  }
  const notes = [...document.querySelectorAll("header, .legend, #controls-content > .note")]
    .map((e) => e.innerText.trim()).filter(Boolean);
  return { problems, emptyGrey, details, notes };
}"""

FUTURES_PRESS = r"""async () => {
  const bad = /\bNaN\b|\bInfinity\b|\bundefined\b|\[object Object\]/;
  const shown = () => [...document.querySelectorAll("svg text, [id^='v-'], .value, .ends, td")]
    .map((e) => e.textContent).join("\n");
  const problems = [];
  for (const id of ["one", "many", "again", "one"]) {
    const b = document.getElementById(id);
    if (!b) { problems.push(`no #${id} button`); continue; }
    b.click();
    await new Promise((r) => setTimeout(r, 1500));
    const m = bad.exec(shown());
    if (m) problems.push(`after pressing #${id} the page shows "${m[0]}"`);
  }
  return problems;
}"""

#: The heading an element sits under, which is how the report names a place on the page.
UNDER = r"""(el) => {
  const top = el.getBoundingClientRect().top;
  let heading = null;
  for (const h of document.querySelectorAll("#main h1, #main h2, #main h3")) {
    if (h.getBoundingClientRect().top <= top + 1) heading = h; else break;
  }
  return heading ? heading.textContent.trim().slice(0, 70) : "the top of the page";
}"""

#: What an Expand holds, numbered the way the report counts models and futures pages.
EXPAND_HOLDS = r"""(button) => {
  const box = button.closest("figure, .wide-block, .editable-block") || button.parentElement;
  const frame = box.querySelector("iframe");
  if (frame) {
    const kind = frame.classList.contains("futures") ? "futures" : "viewer";
    const n = [...document.querySelectorAll(`#main iframe.${kind}`)].indexOf(frame) + 1;
    return `${kind === "viewer" ? "model" : "futures"} ${n}`;
  }
  return box.querySelector("table") ? "the table"
    : box.classList.contains("editable-block") ? "the problem's code" : "the code block";
}"""

PROBLEM_LABEL = r"""(problem) => {
  for (let el = problem.previousElementSibling; el; el = el.previousElementSibling) {
    const m = /^\s*(\d+\.\d+)/.exec(el.textContent);
    if (m) return m[1];
    if (/^H[1-3]$/.test(el.tagName)) break;
  }
  return "";
}"""

TYPE_IN = r"""(pre, code) => {
  pre.textContent = code;
  pre.dispatchEvent(new Event("input", { bubbles: true }));
}"""


# -- fetching ----------------------------------------------------------------------------------


class Fetcher:
    """Plain HTTP from Python, for link checks and, when asked, for everything the browser loads.

    The browser can be pointed at it because some proxies refuse a browser's retries where they
    let a plain client through; in that case the page cannot even start Python, and the review
    would report the network rather than the book.
    """

    def __init__(self) -> None:
        self.cache: dict[str, tuple[int, dict[str, str], bytes]] = {}

    def get(self, url: str, timeout: float = 60) -> tuple[int, dict[str, str], bytes]:
        if url in self.cache:
            return self.cache[url]
        request = urllib.request.Request(url, headers={"User-Agent": "sizing-and-tco review"})
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                got = (response.status, dict(response.headers), response.read())
        except urllib.error.HTTPError as error:
            got = (error.code, dict(error.headers or {}), error.read() or b"")
        self.cache[url] = got
        return got

    def route(self, route) -> None:
        request = route.request
        if request.method != "GET" or not request.url.startswith("http"):
            route.continue_()
            return
        try:
            status, headers, body = self.get(request.url)
        except Exception:  # the browser reports a failed request as it would
            route.abort()
            return
        drop = {"content-encoding", "transfer-encoding", "content-length", "connection"}
        kept = {k: v for k, v in headers.items() if k.lower() not in drop}
        kept["access-control-allow-origin"] = "*"
        route.fulfill(status=status, headers=kept, body=body)


# -- one page ----------------------------------------------------------------------------------


class Reviewer:
    def __init__(self, browser, args, fetcher: Fetcher) -> None:
        self.browser = browser
        self.args = args
        self.fetcher = fetcher
        self.links: dict[str, str | None] = {}
        widths = sorted(args.widths)
        self.deep = 1440 if 1440 in widths else widths[-1]
        self.narrow = widths[0] if widths[0] <= 400 else None
        self.phone = next((w for w in widths if 360 <= w <= 400), self.narrow)

    def context(self, width: int, dark: bool = False):
        touch = width < 1024
        ctx = self.browser.new_context(
            viewport={"width": width, "height": HEIGHT.get(width, 900)},
            color_scheme="dark" if dark else "light",
            has_touch=touch,
            is_mobile=width < 800,
            service_workers="block",
        )
        if self.args.fetch_in_python:
            ctx.route("**/*", self.fetcher.route)
        return ctx

    def review(self, page: Page) -> None:
        folder = self.args.out / page.slug
        folder.mkdir(parents=True, exist_ok=True)
        url = urljoin(self.args.base, page.name)
        for width in sorted(self.args.widths):
            self.one_width(page, url, folder, width, dark=False)
        if not self.args.no_dark:
            self.one_width(page, url, folder, self.deep, dark=True)

    def one_width(self, page: Page, url: str, folder: Path, width: int, dark: bool) -> None:
        label = f"{width}{'-dark' if dark else ''}"
        shots = folder / label
        shots.mkdir(exist_ok=True)
        ctx = self.context(width, dark)
        tab = ctx.new_page()
        origin = urlparse(self.args.base).netloc

        def failed(request) -> None:
            same = urlparse(request.url).netloc == origin
            page.add(
                "blocks" if same else "hides",
                "a request failed",
                request.url[:120],
                str(request.failure),
                label,
            )

        def status(response) -> None:
            if response.status >= 400:
                page.add("blocks", "HTTP error", response.url[:120], str(response.status), label)

        def console(message) -> None:
            if message.type == "error" and "ServiceWorker" not in message.text:
                page.add("look", "console error", "the page", message.text[:300], label)

        tab.on("requestfailed", failed)
        tab.on("response", status)
        tab.on("console", console)
        tab.on(
            "pageerror",
            lambda e: page.add("blocks", "script error", "the page", str(e)[:300], label),
        )
        try:
            tab.goto(url, wait_until="networkidle", timeout=90_000)
        except Exception as error:  # a page that will not load is the finding
            page.add("blocks", "page did not load", url, str(error)[:200], label)
            ctx.close()
            return
        page.title = page.title or tab.title().removesuffix(" — Sizing and TCO")
        tab.wait_for_timeout(500)
        tab.screenshot(path=shots / "top.png")

        self.layout(page, tab, label, width)
        if width == self.phone and not dark:
            for sentence in tab.evaluate(POINTER):
                page.add("look", "wording assumes a mouse", "the page", sentence, label)
        self.viewers(
            page,
            tab,
            shots,
            label,
            phone=(width == self.phone and not dark),
            deep=(width == self.deep and not dark),
        )
        self.element_shots(tab, shots)
        if not dark and width in (self.phone, self.deep):
            self.expands(page, tab, shots, label)
        self.open_details(page, tab, label)
        if width == self.deep:
            for item in tab.evaluate(CONTRAST):
                page.add(
                    "hides",
                    "contrast too low",
                    item["element"],
                    f"{item['ratio']}:1, needs {item['need']}:1 -- “{item['sample']}”",
                    label,
                )
        if width == self.deep and not dark:
            self.page_once(page, tab, folder, label)
        ctx.close()

    def layout(self, page: Page, tab, label: str, width: int) -> None:
        got = tab.evaluate(LAYOUT)
        if got["overflow"] > 1:
            page.add(
                "hides",
                "the page scrolls sideways",
                "the page",
                f"{got['overflow']}px wider than the screen",
                label,
            )
        for control in got["header"]:
            page.add(
                "hides", "header control outside the header", "the header", f"“{control}”", label
            )
        for table in got["tables"]:
            parts = []
            if table["hidden"]:
                parts.append("out of sight: " + ", ".join(table["hidden"]))
            if table["cut"]:
                parts.append("cut through: " + ", ".join(table["cut"]))
            page.add(
                "hides",
                "table columns need sideways scrolling",
                f"table {table['index']}, under “{table['where']}”",
                "; ".join(parts),
                label,
            )
        for code in got["code"]:
            what = "problem's code" if code["problem"] else "code block"
            page.add(
                "look" if not code["problem"] else "hides",
                f"{what} lines cut at the right edge",
                f"block {code['index']}, under “{code['where']}”",
                f"{code['long']} of {code['lines']} lines are longer than the {code['room']} characters that fit",
                label,
            )
        for src in got["images"]:
            page.add("hides", "image with no alt text", src or "an image", "no alt", label)
        for figure in got["figures"]:
            if figure["smallest"] < 9:
                page.add(
                    "look",
                    "figure text below 9px",
                    f"figure {figure['index']}, under “{figure['where']}”",
                    f"smallest text renders at {figure['smallest']}px",
                    label,
                )
            if not figure["named"] and width == self.deep:
                page.add(
                    "look",
                    "figure with no text alternative",
                    f"figure {figure['index']}, under “{figure['where']}”",
                    "no <title>, aria-label or caption",
                    label,
                )

    def frame_of(self, tab, element, ready: str):
        """The frame inside an iframe, once its content has drawn. Frames load lazily."""
        element.scroll_into_view_if_needed()
        deadline = time.monotonic() + self.args.timeout
        while time.monotonic() < deadline:
            frame = element.content_frame()
            try:
                if frame and frame.query_selector(ready):
                    tab.wait_for_timeout(300)
                    return frame
            except Exception:  # the frame is navigating; try again
                pass
            tab.wait_for_timeout(250)
        return None

    def viewers(self, page: Page, tab, shots: Path, label: str, phone: bool, deep: bool) -> None:
        transcript = []
        for i, element in enumerate(tab.query_selector_all("#main iframe.viewer"), 1):
            frame = self.frame_of(tab, element, "body > *")
            where = f"model {i}, under “{element.evaluate(UNDER)}”"
            if not frame:
                page.add(
                    "blocks", "model did not load", where, element.get_attribute("src") or "", label
                )
                continue
            element.screenshot(path=shots / f"model-{i}.png")
            if not frame.query_selector("#toggle-controls"):
                # Not one of the book's models: Appendix H's viewer waits for a reader's own
                # file. It loaded, and there is nothing in it yet to press.
                continue
            got = frame.evaluate(VIEWER_LAYOUT)
            if got["outside"]:
                page.add(
                    "look",
                    "graph nodes outside the frame",
                    where,
                    f"{len(got['outside'])} of {got['total']} need sideways scrolling: "
                    + ", ".join(got["outside"][:8])
                    + ("…" if len(got["outside"]) > 8 else ""),
                    label,
                )
            if phone:
                for sentence in frame.evaluate(POINTER):
                    page.add_in_model("look", "wording assumes a mouse", sentence, str(i))
            if not deep:
                continue
            for name in frame.evaluate(NAMES):
                page.add_in_model("look", "control with no accessible name", name, str(i))
            pressed = frame.evaluate(VIEWER_PRESS)
            for problem in pressed["problems"]:
                page.add("blocks", "a model shows a broken value", where, problem, label)
            if pressed["emptyGrey"]:
                page.add(
                    "look",
                    "a note describes greyed rows and none are grey",
                    where,
                    "“Greyed rows cannot be moved by …”, with every row moving",
                    label,
                )
            element.screenshot(path=shots / f"model-{i}-open.png")
            transcript.append(
                f"## {where}\n\n"
                + "\n\n".join(pressed["notes"])
                + "\n\n"
                + "\n".join(pressed["details"])
            )
        for i, element in enumerate(tab.query_selector_all("#main iframe.futures"), 1):
            frame = self.frame_of(tab, element, "#one")
            where = f"futures {i}, under “{element.evaluate(UNDER)}”"
            if not frame:
                page.add(
                    "blocks",
                    "futures page did not load",
                    where,
                    element.get_attribute("src") or "",
                    label,
                )
                continue
            element.screenshot(path=shots / f"futures-{i}.png")
            if deep:
                for problem in frame.evaluate(FUTURES_PRESS):
                    page.add(
                        "blocks", "the futures page shows a broken value", where, problem, label
                    )
                element.screenshot(path=shots / f"futures-{i}-pressed.png")
        page.settle(label)
        if transcript:
            (self.args.out / page.slug / "models.md").write_text(
                f"# What the models on {page.name} say, node by node\n\n" + "\n\n".join(transcript)
            )

    def element_shots(self, tab, shots: Path) -> None:
        shown = {
            "table": "#main table",
            "figure": "#main figure:not(:has(iframe))",
            "problem": "#main .problem",
        }
        for kind, selector in shown.items():
            for i, element in enumerate(tab.query_selector_all(selector), 1):
                try:
                    if element.is_visible():
                        element.scroll_into_view_if_needed()
                        element.screenshot(path=shots / f"{kind}-{i}.png")
                except Exception:  # a screenshot is evidence, never a finding
                    pass

    def expands(self, page: Page, tab, shots: Path, label: str) -> None:
        """Open every Expand, then close it the ways a reader would: Escape, then its button.

        A model is tried twice, because a reader who expands one then clicks inside it -- on a
        node, a slider -- has moved the keyboard into the model's own page, where the chapter's
        Escape handler cannot hear it.
        """
        for i, button in enumerate(tab.query_selector_all("#main button.expand"), 1):
            if not button.is_visible():
                continue
            # Named by what it holds and where, so the same box has the same name at every
            # width: a table only gets its button at the widths that squeeze it.
            where = f"{button.evaluate(EXPAND_HOLDS)}, under “{button.evaluate(UNDER)}”"
            frame = button.evaluate_handle(
                "(b) => (b.closest('figure, .wide-block, .editable-block') || b.parentElement)"
                ".querySelector('iframe') || null"
            ).as_element()
            if not self.expand(page, tab, button, where, label):
                continue
            tab.screenshot(path=shots / f"expand-{i}.png")
            tab.keyboard.press("Escape")
            tab.wait_for_timeout(500)
            if tab.query_selector(".expanded"):
                page.add(
                    "look",
                    "Escape does not close an expanded box",
                    where,
                    "focus on the page",
                    label,
                )
                if not self.shut(page, tab, where, label):
                    continue
            if not frame or not self.expand(page, tab, button, where, label):
                continue
            with contextlib.suppress(Exception):  # the click is the reader's; Escape comes anyway
                frame.click(position={"x": 40, "y": 40}, timeout=3000)
            tab.keyboard.press("Escape")
            tab.wait_for_timeout(500)
            if tab.query_selector(".expanded"):
                page.add(
                    "look",
                    "Escape does not close an expanded box",
                    where,
                    "after a click inside the model",
                    label,
                )
                self.shut(page, tab, where, label)

    def expand(self, page: Page, tab, button, where: str, label: str) -> bool:
        button.scroll_into_view_if_needed()
        button.click()
        tab.wait_for_timeout(600)
        covers = tab.evaluate(
            "() => { const e = document.querySelector('.expanded'); if (!e) return null;"
            " const r = e.getBoundingClientRect();"
            " return r.width >= innerWidth - 2 && r.height >= innerHeight - 2; }"
        )
        if covers is None:
            page.add("blocks", "Expand opened nothing", where, "", label)
            return False
        if not covers:
            page.add("hides", "an expanded box does not fill the screen", where, "", label)
        return True

    def shut(self, page: Page, tab, where: str, label: str) -> bool:
        """Close an expanded box with its own button, as a reader would after Escape failed."""
        close = tab.query_selector(".expanded button.expand")
        if close:
            close.click()
            tab.wait_for_timeout(500)
        if tab.query_selector(".expanded"):
            page.add("blocks", "an expanded box cannot be closed", where, "", label)
            tab.evaluate("() => history.back()")
            tab.wait_for_timeout(500)
            return False
        return True

    def open_details(self, page: Page, tab, label: str) -> None:
        spare = "() => document.documentElement.scrollWidth - document.documentElement.clientWidth"
        before = tab.evaluate(spare)
        tab.evaluate(
            "() => document.querySelectorAll('#main details').forEach((d) => { d.open = true; })"
        )
        tab.wait_for_timeout(200)
        after = tab.evaluate(spare)
        if after > max(before, 1):
            page.add(
                "hides",
                "an opened collapsible makes the page scroll sideways",
                "the page",
                f"{after}px wider than the screen",
                label,
            )

    def page_once(self, page: Page, tab, folder: Path, label: str) -> None:
        """What only needs doing once: text, names, links, the icon font, the problems."""
        (folder / "text.txt").write_text(
            tab.inner_text("#main") if tab.query_selector("#main") else ""
        )
        for name in tab.evaluate(NAMES):
            page.add("look", "control with no accessible name", "the page", name, label)
        if not tab.evaluate(ICON_FONT):
            page.add(
                "hides",
                "the icon font did not load",
                "every note, definition and takeaway box",
                "the boxes show the icon's name, such as “info”, instead of the icon",
                label,
            )
        self.check_links(page, tab, label)
        if self.args.problems or self.args.attempts:
            self.problems(page, tab, folder, label)

    def check_links(self, page: Page, tab, label: str) -> None:
        origin = urlparse(self.args.base).netloc
        for link in tab.evaluate(LINKS):
            href, text = link["href"], link["text"]
            if link["missing"]:
                page.add("blocks", "link to a missing anchor", f"“{text}”", href, label)
                continue
            base, frag = urldefrag(href)
            internal = urlparse(base).netloc == origin
            if not internal and self.args.no_external_links:
                continue
            if base not in self.links:
                self.links[base] = self.fetch_page(base, internal)
            body = self.links[base]
            if body is None:
                page.add(
                    "blocks" if internal else "look",
                    "broken link",
                    f"“{text}”",
                    href,
                    label,
                )
            elif frag and internal and not re.search(rf'(id|name)="{re.escape(frag)}"', body):
                page.add("blocks", "link to a missing anchor", f"“{text}”", href, label)

    def fetch_page(self, url: str, internal: bool) -> str | None:
        try:
            status, _, body = self.fetcher.get(url, timeout=30 if internal else 15)
        except Exception:  # unreachable is the finding
            return None
        if status >= 400:
            return None
        return body.decode("utf-8", "replace") if internal else ""

    def problems(self, page: Page, tab, folder: Path, label: str) -> None:
        attempts_dir = self.args.attempts / page.slug if self.args.attempts else None
        record = folder / "problems"
        record.mkdir(exist_ok=True)
        for i, problem in enumerate(tab.query_selector_all("#main .problem"), 1):
            number = problem.evaluate(PROBLEM_LABEL) or f"problem {i}"
            editable = problem.query_selector("pre.editable")
            if not editable or not problem.query_selector(".check-here"):
                continue
            stub = editable.evaluate("(p) => p.textContent")
            if self.args.problems:
                verdict, output = self.press_check(tab, problem)
                page.checks.append(
                    f"{number}, as written: {verdict.splitlines()[0] if verdict else 'no verdict'}"
                )
                (record / f"{number}-stub.txt").write_text(verdict + "\n\n" + output)
                if not verdict:
                    page.add(
                        "blocks",
                        "Check gave no verdict",
                        number,
                        f"nothing after {self.args.check_timeout}s",
                        label,
                    )
                elif "did not start" in verdict or "could not start" in verdict:
                    page.add(
                        "blocks",
                        "Check could not run",
                        number,
                        verdict.splitlines()[0][:300],
                        label,
                    )
                elif verdict.startswith("Solved"):
                    page.add(
                        "blocks",
                        "the stub already passes",
                        number,
                        "an unedited stub is solved",
                        label,
                    )
                elif "fault in the book" in verdict:
                    page.add("blocks", "the book's own checks fail", number, verdict[:300], label)
            if not attempts_dir or not attempts_dir.is_dir():
                continue
            boxes = problem.query_selector_all("pre.editable")
            for attempt in sorted(attempts_dir.glob(f"{number}-*")):
                text = attempt.read_text()
                # Into the box that holds the function the attempt defines: a problem can show
                # another problem's function above its own (ch12's 12.2 shows 12.1's).
                box = self.box_for(boxes, text) or editable
                before = box.evaluate("(p) => p.textContent")
                box.evaluate(TYPE_IN, text)
                verdict, output = self.press_check(tab, problem)
                name = attempt.stem
                (record / f"{name}.txt").write_text(verdict + "\n\n" + output)
                problem.screenshot(path=record / f"{name}.png")
                page.attempts.append(
                    f"`{attempt.name}`: {verdict.splitlines()[0] if verdict else 'no verdict'}"
                )
                box.evaluate(TYPE_IN, before)
            editable.evaluate(TYPE_IN, stub)

    @staticmethod
    def box_for(boxes, text: str):
        """The editable box defining the same function as the attempt, if one does."""
        wanted = re.search(r"^def (\w+)", text, re.M)
        if not wanted:
            return None
        for box in boxes:
            if re.search(rf"^def {wanted[1]}\b", box.evaluate("(p) => p.textContent"), re.M):
                return box
        return None

    def press_check(self, tab, problem) -> tuple[str, str]:
        button = problem.query_selector(".check-here")
        try:
            button.click(timeout=5000)
        except Exception:  # the page is still scrolling to the last verdict; press it in place
            button.evaluate("(b) => b.click()")
        verdicts = problem.query_selector(".verdicts")
        deadline = time.monotonic() + self.args.check_timeout
        text = ""
        while time.monotonic() < deadline:
            tab.wait_for_timeout(1000)
            text = verdicts.inner_text() if verdicts else ""
            if VERDICT.search(text):
                break
        else:
            return "", text
        output = verdicts.evaluate(
            "(v) => { const t = v.querySelector('pre.terminal'); return t ? t.textContent : ''; }"
        )
        return text.strip(), output


# -- the report --------------------------------------------------------------------------------

NOT_CHECKED = """\
## What this pass did not check

A clean run here is not a reviewed page. These need a reader, working from each page's
`text.txt`, `models.md` and screenshots beside this report, the markdown source, STYLE.md and
CLAUDE.md:

- whether each sentence and paragraph lands: STYLE.md's two passes;
- whether each cross-reference delivers what it promises (“problem 1.3 asks you to …”);
- whether each number in the prose matches the table and the model beside it;
- whether each problem is answerable from the page, and whether its feedback helps a reader
  who got it wrong -- type plausible wrong attempts in with `--attempts`;
- which of the layout findings below matter: a hidden column matters when the prose points
  at it;
- the offline install, which this blocks, and any browser but Chromium.
"""


def report(pages_done: list[Page], args, version: str) -> str:
    when = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
    widths = ", ".join(str(w) for w in sorted(args.widths))
    lines = [
        "# Editorial review: the mechanical pass",
        "",
        f"{args.base} · {when} · Chromium {version} · widths {widths}px"
        + (
            ""
            if args.no_dark
            else f", and the dark theme at {1440 if 1440 in args.widths else max(args.widths)}px"
        ),
        "",
        NOT_CHECKED,
        "## Severities",
        "",
        *[f"- **{name}**: {meaning}." for name, meaning in SEVERITY.items()],
        "",
        "## Summary",
        "",
        "| Page | blocks | hides | look |",
        "|---|---:|---:|---:|",
    ]
    for page in pages_done:
        counts = {s: sum(1 for f in page.findings.values() if f.severity == s) for s in SEVERITY}
        lines.append(
            f"| [{page.title or page.name}](#{page.slug}) | {counts['blocks']} | {counts['hides']} | {counts['look']} |"
        )
    for page in pages_done:
        lines += ["", f'<a id="{page.slug}"></a>', f"## {page.title or page.name}", ""]
        lines.append(f"`{page.source}` · {urljoin(args.base, page.name)} · files in `{page.slug}/`")
        for severity in SEVERITY:
            found = [f for f in page.findings.values() if f.severity == severity]
            if not found:
                continue
            lines += ["", f"### {severity.capitalize()}", ""]
            for f in sorted(found, key=lambda f: (f.kind, f.where)):
                lines.append(f"- **{f.kind}**, {f.where}{f.describe()}")
        if page.checks:
            lines += ["", "### Problems, as written", "", *[f"- {c}" for c in page.checks]]
        if page.attempts:
            lines += ["", "### Attempts", "", *[f"- {a}" for a in page.attempts]]
        if not page.findings and not page.checks:
            lines += ["", "Nothing found."]
    return "\n".join(lines) + "\n"


# -- the command -------------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--base", default=PUBLISHED, help=f"the site to walk (default {PUBLISHED})")
    parser.add_argument(
        "--only", nargs="+", default=[], metavar="NAME", help="published page names"
    )
    parser.add_argument("--widths", type=int, nargs="+", default=list(WIDTHS), metavar="PX")
    parser.add_argument("--no-dark", action="store_true", help="skip the dark-theme pass")
    parser.add_argument("--problems", action="store_true", help="press each problem's Check")
    parser.add_argument(
        "--attempts",
        type=Path,
        metavar="DIR",
        help="DIR/<page>/<problem>-<label>.<ext>, typed into that problem and checked. "
        "Keep DIR outside the repository: a correct attempt is an answer.",
    )
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--timeout", type=float, default=20, help="seconds to wait for a model")
    parser.add_argument(
        "--check-timeout", type=float, default=240, help="seconds to wait for a Check"
    )
    parser.add_argument("--no-external-links", action="store_true")
    parser.add_argument(
        "--fetch-in-python",
        action="store_true",
        help="load everything through Python rather than the browser's own network, for a "
        "proxy the browser cannot use",
    )
    parser.add_argument("--list", action="store_true", help="print the pages and stop")
    args = parser.parse_args()
    args.base = args.base.rstrip("/") + "/"

    chosen = pages()
    if args.only:
        wanted = {n.removesuffix(".html") for n in args.only}
        known = {name.removesuffix(".html") for _, name in chosen}
        unknown = sorted(wanted - known)
        if unknown:
            print(f"no page called {', '.join(unknown)}; --list shows every name", file=sys.stderr)
            return 2
        chosen = [(s, n) for s, n in chosen if n.removesuffix(".html") in wanted]
    if args.list:
        for source, name in chosen:
            print(f"{name:45} {source}")
        return 0

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print(
            "This needs Playwright, which CI does not install:\n"
            "  python3 -m pip install -r requirements-review.txt\n"
            "  python3 -m playwright install chromium   # unless a Chromium is already provided",
            file=sys.stderr,
        )
        return 2

    args.out.mkdir(parents=True, exist_ok=True)
    fetcher = Fetcher()
    done: list[Page] = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        reviewer = Reviewer(browser, args, fetcher)
        for n, (source, name) in enumerate(chosen, 1):
            page = Page(source, name)
            started = time.monotonic()
            print(f"[{n}/{len(chosen)}] {name}", end="", flush=True)
            try:
                reviewer.review(page)
            except Exception as error:  # one page that trips the walker must not cost the run
                page.add(
                    "look",
                    "the review could not finish this page",
                    "the page",
                    repr(error)[:300],
                    "-",
                )
            counts = {
                s: sum(1 for f in page.findings.values() if f.severity == s) for s in SEVERITY
            }
            print(
                f" — {counts['blocks']} blocks, {counts['hides']} hides, {counts['look']} look"
                f" ({time.monotonic() - started:.0f}s)"
            )
            done.append(page)
            # After every page, so a long run that stops still leaves what it found.
            (args.out / "report.md").write_text(report(done, args, browser.version))
            (args.out / "findings.json").write_text(
                json.dumps({p.name: [vars(f) for f in p.findings.values()] for p in done}, indent=2)
            )
        browser.close()
    print(f"\nWrote {args.out / 'report.md'}")
    return 1 if any(f.severity == "blocks" for p in done for f in p.findings.values()) else 0


if __name__ == "__main__":
    sys.exit(main())
