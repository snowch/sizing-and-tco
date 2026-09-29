#!/usr/bin/env python3
"""Build a chapter's video summary from a talk track, the book's own figures and a local voice.

The chapter videos were first made by a hosted tool from each chapter's text. An audit of every
frame found half of them showing figures their chapter does not give: ranges rounded or cut
short, inputs invented, a ratio drawn as an addition. The failure was structural, not a matter
of prompting: the tool wrote its own slides.

This builds the video the way the book builds a page. A talk track, ``video/<slug>.yml``, lists
the scenes. Each has the words to be spoken and what the slide shows. A slide shows the book's
own generated tables and figures, or a definition box quoted from the chapter, so what is on
screen is what the page says. A number in the narration is a placeholder, ``{node.stat}``,
read from the stamped result the chapter's tables come from, so a figure cannot be typed,
rounded or left behind when the model is re-run. The script refuses a digit anywhere else, the
same rule ``verify-numbers.py`` holds the pages to.

The voice is Kokoro, an open-weight text-to-speech model run locally through ``kokoro-onnx``.
Its two model files are downloaded once into ``--kokoro``. Each scene is spoken separately and
its slide is held for exactly as long as it speaks, so picture and sound cannot drift apart.

    python3 scripts/build-video.py littles_law --kokoro ~/.cache/kokoro
"""

from __future__ import annotations

import argparse
import html
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from bench.outline import CHAPTERS  # noqa: E402
from bench.stamp import RESULTS_DIR  # noqa: E402
from bench.tables import fmt  # noqa: E402

TRACKS = ROOT / "video"
GENERATED = ROOT / "chapters" / "_generated"
FIGURES = ROOT / "chapters" / "_figures"
MODEL_FILES = {
    "kokoro-v1.0.onnx": "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx",
    "voices-v1.0.bin": "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin",
}
WIDTH, HEIGHT = 1920, 1080
#: Silence after each scene, so one slide's last word is not the next slide's first.
PAUSE = 0.6

PLACEHOLDER = re.compile(r"\{([a-z_][a-z0-9_]*)\.(point|p5|p50|p95)\}")


# -- Numbers --------------------------------------------------------------------------------

ONES = [
    "nought",
    "one",
    "two",
    "three",
    "four",
    "five",
    "six",
    "seven",
    "eight",
    "nine",
    "ten",
    "eleven",
    "twelve",
    "thirteen",
    "fourteen",
    "fifteen",
    "sixteen",
    "seventeen",
    "eighteen",
    "nineteen",
]
TENS = ["_", "_", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]
SCALES = ((10**9, "billion"), (10**6, "million"), (1000, "thousand"))


def _below_thousand(n: int) -> str:
    hundreds, rest = divmod(n, 100)
    words = [f"{ONES[hundreds]} hundred"] if hundreds else []
    if rest:
        tens, ones = divmod(rest, 10)
        small = ONES[rest] if rest < 20 else TENS[tens] + (f"-{ONES[ones]}" if ones else "")
        words.append(("and " if hundreds else "") + small)
    return " ".join(words)


def whole(n: int) -> str:
    """A whole number as British English says it: two thousand, one hundred and forty-seven."""
    if n == 0:
        return "nought"
    parts = []
    for size, name in SCALES:
        if n >= size:
            parts.append(f"{_below_thousand(n // size)} {name}")
            n %= size
    tail = ""
    if n:
        if parts and n < 100:
            tail = " and " + _below_thousand(n)
        else:
            parts.append(_below_thousand(n))
    return ", ".join(parts) + tail


def spoken(shown: str) -> str:
    """How a figure as the tables print it is said aloud: 2,147 and 0.644 and $1,508,230."""
    text = shown.strip()
    currency = text.startswith("$")
    text = text.lstrip("$").replace(",", "")
    percent = text.endswith("%")
    text = text.rstrip("%")
    integer, _, decimals = text.partition(".")
    words = whole(int(integer or 0))
    if decimals:
        words += " point " + " ".join(ONES[int(d)] for d in decimals)
    if currency:
        words += " dollars"
    if percent:
        words += " per cent"
    return words


# -- The talk track -------------------------------------------------------------------------


def load_track(slug: str) -> dict:
    track = yaml.safe_load((TRACKS / f"{slug}.yml").read_text())
    chapter = next(c for c in CHAPTERS if c.slug == slug)
    track["chapter"] = chapter
    track["nodes"] = json.loads((RESULTS_DIR / f"{track['result']}.json").read_text())["summary"][
        "nodes"
    ]
    return track


def figure(nodes: dict, name: str, stat: str) -> str:
    """A placeholder's value, formatted exactly as the chapter's tables print it."""
    node = nodes[name]
    value = node["point"] if stat == "point" else node["summary"][stat]
    return fmt(value, node["unit"])


def fill(text: str, nodes: dict, say: bool) -> str:
    def one(match: re.Match) -> str:
        shown = figure(nodes, match[1], match[2])
        return spoken(shown) if say else shown

    return PLACEHOLDER.sub(one, text)


def typed_digits(track: dict) -> list[str]:
    """Every digit written into the track by hand. The chapter number is the outline's."""
    problems = []
    for n, scene in enumerate(track["scenes"], start=1):
        texts = [scene["say"], *_slide_texts(scene["slide"])]
        for text in texts:
            bare = PLACEHOLDER.sub("", text)
            if re.search(r"\d", bare):
                problems.append(f"scene {n}: a typed digit in {text[:60]!r}")
    return problems


def _slide_texts(slide: dict) -> list[str]:
    return [str(v) for k, v in slide.items() if k in ("title", "text", "term")] + [
        str(item) for item in slide.get("items", [])
    ]


# -- Slides ---------------------------------------------------------------------------------

CSS = """
:root { --ink:#263238; --muted:#41555e; --faint:#5a707b; --edge:#dfe5e8; --rule:#c4d0d6;
        --bg:#fdfdfc; --panel:#f2f6f7; --accent:#35648f; --wash:rgba(53,100,143,.09); }
* { box-sizing: border-box; }
html, body { margin:0; width:1920px; height:1080px; background:var(--bg); color:var(--ink); }
body { font-family: Charter, "Bitstream Charter", Georgia, serif; }
.slide { position:absolute; inset:0; padding:120px 160px; display:flex; flex-direction:column;
         justify-content:center; gap:36px; }
.kicker { font:600 30px/1.2 system-ui, sans-serif; letter-spacing:.08em; text-transform:uppercase;
          color:var(--accent); }
h1 { font:600 96px/1.1 system-ui, sans-serif; letter-spacing:-.02em; margin:0; }
h2 { font:600 64px/1.15 system-ui, sans-serif; letter-spacing:-.015em; margin:0; }
.lead { font-size:52px; line-height:1.35; max-width:1500px; margin:0; }
.question { font-size:48px; line-height:1.35; color:var(--muted); font-style:italic; max-width:1500px; }
.box { border-left:10px solid var(--accent); background:var(--wash); padding:48px 56px;
       border-radius:6px; font-size:50px; line-height:1.35; max-width:1560px; }
.box b { font-family: system-ui, sans-serif; }
table { border-collapse:collapse; font:36px/1.3 system-ui, sans-serif; width:100%; }
table + table { margin-top:56px; }
th { text-align:left; color:var(--faint); font-weight:600; font-size:28px; letter-spacing:.04em;
     text-transform:uppercase; padding:0 28px 18px 0; border-bottom:2px solid var(--rule); }
td { padding:22px 28px 22px 0; border-bottom:1px solid var(--edge); font-variant-numeric:tabular-nums; }
td.n, th.n { text-align:right; }
img.fig { width:1600px; height:760px; object-fit:contain; align-self:center;
          background:#fff; border:1px solid var(--edge); border-radius:6px; padding:24px; }
ol { margin:0; padding-left:1.1em; font-size:46px; line-height:1.4; }
ol li { margin:0 0 22px; padding-left:.3em; }
ol li b { font-family: system-ui, sans-serif; }
.foot { position:absolute; left:160px; right:160px; bottom:56px; display:flex;
        justify-content:space-between; font:26px system-ui, sans-serif; color:var(--faint); }
"""


def definition(chapter_path: str, term: str) -> str:
    """The chapter's own definition box for a term, as HTML: quoted, never paraphrased."""
    text = (ROOT / chapter_path).read_text()
    for box in re.findall(r":::\{div\}\n:class: definition\n\n(.*?)\n:::", text, re.S):
        if re.search(rf"\*\*{re.escape(term)}\*\*", box, re.I):
            flat = " ".join(box.split())
            flat = re.sub(r"`([^`]*)`", r"\1", flat)
            flat = html.escape(flat)
            return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", flat)
    raise KeyError(f"{chapter_path} has no definition box for {term!r}")


def table(names: str | list[str], rows: list[str] | None) -> str:
    """Generated tables from chapters/_generated, as HTML, optionally narrowed to some rows."""
    if isinstance(names, list):
        return "".join(table(name, rows) for name in names)
    name = names
    lines = [ln for ln in (GENERATED / f"{name}.md").read_text().splitlines() if ln.startswith("|")]
    cells = [[c.strip() for c in ln.strip("|").split("|")] for ln in lines]
    head, body = cells[0], [r for r in cells[2:] if not rows or r[0] in rows]
    if not body:
        return ""
    numeric = [i for i, c in enumerate(lines[1].strip("|").split("|")) if c.strip().endswith(":")]

    def row(r, tag):
        return "".join(
            f'<{tag} class="{"n" if i in numeric else ""}">{html.escape(c).replace("*", "")}</{tag}>'
            for i, c in enumerate(r)
        )

    return (
        f"<table><tr>{row(head, 'th')}</tr>"
        + "".join(f"<tr>{row(r, 'td')}</tr>" for r in body)
        + "</table>"
    )


def bold(text: str) -> str:
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)


def slide_html(track: dict, scene: dict, n: int, total: int) -> str:
    chapter, slide, nodes = track["chapter"], scene["slide"], track["nodes"]
    kind = slide["kind"]
    title = html.escape(fill(slide.get("title", ""), nodes, say=False))
    if kind == "title":
        inner = (
            f'<div class="kicker">{chapter.label}</div><h1>{html.escape(chapter.title)}</h1>'
            f'<p class="question">{html.escape(chapter.question)}</p>'
        )
    elif kind == "statement":
        inner = (f"<h2>{title}</h2>" if title else "") + (
            f'<p class="lead">{html.escape(fill(slide["text"], nodes, say=False))}</p>'
        )
    elif kind == "definition":
        inner = f'<div class="box">{definition(chapter.path, slide["term"])}</div>'
    elif kind == "table":
        inner = f"<h2>{title}</h2>{table(slide['table'], slide.get('rows'))}"
    elif kind == "figure":
        src = (FIGURES / f"{slide['figure']}.svg").as_uri()
        inner = (f"<h2>{title}</h2>" if title else "") + f'<img class="fig" src="{src}">'
    elif kind == "points":
        items = "".join(f"<li>{bold(html.escape(str(i)))}</li>" for i in slide["items"])
        inner = f"<h2>{title}</h2><ol>{items}</ol>"
    else:
        raise ValueError(f"scene {n}: unknown slide kind {kind!r}")
    foot = (
        f'<div class="foot"><span>Sizing and TCO · {chapter.label} · {html.escape(chapter.title)}'
        f"</span><span>{n} / {total}</span></div>"
        if kind != "title"
        else ""
    )
    return (
        f"<!doctype html><meta charset=utf-8><style>{CSS}</style>"
        f'<div class="slide">{inner}</div>{foot}'
    )


# -- Voice and assembly ---------------------------------------------------------------------


def ensure_model(directory: Path) -> tuple[Path, Path]:
    directory.mkdir(parents=True, exist_ok=True)
    for name, url in MODEL_FILES.items():
        if not (directory / name).exists():
            print(f"fetching {name}")
            subprocess.run(["curl", "-sSLf", "-o", str(directory / name), url], check=True)
    return directory / "kokoro-v1.0.onnx", directory / "voices-v1.0.bin"


def ffmpeg() -> str:
    found = shutil.which("ffmpeg")
    if found:
        return found
    import imageio_ffmpeg

    return imageio_ffmpeg.get_ffmpeg_exe()


def timestamp(seconds: float) -> str:
    h, rest = divmod(seconds, 3600)
    m, s = divmod(rest, 60)
    return f"{int(h):02d}:{int(m):02d}:{s:06.3f}"


def build(slug: str, kokoro_dir: Path, out: Path, only_slides: bool = False) -> Path:
    import soundfile
    from playwright.sync_api import sync_playwright

    track = load_track(slug)
    problems = typed_digits(track)
    if problems:
        raise SystemExit("build-video: " + "; ".join(problems))
    scenes, nodes = track["scenes"], track["nodes"]
    work = Path(tempfile.mkdtemp(prefix=f"video-{slug}-"))
    out.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=_chromium())
        page = browser.new_page(viewport={"width": WIDTH, "height": HEIGHT})
        for n, scene in enumerate(scenes, start=1):
            doc = work / f"{n:02d}.html"
            doc.write_text(slide_html(track, scene, n, len(scenes)))
            page.goto(doc.as_uri())
            page.wait_for_load_state("load")
            page.screenshot(path=str(work / f"{n:02d}.png"))
        browser.close()
    if only_slides:
        for png in sorted(work.glob("*.png")):
            shutil.copy(png, out / f"{slug}-{png.name}")
        return out

    from kokoro_onnx import Kokoro

    model, voices = ensure_model(kokoro_dir)
    voice = Kokoro(str(model), str(voices))
    ff, clips, captions, clock = ffmpeg(), [], ["WEBVTT", ""], 0.0
    for n, scene in enumerate(scenes, start=1):
        words = " ".join(fill(scene["say"], nodes, say=True).split())
        audio, rate = voice.create(
            words, voice=track["voice"], speed=track.get("speed", 1.0), lang="en-gb"
        )
        wav = work / f"{n:02d}.wav"
        soundfile.write(wav, audio, rate)
        length = len(audio) / rate + PAUSE
        clip = work / f"{n:02d}.mp4"
        subprocess.run(
            [
                ff,
                "-v",
                "error",
                "-y",
                "-loop",
                "1",
                "-framerate",
                "24",
                "-i",
                str(work / f"{n:02d}.png"),
                "-i",
                str(wav),
                "-af",
                f"apad=pad_dur={PAUSE}",
                "-t",
                f"{length:.3f}",
                "-c:v",
                "libx264",
                "-tune",
                "stillimage",
                "-pix_fmt",
                "yuv420p",
                "-r",
                "24",
                "-c:a",
                "aac",
                "-b:a",
                "64k",
                "-ac",
                "1",
                "-ar",
                "24000",
                str(clip),
            ],
            check=True,
        )
        clips.append(clip)
        shown = " ".join(fill(scene["say"], nodes, say=False).split())
        captions += [
            str(n),
            f"{timestamp(clock)} --> {timestamp(clock + length - PAUSE)}",
            shown,
            "",
        ]
        clock += length
        print(f"scene {n:2d}: {length:5.1f}s")

    listing = work / "clips.txt"
    listing.write_text("".join(f"file '{c}'\n" for c in clips))
    name = f"{track['chapter'].label}-{slug.replace('_', '-')}"
    video = out / f"{name}.mp4"
    subprocess.run(
        [
            ff,
            "-v",
            "error",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(listing),
            "-c",
            "copy",
            "-movflags",
            "+faststart",
            str(video),
        ],
        check=True,
    )
    (out / f"{name}.vtt").write_text("\n".join(captions))
    print(f"build-video: {video} ({clock / 60:.1f} min)")
    return video


def _chromium() -> str | None:
    fixed = Path("/opt/pw-browsers/chromium")
    return str(fixed) if fixed.exists() else None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("slug", help="the chapter's slug, which names video/<slug>.yml")
    parser.add_argument("--kokoro", type=Path, default=Path.home() / ".cache" / "kokoro")
    parser.add_argument("--out", type=Path, default=ROOT / "_build" / "video")
    parser.add_argument("--slides", action="store_true", help="render the slides only")
    args = parser.parse_args()
    build(args.slug, args.kokoro, args.out, only_slides=args.slides)
    return 0


if __name__ == "__main__":
    sys.exit(main())
