import os

from flask import Flask, render_template
from config import Config
from database import init_db
from api.routes import api_bp


def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_object(Config)

    os.makedirs(Config.DATA_DIR, exist_ok=True)
    os.makedirs(Config.REPOS_DIR, exist_ok=True)
    os.makedirs(Config.REPORTS_DIR, exist_ok=True)

    init_db(app)
    app.register_blueprint(api_bp, url_prefix="/api")

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/project/<int:project_id>")
    def project_page(project_id):
        return render_template("project.html", project_id=project_id)

    @app.route("/dashboard")
    def dashboard():
        return render_template("dashboard.html")

    @app.route("/analysis/<int:run_id>")
    def analysis_page(run_id):
        return render_template("analysis.html", run_id=run_id)

    @app.route("/export/<int:run_id>")
    def export_page(run_id):
        return render_template("export.html", run_id=run_id)

    return app


if __name__ == "__main__":
    app = create_app()
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    print("Starting Multi-Git Repository Code Analysis Dashboard...")
    print(f"Open http://localhost:5000 in your browser")
    app.run(host="0.0.0.0", port=5000, debug=debug)
