"""Independent claim checker, written before viewing implementation or tests.

Derived from claim.md and Python 3.12's documented format-string syntax.
Run as a python -c argument inside the trusted night.py container helper.
"""

import json
import platform
import string
import sys
from types import SimpleNamespace

from boltons.formatutils import infer_positional_format_args, tokenize_format_str


cases = []


def add(label, original, expected, args=(), kwargs=None):
    cases.append((label, original, expected, args, kwargs or {}))


add("claim-example", "{[{}]} {}", "{0[{}]} {1}", ({"{}": "value"}, "tail"))
keys = ("{", "}", "{}", "{{", "}}", "}{", "{word}", "a{b}c", "[{}", "[", "!r:{}", "a:b!c{d", "x y{z}")
for key in keys:
    data = {key: "value"}
    item = "[" + key + "]"
    add("auto-" + repr(key), "{" + item + "}|{}", "{0" + item + "}|{1}", (data, "tail"))
    add("named-" + repr(key), "{data" + item + "}|{}", "{data" + item + "}|{0}", ("tail",), {"data": data})
    explicit = "{0" + item + "}|{1}"
    add("explicit-" + repr(key), explicit, explicit, (data, "tail"))
    add("conversion-" + repr(key), "{" + item + "!r:>{}}|{}", "{0" + item + "!r:>{1}}|{2}", (data, 10, "tail"))
    # str.format rejects unbalanced braces inside a nested format spec, even
    # when the same key is valid in a top-level field. Keep these width cases
    # within the built-in formatter's supported inputs.
    if key not in {"{", "}", "{{", "}}", "a:b!c{d"}:
        add("nested-width-" + repr(key), "{:>{" + item + "}}|{}", "{0:>{1" + item + "}}|{2}", ("x", {key: 4}, "tail"))

add("nested-items", "{[{outer}][}inner{]} {}", "{0[{outer}][}inner{]} {1}", ({"{outer}": {"}inner{": "value"}}, "tail"))
add("attribute-then-item", "{.value[{}]} {}", "{0.value[{}]} {1}", (SimpleNamespace(value={"{}": "value"}), "tail"))
add("item-then-attribute", "{[{}].value} {}", "{0[{}].value} {1}", ({"{}": SimpleNamespace(value="value")}, "tail"))
add("escaped-braces", "{{{[{}]}}} [{}]", "{{{0[{}]}}} [{1}]", ({"{}": "value"}, "tail"))
add("named-width", "{data[{}]!a:>{width[{}]}} {tail}", "{data[{}]!a:>{width[{}]}} {tail}", (), {"data": {"{}": "value"}, "width": {"{}": 12}, "tail": "tail"})
add("literal-open-bracket", "[ {} {}", "[ {0} {1}", ("first", "second"))
add("literal-close-bracket", "] {} [] {}", "] {0} [] {1}", ("first", "second"))
add("bracket-fill", "{:[<5}|{}", "{0:[<5}|{1}", ("x", "tail"))
add("bracket-fill-width", "{:[<{}}|{}", "{0:[<{1}}|{2}", ("x", 5, "tail"))
add("close-bracket-fill-width", "{:]<{}}|{}", "{0:]<{1}}|{2}", ("x", 5, "tail"))
add("ordinary", "{} {name} {!s} {!a} {!r}", "{0} {name} {1!s} {2!a} {3!r}", (1, 2, "é", "x"), {"name": "N"})
add("numeric", "{:06d} {:.2f} {:#x}", "{0:06d} {1:.2f} {2:#x}", (42, 2.5, 255))
add("width-precision", "{:{}.{}f} {}", "{0:{1}.{2}f} {3}", (3.14159, 8, 3, "tail"))
add("escaped-only", "{{}} [{{x}}]", "{{}} [{{x}}]")
add("empty", "", "")

failures = []
oracle_errors = []
formatter = string.Formatter()
for label, original, expected, args, kwargs in cases:
    try:
        original_output = original.format(*args, **kwargs)
        expected_output = expected.format(*args, **kwargs)
        assert original_output == expected_output, (original_output, expected_output)
        expected_fields = [name for _, name, _, _ in formatter.parse(expected) if name is not None]
    except Exception as exc:
        oracle_errors.append({"case": label, "error": type(exc).__name__, "detail": str(exc)})
        continue
    result = {"case": label, "input": original, "expected": expected}
    problems = []
    try:
        actual = infer_positional_format_args(original)
        result["actual"] = actual
        if actual != expected:
            problems.append("inferred format differs")
        try:
            output = actual.format(*args, **kwargs)
            if output != original_output:
                problems.append("formatted output differs")
        except Exception as exc:
            problems.append("format raised " + type(exc).__name__ + ": " + str(exc))
    except Exception as exc:
        problems.append("inference raised " + type(exc).__name__ + ": " + str(exc))
    try:
        actual_fields = [token.fname for token in tokenize_format_str(original) if not isinstance(token, str)]
        if actual_fields != expected_fields:
            result["expected_fields"] = expected_fields
            result["actual_fields"] = actual_fields
            problems.append("token fields differ")
    except Exception as exc:
        problems.append("tokenization raised " + type(exc).__name__ + ": " + str(exc))
    if problems:
        result["problems"] = problems
        failures.append(result)

print(json.dumps({"python": platform.python_version(), "cases": len(cases), "oracle_errors": oracle_errors, "failures": failures, "passed": len(cases) - len(failures) - len(oracle_errors)}, sort_keys=True, indent=2))
sys.exit(bool(failures or oracle_errors))
