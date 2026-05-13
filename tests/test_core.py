import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from database import db
from models import (
    Project, Repository, AnalysisRun, Finding, Feedback, Recommendation,
    SourceFile, CommitSignal
)
from commit_intel.classifier import CommitClassifier
from commit_intel.frequency import compute_change_frequency
from analyzers.ast_engine import ASTEngine, extract_imports
from analyzers.complexity import compute_complexity
from analyzers.duplication import detect_duplicates
from analyzers.dependency import analyze_dependencies
from scoring.sentiment import compute_sentiment_score, compute_improvement_score
from scoring.engine import compute_priority_score, compute_finding_score

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


class TestModels(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        self.client = self.app.test_client()
        with self.app.app_context():
            db.create_all()

    def tearDown(self):
        with self.app.app_context():
            db.drop_all()

    def test_create_project(self):
        with self.app.app_context():
            p = Project(name="Test Project", description="A test")
            db.session.add(p)
            db.session.commit()
            self.assertEqual(p.name, "Test Project")
            self.assertIsNotNone(p.id)
            self.assertIsNotNone(p.created_at)

    def test_create_repository(self):
        with self.app.app_context():
            p = Project(name="Test")
            db.session.add(p)
            db.session.flush()
            r = Repository(project_id=p.id, provider="github", remote_url="https://github.com/test/repo")
            db.session.add(r)
            db.session.commit()
            self.assertEqual(r.provider, "github")
            self.assertEqual(r.project_id, p.id)

    def test_analysis_run_lifecycle(self):
        with self.app.app_context():
            p = Project(name="Test")
            db.session.add(p)
            db.session.flush()
            run = AnalysisRun(project_id=p.id, status="queued", repository_ids=[])
            db.session.add(run)
            db.session.commit()
            self.assertEqual(run.status, "queued")
            run.status = "running"
            run.progress = 50.0
            db.session.commit()
            self.assertEqual(run.progress, 50.0)

    def test_finding_creation(self):
        with self.app.app_context():
            p = Project(name="Test")
            db.session.add(p)
            db.session.flush()
            r = Repository(project_id=p.id, provider="local", remote_url="/tmp/test")
            db.session.add(r)
            db.session.flush()
            run = AnalysisRun(project_id=p.id, repository_ids=[r.id])
            db.session.add(run)
            db.session.flush()
            f = Finding(
                run_id=run.id,
                repository_id=r.id,
                tool="pylint",
                rule_id="C0301",
                severity="minor",
                category="style",
                message="Line too long",
                location={"file": "test.py", "line": 10},
                fingerprint="abc123",
            )
            db.session.add(f)
            db.session.commit()
            self.assertEqual(f.tool, "pylint")

    def test_feedback_submission(self):
        with self.app.app_context():
            p = Project(name="Test")
            db.session.add(p)
            db.session.flush()
            run = AnalysisRun(project_id=p.id, repository_ids=[])
            db.session.add(run)
            db.session.flush()
            fb = Feedback(run_id=run.id, rating=4, comment="Good analysis", sentiment_score=4.5)
            db.session.add(fb)
            db.session.commit()
            self.assertEqual(fb.rating, 4)

    def test_recommendation(self):
        with self.app.app_context():
            p = Project(name="Test")
            db.session.add(p)
            db.session.flush()
            run = AnalysisRun(project_id=p.id, repository_ids=[])
            db.session.add(run)
            db.session.flush()
            rec = Recommendation(
                run_id=run.id,
                target_type="file",
                target_id=1,
                priority_score=75.5,
                rationale="High complexity and frequent changes",
                contributing_signals={"complexity": 8.0, "changes": 7.0},
            )
            db.session.add(rec)
            db.session.commit()
            self.assertGreater(rec.priority_score, 50)


class TestAPI(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        self.client = self.app.test_client()
        with self.app.app_context():
            db.create_all()

    def tearDown(self):
        with self.app.app_context():
            db.drop_all()

    def test_project_crud(self):
        resp = self.client.post("/api/projects", json={"name": "API Project", "description": "desc"})
        self.assertEqual(resp.status_code, 201)
        data = resp.get_json()
        pid = data["id"]

        resp = self.client.get("/api/projects")
        self.assertEqual(resp.status_code, 200)
        projects = resp.get_json()
        self.assertEqual(len(projects), 1)

        resp = self.client.get(f"/api/projects/{pid}")
        self.assertEqual(resp.status_code, 200)

        resp = self.client.delete(f"/api/projects/{pid}")
        self.assertEqual(resp.status_code, 200)

    def test_add_repository(self):
        resp = self.client.post("/api/projects", json={"name": "Test"})
        pid = resp.get_json()["id"]

        resp = self.client.post(
            f"/api/projects/{pid}/repositories",
            json={"provider": "local", "remote_url": "/tmp/test", "default_branch": "main"},
        )
        self.assertEqual(resp.status_code, 201)
        data = resp.get_json()
        self.assertEqual(data["provider"], "local")

    def test_feedback_submission(self):
        resp = self.client.post("/api/projects", json={"name": "Test"})
        pid = resp.get_json()["id"]

        with self.app.app_context():
            run = AnalysisRun(project_id=pid, repository_ids=[], status="completed")
            db.session.add(run)
            db.session.commit()
            rid = run.id

        resp = self.client.post(
            f"/api/analysis-runs/{rid}/feedback",
            json={"rating": 4, "comment": "Great analysis"},
        )
        self.assertEqual(resp.status_code, 201)
        data = resp.get_json()
        self.assertEqual(data["rating"], 4)

    def test_feedback_validation(self):
        resp = self.client.post("/api/projects", json={"name": "Test"})
        pid = resp.get_json()["id"]

        with self.app.app_context():
            run = AnalysisRun(project_id=pid, repository_ids=[], status="completed")
            db.session.add(run)
            db.session.commit()
            rid = run.id

        resp = self.client.post(
            f"/api/analysis-runs/{rid}/feedback",
            json={"rating": 6, "comment": "Invalid"},
        )
        self.assertEqual(resp.status_code, 400)

    def test_export(self):
        resp = self.client.post("/api/projects", json={"name": "Test"})
        pid = resp.get_json()["id"]

        with self.app.app_context():
            run = AnalysisRun(project_id=pid, repository_ids=[], status="completed")
            db.session.add(run)
            db.session.commit()
            rid = run.id

        resp = self.client.get(f"/api/analysis-runs/{rid}/export?format=markdown")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertIn("content", data)

        resp = self.client.get(f"/api/analysis-runs/{rid}/export?format=json")
        self.assertEqual(resp.status_code, 200)


class TestCommitClassifier(unittest.TestCase):
    def setUp(self):
        self.classifier = CommitClassifier()

    def test_rule_based_fix(self):
        result = self.classifier.classify_rule_based("fix bug in login handler")
        self.assertEqual(result, "bug_fix")

    def test_rule_based_feature(self):
        result = self.classifier.classify_rule_based("add new user registration feature")
        self.assertEqual(result, "feature")

    def test_rule_based_refactor(self):
        result = self.classifier.classify_rule_based("refactor database connection pool")
        self.assertEqual(result, "refactoring")

    def test_rule_based_docs(self):
        result = self.classifier.classify_rule_based("update README with setup docs")
        self.assertEqual(result, "documentation")

    def test_rule_based_test(self):
        result = self.classifier.classify_rule_based("write unit tests for auth module")
        self.assertEqual(result, "test")

    def test_rule_based_build(self):
        result = self.classifier.classify_rule_based("update npm dependencies and build config")
        self.assertEqual(result, "build_config")

    def test_classify_batch(self):
        messages = ["fix bug", "add feature", "update docs", "refactor code"]
        results = self.classifier.classify_batch(messages)
        self.assertEqual(len(results), 4)

    def test_cluster_unsupervised(self):
        messages = [f"commit message {i}: fix bug in part {i % 3}" for i in range(50)]
        labels, terms = self.classifier.cluster_unsupervised(messages)
        self.assertTrue(len(labels) > 0)

    def test_transition_to_supervised(self):
        messages = [
            "fix null pointer bug",
            "add new login feature",
            "update README documentation",
            "refactor auth module",
            "add unit tests",
            "fix memory leak",
            "implement search feature",
            "update build configuration",
            "fix broken tests",
            "add API documentation",
            "refactor database layer",
            "fix crash on startup",
        ]
        labels = [
            "bug_fix",
            "feature",
            "documentation",
            "refactoring",
            "test",
            "bug_fix",
            "feature",
            "build_config",
            "test",
            "documentation",
            "refactoring",
            "bug_fix",
        ]
        success = self.classifier.transition_to_supervised(messages, labels)
        self.assertTrue(success)
        self.assertTrue(self.classifier.is_supervised_ready)

        predictions = self.classifier.predict(["fix another bug", "add new feature"])
        self.assertEqual(len(predictions), 2)


class TestChangeFrequency(unittest.TestCase):
    def test_compute_frequency(self):
        commits = [
            {"sha": "a1", "author": "alice", "date": "2024-01-01", "message": "fix", "files": ["src/main.py", "src/utils.py"]},
            {"sha": "a2", "author": "bob", "date": "2024-01-02", "message": "feature", "files": ["src/main.py"]},
            {"sha": "a3", "author": "alice", "date": "2024-01-03", "message": "refactor", "files": ["src/utils.py", "tests/test.py"]},
        ]
        result = compute_change_frequency(commits)
        self.assertEqual(result["total_commits"], 3)
        self.assertEqual(result["total_files_changed"], 3)
        self.assertEqual(result["file_frequency"]["src/main.py"], 2)
        self.assertEqual(result["file_frequency"]["src/utils.py"], 2)
        self.assertEqual(result["author_frequency"]["alice"], 4)


class TestASTEngine(unittest.TestCase):
    def setUp(self):
        self.engine = ASTEngine()

    def test_parse_python_functions(self):
        content = '''
def hello():
    pass

class MyClass:
    def method(self):
        if True:
            print("hi")
'''
        symbols = self.engine.extract_symbols("test.py", content, "Python")
        self.assertTrue(len(symbols) >= 2)
        func_names = [s["name"] for s in symbols if s["kind"] == "function"]
        self.assertIn("hello", func_names)
        self.assertIn("method", func_names)

    def test_parse_python_complexity(self):
        content = '''
def complex_func(x):
    if x > 0:
        for i in range(x):
            if i % 2 == 0:
                print(i)
            elif i % 3 == 0:
                print("three")
    return x
'''
        symbols = self.engine.extract_symbols("test.py", content, "Python")
        func = next((s for s in symbols if s["name"] == "complex_func"), None)
        self.assertIsNotNone(func)
        self.assertGreater(func["complexity"], 2)

    def test_parse_js(self):
        content = '''
function greet(name) {
    return "Hello " + name;
}

class UserService {
    getUser(id) {
        return {id: id};
    }
}
'''
        symbols = self.engine.extract_symbols("test.js", content, "JavaScript")
        self.assertTrue(len(symbols) >= 2)

    def test_extract_imports_python(self):
        content = "import os\nfrom collections import defaultdict\nimport numpy as np\n"
        imports = extract_imports(content, "Python")
        self.assertIn("os", imports)
        self.assertIn("collections", imports)


class TestComplexity(unittest.TestCase):
    def test_python_complexity(self):
        content = '''
def example(x):
    if x > 0:
        for i in range(x):
            if i % 2:
                print(i)
    return x
'''
        result = compute_complexity(content, "Python")
        self.assertGreater(result["cyclomatic"], 0)
        self.assertGreater(result["sloc"], 0)

    def test_generic_complexity(self):
        content = "if (x) { while (y) { z++; } }"
        result = compute_complexity(content, "JavaScript")
        self.assertGreater(result["cyclomatic"], 0)


class TestDuplication(unittest.TestCase):
    def test_detect_duplicates(self):
        block = "def foo():\n    x = 1\n    y = 2\n    z = 3\n    w = 4\n    v = 5\n    return x"
        files = {
            "file_a.py": block + "\n\n# unique a",
            "file_b.py": block + "\n\n# unique b",
        }
        dupes = detect_duplicates(files, min_lines=6)
        self.assertGreater(len(dupes), 0)

    def test_no_duplicates(self):
        files = {
            "a.py": "def unique_a():\n    pass",
            "b.py": "def unique_b():\n    return 42",
        }
        dupes = detect_duplicates(files, min_lines=3)
        self.assertEqual(len(dupes), 0)


class TestDependencies(unittest.TestCase):
    def test_analyze_deps(self):
        files = {
            "src/main.py": "import os\nfrom src.utils import helper\n",
            "src/utils.py": "import json\nfrom collections import defaultdict\n",
        }
        result = analyze_dependencies(files, "Python")
        self.assertIn("src/main.py", result["internal_deps"])
        self.assertIn("src/utils.py", result["depended_by"])


class TestSentiment(unittest.TestCase):
    def test_positive(self):
        score = compute_sentiment_score("This is a great and helpful analysis")
        self.assertGreater(score, 3.0)

    def test_negative(self):
        score = compute_sentiment_score("This analysis is inaccurate and messy")
        self.assertLess(score, 3.0)

    def test_neutral(self):
        score = compute_sentiment_score("Analysis complete")
        self.assertEqual(score, 3.0)

    def test_improvement_score(self):
        score = compute_improvement_score(5, 4.0)
        self.assertGreater(score, 4.0)

    def test_korean_sentiment(self):
        score = compute_sentiment_score("분석 결과가 매우 유용하고 정확합니다 좋은")
        self.assertGreater(score, 3.0)


class TestScoring(unittest.TestCase):
    def test_finding_score(self):
        findings = [
            {"severity": "critical"},
            {"severity": "major"},
            {"severity": "minor"},
        ]
        score = compute_finding_score(findings)
        self.assertGreater(score, 0)

    def test_priority_score(self):
        signals = {
            "finding_score": 8.0,
            "complexity_score": 7.0,
            "duplication_score": 3.0,
            "dependency_score": 5.0,
            "change_frequency_score": 6.0,
            "feedback_score": 4.0,
        }
        score = compute_priority_score(signals)
        self.assertGreater(score, 0)
        self.assertLessEqual(score, 100)


class TestFrontendPages(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        self.client = self.app.test_client()
        with self.app.app_context():
            db.create_all()

    def tearDown(self):
        with self.app.app_context():
            db.drop_all()

    def test_index_page(self):
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Projects", resp.data)

    def test_dashboard_page(self):
        resp = self.client.get("/dashboard")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Dashboard", resp.data)

    def test_dashboard_with_run(self):
        with self.app.app_context():
            p = Project(name="Test")
            db.session.add(p)
            db.session.flush()
            run = AnalysisRun(project_id=p.id, repository_ids=[], status="completed")
            db.session.add(run)
            db.session.commit()
            rid = run.id

        resp = self.client.get(f"/dashboard?run_id={rid}")
        self.assertEqual(resp.status_code, 200)

    def test_analysis_page(self):
        with self.app.app_context():
            p = Project(name="Test")
            db.session.add(p)
            db.session.flush()
            run = AnalysisRun(project_id=p.id, repository_ids=[], status="running")
            db.session.add(run)
            db.session.commit()
            rid = run.id

        resp = self.client.get(f"/analysis/{rid}")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Analysis Run", resp.data)

    def test_export_page(self):
        with self.app.app_context():
            p = Project(name="Test")
            db.session.add(p)
            db.session.flush()
            run = AnalysisRun(project_id=p.id, repository_ids=[], status="completed")
            db.session.add(run)
            db.session.commit()
            rid = run.id

        resp = self.client.get(f"/export/{rid}")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Export", resp.data)

    def test_project_page(self):
        with self.app.app_context():
            p = Project(name="Test")
            db.session.add(p)
            db.session.commit()
            pid = p.id

        resp = self.client.get(f"/project/{pid}")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Project", resp.data)


class TestFixtureFiles(unittest.TestCase):
    def setUp(self):
        self.engine = ASTEngine()

    def _read_fixture(self, name):
        path = os.path.join(FIXTURES_DIR, name)
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    def test_python_fixture_ast(self):
        content = self._read_fixture("sample.py")
        symbols = self.engine.extract_symbols("sample.py", content, "Python")
        self.assertGreater(len(symbols), 0)
        funcs = [s for s in symbols if s["kind"] == "function"]
        classes = [s for s in symbols if s["kind"] == "class"]
        self.assertGreaterEqual(len(funcs), 2)
        self.assertGreaterEqual(len(classes), 1)

    def test_python_fixture_complexity(self):
        content = self._read_fixture("sample.py")
        result = compute_complexity(content, "Python")
        self.assertGreater(result["cyclomatic"], 0)
        self.assertGreater(result["sloc"], 0)

    def test_java_fixture_ast(self):
        content = self._read_fixture("sample.java")
        symbols = self.engine.extract_symbols("sample.java", content, "Java")
        self.assertGreaterEqual(len(symbols), 1)

    def test_java_fixture_complexity(self):
        content = self._read_fixture("sample.java")
        result = compute_complexity(content, "Java")
        self.assertGreater(result["sloc"], 0)

    def test_javascript_fixture_ast(self):
        content = self._read_fixture("sample.js")
        symbols = self.engine.extract_symbols("sample.js", content, "JavaScript")
        self.assertGreaterEqual(len(symbols), 1)

    def test_javascript_fixture_complexity(self):
        content = self._read_fixture("sample.js")
        result = compute_complexity(content, "JavaScript")
        self.assertGreater(result["cyclomatic"], 0)

    def test_cpp_fixture_ast(self):
        content = self._read_fixture("sample.cpp")
        symbols = self.engine.extract_symbols("sample.cpp", content, "C++")
        self.assertGreaterEqual(len(symbols), 1)

    def test_cpp_fixture_complexity(self):
        content = self._read_fixture("sample.cpp")
        result = compute_complexity(content, "C++")
        self.assertGreater(result["sloc"], 0)

    def test_fixture_duplication_detection(self):
        py_content = self._read_fixture("sample.py")
        files = {"a.py": py_content, "b.py": py_content}
        dupes = detect_duplicates(files, min_lines=2)
        self.assertGreater(len(dupes), 0)

    def test_fixture_imports(self):
        content = self._read_fixture("sample.py")
        imports = extract_imports(content, "Python")
        self.assertIsInstance(imports, list)


class TestRetryPreservation(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        self.client = self.app.test_client()
        with self.app.app_context():
            db.create_all()

    def tearDown(self):
        with self.app.app_context():
            db.drop_all()

    def test_retry_preserves_other_repo_findings(self):
        with self.app.app_context():
            p = Project(name="Test")
            db.session.add(p)
            db.session.flush()

            r1 = Repository(project_id=p.id, provider="local", remote_url="/tmp/a")
            r2 = Repository(project_id=p.id, provider="local", remote_url="/tmp/b")
            db.session.add_all([r1, r2])
            db.session.flush()

            run = AnalysisRun(project_id=p.id, repository_ids=[r1.id, r2.id], status="completed")
            db.session.add(run)
            db.session.flush()

            sf1 = SourceFile(repository_id=r1.id, path="a.py", language="Python", size=100, hash="abc")
            sf2 = SourceFile(repository_id=r2.id, path="b.py", language="Python", size=200, hash="def")
            db.session.add_all([sf1, sf2])
            db.session.flush()

            f1 = Finding(run_id=run.id, repository_id=r1.id, file_id=sf1.id, tool="pylint",
                         rule_id="C001", severity="minor", category="style", message="test",
                         location={"file": "a.py", "line": 1}, fingerprint="fp1", raw_payload={})
            f2 = Finding(run_id=run.id, repository_id=r2.id, file_id=sf2.id, tool="pylint",
                         rule_id="C002", severity="major", category="style", message="test2",
                         location={"file": "b.py", "line": 2}, fingerprint="fp2", raw_payload={})
            db.session.add_all([f1, f2])
            db.session.commit()

            self.assertEqual(Finding.query.filter_by(run_id=run.id).count(), 2)

            resp = self.client.post(
                f"/api/analysis-runs/{run.id}/retry",
                json={"repository_ids": [r1.id], "period": "1m"},
            )
            self.assertEqual(resp.status_code, 200)

            findings = Finding.query.filter_by(run_id=run.id).all()
            repo_ids_in_findings = {f.repository_id for f in findings}
            self.assertIn(r2.id, repo_ids_in_findings)
            self.assertNotIn(r1.id, repo_ids_in_findings)
            self.assertEqual(len(findings), 1)
            self.assertEqual(findings[0].repository_id, r2.id)

    def test_feedback_recalculates_recommendations(self):
        with self.app.app_context():
            p = Project(name="Test")
            db.session.add(p)
            db.session.flush()
            run = AnalysisRun(project_id=p.id, repository_ids=[], status="completed")
            db.session.add(run)
            db.session.flush()
            run_id = run.id

            rec = Recommendation(
                run_id=run.id, target_type="file", target_id=1,
                priority_score=50.0, rationale="test",
                contributing_signals={
                    "finding_score": 5.0, "complexity_score": 3.0,
                    "duplication_score": 2.0, "dependency_score": 1.0,
                    "change_frequency_score": 4.0, "feedback_score": 5.0,
                }
            )
            db.session.add(rec)
            db.session.commit()
            rec_id = rec.id
            old_score = rec.priority_score

        resp = self.client.post(
            f"/api/analysis-runs/{run_id}/feedback",
            json={"rating": 1, "comment": "poor inaccurate analysis"},
        )
        self.assertEqual(resp.status_code, 201)

        with self.app.app_context():
            updated = db.session.get(Recommendation, rec_id)
            self.assertIsNotNone(updated)
            self.assertNotEqual(updated.priority_score, old_score)
            signals = updated.contributing_signals or {}
            self.assertLess(signals.get("feedback_score", 5.0), 5.0)


if __name__ == "__main__":
    unittest.main()
