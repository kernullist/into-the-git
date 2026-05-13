import hashlib
from collections import defaultdict


def detect_duplicates(files_dict, min_lines=6):
    file_hashes = {}
    line_hashes = defaultdict(list)

    for file_path, content in files_dict.items():
        lines = content.split("\n")
        file_hash = hashlib.sha256(content.encode("utf-8", errors="replace")).hexdigest()
        if file_hash in file_hashes:
            continue
        file_hashes[file_hash] = file_path

        for i in range(len(lines) - min_lines + 1):
            block = "\n".join(lines[i : i + min_lines])
            block_hash = hashlib.sha256(block.encode("utf-8", errors="replace")).hexdigest()
            line_hashes[block_hash].append(
                {"file": file_path, "start_line": i + 1, "end_line": i + min_lines}
            )

    duplicates = []
    seen_pairs = set()
    for block_hash, occurrences in line_hashes.items():
        if len(occurrences) < 2:
            continue
        for i in range(len(occurrences)):
            for j in range(i + 1, len(occurrences)):
                pair_key = (
                    occurrences[i]["file"],
                    occurrences[i]["start_line"],
                    occurrences[j]["file"],
                    occurrences[j]["start_line"],
                )
                if pair_key in seen_pairs:
                    continue
                seen_pairs.add(pair_key)
                duplicates.append(
                    {
                        "file_a": occurrences[i]["file"],
                        "file_b": occurrences[j]["file"],
                        "line_a": occurrences[i]["start_line"],
                        "line_b": occurrences[j]["start_line"],
                        "lines": min_lines,
                    }
                )
    return duplicates
