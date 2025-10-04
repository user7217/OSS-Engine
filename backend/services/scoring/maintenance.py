from datetime import datetime, timezone
import dateutil.parser
import math
from services.scoring.database import get_cached_score, save_score

def decay_score(value, max_value, min_score=0, max_score=10):
    # Linear interpolation capped within score range
    if value >= max_value:
        return max_score
    elif value <= 0:
        return min_score
    return min_score + (max_score - min_score) * (value / max_value)

def calculate_commit_activity(pushed_at, commit_count_last_90_days, total_commit_count):
    if not pushed_at:
        return 0
    pushed_dt = dateutil.parser.isoparse(pushed_at)
    now = datetime.now(timezone.utc)
    hours_diff = (now - pushed_dt).total_seconds() / 3600

    recency_val = max(0, 2160 - hours_diff)
    recency_score = decay_score(recency_val, 2160, min_score=0)

    freq_score = decay_score(min(commit_count_last_90_days, 100), 100, min_score=0)


    # Normalize total commits capped at 2000 commits
    volume_score = decay_score(min(total_commit_count, 2000), 2000, min_score=0)


    # Updated weighted blend: 50% recency, 30% recent commits, 20% total commits
    return round(0.5 * recency_score + 0.3 * freq_score + 0.2 * volume_score, 2)


def calculate_pr_merge_rate(total_prs, merged_prs, avg_merge_time_days=5):
    if total_prs == 0:
        return 0  # Strong penalty for no PR activity
    base_rate = merged_prs / total_prs
    rate_score = decay_score(base_rate, 1.0, min_score=0)

    # Penalize merges slower than 7 days
    if avg_merge_time_days > 7:
        time_penalty = max(0, 1 - 0.1 * (avg_merge_time_days - 7))
    else:
        time_penalty = 1

    final_score = rate_score * time_penalty * 10
    return round(max(0, min(final_score, 10)), 2)

def calculate_issue_resolution_rate(total_issues, closed_issues, avg_close_time_days=10):
    if total_issues == 0:
        return 0  # Strong penalty for no issue activity
    base_rate = closed_issues / total_issues
    rate_score = decay_score(base_rate, 1.0, min_score=0)

    # Penalize issues closed slower than 14 days
    if avg_close_time_days > 14:
        time_penalty = max(0, 1 - 0.05 * (avg_close_time_days - 14))
    else:
        time_penalty = 1

    final_score = rate_score * time_penalty * 10
    return round(max(0, min(final_score, 10)), 2)

def calculate_ci_presence(ci_found=True, coverage_percent=80):
    if not ci_found:
        return 0
    if coverage_percent >= 80:
        return 10
    elif coverage_percent >= 50:
        return 7
    else:
        return 5

def calculate_category_1_score(data, owner=None, repo=None):
    if owner and repo:
        cached = get_cached_score(owner, repo)
        if cached and "maintenance_score" in cached:
            return cached["maintenance_score"]
    commit_activity = calculate_commit_activity(
        data.get("pushedAt"),
        data.get("commitCountLast90Days", 0),
        data.get("totalCommitCount", 0)
    )
    pr_merge_rate = calculate_pr_merge_rate(
        data.get("pullRequests", {}).get("totalCount", 0),
        data.get("pullRequests", {}).get("merged", 0),
        data.get("pullRequests", {}).get("avgMergeTimeDays", 5)
    )
    issue_resolution_rate = calculate_issue_resolution_rate(
        data.get("issues", {}).get("totalCount", 0),
        data.get("issues", {}).get("closed", 0),
        data.get("issues", {}).get("avgCloseTimeDays", 10)
    )
    ci_presence = calculate_ci_presence(
        data.get("ciPresent", True),
        data.get("testCoveragePercent", 80)
    )
    print(commit_activity, pr_merge_rate, issue_resolution_rate, ci_presence)
    score = (
        0.75 * commit_activity +
        0.15 * pr_merge_rate +
        0.05 * issue_resolution_rate +
        0.05 * ci_presence
    )
    if owner and repo:
        cached = get_cached_score(owner, repo)
        cached["maintenance_score"] = round(score, 2)
        save_score(owner, repo, cached)

    return round(score, 2)
