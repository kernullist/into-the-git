import json
import os
from datetime import datetime, timezone
from io import BytesIO

from flask import Blueprint, jsonify, request, send_file
from database import db
from models import (
    Project,
    Repository,
    AnalysisRun,
    Finding,
    MetricSnapshot,
    Feedback,
    Recommendation,
    ExportReport,
    CommitSignal,
    SourceFile,
    CodeSymbol,
)

api_bp = Blueprint("api", __name__)


# ── Projects ─────────────────────────────────────────────
@api_bp.route("/projects", methods=["GET"])
def list_projects():
    projects = Project.query.order_by(Project.updated_at.desc()).all()
    return jsonify([p.to_dict() for p in projects])


@api_bp.route("/projects", methods=["POST"])
def create_project():
    data = request.get_json() or {}
    project = Project(name=data.get("name", "Unnamed Project"), description=data.get("description", ""))
    db.session.add(project)
    db.session.commit()
    return jsonify(project.to_dict()), 201


@api_bp.route("/projects/<int:project_id>", methods=["GET"])
def get_project(project_id):
    project = db.session.get(Project, project_id)
    if not project:
        return jsonify({"error": "Project not found"}), 404
    return jsonify(project.to_dict())


@api_bp.route("/projects/<int:project_id>", methods=["DELETE"])
def delete_project(project_id):
    project = db.session.get(Project, project_id)
    if not project:
        return jsonify({"error": "Project not found"}), 404
    for run in project.analysis_runs.all():
        Finding.query.filter_by(run_id=run.id).delete()
        MetricSnapshot.query.filter_by(run_id=run.id).delete()
        Feedback.query.filter_by(run_id=run.id).delete()
        Recommendation.query.filter_by(run_id=run.id).delete()
        ExportReport.query.filter_by(run_id=run.id).delete()
        db.session.delete(run)
    for repo in project.repositories.all():
        sf_ids = [sf.id for sf in SourceFile.query.filter_by(repository_id=repo.id).all()]
        if sf_ids:
            CodeSymbol.query.filter(CodeSymbol.file_id.in_(sf_ids)).delete(synchronize_session="fetch")
        SourceFile.query.filter_by(repository_id=repo.id).delete()
        CommitSignal.query.filter_by(repository_id=repo.id).delete()
        Finding.query.filter_by(repository_id=repo.id).delete()
        db.session.delete(repo)
    db.session.delete(project)
    db.session.commit()
    return jsonify({"ok": True})


# ── Repositories ─────────────────────────────────────────
@api_bp.route("/projects/<int:project_id>/repositories", methods=["GET"])
def list_repositories(project_id):
    repos = Repository.query.filter_by(project_id=project_id).all()
    return jsonify([r.to_dict() for r in repos])


@api_bp.route("/projects/<int:project_id>/repositories", methods=["POST"])
def add_repository(project_id):
    project = db.session.get(Project, project_id)
    if not project:
        return jsonify({"error": "Project not found"}), 404
    data = request.get_json() or {}
    repo = Repository(
        project_id=project_id,
        provider=data.get("provider", "local"),
        remote_url=data.get("remote_url", ""),
        default_branch=data.get("default_branch", "main"),
        selected_branches=data.get("selected_branches", []),
        language_summary=data.get("language_summary", {}),
    )
    db.session.add(repo)
    db.session.commit()
    return jsonify(repo.to_dict()), 201


@api_bp.route("/repositories/<int:repository_id>", methods=["GET"])
def get_repository(repository_id):
    repo = db.session.get(Repository, repository_id)
    if not repo:
        return jsonify({"error": "Repository not found"}), 404
    return jsonify(repo.to_dict())


@api_bp.route("/repositories/<int:repository_id>", methods=["PUT"])
def update_repository(repository_id):
    repo = db.session.get(Repository, repository_id)
    if not repo:
        return jsonify({"error": "Repository not found"}), 404
    data = request.get_json() or {}
    if "selected_branches" in data:
        repo.selected_branches = data["selected_branches"]
    if "default_branch" in data:
        repo.default_branch = data["default_branch"]
    db.session.commit()
    return jsonify(repo.to_dict())


@api_bp.route("/repositories/<int:repository_id>", methods=["DELETE"])
def delete_repository(repository_id):
    repo = db.session.get(Repository, repository_id)
    if not repo:
        return jsonify({"error": "Repository not found"}), 404
    sf_ids = [sf.id for sf in SourceFile.query.filter_by(repository_id=repo.id).all()]
    if sf_ids:
        CodeSymbol.query.filter(CodeSymbol.file_id.in_(sf_ids)).delete(synchronize_session="fetch")
    SourceFile.query.filter_by(repository_id=repo.id).delete()
    CommitSignal.query.filter_by(repository_id=repo.id).delete()
    Finding.query.filter_by(repository_id=repo.id).delete()
    db.session.delete(repo)
    db.session.commit()
    return jsonify({"ok": True})


@api_bp.route("/repositories/<int:repository_id>/branches", methods=["GET"])
def get_branches(repository_id):
    repo = db.session.get(Repository, repository_id)
    if not repo:
        return jsonify({"error": "Repository not found"}), 404
    from connectors.local import LocalConnector
    from connectors.github import GitHubConnector
    from connectors.gitlab import GitLabConnector

    local_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "data",
        "repos",
        f"repo_{repo.id}",
    )
    provider = repo.provider
    if provider == "github":
        connector = GitHubConnector(repo.remote_url, local_path, repo.default_branch)
    elif provider == "gitlab":
        connector = GitLabConnector(repo.remote_url, local_path, repo.default_branch)
    else:
        connector = LocalConnector(repo.remote_url, local_path, repo.default_branch)
    try:
        connector.clone_or_fetch()
        branches = connector.get_branches()
    except Exception:
        branches = [repo.default_branch]

    return jsonify({"branches": branches, "default_branch": repo.default_branch})


# ── Analysis Runs ────────────────────────────────────────
@api_bp.route("/projects/<int:project_id>/analysis-runs", methods=["GET"])
def list_analysis_runs(project_id):
    runs = (
        AnalysisRun.query.filter_by(project_id=project_id)
        .order_by(AnalysisRun.created_at.desc())
        .all()
    )
    return jsonify([r.to_dict() for r in runs])


@api_bp.route("/analysis-runs", methods=["POST"])
def create_analysis_run():
    data = request.get_json() or {}
    project_id = data.get("project_id")
    repository_ids = data.get("repository_ids", [])
    branch_refs = data.get("branch_refs", [])

    project = db.session.get(Project, project_id)
    if not project:
        return jsonify({"error": "Project not found"}), 404

    for rid in repository_ids:
        repo = db.session.get(Repository, rid)
        if repo and branch_refs and not repo.selected_branches:
            repo.selected_branches = branch_refs
            db.session.commit()

    run = AnalysisRun(
        project_id=project_id,
        repository_ids=repository_ids,
        branch_refs=branch_refs,
        status="queued",
        progress=0.0,
    )
    db.session.add(run)
    db.session.commit()

    from analysis.runner import run_analysis
    from concurrent.futures import ThreadPoolExecutor
    from flask import current_app

    period = data.get("period", "1m")
    executor = ThreadPoolExecutor(max_workers=1)
    executor.submit(run_analysis, current_app._get_current_object(), run.id, None, period)
    executor.shutdown(wait=False)

    return jsonify(run.to_dict()), 201


@api_bp.route("/analysis-runs/<int:run_id>", methods=["GET"])
def get_analysis_run(run_id):
    run = db.session.get(AnalysisRun, run_id)
    if not run:
        return jsonify({"error": "Analysis run not found"}), 404
    return jsonify(run.to_dict())


@api_bp.route("/analysis-runs/<int:run_id>/cancel", methods=["POST"])
def cancel_analysis_run(run_id):
    run = db.session.get(AnalysisRun, run_id)
    if not run:
        return jsonify({"error": "Analysis run not found"}), 404
    if run.status in ("queued", "running"):
        run.status = "cancelled"
        run.finished_at = datetime.now(timezone.utc)
        db.session.commit()
    return jsonify(run.to_dict())


@api_bp.route("/analysis-runs/<int:run_id>/retry", methods=["POST"])
def retry_analysis_run(run_id):
    run = db.session.get(AnalysisRun, run_id)
    if not run:
        return jsonify({"error": "Analysis run not found"}), 404

    data = request.get_json() or {}
    retry_repo_ids = data.get("repository_ids", None)

    if retry_repo_ids:
        Finding.query.filter(
            Finding.run_id == run_id, Finding.repository_id.in_(retry_repo_ids)
        ).delete(synchronize_session="fetch")
        MetricSnapshot.query.filter(
            MetricSnapshot.run_id == run_id,
            MetricSnapshot.scope_type == "repository",
            MetricSnapshot.scope_id.in_(retry_repo_ids),
        ).delete(synchronize_session="fetch")
        source_ids = [
            sf.id for sf in SourceFile.query.filter(
                SourceFile.repository_id.in_(retry_repo_ids)
            ).all()
        ]
        if source_ids:
            CodeSymbol.query.filter(CodeSymbol.file_id.in_(source_ids)).delete(synchronize_session="fetch")
        SourceFile.query.filter(SourceFile.repository_id.in_(retry_repo_ids)).delete(synchronize_session="fetch")
        CommitSignal.query.filter(CommitSignal.repository_id.in_(retry_repo_ids)).delete(synchronize_session="fetch")
    else:
        Finding.query.filter_by(run_id=run_id).delete()
        MetricSnapshot.query.filter_by(run_id=run_id).delete()
        Recommendation.query.filter_by(run_id=run_id).delete()

    run.status = "queued"
    run.progress = 0.0
    run.started_at = None
    run.finished_at = None
    run.logs = ""
    run.error_summary = ""
    db.session.commit()

    from analysis.runner import run_analysis
    from concurrent.futures import ThreadPoolExecutor
    from flask import current_app

    period = data.get("period", "1m")
    executor = ThreadPoolExecutor(max_workers=1)
    executor.submit(
        run_analysis, current_app._get_current_object(), run.id, retry_repo_ids, period
    )
    executor.shutdown(wait=False)

    return jsonify(run.to_dict())


# ── Findings ─────────────────────────────────────────────
@api_bp.route("/analysis-runs/<int:run_id>/findings", methods=["GET"])
def get_findings(run_id):
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 100, type=int)
    severity = request.args.get("severity")
    category = request.args.get("category")
    tool = request.args.get("tool")
    repository_id = request.args.get("repository_id", type=int)

    q = Finding.query.filter_by(run_id=run_id)
    if severity:
        q = q.filter_by(severity=severity)
    if category:
        q = q.filter_by(category=category)
    if tool:
        q = q.filter_by(tool=tool)
    if repository_id:
        q = q.filter_by(repository_id=repository_id)

    total = q.count()
    findings = q.order_by(Finding.id.desc()).offset((page - 1) * per_page).limit(per_page).all()
    return jsonify(
        {
            "findings": [f.to_dict() for f in findings],
            "total": total,
            "page": page,
            "per_page": per_page,
        }
    )


@api_bp.route("/analysis-runs/<int:run_id>/findings/summary", methods=["GET"])
def get_findings_summary(run_id):
    from sqlalchemy import func

    by_severity = dict(
        db.session.query(Finding.severity, func.count(Finding.id))
        .filter_by(run_id=run_id)
        .group_by(Finding.severity)
        .all()
    )
    by_category = dict(
        db.session.query(Finding.category, func.count(Finding.id))
        .filter_by(run_id=run_id)
        .group_by(Finding.category)
        .all()
    )
    by_tool = dict(
        db.session.query(Finding.tool, func.count(Finding.id))
        .filter_by(run_id=run_id)
        .group_by(Finding.tool)
        .all()
    )
    total = sum(by_severity.values())
    return jsonify(
        {
            "total": total,
            "by_severity": by_severity,
            "by_category": by_category,
            "by_tool": by_tool,
        }
    )


# ── Metrics ──────────────────────────────────────────────
@api_bp.route("/analysis-runs/<int:run_id>/metrics", methods=["GET"])
def get_metrics(run_id):
    metrics = MetricSnapshot.query.filter_by(run_id=run_id).all()
    return jsonify([m.to_dict() for m in metrics])


# ── Recommendations ──────────────────────────────────────
@api_bp.route("/analysis-runs/<int:run_id>/recommendations", methods=["GET"])
def get_recommendations(run_id):
    recs = (
        Recommendation.query.filter_by(run_id=run_id)
        .order_by(Recommendation.priority_score.desc())
        .limit(50)
        .all()
    )
    return jsonify([r.to_dict() for r in recs])


# ── Feedback ─────────────────────────────────────────────
@api_bp.route("/analysis-runs/<int:run_id>/feedback", methods=["GET"])
def get_feedback(run_id):
    feedbacks = Feedback.query.filter_by(run_id=run_id).order_by(Feedback.created_at.desc()).all()
    avg_rating = 0.0
    if feedbacks:
        avg_rating = sum(f.rating for f in feedbacks) / len(feedbacks)
    return jsonify(
        {
            "feedbacks": [f.to_dict() for f in feedbacks],
            "average_rating": round(avg_rating, 1),
            "count": len(feedbacks),
        }
    )


@api_bp.route("/analysis-runs/<int:run_id>/feedback", methods=["POST"])
def submit_feedback(run_id):
    run = db.session.get(AnalysisRun, run_id)
    if not run:
        return jsonify({"error": "Analysis run not found"}), 404

    data = request.get_json() or {}
    rating = data.get("rating", 3)
    comment = data.get("comment", "")

    if not 1 <= rating <= 5:
        return jsonify({"error": "Rating must be between 1 and 5"}), 400

    from scoring.sentiment import compute_sentiment_score, compute_improvement_score

    sentiment = compute_sentiment_score(comment)
    improvement = compute_improvement_score(rating, sentiment)

    feedback = Feedback(
        run_id=run_id, rating=rating, comment=comment, sentiment_score=sentiment
    )
    db.session.add(feedback)
    db.session.flush()

    _recalculate_recommendation_feedback(run_id, improvement)
    db.session.commit()

    return jsonify(feedback.to_dict()), 201


def _recalculate_recommendation_feedback(run_id, improvement_score):
    from sqlalchemy.orm.attributes import flag_modified

    recs = Recommendation.query.filter_by(run_id=run_id).all()
    for rec in recs:
        signals = dict(rec.contributing_signals or {})
        old_feedback = signals.get("feedback_score", 5.0)
        signals["feedback_score"] = round((old_feedback + improvement_score) / 2, 1)
        rec.contributing_signals = signals
        flag_modified(rec, "contributing_signals")
        rec.priority_score = _recalc_priority(signals)
    db.session.commit()


def _recalc_priority(signals):
    weights = {
        "finding_score": 0.35,
        "complexity_score": 0.20,
        "duplication_score": 0.10,
        "dependency_score": 0.10,
        "change_frequency_score": 0.15,
        "feedback_score": 0.10,
    }
    score = sum(signals.get(k, 0.0) * w for k, w in weights.items())
    return round(min(100.0, score * 10), 1)


# ── Commit Signals ───────────────────────────────────────
@api_bp.route("/analysis-runs/<int:run_id>/commit-signals", methods=["GET"])
def get_commit_signals(run_id):
    run = db.session.get(AnalysisRun, run_id)
    if not run:
        return jsonify({"error": "Analysis run not found"}), 404

    signals = (
        CommitSignal.query.join(Repository, CommitSignal.repository_id == Repository.id)
        .filter(Repository.project_id == run.project_id)
        .order_by(CommitSignal.committed_at.desc())
        .limit(200)
        .all()
    )
    return jsonify([s.to_dict() for s in signals])


@api_bp.route("/analysis-runs/<int:run_id>/commit-signals/summary", methods=["GET"])
def get_commit_signals_summary(run_id):
    run = db.session.get(AnalysisRun, run_id)
    if not run:
        return jsonify({"error": "Analysis run not found"}), 404

    signals = (
        CommitSignal.query.join(Repository, CommitSignal.repository_id == Repository.id)
        .filter(Repository.project_id == run.project_id)
        .all()
    )
    by_purpose = {}
    for s in signals:
        cat = s.purpose_category or "other"
        by_purpose[cat] = by_purpose.get(cat, 0) + 1
    return jsonify({"total": len(signals), "by_purpose": by_purpose})


# ── Export ───────────────────────────────────────────────
@api_bp.route("/analysis-runs/<int:run_id>/export", methods=["GET"])
def export_report(run_id):
    run = db.session.get(AnalysisRun, run_id)
    if not run:
        return jsonify({"error": "Analysis run not found"}), 404

    fmt = request.args.get("format", "markdown")

    if fmt == "markdown":
        content = _generate_markdown_report(run)
        report = ExportReport(
            run_id=run_id,
            title=f"Analysis Report - Run #{run_id}",
            format="markdown",
            content=content,
        )
        db.session.add(report)
        db.session.commit()
        return jsonify({"id": report.id, "format": "markdown", "content": content[:5000]})
    elif fmt == "json":
        data = _generate_json_report(run)
        content = json.dumps(data, indent=2, default=str)
        report = ExportReport(
            run_id=run_id,
            title=f"Analysis Report - Run #{run_id}",
            format="json",
            content=content,
        )
        db.session.add(report)
        db.session.commit()
        return jsonify({"id": report.id, "format": "json", "content_preview": content[:2000]})
    else:
        return jsonify({"error": "Unsupported format"}), 400


@api_bp.route("/exports/<int:export_id>/download", methods=["GET"])
def download_export(export_id):
    report = db.session.get(ExportReport, export_id)
    if not report:
        return jsonify({"error": "Export not found"}), 404

    mimetypes = {"markdown": "text/markdown", "json": "application/json"}
    ext_map = {"markdown": "md", "json": "json"}
    ext = ext_map.get(report.format, "txt")
    return send_file(
        BytesIO(report.content.encode("utf-8")),
        mimetype=mimetypes.get(report.format, "text/plain"),
        as_attachment=True,
        download_name=f"analysis_report_{report.run_id}.{ext}",
    )


# ── Dashboard aggregated data ────────────────────────────
@api_bp.route("/dashboard/overview", methods=["GET"])
def dashboard_overview():
    project_id = request.args.get("project_id", type=int)
    run_id = request.args.get("run_id", type=int)
    repository_id = request.args.get("repository_id", type=int)
    language = request.args.get("language")
    severity = request.args.get("severity")
    category = request.args.get("category")
    period = request.args.get("period", "1m")

    if run_id:
        run = db.session.get(AnalysisRun, run_id)
    elif project_id:
        run = (
            AnalysisRun.query.filter_by(project_id=project_id)
            .order_by(AnalysisRun.created_at.desc())
            .first()
        )
    else:
        run = AnalysisRun.query.order_by(AnalysisRun.created_at.desc()).first()

    if not run:
        return jsonify({"error": "No analysis run found"}), 404

    findings_q = Finding.query.filter_by(run_id=run.id)
    if repository_id:
        findings_q = findings_q.filter_by(repository_id=repository_id)
    if severity:
        findings_q = findings_q.filter_by(severity=severity)
    if category:
        findings_q = findings_q.filter_by(category=category)

    total_findings = findings_q.count()
    total_recommendations = Recommendation.query.filter_by(run_id=run.id).count()
    feedbacks = Feedback.query.filter_by(run_id=run.id).all()
    avg_rating = sum(f.rating for f in feedbacks) / max(1, len(feedbacks))

    metrics = MetricSnapshot.query.filter_by(run_id=run.id).all()
    if repository_id:
        metrics = [m for m in metrics if m.scope_id == repository_id or m.scope_type == "project"]

    findings_summary = {}
    by_category = {}
    for f in findings_q.all():
        findings_summary[f.severity] = findings_summary.get(f.severity, 0) + 1
        by_category[f.category] = by_category.get(f.category, 0) + 1

    recommendations = (
        Recommendation.query.filter_by(run_id=run.id)
        .order_by(Recommendation.priority_score.desc())
        .limit(10)
        .all()
    )

    repos = Repository.query.filter(
        Repository.id.in_(run.repository_ids or [])
    ).all()

    return jsonify(
        {
            "run": run.to_dict(),
            "total_findings": total_findings,
            "total_recommendations": total_recommendations,
            "average_rating": round(avg_rating, 1),
            "feedback_count": len(feedbacks),
            "findings_by_severity": findings_summary,
            "findings_by_category": by_category,
            "metrics": [m.to_dict() for m in metrics],
            "top_recommendations": [r.to_dict() for r in recommendations],
            "recent_feedback": [f.to_dict() for f in feedbacks[-5:]],
            "repositories": [r.to_dict() for r in repos],
        }
    )


# ── File Detail Drilldown ────────────────────────────────
@api_bp.route("/analysis-runs/<int:run_id>/files/<path:file_path>", methods=["GET"])
def get_file_detail(run_id, file_path):
    run = db.session.get(AnalysisRun, run_id)
    if not run:
        return jsonify({"error": "Analysis run not found"}), 404

    findings = Finding.query.filter_by(run_id=run_id).filter(
        Finding.location.cast(db.Text).like(f"%{file_path}%")
    ).all()

    source_file = SourceFile.query.filter_by(path=file_path).first()
    symbols = []
    if source_file:
        symbols = CodeSymbol.query.filter_by(file_id=source_file.id).all()

    commits = (
        CommitSignal.query.join(Repository, CommitSignal.repository_id == Repository.id)
        .filter(Repository.project_id == run.project_id)
        .filter(CommitSignal.file_id == (source_file.id if source_file else None))
        .order_by(CommitSignal.committed_at.desc())
        .limit(20)
        .all()
    )

    recs_for_file = [
        r for r in Recommendation.query.filter_by(run_id=run_id).all()
        if r.target_type == "file" and (source_file and str(r.target_id) == str(source_file.id))
    ]

    return jsonify({
        "file_path": file_path,
        "source_file": source_file.to_dict() if source_file else None,
        "findings": [f.to_dict() for f in findings],
        "symbols": [s.to_dict() for s in symbols],
        "commits": [c.to_dict() for c in commits],
        "recommendations": [r.to_dict() for r in recs_for_file],
    })


# ── Complexity Trend ─────────────────────────────────────
@api_bp.route("/analysis-runs/<int:run_id>/complexity-trend", methods=["GET"])
def get_complexity_trend(run_id):
    run = db.session.get(AnalysisRun, run_id)
    if not run:
        return jsonify({"error": "Analysis run not found"}), 404

    symbols = (
        CodeSymbol.query.join(SourceFile, CodeSymbol.file_id == SourceFile.id)
        .join(Repository, SourceFile.repository_id == Repository.id)
        .filter(Repository.project_id == run.project_id)
        .order_by(CodeSymbol.complexity.desc())
        .limit(30)
        .all()
    )

    complexity_data = []
    for sym in symbols:
        sf = db.session.get(SourceFile, sym.file_id)
        complexity_data.append({
            "name": sym.name,
            "file": sf.path if sf else "",
            "kind": sym.kind,
            "complexity": sym.complexity,
        })

    return jsonify({
        "run_id": run_id,
        "symbols": complexity_data,
        "avg_complexity": sum(s["complexity"] for s in complexity_data) / max(1, len(complexity_data)),
    })


def _generate_markdown_report(run):
    lines = []
    lines.append(f"# Code Analysis Report - Run #{run.id}")
    lines.append(f"**Project ID**: {run.project_id}")
    lines.append(f"**Status**: {run.status}")
    lines.append(f"**Created**: {run.created_at}")
    if run.finished_at:
        lines.append(f"**Finished**: {run.finished_at}")
    lines.append("")

    findings = Finding.query.filter_by(run_id=run.id).all()
    lines.append(f"## Findings ({len(findings)} total)")
    lines.append("")
    lines.append("| Severity | Rule ID | Category | Message | File |")
    lines.append("|----------|---------|----------|---------|------|")
    for f in findings[:100]:
        location = f.location or {}
        file_path = location.get("file", "")
        lines.append(
            f"| {f.severity} | {f.rule_id} | {f.category} | {f.message[:80]} | {file_path} |"
        )
    if len(findings) > 100:
        lines.append(f"\n*...and {len(findings) - 100} more findings*")

    recommendations = (
        Recommendation.query.filter_by(run_id=run.id)
        .order_by(Recommendation.priority_score.desc())
        .all()
    )
    lines.append("")
    lines.append(f"## Recommendations ({len(recommendations)} total)")
    lines.append("")
    for r in recommendations[:20]:
        lines.append(f"- **[{r.priority_score:.1f}]** {r.target_type}: {r.target_id or 'N/A'} - {r.rationale}")

    feedbacks = Feedback.query.filter_by(run_id=run.id).all()
    if feedbacks:
        avg = sum(f.rating for f in feedbacks) / len(feedbacks)
        lines.append("")
        lines.append(f"## User Feedback ({len(feedbacks)} ratings, avg: {avg:.1f}/5)")
        for f in feedbacks[-5:]:
            lines.append(f"- Rating: {f.rating}/5 - {f.comment[:100]}")

    lines.append("")
    lines.append("---")
    lines.append(
        "*This report was auto-generated by the Multi-Git Repository Code Analysis Dashboard.*"
    )
    lines.append(
        "*This Markdown file is the AI-agent handoff artifact. Provide it to coding AI agents for implementation guidance.*"
    )
    return "\n".join(lines)


def _generate_json_report(run):
    return {
        "run_id": run.id,
        "project_id": run.project_id,
        "status": run.status,
        "created_at": str(run.created_at),
        "findings": [
            f.to_dict()
            for f in Finding.query.filter_by(run_id=run.id)
            .limit(500)
            .all()
        ],
        "recommendations": [
            r.to_dict()
            for r in Recommendation.query.filter_by(run_id=run.id)
            .order_by(Recommendation.priority_score.desc())
            .limit(50)
            .all()
        ],
        "feedbacks": [
            f.to_dict() for f in Feedback.query.filter_by(run_id=run.id).all()
        ],
        "metrics": [
            m.to_dict() for m in MetricSnapshot.query.filter_by(run_id=run.id).all()
        ],
        "export_note": "This JSON export contains machine-readable analysis results suitable for automated processing.",
    }
