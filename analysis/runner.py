import hashlib
import os
import traceback
from datetime import datetime, timedelta, timezone

from database import db
from models import (
    AnalysisRun,
    Repository,
    SourceFile,
    CodeSymbol,
    Finding,
    MetricSnapshot,
    CommitSignal,
    Recommendation,
)
from connectors.local import LocalConnector
from connectors.github import GitHubConnector
from connectors.gitlab import GitLabConnector
from connectors.base import BaseConnector as ConnectorBase
from analyzers.adapters import get_adapters_for_language
from analyzers.ast_engine import ASTEngine
from analyzers.complexity import compute_complexity
from analyzers.duplication import detect_duplicates
from analyzers.dependency import analyze_dependencies
from commit_intel.classifier import CommitClassifier
from commit_intel.frequency import compute_change_frequency
from scoring.engine import (
    compute_finding_score,
    compute_complexity_score,
    compute_duplication_score,
    compute_change_frequency_score,
    compute_priority_score,
    generate_recommendations,
)


def _get_connector(repository):
    provider = repository.provider
    local_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "data",
        "repos",
        f"repo_{repository.id}",
    )
    branch = (
        repository.selected_branches[0]
        if repository.selected_branches
        else repository.default_branch
    )
    if provider == "github":
        return GitHubConnector(repository.remote_url, local_path, branch)
    elif provider == "gitlab":
        return GitLabConnector(repository.remote_url, local_path, branch)
    else:
        return LocalConnector(repository.remote_url, local_path, branch)


def run_analysis(app, run_id, retry_repository_ids=None, period="1m"):
    import time as time_mod

    start_time = time_mod.time()
    timeout = app.config.get("MAX_ANALYSIS_TIMEOUT", 3600)

    with app.app_context():
        run = db.session.get(AnalysisRun, run_id)
        if not run:
            return

        run.status = "running"
        run.started_at = datetime.now(timezone.utc)
        run.logs = ""
        db.session.commit()

        try:
            repository_ids = run.repository_ids or []
            if retry_repository_ids:
                repository_ids = [rid for rid in repository_ids if rid in retry_repository_ids]

            since_date = _compute_since_date(period)
            total_repos = len(repository_ids)
            all_file_signals = {}

            for idx, repo_id in enumerate(repository_ids):
                if time_mod.time() - start_time > timeout:
                    _log(run, "Analysis timeout reached. Stopping.")
                    run.error_summary = f"Analysis timed out after {timeout}s"
                    break

                _log(run, f"Analyzing repository {repo_id}...")
                try:
                    repo = db.session.get(Repository, repo_id)
                    if not repo:
                        _log(run, f"Repository {repo_id} not found, skipping")
                        continue

                    connector = _get_connector(repo)
                    _log(run, f"Cloning/fetching {repo.remote_url}...")
                    clone_result = connector.clone_or_fetch()

                    if not clone_result["success"]:
                        _log(run, f"Clone/fetch failed: {clone_result.get('stderr', '')}")
                        repo.last_fetched_at = datetime.now(timezone.utc)
                        db.session.commit()
                        continue

                    repo.last_fetched_at = datetime.now(timezone.utc)
                    db.session.commit()

                    _log(run, "Discovering branches...")
                    branches = connector.get_branches()
                    if branches and not repo.selected_branches:
                        repo.selected_branches = branches[:1]
                        _log(run, f"Auto-selected branch: {repo.selected_branches[0]}")

                    _log(run, f"Getting commit history since {since_date}..." if since_date else "Getting commit history...")
                    all_commits = connector.get_commit_history(
                        since=since_date.strftime("%Y-%m-%d") if since_date else None
                    )

                    _log(run, "Getting file list...")
                    files = connector.get_file_list()

                    _analyze_files(app, run, repo, connector, files, all_commits, all_file_signals)

                    _log(run, "Classifying commits...")
                    classifier = CommitClassifier()
                    messages = [c.get("message", "") for c in all_commits[:1000]]
                    result = classifier.cluster_unsupervised(messages)
                    if isinstance(result, tuple):
                        cluster_labels, cluster_terms = result
                    else:
                        cluster_labels, cluster_terms = [classifier.classify_rule_based(m) for m in messages], {}
                    rule_labels = classifier.classify_batch(messages)

                    final_labels = cluster_labels if isinstance(cluster_labels, list) else list(cluster_labels)

                    _store_commit_signals(run, repo, all_commits, final_labels, files)

                    _log(run, "Computing change frequency...")
                    freq_data = compute_change_frequency(all_commits)
                    for file_path, change_count in freq_data.get("file_frequency", {}).items():
                        if file_path in all_file_signals:
                            total = max(1, len(all_commits))
                            all_file_signals[file_path]["change_frequency_score"] = min(
                                10.0, (change_count / total) * 20
                            )

                    run.progress = ((idx + 1) / total_repos) * 100
                    db.session.commit()

                except Exception as e:
                    _log(run, f"Error analyzing repository {repo_id}: {str(e)}")
                    _log(run, traceback.format_exc())

            _log(run, "Generating recommendations...")
            recommendations = generate_recommendations(all_file_signals)
            for rec in recommendations:
                db.session.add(
                    Recommendation(
                        run_id=run.id,
                        target_type=rec["target_type"],
                        target_id=rec["target_id"],
                        priority_score=rec["priority_score"],
                        rationale=rec["rationale"],
                        contributing_signals=rec["contributing_signals"],
                        status="open",
                    )
                )

            _log(run, "Computing aggregate metrics...")
            _store_aggregate_metrics(run, all_file_signals)

            run.status = "completed"
            run.progress = 100.0
            run.finished_at = datetime.now(timezone.utc)
            run.tool_versions = _get_tool_versions()
            db.session.commit()

        except Exception as e:
            _log(run, f"Analysis failed: {str(e)}")
            _log(run, traceback.format_exc())
            run.status = "failed"
            run.error_summary = str(e)[:1000]
            run.finished_at = datetime.now(timezone.utc)
            db.session.commit()


def _analyze_files(app, run, repo, connector, files, all_commits, all_file_signals):
    ast_engine = ASTEngine()
    language_files = {}
    for f in files:
        lang = f["language"]
        if lang not in language_files:
            language_files[lang] = []
        language_files[lang].append(f)

    finding_count = 0
    file_finding_map = {}

    for language, lang_files in language_files.items():
        _log(run, f"Analyzing {len(lang_files)} {language} files...")

        adapters = get_adapters_for_language(language)
        available_adapters = [a for a in adapters if a.is_available()]

        if not available_adapters:
            _log(run, f"No {language} static analyzers available; using built-in analysis only")

        lang_content = {}
        max_files = 200
        for file_info in lang_files[:max_files]:
            if len(lang_files) > max_files and file_info == lang_files[max_files - 1]:
                _log(run, f"WARNING: Truncating {language} analysis to {max_files} files ({len(lang_files)} total). Use narrower branch/period filters.")
            content = connector.get_file_content(file_info["path"])
            if not content:
                continue
            lang_content[file_info["path"]] = content

            file_hash = ConnectorBase.compute_file_hash(content)
            last_sha = connector.get_last_commit_for_file(file_info["path"])

            source_file = SourceFile(
                repository_id=repo.id,
                path=file_info["path"],
                language=language,
                size=file_info["size"],
                hash=file_hash,
                last_commit_sha=last_sha,
                owner_hint=connector.get_owner_hint(file_info["path"], all_commits),
            )
            db.session.add(source_file)
            db.session.flush()

            file_findings = []
            for adapter in available_adapters:
                raw_findings = adapter.analyze(
                    file_info["path"], content, language
                )
                for f_data in raw_findings:
                    fingerprint = hashlib.sha256(
                        f"{adapter.name}|{f_data['rule_id']}|{file_info['path']}|{f_data['location'].get('line',0)}|{f_data['message']}".encode()
                    ).hexdigest()[:32]
                    finding = Finding(
                        run_id=run.id,
                        repository_id=repo.id,
                        file_id=source_file.id,
                        tool=adapter.name,
                        rule_id=f_data["rule_id"],
                        severity=f_data["severity"],
                        category=f_data["category"],
                        message=f_data["message"],
                        location=f_data["location"],
                        fingerprint=fingerprint,
                        raw_payload=f_data,
                    )
                    db.session.add(finding)
                    file_findings.append({"severity": f_data["severity"]})
                    finding_count += 1

            file_finding_map[file_info["path"]] = file_findings

            symbols = ast_engine.extract_symbols(
                file_info["path"], content, language
            )
            for sym_data in symbols:
                code_symbol = CodeSymbol(
                    file_id=source_file.id,
                    kind=sym_data["kind"],
                    name=sym_data["name"],
                    location=sym_data["location"],
                    signature=sym_data.get("signature", ""),
                    complexity=sym_data.get("complexity", 0),
                    dependency_refs=[],
                )
                db.session.add(code_symbol)

            complexity_data = compute_complexity(content, language)

            signals = {
                "finding_score": compute_finding_score(file_findings),
                "complexity_score": compute_complexity_score(
                    complexity_data["cyclomatic"], complexity_data["sloc"]
                ),
                "duplication_score": 0.0,
                "dependency_score": 0.0,
                "change_frequency_score": 0.0,
                "feedback_score": 5.0,
            }
            all_file_signals[file_info["path"]] = signals

        if lang_content:
            duplicates = detect_duplicates(lang_content)
            for dup in duplicates:
                if dup["file_a"] in all_file_signals:
                    all_file_signals[dup["file_a"]]["duplication_score"] += 2.0

            deps = analyze_dependencies(lang_content, language)
            for file_path, dep_count in deps.get("dep_count", {}).items():
                if file_path in all_file_signals:
                    all_file_signals[file_path]["dependency_score"] = min(
                        10.0, dep_count * 0.5
                    )
                    all_file_signals[file_path]["fan_in"] = deps.get("fan_in", {}).get(
                        file_path, 0
                    )
                    all_file_signals[file_path]["fan_out"] = deps.get("fan_out", {}).get(
                        file_path, 0
                    )

    db.session.commit()
    _log(run, f"Total findings: {finding_count}")


def _store_commit_signals(run, repo, all_commits, labels, files):
    file_paths = {f["path"] for f in files}
    source_files = {sf.path: sf.id for sf in SourceFile.query.filter_by(repository_id=repo.id).all()}
    count = 0
    for commit_idx, commit in enumerate(all_commits[:500]):
        purpose = labels[commit_idx] if commit_idx < len(labels) else "other"
        for file_path in commit.get("files", []):
            if file_path not in file_paths:
                continue
            file_id = source_files.get(file_path)
            cs = CommitSignal(
                repository_id=repo.id,
                file_id=file_id,
                commit_sha=commit.get("sha", ""),
                author=commit.get("author", ""),
                committed_at=_parse_date(commit.get("date", "")),
                purpose_category=purpose,
                message=commit.get("message", ""),
                touched_lines=1,
            )
            db.session.add(cs)
            count += 1
            if count >= 1000:
                break
        if count >= 1000:
            break
    db.session.commit()


def _store_aggregate_metrics(run, all_file_signals):
    total_findings = Finding.query.filter_by(run_id=run.id).count()
    avg_complexity = 0.0
    avg_duplication = 0.0
    if all_file_signals:
        avg_complexity = sum(
            s.get("complexity_score", 0) for s in all_file_signals.values()
        ) / len(all_file_signals)
        avg_duplication = sum(
            s.get("duplication_score", 0) for s in all_file_signals.values()
        ) / len(all_file_signals)

    metrics = [
        ("project", None, "total_findings", float(total_findings), "count"),
        ("project", None, "total_files", float(len(all_file_signals)), "count"),
        ("project", None, "avg_complexity", avg_complexity, "score"),
        ("project", None, "avg_duplication", avg_duplication, "score"),
    ]
    for scope_type, scope_id, name, value, unit in metrics:
        db.session.add(
            MetricSnapshot(
                run_id=run.id,
                scope_type=scope_type,
                scope_id=scope_id,
                metric_name=name,
                value=value,
                unit=unit,
            )
        )
    db.session.commit()


_log_counter = 0

def _log(run, message):
    global _log_counter
    timestamp = datetime.now(timezone.utc).strftime("%H:%M:%S")
    run.logs = (run.logs or "") + f"[{timestamp}] {message}\n"
    _log_counter += 1
    if _log_counter % 5 == 0:
        db.session.commit()


def _parse_date(date_str):
    try:
        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return datetime.now(timezone.utc)


def _get_tool_versions():
    import sys
    return {
        "python": sys.version.split()[0],
    }


def _compute_since_date(period):
    if not period:
        return None
    now = datetime.now(timezone.utc)
    if period == "1w":
        return now - timedelta(weeks=1)
    elif period == "1m":
        return now - timedelta(days=30)
    elif period == "3m":
        return now - timedelta(days=90)
    try:
        return datetime.fromisoformat(period).replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        return None
