"""The formula language: small enough to have two implementations and check they agree.

A ``derived`` node's formula is parsed here into a tiny tree of dictionaries, and that tree is
what gets written into the exported JSON. The published page carries a forty-line interpreter for
it (``sizing/viewer/evaluate.js``), which is how moving a slider recomputes the whole model with
no server and no second copy of the arithmetic.

**Two implementations is a risk, and it is paid for rather than denied.** The build writes a set
of Python-evaluated answers into every export, and ``tests/test_viewer.py`` runs the JavaScript
over the same inputs and fails if a single one differs. A browser that quietly disagreed with the
build about what a model says would be the exact failure this repository exists to prevent, so it
is checked on every push rather than assumed.

The language is deliberately not Python. It is parsed *with* Python's parser — there is no reason
to write a worse one — and then every node is checked against a whitelist, so a formula cannot
call anything, index anything, or reach outside the model. Five operators and seven functions
covered both reference models without argument; an eighth should have to earn its place in the
JavaScript too.
"""

from __future__ import annotations

import ast
import math
from typing import Any

#: Binary operators, mapped to the tag the exported tree uses.
BINARY = {
    ast.Add: "+",
    ast.Sub: "-",
    ast.Mult: "*",
    ast.Div: "/",
    ast.Pow: "**",
}

#: Functions a formula may call. ``ceil`` is the one a sizing model cannot do without — you
#: cannot buy two thirds of a node — and it is also where a chain of multiplications stops being
#: a smooth function of its inputs, which ch08 has something to say about.
FUNCTIONS: dict[str, Any] = {
    "min": min,
    "max": max,
    "ceil": math.ceil,
    "floor": math.floor,
    "sqrt": math.sqrt,
    "log": math.log,
    "exp": math.exp,
}


class FormulaError(ValueError):
    """A formula this language will not accept, and why."""


def parse(formula: str, *, where: str = "formula") -> dict:
    """A formula string as an expression tree.

    ``where`` names the node, so a failure says which line of which model file to go and look at
    rather than leaving the reader to grep for a fragment of arithmetic.
    """
    try:
        tree = ast.parse(formula.strip(), mode="eval")
    except SyntaxError as exc:
        raise FormulaError(f"{where}: {formula!r} does not parse ({exc.msg})") from exc
    return _convert(tree.body, formula, where)


def _convert(node: ast.AST, formula: str, where: str) -> dict:
    if isinstance(node, ast.Constant):
        if isinstance(node.value, bool) or not isinstance(node.value, int | float):
            raise FormulaError(f"{where}: {node.value!r} is not a number")
        return {"op": "const", "value": float(node.value)}

    if isinstance(node, ast.Name):
        return {"op": "ref", "name": node.id}

    if isinstance(node, ast.BinOp) and type(node.op) in BINARY:
        return {
            "op": BINARY[type(node.op)],
            "args": [
                _convert(node.left, formula, where),
                _convert(node.right, formula, where),
            ],
        }

    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        return {"op": "neg", "args": [_convert(node.operand, formula, where)]}
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.UAdd):
        return _convert(node.operand, formula, where)

    if isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name) or node.func.id not in FUNCTIONS:
            name = getattr(node.func, "id", "that")
            raise FormulaError(
                f"{where}: {formula!r} calls {name!r}. A formula may call only "
                f"{', '.join(sorted(FUNCTIONS))} — anything else would have to exist in the "
                "browser evaluator too."
            )
        if node.keywords:
            raise FormulaError(f"{where}: {node.func.id}() takes positional arguments only")
        return {
            "op": "call",
            "fn": node.func.id,
            "args": [_convert(arg, formula, where) for arg in node.args],
        }

    raise FormulaError(
        f"{where}: {formula!r} uses {type(node).__name__}, which this language does not have. "
        "Formulas are arithmetic over other nodes; anything that needs more than that is a node "
        "of its own, which is also how it acquires a unit and a name the graph can show."
    )


def refs(tree: dict) -> set[str]:
    """Every node name a formula depends on."""
    if tree["op"] == "ref":
        return {tree["name"]}
    return {name for arg in tree.get("args", ()) for name in refs(arg)}


def render(tree: dict) -> str:
    """The tree back as readable arithmetic, for a caption or an error message.

    Round-trips rather than echoing the source string, so what a figure shows is what the build
    actually parsed. A caption quoting the original text would keep saying the right thing about
    a formula the build was reading differently.
    """
    op = tree["op"]
    if op == "const":
        value = tree["value"]
        return str(int(value)) if value == int(value) else repr(value)
    if op == "ref":
        return tree["name"]
    if op == "neg":
        return f"-{render(tree['args'][0])}"
    if op == "call":
        return f"{tree['fn']}(" + ", ".join(render(arg) for arg in tree["args"]) + ")"
    left, right = (render(arg) for arg in tree["args"])
    return f"({left} {op} {right})"
