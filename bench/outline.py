"""The book's shape, in one machine-readable place.

PLAN.md holds the argument — what each chapter is for and what it must produce. This module holds
only the facts a script or a test needs: the number, the title, the part, the question, and what
the chapter owes the reader before it stops being a draft.

Keeping them apart is deliberate. Prose that tries to be a data structure goes stale silently; a
data structure that tries to be prose stops being readable. ``tests/test_book.py`` ties the two
together by checking that every chapter here appears in ``myst.yml``'s table of contents, exists
on disk, and declares in its own header the model or results named here.
"""

from __future__ import annotations

from dataclasses import dataclass

#: What a chapter means when it says where its figures came from.
SOURCE_MEANING = {
    "corpus": "a deterministic measurement over a declared corpus with a named codec",
    "rig": "a timing taken natively on the declared reference machine",
    "estate": "an observation of a running system, disclosed rather than verified",
    "model": "a stamped run of a model file in models/",
}


@dataclass(frozen=True)
class Chapter:
    number: int
    slug: str
    title: str
    part: str
    #: The one question the chapter answers. Its opening paragraph is an expansion of this.
    question: str
    #: What this chapter must produce before it loses its ``[DRAFT]`` marker, in one line.
    #:
    #: A stub that names its debt is a table of contents for work not yet done. A stub that names
    #: a placeholder is twenty identical pages.
    owes: str | None = None
    #: Which model files and stamped results this chapter's figures come from. Checked by
    #: ``tests/test_book.py`` to be real, and rendered as a row in the chapter header — because
    #: prose saying the same thing gets dropped the first time a chapter is rewritten, and data
    #: does not.
    consumes: tuple[str, ...] = ()
    #: Earlier chapters this one needs. Checked to point backwards.
    needs: tuple[str, ...] = ()

    @property
    def anchor(self) -> str:
        """The chapter's identity: its title, and never its position.

        Everything that must survive a chapter being inserted uses this — the MyST label, the file
        on disk, the directory its problems live in, the ids of its figures, the URL a reader
        bookmarks. The number is deliberately absent: a chapter number is a number, it goes stale,
        and the rule here is the rule for every other number in this book. Derive it, never type
        it.
        """
        return self.slug.replace("_", "-")

    @property
    def label(self) -> str:
        """``ch13`` — how prose refers to a chapter. Derived from position, never an identifier."""
        return f"ch{self.number:02d}"

    @property
    def path(self) -> str:
        return f"chapters/{self.slug}.md"

    @property
    def tests_dir(self) -> str:
        return f"tests/{self.slug}"


@dataclass(frozen=True)
class Appendix:
    letter: str
    slug: str
    title: str
    purpose: str
    consumes: tuple[str, ...] = ()

    @property
    def anchor(self) -> str:
        return self.slug.replace("_", "-")

    @property
    def label(self) -> str:
        return f"Appendix {self.letter}"

    @property
    def path(self) -> str:
        return f"appendices/{self.slug}.md"


PARTS = (
    "Getting started",
    "Part I — What you are sizing",
    "Part II — Ceilings",
    "Part III — Sizing",
    "Part IV — Uncertainty",
    "Part V — Cost",
    "Part VI — Sensitivity",
    "Part VII — Presenting it",
)

CHAPTERS: tuple[Chapter, ...] = (
    Chapter(
        0,
        "prerequisites_and_setup",
        "Prerequisites and setup",
        PARTS[0],
        "What do I need installed, and how do I check that a model in this book still says what "
        "it says here?",
        owes="The setup check's own output, as a stamped result.",
    ),
    Chapter(
        1,
        "reading_a_model",
        "Reading a model",
        PARTS[0],
        "What is a model file, and why is it not a spreadsheet?",
        owes="A walk through every node kind against the storage model, and the DSL's own "
        "reference scenario.",
        consumes=("models/storage_cluster/model.yaml", "storage_cluster-reference"),
    ),
    Chapter(
        2,
        "what_a_workload_is",
        "What a workload is",
        PARTS[1],
        "Which quantities actually size a system, and which ones only look as though they do?",
        owes="The workload table for both reference models, derived from their input nodes.",
    ),
    Chapter(
        3,
        "where_the_numbers_come_from",
        "Where the numbers come from",
        PARTS[1],
        "What is the difference between a number you measured, a number you were told and a "
        "number you decided?",
        owes="Every corpus constant in the book, with its corpus, codec and standard error; and "
        "the provenance census of both models.",
        consumes=(
            "logs-line-bytes",
            "metrics-sample-bytes",
            "traces-span-bytes",
            "storage-object-compression",
        ),
        needs=("reading_a_model",),
    ),
    Chapter(
        4,
        "peak_mean_and_growth",
        "Peak, mean and growth",
        PARTS[1],
        "Which number in a demand curve is the one that sizes you, and what is a five-year growth "
        "rate actually a claim about?",
        owes="The growth sensitivity of the storage model, as a swing across the declared range.",
    ),
    Chapter(
        5,
        "littles_law",
        "Little's law",
        PARTS[2],
        "What can you infer about a system from the one relationship that is always true, and "
        "what can you not?",
        owes="A worked derivation against the observability ingest chain.",
    ),
    Chapter(
        6,
        "queueing_and_the_knee",
        "Queueing, and the knee",
        PARTS[2],
        "Why does response time climb long before a device is busy, and what does headroom "
        "actually buy?",
        owes="The utilisation-against-waiting-time curve, drawn from the model rather than "
        "asserted.",
    ),
    Chapter(
        7,
        "when_adding_servers_stops_helping",
        "When adding servers stops helping",
        PARTS[2],
        "How far does a system scale, and how would you find out from the two measurements you "
        "actually have?",
        owes="A universal scalability law fit, and what it predicts for the observability ingest "
        "tier.",
    ),
    Chapter(
        8,
        "regime_changes",
        "Regime changes",
        PARTS[2],
        "Which ceilings can a chain of multiplications not model at all?",
        owes="The cardinality explosion, as a distribution rather than a warning.",
        consumes=("observability-reference",),
    ),
    Chapter(
        9,
        "capacity",
        "Capacity",
        PARTS[3],
        "How far is what you buy from what you can use?",
        owes="The raw-to-usable chain of the storage model, node by node.",
        consumes=("storage_cluster-reference",),
    ),
    Chapter(
        10,
        "bandwidth_and_the_binding_constraint",
        "Bandwidth, and the binding constraint",
        PARTS[3],
        "When two independent chains each demand a different size, which one are you actually "
        "buying?",
        owes="How often each chain binds across the storage model's uncertainty.",
        consumes=("storage_cluster-reference",),
    ),
    Chapter(
        11,
        "headroom_and_failure_domains",
        "Headroom, failure domains and reservations",
        PARTS[3],
        "Why is headroom a rule rather than a number?",
        owes="Each ceiling's declared margin and the reason for it, from both models.",
        consumes=("storage_cluster-reference", "observability-reference"),
    ),
    Chapter(
        12,
        "the_sizing_model",
        "The sizing model",
        PARTS[3],
        "What does the whole chain produce, and how much of it would you defend?",
        owes="The storage model end to end, and the node count it recommends.",
        consumes=("storage_cluster-reference", "storage_cluster-sized_for_growth"),
        needs=("capacity", "bandwidth_and_the_binding_constraint", "headroom_and_failure_domains"),
    ),
    Chapter(
        13,
        "monte_carlo",
        "Monte Carlo",
        PARTS[4],
        "The sizing model has produced a node count. How sure are we?",
        consumes=("storage_cluster-reference", "storage_cluster-sized_for_growth"),
        needs=("the_sizing_model",),
    ),
    Chapter(
        14,
        "correlation_and_convergence",
        "Correlation and convergence",
        PARTS[4],
        "That interval assumed every input moves on its own, and that more samples would settle "
        "it. Are either of those true?",
        consumes=("correlation-effect", "convergence-storage-tco", "observability-reference"),
        needs=("monte_carlo",),
    ),
    Chapter(
        15,
        "capex_opex_and_lifecycle",
        "Capex, opex and the lifecycle",
        PARTS[5],
        "What do you pay once, what do you pay every month, and what does this book deliberately "
        "not model?",
        owes="The storage model's capital and running cost split, over its declared horizon.",
        consumes=("storage_cluster-reference",),
    ),
    Chapter(
        16,
        "power_first",
        "Power first",
        PARTS[5],
        "What changes when watts are the binding constraint rather than money?",
        owes="The storage model resized from a power budget inwards.",
    ),
    Chapter(
        17,
        "unit_economics",
        "Unit economics",
        PARTS[5],
        "What does a cost per unit have to have before it means anything?",
        owes="Cost per usable TB-month from the storage model, and what its denominator assumes.",
        consumes=("storage_cluster-reference",),
    ),
    Chapter(
        18,
        "the_five_year_model",
        "The five-year model",
        PARTS[5],
        "How does a cost model consume a sizing model's output without swallowing its uncertainty?",
        owes="Both models joined at the unit price, end to end.",
        consumes=("storage_cluster-reference", "observability-reference"),
    ),
    Chapter(
        19,
        "which_input_is_the_answer",
        "Which input is the answer?",
        PARTS[6],
        "Which input should you go and measure first, and how would the model tell you?",
        owes="Tornado charts for every output of both models, and what the widest bar has in "
        "common across them.",
        consumes=("storage_cluster-reference", "observability-reference"),
        needs=("monte_carlo",),
    ),
    Chapter(
        20,
        "the_missing_node",
        "The missing node",
        PARTS[6],
        "How do you find the error that no amount of sampling can see?",
        owes="The observability model's incomplete ingest total, and what it costs to believe it.",
        consumes=("observability-reference",),
        needs=("correlation_and_convergence",),
    ),
    Chapter(
        21,
        "a_tco_for_finance",
        "A TCO for a finance audience",
        PARTS[7],
        "How do you present an interval to somebody who has asked you for a number?",
        owes="The two storage scenarios as a decision, priced.",
        consumes=("storage_cluster-reference", "storage_cluster-sized_for_growth"),
        needs=("the_five_year_model", "which_input_is_the_answer"),
    ),
)

APPENDICES: tuple[Appendix, ...] = (
    Appendix(
        "A",
        "appendix_a_dsl_reference",
        "The DSL, in full",
        "Every node kind, every field, every distribution, and what the build checks.",
    ),
    Appendix(
        "B",
        "appendix_b_monte_carlo_module",
        "The Monte Carlo module, read end to end",
        "sizing/mc.py, quoted in order, with the reasoning for each piece.",
    ),
    Appendix(
        "C",
        "appendix_c_distributions",
        "Distributions, and when each is honest",
        "One page each: what it is for, what it assumes, and how it lies.",
    ),
    Appendix(
        "D",
        "appendix_d_units",
        "Units, and the conversions that bite",
        "TB against TiB, bits against bytes, month lengths, and why the build converts.",
    ),
    Appendix(
        "E",
        "appendix_e_storage_model",
        "The storage cluster model, in full",
        "All six outputs for the book's cost exemplar.",
        consumes=("storage_cluster-reference", "storage_cluster-sized_for_growth"),
    ),
    Appendix(
        "F",
        "appendix_f_observability_model",
        "The observability model, in full",
        "All six outputs for the book's sizing exemplar, including what is not yet measured.",
        consumes=("observability-reference", "observability-knobs_turned_down"),
    ),
    Appendix(
        "G",
        "appendix_g_glossary",
        "Glossary",
        "Every term the book introduces, with the chapter that introduces it.",
    ),
)

BY_SLUG = {chapter.slug: chapter for chapter in CHAPTERS}


def chapter(slug: str) -> Chapter:
    return BY_SLUG[slug]


def label_of(slug: str) -> str:
    return BY_SLUG[slug].label
