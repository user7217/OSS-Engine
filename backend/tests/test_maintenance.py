from services.scoring.maintenance import (
    calculate_commit_activity,
    calculate_pr_merge_rate,
    calculate_issue_resolution_rate,
    calculate_category_1_score
)

def test_commit_activity():
    # Recent commit returns max score
    assert calculate_commit_activity("2025-09-01T00:00:00Z") == 10
    # Old commit returns low score
    assert calculate_commit_activity("2024-01-01T00:00:00Z") == 1

def test_pr_merge_rate():
    assert calculate_pr_merge_rate(10, 9) == 10
    assert calculate_pr_merge_rate(10, 7) == 7
    assert calculate_pr_merge_rate(10, 3) == 4
    assert calculate_pr_merge_rate(0, 0) == 0

def test_issue_resolution_rate():
    assert calculate_issue_resolution_rate(10, 9) == 10
    assert calculate_issue_resolution_rate(10, 7) == 7
    assert calculate_issue_resolution_rate(10, 3) == 4
    assert calculate_issue_resolution_rate(0, 0) == 0

def test_category_1_score():
    data = {
      "pushedAt": "2025-09-01T00:00:00Z",
      "pullRequests": {"totalCount": 10, "merged": 9},
      "issues": {"totalCount": 10, "closed": 9}
    }
    score = calculate_category_1_score(data)
    # Weighted sum approx 10
    assert score > 9
