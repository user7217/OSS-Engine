import os
import requests
from datetime import datetime, timedelta
from typing import List, Optional, Dict

GITHUB_API_URL = "https://api.github.com"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
HEADERS = {"Authorization": f"Bearer {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}

def build_github_search_query(keywords: Optional[str], language: Optional[str], topics: Optional[List[str]],
                              min_good_first_issues: int, max_good_first_issues: int, recent_commit_days: int) -> str:
    query_parts = []

    if keywords:
        query_parts.append(f'{keywords} in:name,description')

    if language:
        query_parts.append(f'language:{language}')

    if topics:
        for topic in topics:
            query_parts.append(f'topic:{topic}')

    date_threshold = (datetime.utcnow() - timedelta(days=recent_commit_days)).date().isoformat()
    query_parts.append(f'pushed:>={date_threshold}')

    return " ".join(query_parts)

def search_repos(keywords: Optional[str] = None,
                 language: Optional[str] = None,
                 min_good_first_issues: int = 0,
                 max_good_first_issues: int = 1000,
                 topics: Optional[List[str]] = None,
                 recent_commit_days: int = 90,
                 max_repos: int = 150) -> List[Dict]:
    repos = []
    page = 1
    per_page = 50
    query = build_github_search_query(keywords, language, topics, min_good_first_issues, max_good_first_issues, recent_commit_days)

    while len(repos) < max_repos:
        url = f"{GITHUB_API_URL}/search/repositories"
        params = {
            "q": query,
            "sort": "stars",
            "order": "desc",
            "per_page": per_page,
            "page": page
        }
        response = requests.get(url, headers=HEADERS, params=params, timeout=15)
        if response.status_code != 200:
            print(f"GitHub search API error: {response.status_code} {response.text}")
            break

        data = response.json()
        items = data.get("items", [])
        if not items:
            break

        for repo in items:
            owner = repo["owner"]["login"]
            repo_name = repo["name"]
            good_first_issues_count = fetch_good_first_issues_count(owner, repo_name)
            if min_good_first_issues <= good_first_issues_count <= max_good_first_issues:
                repo_meta = {
                    "full_name": repo["full_name"],
                    "owner": owner,
                    "name": repo_name,
                    "stargazers_count": repo.get("stargazers_count", 0),
                    "open_issues_count": repo.get("open_issues_count", 0),
                    "pushed_at": repo.get("pushed_at"),
                    "topics": fetch_repo_topics(owner, repo_name),
                    "good_first_issues_count": good_first_issues_count,
                }
                repos.append(repo_meta)
                if len(repos) >= max_repos:
                    break

        page += 1

    return repos

def fetch_good_first_issues_count(owner: str, repo: str) -> int:
    url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/issues"
    params = {"state": "open", "labels": "good first issue", "per_page": 1}
    response = requests.get(url, headers=HEADERS, params=params, timeout=15)
    if response.status_code != 200:
        print(f"Failed to fetch good first issues for {owner}/{repo}: {response.status_code}")
        return 0
    issues = response.json()
    return len(issues)

def fetch_repo_topics(owner: str, repo: str) -> List[str]:
    url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/topics"
    headers = dict(HEADERS)
    headers["Accept"] = "application/vnd.github.mercy-preview+json"
    response = requests.get(url, headers=headers, timeout=15)
    if response.status_code != 200:
        print(f"Failed to fetch topics for {owner}/{repo}: {response.status_code}")
        return []
    data = response.json()
    return data.get("names", [])
