import hashlib
import json
import os
import subprocess
import tempfile
from abc import ABC, abstractmethod


class BaseAnalyzer(ABC):
    name = "base"
    supported_languages = []

    @abstractmethod
    def is_available(self):
        pass

    @abstractmethod
    def analyze(self, file_path, content, language):
        pass

    def make_fingerprint(self, tool, rule_id, file_path, location, message):
        raw = f"{tool}|{rule_id}|{file_path}|{json.dumps(location)}|{message}"
        return hashlib.sha256(raw.encode()).hexdigest()[:32]

    def _run_tool(self, cmd, timeout=300):
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=timeout
            )
            return {
                "success": result.returncode >= 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "stdout": "",
                "stderr": "Tool execution timed out",
                "returncode": -1,
            }
        except FileNotFoundError:
            return {
                "success": False,
                "stdout": "",
                "stderr": f"Tool not found",
                "returncode": -1,
            }
