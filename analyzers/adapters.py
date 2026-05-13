import json
import os
import re
import tempfile

from .base import BaseAnalyzer


class CppCheckAdapter(BaseAnalyzer):
    name = "cppcheck"
    supported_languages = ["C++"]

    def is_available(self):
        result = self._run_tool(["cppcheck", "--version"])
        return result["success"]

    def analyze(self, file_path, content, language):
        if language not in self.supported_languages:
            return []

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".cpp", delete=False, encoding="utf-8"
        ) as f:
            f.write(content)
            tmp_path = f.name

        try:
            result = self._run_tool(
                [
                    "cppcheck",
                    "--enable=all",
                    "--inconclusive",
                    "--quiet",
                    "--template={file}|{line}|{column}|{severity}|{id}|{message}",
                    tmp_path,
                ]
            )

            findings = []
            if result["success"]:
                for line in result["stdout"].split("\n"):
                    if not line.strip():
                        continue
                    parts = line.split("|", 5)
                    if len(parts) >= 6:
                        parsed_file = parts[0]
                        try:
                            line_num = int(parts[1])
                        except ValueError:
                            line_num = 0
                        severity = self._map_severity(parts[3])
                        rule_id = parts[4]
                        message = parts[5]

                        findings.append(
                            {
                                "tool": self.name,
                                "rule_id": rule_id,
                                "severity": severity,
                                "category": self._map_category(rule_id),
                                "message": message.strip(),
                                "location": {
                                    "file": file_path,
                                    "line": line_num,
                                    "column": 0,
                                },
                            }
                        )
            return findings
        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

    def _map_severity(self, cppcheck_severity):
        mapping = {
            "error": "critical",
            "warning": "major",
            "style": "minor",
            "performance": "minor",
            "portability": "minor",
            "information": "info",
        }
        return mapping.get(cppcheck_severity, "minor")

    def _map_category(self, rule_id):
        rule_lower = rule_id.lower()
        if "nullpointer" in rule_lower or "null" in rule_lower.split("_") or re.search(r'\bnull\b', rule_lower):
            return "null_pointer"
        if "memory" in rule_id.lower() or "leak" in rule_id.lower():
            return "memory"
        if "bound" in rule_id.lower() or "overflow" in rule_id.lower():
            return "buffer_overflow"
        if "unused" in rule_id.lower():
            return "unused_code"
        if "style" in rule_id.lower():
            return "code_style"
        return "general"


class PylintAdapter(BaseAnalyzer):
    name = "pylint"
    supported_languages = ["Python"]

    def is_available(self):
        result = self._run_tool(["pylint", "--version"])
        return result["success"]

    def analyze(self, file_path, content, language):
        if language not in self.supported_languages:
            return []

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, encoding="utf-8"
        ) as f:
            f.write(content)
            tmp_path = f.name

        try:
            result = self._run_tool(
                [
                    "pylint",
                    "--output-format=json",
                    "--disable=all",
                    "--enable=C,R,W,E",
                    tmp_path,
                ]
            )

            findings = []
            if result["success"]:
                try:
                    data = json.loads(result["stdout"])
                except json.JSONDecodeError:
                    data = []
                for item in data:
                    findings.append(
                        {
                            "tool": self.name,
                            "rule_id": item.get("message-id", ""),
                            "severity": self._map_severity(item.get("type", "W")),
                            "category": item.get("symbol", "general"),
                            "message": item.get("message", ""),
                            "location": {
                                "file": file_path,
                                "line": item.get("line", 0),
                                "column": item.get("column", 0),
                            },
                        }
                    )
            return findings
        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

    def _map_severity(self, msg_type):
        mapping = {
            "E": "critical",
            "F": "critical",
            "W": "major",
            "R": "minor",
            "C": "minor",
            "I": "info",
        }
        return mapping.get(msg_type, "minor")


class BanditAdapter(BaseAnalyzer):
    name = "bandit"
    supported_languages = ["Python"]

    def is_available(self):
        result = self._run_tool(["bandit", "--version"])
        return result["success"]

    def analyze(self, file_path, content, language):
        if language not in self.supported_languages:
            return []

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, encoding="utf-8"
        ) as f:
            f.write(content)
            tmp_path = f.name

        try:
            result = self._run_tool(
                ["bandit", "-f", "json", "-q", tmp_path]
            )

            findings = []
            if result["success"]:
                try:
                    data = json.loads(result["stdout"])
                except json.JSONDecodeError:
                    data = {"results": []}
                for item in data.get("results", []):
                    findings.append(
                        {
                            "tool": self.name,
                            "rule_id": item.get("test_id", ""),
                            "severity": self._map_severity(item.get("issue_severity", "low")),
                            "category": "security",
                            "message": item.get("issue_text", ""),
                            "location": {
                                "file": file_path,
                                "line": item.get("line_number", 0),
                                "column": item.get("col_offset", 0),
                            },
                        }
                    )
            return findings
        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

    def _map_severity(self, bandit_severity):
        mapping = {
            "HIGH": "critical",
            "MEDIUM": "major",
            "LOW": "minor",
        }
        return mapping.get(bandit_severity, "minor")


class PMDAdapter(BaseAnalyzer):
    name = "pmd"
    supported_languages = ["Java"]

    def is_available(self):
        result = self._run_tool(["pmd", "--version"])
        return result["success"]

    def analyze(self, file_path, content, language):
        if language not in self.supported_languages:
            return []

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".java", delete=False, encoding="utf-8"
        ) as f:
            f.write(content)
            tmp_path = f.name

        try:
            result = self._run_tool(
                [
                    "pmd",
                    "check",
                    "-f",
                    "json",
                    "-R",
                    "rulesets/java/quickstart.xml",
                    "-d",
                    tmp_path,
                ],
                timeout=300,
            )

            findings = []
            if result["success"] or result["stdout"]:
                try:
                    data = json.loads(result["stdout"])
                except json.JSONDecodeError:
                    data = {"files": []}
                for file_data in data.get("files", []):
                    for violation in file_data.get("violations", []):
                        findings.append(
                            {
                                "tool": self.name,
                                "rule_id": violation.get("rule", ""),
                                "severity": self._map_severity(
                                    violation.get("priority", 3)
                                ),
                                "category": violation.get("ruleset", "general"),
                                "message": violation.get("description", ""),
                                "location": {
                                    "file": file_path,
                                    "line": violation.get("beginline", 0),
                                    "column": violation.get("begincolumn", 0),
                                },
                            }
                        )
            return findings
        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

    def _map_severity(self, priority):
        mapping = {1: "critical", 2: "major", 3: "minor", 4: "info", 5: "info"}
        return mapping.get(priority, "minor")


class ESLintAdapter(BaseAnalyzer):
    name = "eslint"
    supported_languages = ["JavaScript"]

    def is_available(self):
        result = self._run_tool(["eslint", "--version"])
        return result["success"]

    def analyze(self, file_path, content, language):
        if language not in self.supported_languages:
            return []

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".js", delete=False, encoding="utf-8"
        ) as f:
            f.write(content)
            tmp_path = f.name

        try:
            result = self._run_tool(
                ["eslint", "--format=json", tmp_path], timeout=300
            )

            findings = []
            if result["success"] or result["stdout"]:
                try:
                    data = json.loads(result["stdout"])
                except json.JSONDecodeError:
                    data = []
                for file_data in data:
                    for msg in file_data.get("messages", []):
                        findings.append(
                            {
                                "tool": self.name,
                                "rule_id": msg.get("ruleId", ""),
                                "severity": self._map_severity(msg.get("severity", 1)),
                                "category": "code_style",
                                "message": msg.get("message", ""),
                                "location": {
                                    "file": file_path,
                                    "line": msg.get("line", 0),
                                    "column": msg.get("column", 0),
                                },
                            }
                        )
            return findings
        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

    def _map_severity(self, eslint_severity):
        mapping = {2: "critical", 1: "major", 0: "info"}
        return mapping.get(eslint_severity, "minor")


def get_all_adapters():
    return [
        CppCheckAdapter(),
        PylintAdapter(),
        BanditAdapter(),
        PMDAdapter(),
        ESLintAdapter(),
    ]


def get_adapters_for_language(language):
    all_adapters = get_all_adapters()
    return [a for a in all_adapters if language in a.supported_languages]
