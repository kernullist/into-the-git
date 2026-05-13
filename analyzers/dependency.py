from collections import defaultdict
from .ast_engine import extract_imports


def analyze_dependencies(files_dict, language):
    import_map = {}
    for file_path, content in files_dict.items():
        imports = extract_imports(content, language)
        import_map[file_path] = imports

    internal_deps = defaultdict(list)
    external_deps = defaultdict(list)
    depended_by = defaultdict(list)

    all_paths = set(files_dict.keys())
    for file_path, imports in import_map.items():
        for imp in imports:
            import_parts = imp.replace(".", "/").replace("\\", "/")
            found = False
            for fpath in all_paths:
                fpath_normalized = fpath.replace("\\", "/")
                if import_parts in fpath_normalized or fpath_normalized.endswith(
                    import_parts + "." + _get_ext(fpath_normalized)
                ):
                    internal_deps[file_path].append(fpath)
                    depended_by[fpath].append(file_path)
                    found = True
            if not found:
                external_deps[file_path].append(imp)

    result = {
        "internal_deps": dict(internal_deps),
        "external_deps": dict(external_deps),
        "depended_by": dict(depended_by),
        "dep_count": {f: len(internal_deps.get(f, [])) for f in all_paths},
        "fan_in": {f: len(depended_by.get(f, [])) for f in all_paths},
        "fan_out": {f: len(internal_deps.get(f, [])) for f in all_paths},
    }
    return result


def _get_ext(filepath):
    parts = filepath.rsplit(".", 1)
    return parts[1] if len(parts) > 1 else ""
