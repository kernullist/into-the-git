import math

from .sentiment import compute_sentiment_score, compute_improvement_score


SEVERITY_WEIGHTS = {
    "critical": 10,
    "blocker": 10,
    "major": 5,
    "minor": 2,
    "info": 1,
}


def compute_finding_score(findings):
    if not findings:
        return 0.0
    total = sum(SEVERITY_WEIGHTS.get(f.get("severity", "info"), 1) for f in findings)
    return math.log1p(total)


def compute_complexity_score(complexity_value, loc):
    if loc == 0:
        return 0.0
    ratio = complexity_value / loc
    return min(10.0, ratio * 100)


def compute_duplication_score(duplicate_count, file_count):
    if file_count == 0:
        return 0.0
    return min(10.0, (duplicate_count / file_count) * 10)


def compute_change_frequency_score(change_count, total_commits):
    if total_commits == 0:
        return 0.0
    ratio = change_count / total_commits
    return min(10.0, ratio * 20)


def compute_priority_score(signals):
    weights = {
        "finding_score": 0.35,
        "complexity_score": 0.20,
        "duplication_score": 0.10,
        "dependency_score": 0.10,
        "change_frequency_score": 0.15,
        "feedback_score": 0.10,
    }
    score = 0.0
    for key, weight in weights.items():
        score += signals.get(key, 0.0) * weight
    return round(min(100.0, score * 10), 1)


def generate_recommendations(file_signals, top_n=20):
    scored = []
    for file_path, signals in file_signals.items():
        priority = compute_priority_score(signals)
        scored.append(
            {
                "target_type": "file",
                "target_name": file_path,
                "target_id": None,
                "priority_score": priority,
                "contributing_signals": signals,
                "rationale": _build_rationale(signals),
            }
        )
    scored.sort(key=lambda x: x["priority_score"], reverse=True)
    return scored[:top_n]


def _build_rationale(signals):
    parts = []
    if signals.get("finding_score", 0) > 5:
        parts.append(f"High static analysis issues (score: {signals['finding_score']:.1f})")
    if signals.get("complexity_score", 0) > 5:
        parts.append(f"High complexity (score: {signals['complexity_score']:.1f})")
    if signals.get("duplication_score", 0) > 3:
        parts.append(f"Code duplication detected (score: {signals['duplication_score']:.1f})")
    if signals.get("change_frequency_score", 0) > 5:
        parts.append(f"Frequently changed (score: {signals['change_frequency_score']:.1f})")
    if signals.get("feedback_score", 0) < 3:
        parts.append(f"Low user feedback (score: {signals['feedback_score']:.1f})")
    if not parts:
        return "Minor improvements suggested"
    return "; ".join(parts)
