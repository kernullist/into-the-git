def compute_complexity(content, language):
    if language == "Python":
        return _python_complexity(content)
    return _generic_complexity(content)


def _python_complexity(content):
    try:
        from radon.complexity import cc_visit
        from radon.raw import analyze
        from radon.metrics import mi_visit

        results = {"cyclomatic": 0, "loc": 0, "lloc": 0, "sloc": 0, "comments": 0, "mi": 100.0}

        try:
            blocks = cc_visit(content)
            if blocks:
                results["cyclomatic"] = sum(b.complexity for b in blocks)
        except Exception:
            pass

        try:
            raw = analyze(content)
            results["loc"] = raw.loc
            results["lloc"] = raw.lloc
            results["sloc"] = raw.sloc
            results["comments"] = raw.comments
        except Exception:
            pass

        try:
            results["mi"] = mi_visit(content, True)
        except Exception:
            pass

        return results
    except ImportError:
        return _generic_complexity(content)


def _generic_complexity(content):
    import math
    import re

    lines = content.split("\n")
    loc = len(lines)
    sloc = len([l for l in lines if l.strip() and not l.strip().startswith("//") and not l.strip().startswith("#")])
    comments = len(
        [
            l
            for l in lines
            if l.strip().startswith("//") or l.strip().startswith("#") or l.strip().startswith("/*") or l.strip().startswith("*")
        ]
    )

    complexity = 1
    keywords = [
        r"\bif\b",
        r"\belse\s+if\b",
        r"\bwhile\b",
        r"\bfor\b",
        r"\bcase\b",
        r"\bcatch\b",
        r"\&\&",
        r"\|\|",
    ]
    for kw in keywords:
        complexity += len(re.findall(kw, content))

    mi = max(0.0, 171.0 - 5.2 * math.log(max(1, complexity)) - 0.23 * complexity - 16.2 * math.log(max(1, sloc)))
    return {
        "cyclomatic": complexity,
        "loc": loc,
        "lloc": sloc - comments,
        "sloc": sloc,
        "comments": comments,
        "mi": round(mi, 1),
    }
