import os
import secrets

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{os.path.join(basedir, 'data', 'dashboard.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    DATA_DIR = os.path.join(basedir, "data")
    REPOS_DIR = os.path.join(DATA_DIR, "repos")
    REPORTS_DIR = os.path.join(DATA_DIR, "reports")

    MAX_ANALYSIS_TIMEOUT = int(os.environ.get("MAX_ANALYSIS_TIMEOUT", "3600"))
    WORKER_THREADS = int(os.environ.get("WORKER_THREADS", "2"))

    GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
    GITLAB_TOKEN = os.environ.get("GITLAB_TOKEN", "")

    # ML configuration
    CLUSTER_MIN_SAMPLES = int(os.environ.get("CLUSTER_MIN_SAMPLES", "30"))
    CLASSIFIER_CONFIDENCE_THRESHOLD = float(
        os.environ.get("CLASSIFIER_CONFIDENCE_THRESHOLD", "0.6")
    )
