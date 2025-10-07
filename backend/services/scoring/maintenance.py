from datetime import datetime, timezone
import dateutil.parser
from services.scoring.database import get_cached_score, save_score


def decay_score(value, max_value, min_score=0, max_score=10):
    if value >= max_value:
        return max_score
    elif value <= 0:
        return min_score
    return min_score + (max_score - min_score) * (value / max_value)


def _normalize_maintenance_inputs(data):
    # Normalize pushed_at field (accept both naming styles)
    pushed_at = data.get("pushed_at") or data.get("pushedAt") or ""

    # Parse commit data safely
    try:
        commit90 = int(data.get("commitCountLast90Days", 0))
    except Exception:
        commit90 = 0

    try:
        total_commits = int(data.get("totalCommitCount", 0))
    except Exception:
        total_commits = 0

    # Ensure pullRequests and issues are dicts, not ints
    pull_requests = data.get("pullRequests", {})
    if isinstance(pull_requests, int):
        pull_requests = {"totalCount": pull_requests}

    issues = data.get("issues", {})
    if isinstance(issues, int):
        issues = {"totalCount": issues}

    normalized = {
        "pushed_at": pushed_at,
        "commitCountLast90Days": commit90,
        "totalCommitCount": total_commits,
        "pullRequests": pull_requests,
        "issues": issues,
        "ciPresent": data.get("ciPresent", True),
        "testCoveragePercent": data.get("testCoveragePercent", 80),
    }

    print(f"[normalize] pushed_at={normalized['pushed_at']}, last90={commit90}, total={total_commits}")
    return normalized


def calculate_commit_activity(pushed_at, commit_count_last_90_days, total_commit_count):
    print("Calculating commit activity...")

    if not pushed_at:
        print("  Error: 'pushed_at' timestamp is missing or empty.")
        return 0

    try:
        pushed_dt = dateutil.parser.isoparse(pushed_at)
        if pushed_dt.tzinfo is None:
            pushed_dt = pushed_dt.replace(tzinfo=timezone.utc)
        print(f"  Parsed pushed_at datetime: {pushed_dt.isoformat()}")
    except Exception as e:
        print(f"  Error parsing 'pushed_at': {e}")
        return 0

    now = datetime.now(timezone.utc)
    hours_diff = (now - pushed_dt).total_seconds() / 3600
    print(f"  Hours difference between now and pushed_at: {hours_diff}")

    # Convert commits safely
    try:
        commit_count_last_90_days = int(commit_count_last_90_days)
    except (TypeError, ValueError):
        commit_count_last_90_days = 0

    try:
        total_commit_count = int(total_commit_count)
    except (TypeError, ValueError):
        total_commit_count = 0

    recency_val = max(0, 2160 - hours_diff)  # 90 days * 24 hours
    recency_score = decay_score(recency_val, 2160)
    freq_score = decay_score(min(commit_count_last_90_days, 100), 100)
    volume_score = decay_score(min(total_commit_count, 2000), 2000)

    final_score = round(0.5 * recency_score + 0.3 * freq_score + 0.2 * volume_score, 2)
    print(f"  Final commit activity score: {final_score}")
    return final_score


def calculate_pr_merge_rate(total_prs, merged_prs, avg_merge_time_days=5):
    if total_prs == 0:
        return 0
    base_rate = merged_prs / total_prs
    rate_score = decay_score(base_rate, 1.0)
    time_penalty = max(0, 1 - 0.1 * (avg_merge_time_days - 7)) if avg_merge_time_days > 7 else 1
    return round(max(0, min(rate_score * time_penalty * 10, 10)), 2)


def calculate_issue_resolution_rate(total_issues, closed_issues, avg_close_time_days=10):
    if total_issues == 0:
        return 0
    base_rate = closed_issues / total_issues
    rate_score = decay_score(base_rate, 1.0)
    time_penalty = max(0, 1 - 0.05 * (avg_close_time_days - 14)) if avg_close_time_days > 14 else 1
    return round(max(0, min(rate_score * time_penalty * 10, 10)), 2)


def calculate_ci_presence(ci_found=True, coverage_percent=80):
    if not ci_found:
        return 0
    if coverage_percent >= 80:
        return 10
    elif coverage_percent >= 50:
        return 7
    return 5


def calculate_category_1_score(data, owner=None, repo=None):
    norm = _normalize_maintenance_inputs(data)
    print(f"calculate_category_1_score inputs: pushed_at={norm.get('pushed_at')}, "
          f"commitCountLast90Days={norm.get('commitCountLast90Days')}, "
          f"totalCommitCount={norm.get('totalCommitCount')}")

    # Check cache
    if owner and repo:
        cached = get_cached_score(owner, repo)
        if cached and "maintenance_score" in cached:
            print(f"Using cached maintenance score for {owner}/{repo}: {cached['maintenance_score']}")
            return cached["maintenance_score"]

    # Compute subscores
    commit_activity = calculate_commit_activity(
        norm.get("pushed_at"),
        norm.get("commitCountLast90Days"),
        norm.get("totalCommitCount")
    )

    pr_merge_rate = calculate_pr_merge_rate(
        norm["pullRequests"].get("totalCount", 0),
        norm["pullRequests"].get("merged", 0),
        norm["pullRequests"].get("avgMergeTimeDays", 5)
    )

    issue_resolution_rate = calculate_issue_resolution_rate(
        norm["issues"].get("totalCount", 0),
        norm["issues"].get("closed", 0),
        norm["issues"].get("avgCloseTimeDays", 10)
    )

    ci_presence = calculate_ci_presence(
        norm.get("ciPresent", True),
        norm.get("testCoveragePercent", 80)
    )

    print(f"Scores → Commit: {commit_activity}, PRs: {pr_merge_rate}, Issues: {issue_resolution_rate}, CI: {ci_presence}")

    # Weighted final score
    score = (
        0.75 * commit_activity +
        0.15 * pr_merge_rate +
        0.05 * issue_resolution_rate +
        0.05 * ci_presence
    )

    final = round(score, 2)

    # Save cache
    if owner and repo:
        cached = get_cached_score(owner, repo) or {}
        cached["maintenance_score"] = final
        save_score(owner, repo, cached)
        print(f"Saved maintenance score for {owner}/{repo}: {final}")

    return final