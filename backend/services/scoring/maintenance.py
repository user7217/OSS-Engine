def calculate_commit_activity(pushed_at):
    from datetime import datetime, timezone
    import dateutil.parser
    if not pushed_at:
        return 0.0
    pushed_dt = dateutil.parser.isoparse(pushed_at)
    days_diff = (datetime.now(timezone.utc) - pushed_dt).days
    if days_diff < 30:
        return 10
    elif days_diff < 90:
        return 7
    elif days_diff < 180:
        return 4
    return 1

def calculate_pr_merge_rate(total_prs, merged_prs):
    if total_prs == 0:
        return 0.0
    rate = merged_prs / total_prs
    if rate >= 0.9:
        return 10
    elif rate >= 0.7:
        return 7
    elif rate >= 0.4:
        return 4
    return 1

def calculate_issue_resolution_rate(total_issues, closed_issues):
    if total_issues == 0:
        return 0.0
    rate = closed_issues / total_issues
    if rate >= 0.9:
        return 10
    elif rate >= 0.7:
        return 7
    elif rate >= 0.4:
        return 4
    return 1

def calculate_ci_presence(presence=True):
    return 10 if presence else 0

def calculate_category_1_score(data):
    commit_activity = calculate_commit_activity(data.get("pushedAt"))
    pr_merge_rate = calculate_pr_merge_rate(
        data.get("pullRequests", {}).get("totalCount", 0),
        data.get("pullRequests", {}).get("merged", 0)
    )
    issue_resolution_rate = calculate_issue_resolution_rate(
        data.get("issues", {}).get("totalCount", 0),
        data.get("issues", {}).get("closed", 0)
    )
    # For now, we do not have CI presence info, so assume True for testing
    ci_presence = calculate_ci_presence(True)

    score = (
        0.4 * commit_activity +
        0.3 * pr_merge_rate +
        0.2 * issue_resolution_rate +
        0.1 * ci_presence
    )

    return round(score, 2)
