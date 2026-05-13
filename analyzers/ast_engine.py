import ast
import os
import re


class ASTEngine:
    LANGUAGE_PARSERS = {}

    def extract_symbols(self, file_path, content, language):
        if language == "Python":
            return self._parse_python(file_path, content)
        elif language == "JavaScript":
            return self._parse_js_ts(file_path, content)
        elif language == "Java":
            return self._parse_java(file_path, content)
        elif language == "C++":
            return self._parse_cpp(file_path, content)
        return []

    def _parse_python(self, file_path, content):
        symbols = []
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    symbols.append(
                        {
                            "kind": "function",
                            "name": node.name,
                            "location": {
                                "file": file_path,
                                "start_line": node.lineno,
                                "end_line": node.end_lineno or node.lineno,
                                "start_col": node.col_offset,
                                "end_col": node.end_col_offset or 0,
                            },
                            "signature": self._get_python_signature(node),
                            "complexity": self._python_cyclomatic(node),
                        }
                    )
                elif isinstance(node, ast.ClassDef):
                    symbols.append(
                        {
                            "kind": "class",
                            "name": node.name,
                            "location": {
                                "file": file_path,
                                "start_line": node.lineno,
                                "end_line": node.end_lineno or node.lineno,
                                "start_col": node.col_offset,
                                "end_col": node.end_col_offset or 0,
                            },
                            "signature": f"class {node.name}",
                            "complexity": 0,
                        }
                    )
        except SyntaxError:
            pass
        return symbols

    def _get_python_signature(self, node):
        args = []
        for arg in node.args.args:
            arg_str = arg.arg
            if arg.annotation:
                arg_str += f": {ast.unparse(arg.annotation)}"
            args.append(arg_str)
        returns = ""
        if node.returns:
            returns = f" -> {ast.unparse(node.returns)}"
        return f"def {node.name}({', '.join(args)}){returns}"

    def _python_cyclomatic(self, node):
        complexity = 1
        for child in ast.walk(node):
            if isinstance(
                child,
                (
                    ast.If,
                    ast.While,
                    ast.For,
                    ast.ExceptHandler,
                    ast.IfExp,
                ),
            ):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        return complexity

    def _parse_js_ts(self, file_path, content):
        symbols = []
        patterns = [
            (
                r"function\s+(\w+)\s*\(([^)]*)\)\s*\{",
                "function",
            ),
            (
                r"(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\(([^)]*)\)\s*=>",
                "function",
            ),
            (
                r"class\s+(\w+)\s*(?:extends\s+\w+)?\s*\{",
                "class",
            ),
            (
                r"(?:async\s+)?(\w+)\s*\(([^)]*)\)\s*\{",
                "method",
            ),
        ]
        for pattern, kind in patterns:
            for match in re.finditer(pattern, content, re.MULTILINE):
                name = match.group(1)
                if kind == "method" and name in (
                    "if",
                    "for",
                    "while",
                    "switch",
                    "catch",
                    "try",
                    "function",
                    "class",
                    "return",
                    "const",
                    "let",
                    "var",
                ):
                    continue
                line = content[: match.start()].count("\n") + 1
                symbols.append(
                    {
                        "kind": kind,
                        "name": name,
                        "location": {
                            "file": file_path,
                            "start_line": line,
                            "end_line": line,
                            "start_col": 0,
                            "end_col": 0,
                        },
                        "signature": f"{kind} {name}({match.group(2) if match.lastindex >= 2 else ''})",
                        "complexity": self._generic_cyclomatic(content, match.start()),
                    }
                )
        unique = {}
        for s in symbols:
            key = f"{s['kind']}|{s['name']}|{s['location']['start_line']}"
            if key not in unique:
                unique[key] = s
        return list(unique.values())

    def _parse_java(self, file_path, content):
        symbols = []
        patterns = [
            (
                r"(?:public|private|protected|static|\s)+[\w<>\[\],\s]+\s+(\w+)\s*\(([^)]*)\)\s*(?:throws\s+[\w\s,]+)?\s*\{",
                "method",
            ),
            (
                r"(?:public|private|protected|\s)+class\s+(\w+)\s*(?:extends\s+\w+)?(?:\s+implements\s+[\w\s,]+)?\s*\{",
                "class",
            ),
        ]
        for pattern, kind in patterns:
            for match in re.finditer(pattern, content, re.MULTILINE):
                name = match.group(1)
                line = content[: match.start()].count("\n") + 1
                symbols.append(
                    {
                        "kind": kind,
                        "name": name,
                        "location": {
                            "file": file_path,
                            "start_line": line,
                            "end_line": line,
                            "start_col": 0,
                            "end_col": 0,
                        },
                        "signature": f"{kind} {name}",
                        "complexity": self._generic_cyclomatic(content, match.start()),
                    }
                )
        return symbols

    def _parse_cpp(self, file_path, content):
        symbols = []
        patterns = [
            (
                r"(?:virtual\s+)?(?:static\s+)?(?:inline\s+)?(?:const\s+)?[\w:*&<>,\s]+\s+(\w+)\s*\(([^)]*)\)\s*(?:const\s*)?(?:override\s*)?(?:noexcept\s*)?\{",
                "function",
            ),
            (
                r"class\s+(\w+)\s*(?::\s*(?:public|private|protected)\s+\w+)?\s*\{",
                "class",
            ),
        ]
        for pattern, kind in patterns:
            for match in re.finditer(pattern, content, re.MULTILINE):
                name = match.group(1)
                if name in (
                    "if",
                    "for",
                    "while",
                    "switch",
                    "catch",
                    "try",
                    "return",
                    "sizeof",
                ):
                    continue
                line = content[: match.start()].count("\n") + 1
                symbols.append(
                    {
                        "kind": kind,
                        "name": name,
                        "location": {
                            "file": file_path,
                            "start_line": line,
                            "end_line": line,
                            "start_col": 0,
                            "end_col": 0,
                        },
                        "signature": f"{kind} {name}",
                        "complexity": self._generic_cyclomatic(content, match.start()),
                    }
                )
        return symbols

    def _generic_cyclomatic(self, content, start_pos):
        complexity = 1
        keywords = [
            r"\bif\b",
            r"\belse\s+if\b",
            r"\bwhile\b",
            r"\bfor\b",
            r"\bcase\b",
            r"\bcatch\b",
            r"\&\&",
            r"\|\|",
            r"\?\s*[^:]+\s*:",
        ]
        for kw in keywords:
            complexity += len(re.findall(kw, content[start_pos:]))
        return complexity


def extract_imports(content, language):
    imports = []
    if language == "Python":
        patterns = [
            r"^import\s+([\w.]+)",
            r"^from\s+([\w.]+)\s+import",
        ]
        for pattern in patterns:
            for match in re.finditer(pattern, content, re.MULTILINE):
                imports.append(match.group(1))
    elif language == "JavaScript":
        patterns = [
            r"(?:import\s+.*?\s+from\s+['\"])([^'\"]+)",
            r"require\s*\(\s*['\"]([^'\"]+)['\"]",
            r"import\s+['\"]([^'\"]+)['\"]",
        ]
        for pattern in patterns:
            for match in re.finditer(pattern, content, re.MULTILINE):
                imports.append(match.group(1))
    elif language == "Java":
        pattern = r"^import\s+([\w.]+)"
        for match in re.finditer(pattern, content, re.MULTILINE):
            imports.append(match.group(1))
    elif language == "C++":
        pattern = r'#include\s+[<"]([^>"]+)[>"]'
        for match in re.finditer(pattern, content, re.MULTILINE):
            imports.append(match.group(1))
    return list(set(imports))
