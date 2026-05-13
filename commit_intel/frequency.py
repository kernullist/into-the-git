from collections import Counter, defaultdict
from datetime import datetime


def compute_change_frequency(commits, files_of_interest=None):
    file_freq = Counter()
    file_commits = defaultdict(list)
    author_freq = Counter()

    for commit in commits:
        author = commit.get("author", "unknown")
        for f in commit.get("files", []):
            file_freq[f] += 1
            file_commits[f].append(
                {
                    "sha": commit.get("sha", ""),
                    "author": author,
                    "date": commit.get("date", ""),
                    "message": commit.get("message", ""),
                }
            )
            author_freq[author] += 1

    most_changed = file_freq.most_common(50)
    hot_files = [{"file": f, "changes": c} for f, c in most_changed]

    result = {
        "total_commits": len(commits),
        "total_files_changed": len(file_freq),
        "most_changed_files": hot_files,
        "file_frequency": dict(file_freq.most_common(100)),
        "author_frequency": dict(author_freq.most_common(20)),
        "file_commit_details": {
            f: details for f, details in file_commits.items() if f in dict(most_changed)
        },
    }

    recent_commits = [
        c for c in commits if (datetime.now() - _parse_date(c.get("date", ""))).days <= 30
    ]
    recent_freq = Counter()
    for c in recent_commits:
        for f in c.get("files", []):
            recent_freq[f] += 1

    result["recent_frequency"] = dict(recent_freq.most_common(50))
    result["recent_commits_count"] = len(recent_commits)

    return result


def _parse_date(date_str):
    try:
        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return datetime.min
