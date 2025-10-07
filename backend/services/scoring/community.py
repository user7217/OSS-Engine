import requests
from datetime import datetime
import os
from dateutil import parser
from services.scoring.database import get_cached_score, save_score
from services.ingest.repo_fetcher import (
    fetch_pull_requests,
    fetch_pr_reviews,
    fetch_issues,
    fetch_issue_comments,
    fetch_contributors_with_locations
)

GITHUB_API_URL = "https://api.github.com"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
HEADERS = {"Authorization": f"Bearer {GITHUB_TOKEN}"}


def parse_country_from_location(location_str):
    if not location_str:
        return None
    parts = location_str.split(",")
    country = parts[-1].strip().lower()
    return country


def calculate_contributor_diversity_score_from_list(contributor_data):
    """
    Calculate diversity score using total contributors and top contributor details.
    """
    if not contributor_data or "top_contributors" not in contributor_data:
        print("No contributor data provided")
        return 0

    total_contributors = contributor_data.get("total_contributors", 0)
    contributors = contributor_data.get("top_contributors", [])

    if total_contributors == 0:
        print("No contributors found")
        return 0

    no_contributors_score = min(total_contributors / 50, 1.0)

    from datetime import timezone
    now = datetime.now(timezone.utc)
    new_contributors_count = 0
    countries = set()

    for profile in contributors:
        created_at_str = profile.get("created_at")
        if created_at_str:
            created_at = datetime.strptime(created_at_str, "%Y-%m-%dT%H:%M:%SZ")
            account_age_days = (now - created_at).days
            if account_age_days <= 365:
                new_contributors_count += 1

        location = profile.get("location", "")
        country = parse_country_from_location(location)
        if country:
            countries.add(country)

    total_top = len(contributors) or 1
    new_ratio = new_contributors_count / total_top
    country_diversity_score = min(len(countries) / 10, 1.0)

    print(f"New Contributors: {new_contributors_count}, Total (all): {total_contributors}, Countries: {len(countries)}")

    score = 0.5 * no_contributors_score + 0.3 * new_ratio + 0.2 * country_diversity_score
    return round(score * 10, 2)


def calculate_pr_review_quality(owner, repo):
    prs = fetch_pull_requests(owner, repo)
    if not prs:
        print(f"No PRs found for {owner}/{repo}")
        return 0

    total_review_comments = 0
    total_review_latencies = []
    reviewed_pr_count = 0

    for pr in prs:
        pr_number = pr["number"]
        pr_created = parser.parse(pr["created_at"])

        reviews = fetch_pr_reviews(owner, repo, pr_number)
        if not reviews:
            continue

        reviewed_pr_count += 1
        total_review_comments += len(reviews)

        first_review_time = min(
            parser.parse(review["submitted_at"])
            for review in reviews
            if review.get("submitted_at")
        )
        latency_seconds = (first_review_time - pr_created).total_seconds()
        total_review_latencies.append(latency_seconds)

    if reviewed_pr_count == 0:
        print(f"No reviewed PRs found for {owner}/{repo}")
        return 0

    avg_comments = total_review_comments / reviewed_pr_count
    avg_latency = sum(total_review_latencies) / len(total_review_latencies) if total_review_latencies else 0

    comments_score = min(avg_comments / 20 * 10, 10)
    max_latency_seconds = 7 * 24 * 3600
    latency_score = max(0, 10 - (avg_latency / max_latency_seconds * 10))

    final_score = (comments_score + latency_score) / 2
    return round(final_score, 2)


def calculate_issue_responsiveness(owner, repo):
    issues = fetch_issues(owner, repo)
    if not issues:
        print(f"No issues found for {owner}/{repo}")
        return 0

    response_times = []
    comments_counts = []

    for issue in issues:
        if "pull_request" in issue:
            continue

        issue_number = issue["number"]
        issue_created = parser.parse(issue["created_at"])

        comments = fetch_issue_comments(owner, repo, issue_number)
        if not comments:
            continue

        first_comment_time = min(parser.parse(c["created_at"]) for c in comments if c.get("created_at"))
        response_time = (first_comment_time - issue_created).total_seconds()
        if response_time >= 0:
            response_times.append(response_time)

        comments_counts.append(len(comments))

    if not response_times or not comments_counts:
        print(f"No comments or response times found for {owner}/{repo}")
        return 0

    avg_response_time = sum(response_times) / len(response_times)
    avg_comments = sum(comments_counts) / len(comments_counts)

    max_good_seconds = 7 * 24 * 3600
    max_bad_seconds = 14 * 24 * 3600
    if avg_response_time <= max_good_seconds:
        response_time_score = 10
    elif avg_response_time >= max_bad_seconds:
        response_time_score = 0
    else:
        response_time_score = 10 * (max_bad_seconds - avg_response_time) / (max_bad_seconds - max_good_seconds)

    comments_score = min(avg_comments / 20 * 10, 10)

    final_score = (response_time_score + comments_score) / 2
    return round(final_score, 2)


def calculate_category_3_score(owner, repo, contributors=None):
    if contributors is None:
        contributors = fetch_contributors_with_locations(owner, repo)

    # Updated structure access
    total_contributors = contributors.get("total_contributors", 0)
    top_contributors = contributors.get("top_contributors", [])

    print(f"Contributor count for {owner}/{repo}: {total_contributors}")
    if top_contributors:
        print(f"Sample contributor created_at for {owner}/{repo}: {top_contributors[0].get('created_at')}")
    else:
        print(f"No top contributors found for {owner}/{repo}")

    contributor_score = calculate_contributor_diversity_score_from_list(contributors)
    pr_score = calculate_pr_review_quality(owner, repo)
    issue_score = calculate_issue_responsiveness(owner, repo)

    score = 0.8 * contributor_score + 0.1 * pr_score + 0.1 * issue_score
    print(f"Community score for {owner}/{repo}: {score}")
    return round(score, 2)
