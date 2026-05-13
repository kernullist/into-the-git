from datetime import datetime, timezone
import hashlib


def normalize_finding(adapter_name, raw_data, file_path, repository_id):
    severity_map = {
        "error": "critical", "warning": "major", "style": "minor",
        "performance": "minor", "information": "info",
        "E": "critical", "F": "critical", "W": "major", "R": "minor", "C": "minor", "I": "info",
        "HIGH": "critical", "MEDIUM": "major", "LOW": "minor",
    }
    location = raw_data.get("location", {"file": file_path, "line": 0, "column": 0})
    return {
        "tool": adapter_name,
        "rule_id": str(raw_data.get("rule_id", "")),
        "severity": severity_map.get(str(raw_data.get("severity", "")), "minor"),
        "category": str(raw_data.get("category", "general")),
        "message": str(raw_data.get("message", "")),
        "location": location,
        "fingerprint": hashlib.sha256(
            f"{adapter_name}|{raw_data.get('rule_id','')}|{file_path}|{location.get('line',0)}|{raw_data.get('message','')}".encode()
        ).hexdigest()[:32],
        "repository_id": repository_id,
        "raw_payload": raw_data,
    }


def normalize_symbol(raw_symbol, file_id):
    return {
        "file_id": file_id,
        "kind": raw_symbol.get("kind", "function"),
        "name": raw_symbol.get("name", ""),
        "location": raw_symbol.get("location", {}),
        "signature": raw_symbol.get("signature", ""),
        "complexity": raw_symbol.get("complexity", 0),
        "dependency_refs": raw_symbol.get("dependency_refs", []),
    }


def normalize_metric(run_id, scope_type, scope_id, metric_name, value, unit=""):
    return {
        "run_id": run_id,
        "scope_type": scope_type,
        "scope_id": scope_id,
        "metric_name": metric_name,
        "value": float(value),
        "unit": unit,
    }


def normalize_commit_signal(repo_id, commit_data, purpose_category):
    return {
        "repository_id": repo_id,
        "commit_sha": commit_data.get("sha", "")[:64],
        "author": commit_data.get("author", ""),
        "committed_at": _parse_datetime(commit_data.get("date", "")),
        "purpose_category": purpose_category,
        "message": commit_data.get("message", "")[:1000],
        "touched_lines": commit_data.get("touched_lines", 1),
    }


def _parse_datetime(date_str):
    try:
        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return datetime.now(timezone.utc)


FINDING_SCHEMA = {
    "tool": str,
    "rule_id": str,
    "severity": str,
    "category": str,
    "message": str,
    "location": dict,
    "fingerprint": str,
    "raw_payload": dict,
}

COMMIT_SIGNAL_SCHEMA = {
    "commit_sha": str,
    "author": str,
    "committed_at": datetime,
    "purpose_category": str,
    "message": str,
    "touched_lines": int,
}

METRIC_SCHEMA = {
    "scope_type": str,
    "scope_id": int,
    "metric_name": str,
    "value": float,
    "unit": str,
}
