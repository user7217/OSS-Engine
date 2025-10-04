import requests
from datetime import datetime
import os

GITHUB_API_URL = "https://api.github.com"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
HEADERS = {"Authorization": f"Bearer {GITHUB_TOKEN}"}

def parse_country_from_location(location_str):
    if not location_str:
        return None
    parts = location_str.split(",")
    country = parts[-1].strip().lower()
    return country

def calculate_contributor_diversity_score_from_list(contributors):
    if not contributors:
        return 0

    now = datetime.utcnow()
    new_contributors_count = 0
    countries = set()

    for profile in contributors:
        created_at_str = profile.get("created_at")
        if not created_at_str:
            continue
        created_at = datetime.strptime(created_at_str, "%Y-%m-%dT%H:%M:%SZ")
        account_age_days = (now - created_at).days
        if account_age_days <= 365:
            new_contributors_count += 1

        location = profile.get("location", "")
        country = parse_country_from_location(location)
        if country:
            countries.add(country)

    total = len(contributors) if len(contributors) > 0 else 1
    new_ratio = new_contributors_count / total
    country_diversity_score = min(len(countries) / 10, 1.0)
    print(f"New Contributors: {new_contributors_count}, Total: {total}, Countries: {len(countries)}")

    score = 0.4 * new_ratio + 0.6 * country_diversity_score
    return round(score * 10, 2)

def calculate_pr_review_quality(owner, repo):
    # TODO: Implement realistic PR review metrics using GitHub API, e.g.:
    # - Average number of review comments per PR
    # - Average review latency (time taken to review)
    # For now, a dummy fixed score is returned.
    return 7.5

def calculate_issue_responsiveness(owner, repo):
    # TODO: Implement issue responsiveness metrics using GitHub API, e.g.:
    # - Average first response time to issues
    # - Number of comments on issues
    # For now, a dummy fixed score is returned.
    return 8.0

def calculate_category_3_score(owner, repo, contributors=None):
    if contributors is None:
        # Fetch contributors if not provided
        from services.ingest.repo_fetcher import fetch_contributors_with_locations
        contributors = fetch_contributors_with_locations(owner, repo)
    
    contributor_score = calculate_contributor_diversity_score_from_list(contributors)
    pr_score = calculate_pr_review_quality(owner, repo)
    issue_score = calculate_issue_responsiveness(owner, repo)

    score = 0.5 * contributor_score + 0.25 * pr_score + 0.25 * issue_score
    return round(score, 2)
