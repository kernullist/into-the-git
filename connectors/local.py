import os
import subprocess
from datetime import datetime, timezone

from .base import BaseConnector


class LocalConnector(BaseConnector):
    def clone_or_fetch(self):
        if not os.path.exists(self.local_path):
            os.makedirs(self.local_path, exist_ok=True)
            result = self._run_git(["clone", self.repo_url, self.local_path])
            if result["success"]:
                self._run_git(["-C", self.local_path, "checkout", self.branch])
            return result
        else:
            result = self._run_git(
                ["-C", self.local_path, "fetch", "--all", "--prune"]
            )
            if result["success"]:
                self._run_git(
                    ["-C", self.local_path, "checkout", self.branch], timeout=30
                )
                self._run_git(
                    ["-C", self.local_path, "pull", "origin", self.branch],
                    timeout=60,
                )
            return result

    def get_branches(self):
        result = self._run_git(["-C", self.local_path, "branch", "-a"])
        if result["success"]:
            branches = []
            for line in result["stdout"].split("\n"):
                line = line.strip().replace("*", "").strip()
                if line and not line.startswith("refs/stash"):
                    branch = line.replace("remotes/origin/", "")
                    if branch and branch not in branches and "HEAD" not in branch:
                        branches.append(branch)
            return branches
        return []

    def get_commit_history(self, since=None):
        cmd = [
            "-C", self.local_path,
            "log", "--all",
            "--format=%H|%an|%aI|%s",
            "--name-only",
        ]
        if since:
            cmd.insert(3, f"--since={since}")

        result = self._run_git(cmd, timeout=120)
        commits = []
        if result["success"]:
            lines = result["stdout"].split("\n")
            current = None
            for line in lines:
                if not line.strip():
                    if current:
                        commits.append(current)
                    current = None
                    continue
                if "|" in line and not line.startswith(" "):
                    if current:
                        commits.append(current)
                    parts = line.split("|", 3)
                    current = {
                        "sha": parts[0],
                        "author": parts[1] if len(parts) > 1 else "",
                        "date": parts[2] if len(parts) > 2 else "",
                        "message": parts[3] if len(parts) > 3 else "",
                        "files": [],
                    }
                elif current and line.strip():
                    current["files"].append(line.strip())
            if current:
                commits.append(current)
        return commits

    def get_file_list(self):
        files = []
        repo_dir = self.local_path
        if not os.path.isdir(repo_dir):
            return files
        for root, dirs, filenames in os.walk(repo_dir):
            dirs[:] = [d for d in dirs if d != ".git" and not d.startswith(".")]
            for f in filenames:
                filepath = os.path.join(root, f)
                relpath = os.path.relpath(filepath, repo_dir)
                lang = self.detect_language(relpath)
                if lang != "Unknown":
                    try:
                        size = os.path.getsize(filepath)
                    except OSError:
                        size = 0
                    files.append(
                        {"path": relpath, "language": lang, "size": size}
                    )
        return files

    def get_file_content(self, file_path):
        full_path = os.path.join(self.local_path, file_path)
        try:
            with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                return f.read()
        except Exception:
            return ""

    def get_last_commit_for_file(self, file_path):
        result = self._run_git(
            ["-C", self.local_path, "log", "-1", "--format=%H", "--", file_path]
        )
        if result["success"]:
            return result["stdout"].strip()
        return ""

    def _run_git(self, cmd, timeout=120):
        try:
            result = subprocess.run(
                ["git"] + cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout,
            )
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "stdout": "",
                "stderr": "Git command timed out",
                "returncode": -1,
            }
        except FileNotFoundError:
            return {
                "success": False,
                "stdout": "",
                "stderr": "Git executable not found. Please install Git.",
                "returncode": -1,
            }
