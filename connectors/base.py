import hashlib
import os
import shutil
import subprocess
from datetime import datetime, timezone
from abc import ABC, abstractmethod


class BaseConnector(ABC):
    def __init__(self, repo_url, local_path, branch=None):
        self.repo_url = repo_url
        self.local_path = local_path
        self.branch = branch or "main"

    @abstractmethod
    def clone_or_fetch(self):
        pass

    @abstractmethod
    def get_branches(self):
        pass

    @abstractmethod
    def get_commit_history(self, since=None):
        pass

    @abstractmethod
    def get_file_list(self):
        pass

    @abstractmethod
    def get_file_content(self, file_path):
        pass

    @staticmethod
    def compute_file_hash(content):
        return hashlib.sha256(content.encode("utf-8", errors="replace")).hexdigest()

    @staticmethod
    def detect_language(file_path):
        ext = os.path.splitext(file_path)[1].lower()
        ext_map = {
            ".py": "Python",
            ".js": "JavaScript",
            ".jsx": "JavaScript",
            ".mjs": "JavaScript",
            ".java": "Java",
            ".cpp": "C++",
            ".cc": "C++",
            ".cxx": "C++",
            ".c": "C",
            ".h": "C/C++",
            ".hpp": "C++",
            ".hxx": "C++",
        }
        return ext_map.get(ext, "Unknown")

    @staticmethod
    def get_owner_hint(file_path, commits):
        if not commits:
            return ""
        author_counts = {}
        for c in commits:
            if file_path in (c.get("files") or []):
                author = c.get("author", "unknown")
                author_counts[author] = author_counts.get(author, 0) + 1
        if not author_counts:
            for c in commits:
                author = c.get("author", "unknown")
                author_counts[author] = author_counts.get(author, 0) + 1
        return max(author_counts, key=author_counts.get) if author_counts else ""
