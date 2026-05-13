from datetime import datetime, timezone
from database import db


class Project(db.Model):
    __tablename__ = "projects"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    repositories = db.relationship("Repository", back_populates="project", lazy="dynamic")
    analysis_runs = db.relationship("AnalysisRun", back_populates="project", lazy="dynamic")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "repository_count": self.repositories.count(),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Repository(db.Model):
    __tablename__ = "repositories"

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=False)
    provider = db.Column(db.String(50), nullable=False, default="local")
    remote_url = db.Column(db.String(1024), nullable=False)
    default_branch = db.Column(db.String(255), default="main")
    selected_branches = db.Column(db.JSON, default=list)
    language_summary = db.Column(db.JSON, default=dict)
    local_path = db.Column(db.String(1024), default="")
    last_fetched_at = db.Column(db.DateTime, nullable=True)

    project = db.relationship("Project", back_populates="repositories")
    source_files = db.relationship("SourceFile", back_populates="repository", lazy="dynamic")
    findings = db.relationship("Finding", back_populates="repository", lazy="dynamic")
    commit_signals = db.relationship("CommitSignal", back_populates="repository", lazy="dynamic")

    def to_dict(self):
        return {
            "id": self.id,
            "project_id": self.project_id,
            "provider": self.provider,
            "remote_url": self.remote_url,
            "default_branch": self.default_branch,
            "selected_branches": self.selected_branches,
            "language_summary": self.language_summary,
            "last_fetched_at": (
                self.last_fetched_at.isoformat() if self.last_fetched_at else None
            ),
        }


class AnalysisRun(db.Model):
    __tablename__ = "analysis_runs"

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=False)
    repository_ids = db.Column(db.JSON, default=list)
    branch_refs = db.Column(db.JSON, default=list)
    status = db.Column(
        db.String(50), default="queued"
    )  # queued, running, completed, failed, cancelled
    progress = db.Column(db.Float, default=0.0)
    started_at = db.Column(db.DateTime, nullable=True)
    finished_at = db.Column(db.DateTime, nullable=True)
    logs = db.Column(db.Text, default="")
    tool_versions = db.Column(db.JSON, default=dict)
    error_summary = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    project = db.relationship("Project", back_populates="analysis_runs")
    findings = db.relationship("Finding", back_populates="analysis_run", lazy="dynamic")
    metric_snapshots = db.relationship(
        "MetricSnapshot", back_populates="analysis_run", lazy="dynamic"
    )
    feedbacks = db.relationship("Feedback", back_populates="analysis_run", lazy="dynamic")
    recommendations = db.relationship(
        "Recommendation", back_populates="analysis_run", lazy="dynamic"
    )
    export_reports = db.relationship(
        "ExportReport", back_populates="analysis_run", lazy="dynamic"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "project_id": self.project_id,
            "repository_ids": self.repository_ids,
            "branch_refs": self.branch_refs,
            "status": self.status,
            "progress": self.progress,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
            "logs": self.logs[-5000:] if self.logs else "",
            "tool_versions": self.tool_versions,
            "error_summary": self.error_summary,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "finding_count": self.findings.count(),
        }


class SourceFile(db.Model):
    __tablename__ = "source_files"

    id = db.Column(db.Integer, primary_key=True)
    repository_id = db.Column(db.Integer, db.ForeignKey("repositories.id"), nullable=False)
    path = db.Column(db.String(1024), nullable=False)
    language = db.Column(db.String(50), nullable=False)
    size = db.Column(db.Integer, default=0)
    hash = db.Column(db.String(64), default="")
    last_commit_sha = db.Column(db.String(64), default="")
    owner_hint = db.Column(db.String(255), default="")

    repository = db.relationship("Repository", back_populates="source_files")
    code_symbols = db.relationship("CodeSymbol", back_populates="source_file", lazy="dynamic")

    def to_dict(self):
        return {
            "id": self.id,
            "repository_id": self.repository_id,
            "path": self.path,
            "language": self.language,
            "size": self.size,
            "hash": self.hash,
            "last_commit_sha": self.last_commit_sha,
            "owner_hint": self.owner_hint,
        }


class CodeSymbol(db.Model):
    __tablename__ = "code_symbols"

    id = db.Column(db.Integer, primary_key=True)
    file_id = db.Column(db.Integer, db.ForeignKey("source_files.id"), nullable=False)
    kind = db.Column(db.String(50), nullable=False)  # function, class, method, module
    name = db.Column(db.String(255), nullable=False)
    location = db.Column(db.JSON, default=dict)  # {start_line, end_line, start_col, end_col}
    signature = db.Column(db.Text, default="")
    complexity = db.Column(db.Integer, default=0)
    dependency_refs = db.Column(db.JSON, default=list)

    source_file = db.relationship("SourceFile", back_populates="code_symbols")

    def to_dict(self):
        return {
            "id": self.id,
            "file_id": self.file_id,
            "kind": self.kind,
            "name": self.name,
            "location": self.location,
            "signature": self.signature,
            "complexity": self.complexity,
            "dependency_refs": self.dependency_refs,
        }


class Finding(db.Model):
    __tablename__ = "findings"

    id = db.Column(db.Integer, primary_key=True)
    run_id = db.Column(db.Integer, db.ForeignKey("analysis_runs.id"), nullable=False)
    repository_id = db.Column(db.Integer, db.ForeignKey("repositories.id"), nullable=False)
    file_id = db.Column(db.Integer, db.ForeignKey("source_files.id"), nullable=True)
    symbol_id = db.Column(db.Integer, db.ForeignKey("code_symbols.id"), nullable=True)
    tool = db.Column(db.String(100), nullable=False)
    rule_id = db.Column(db.String(255), default="")
    severity = db.Column(
        db.String(50), default="info"
    )  # info, minor, major, critical, blocker
    category = db.Column(db.String(100), default="")
    message = db.Column(db.Text, default="")
    location = db.Column(db.JSON, default=dict)
    fingerprint = db.Column(db.String(128), default="")
    raw_payload = db.Column(db.JSON, default=dict)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    analysis_run = db.relationship("AnalysisRun", back_populates="findings")
    repository = db.relationship("Repository", back_populates="findings")

    def to_dict(self):
        return {
            "id": self.id,
            "run_id": self.run_id,
            "repository_id": self.repository_id,
            "file_id": self.file_id,
            "symbol_id": self.symbol_id,
            "tool": self.tool,
            "rule_id": self.rule_id,
            "severity": self.severity,
            "category": self.category,
            "message": self.message,
            "location": self.location,
            "fingerprint": self.fingerprint,
        }


class MetricSnapshot(db.Model):
    __tablename__ = "metric_snapshots"

    id = db.Column(db.Integer, primary_key=True)
    run_id = db.Column(db.Integer, db.ForeignKey("analysis_runs.id"), nullable=False)
    scope_type = db.Column(db.String(50), nullable=False)  # project, repository, file, symbol
    scope_id = db.Column(db.Integer, nullable=True)
    metric_name = db.Column(db.String(100), nullable=False)
    value = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(50), default="")

    analysis_run = db.relationship("AnalysisRun", back_populates="metric_snapshots")

    def to_dict(self):
        return {
            "id": self.id,
            "run_id": self.run_id,
            "scope_type": self.scope_type,
            "scope_id": self.scope_id,
            "metric_name": self.metric_name,
            "value": self.value,
            "unit": self.unit,
        }


class CommitSignal(db.Model):
    __tablename__ = "commit_signals"

    id = db.Column(db.Integer, primary_key=True)
    repository_id = db.Column(db.Integer, db.ForeignKey("repositories.id"), nullable=False)
    file_id = db.Column(db.Integer, db.ForeignKey("source_files.id"), nullable=True)
    symbol_id = db.Column(db.Integer, db.ForeignKey("code_symbols.id"), nullable=True)
    commit_sha = db.Column(db.String(64), nullable=False)
    author = db.Column(db.String(255), default="")
    committed_at = db.Column(db.DateTime, nullable=True)
    purpose_category = db.Column(db.String(100), default="")
    message = db.Column(db.Text, default="")
    touched_lines = db.Column(db.Integer, default=0)

    repository = db.relationship("Repository", back_populates="commit_signals")

    def to_dict(self):
        return {
            "id": self.id,
            "repository_id": self.repository_id,
            "file_id": self.file_id,
            "symbol_id": self.symbol_id,
            "commit_sha": self.commit_sha,
            "author": self.author,
            "committed_at": self.committed_at.isoformat() if self.committed_at else None,
            "purpose_category": self.purpose_category,
            "message": self.message,
            "touched_lines": self.touched_lines,
        }


class Feedback(db.Model):
    __tablename__ = "feedbacks"

    id = db.Column(db.Integer, primary_key=True)
    run_id = db.Column(db.Integer, db.ForeignKey("analysis_runs.id"), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5
    comment = db.Column(db.Text, default="")
    sentiment_score = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    analysis_run = db.relationship("AnalysisRun", back_populates="feedbacks")

    def to_dict(self):
        return {
            "id": self.id,
            "run_id": self.run_id,
            "rating": self.rating,
            "comment": self.comment,
            "sentiment_score": self.sentiment_score,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Recommendation(db.Model):
    __tablename__ = "recommendations"

    id = db.Column(db.Integer, primary_key=True)
    run_id = db.Column(db.Integer, db.ForeignKey("analysis_runs.id"), nullable=False)
    target_type = db.Column(
        db.String(50), nullable=False
    )  # file, function, repository, project
    target_id = db.Column(db.Integer, nullable=True)
    priority_score = db.Column(db.Float, default=0.0)
    rationale = db.Column(db.Text, default="")
    contributing_signals = db.Column(db.JSON, default=dict)
    status = db.Column(db.String(50), default="open")  # open, in_progress, resolved, dismissed

    analysis_run = db.relationship("AnalysisRun", back_populates="recommendations")

    def to_dict(self):
        return {
            "id": self.id,
            "run_id": self.run_id,
            "target_type": self.target_type,
            "target_id": self.target_id,
            "priority_score": self.priority_score,
            "rationale": self.rationale,
            "contributing_signals": self.contributing_signals,
            "status": self.status,
        }


class ExportReport(db.Model):
    __tablename__ = "export_reports"

    id = db.Column(db.Integer, primary_key=True)
    run_id = db.Column(db.Integer, db.ForeignKey("analysis_runs.id"), nullable=False)
    title = db.Column(db.String(255), default="")
    format = db.Column(db.String(50), default="markdown")  # markdown, json, html
    content = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    analysis_run = db.relationship("AnalysisRun", back_populates="export_reports")

    def to_dict(self):
        return {
            "id": self.id,
            "run_id": self.run_id,
            "title": self.title,
            "format": self.format,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
