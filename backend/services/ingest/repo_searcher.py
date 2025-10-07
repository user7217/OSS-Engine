import os
import requests
from datetime import datetime, timedelta
from typing import List, Optional, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed

GITHUB_API_URL = "https://api.github.com"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
HEADERS = {"Authorization": f"Bearer {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}

# ---------- Query Builder ----------
def build_github_search_query(
    keywords: Optional[str],
    language: Optional[str],
    topics: Optional[List[str]],
    min_good_first_issues: int,
    max_good_first_issues: int,
    recent_commit_days: int,
) -> str:
    query_parts = []

    if keywords:
        query_parts.append(f'{keywords} in:name,description,readme')

    if language:
        query_parts.append(f'language:{language}')

    if topics:
        for topic in topics:
            query_parts.append(f'topic:{topic}')

    date_threshold = (datetime.utcnow() - timedelta(days=recent_commit_days)).date().isoformat()
    query_parts.append(f'pushed:>={date_threshold}')
    query_parts.append('fork:false archived:false')
    query_parts.append('stars:>10')
    query_parts.append(f'good-first-issues:>={min_good_first_issues}')

    return " ".join(query_parts)


# ---------- Helper functions ----------
def fetch_good_first_issues_count(owner: str, repo: str) -> int:
    url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/issues"
    params = {"state": "open", "labels": "good first issue", "per_page": 1}
    response = requests.get(url, headers=HEADERS, params=params, timeout=10)
    if response.status_code != 200:
        return 0
    issues = response.json()
    return len(issues)


def fetch_repo_topics(owner: str, repo: str) -> List[str]:
    url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/topics"
    headers = dict(HEADERS)
    headers["Accept"] = "application/vnd.github.mercy-preview+json"
    response = requests.get(url, headers=headers, timeout=10)
    if response.status_code != 200:
        return []
    return response.json().get("names", [])


def process_repo(repo, min_good_first_issues, max_good_first_issues):
    try:
        owner = repo["owner"]["login"]
        repo_name = repo["name"]

        good_first_issues_count = fetch_good_first_issues_count(owner, repo_name)
        if not (min_good_first_issues <= good_first_issues_count <= max_good_first_issues):
            return None

        topics = fetch_repo_topics(owner, repo_name)
        return {
            "full_name": repo["full_name"],
            "owner": owner,
            "name": repo_name,
            "stars": repo.get("stargazers_count", 0),
            "issues": repo.get("open_issues_count", 0),
            "last_push": repo.get("pushed_at"),
            "topics": topics,
            "good_first_issues_count": good_first_issues_count,
        }
    except Exception as e:
        print(f"Error processing {repo.get('full_name')}: {e}")
        return None


# ---------- Main search function ----------
def search_repos(
    keywords: Optional[str] = None,
    language: Optional[str] = None,
    min_good_first_issues: int = 0,
    max_good_first_issues: int = 1000,
    topics: Optional[List[str]] = None,
    recent_commit_days: int = 180,
    max_repos: int = 200,
) -> List[Dict]:
    repos = []
    seen = set()
    per_page = 100
    query = build_github_search_query(
        keywords, language, topics, min_good_first_issues, max_good_first_issues, recent_commit_days
    )

    page = 1
    while len(repos) < max_repos:
        url = f"{GITHUB_API_URL}/search/repositories"
        params = {"q": query, "sort": "stars", "order": "desc", "per_page": per_page, "page": page}
        response = requests.get(url, headers=HEADERS, params=params, timeout=20)
        if response.status_code != 200:
            print(f"GitHub API error {response.status_code}: {response.text}")
            break

        items = response.json().get("items", [])
        if not items:
            break

        # Run concurrent repo detail fetching
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [
                executor.submit(process_repo, repo, min_good_first_issues, max_good_first_issues)
                for repo in items
                if repo["full_name"] not in seen
            ]

            for f in as_completed(futures):
                result = f.result()
                if result:
                    full_name = result["full_name"]
                    if full_name not in seen:
                        repos.append(result)
                        seen.add(full_name)
                        if len(repos) >= max_repos:
                            break

        if len(repos) >= max_repos:
            break
        page += 1

    return repos
