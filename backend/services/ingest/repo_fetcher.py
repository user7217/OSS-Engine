import os
import requests
from datetime import datetime, timedelta
import base64
import re
from services.ingest.github_graphql_client import run_graphql_query

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
if not GITHUB_TOKEN:
    raise RuntimeError("GITHUB_TOKEN environment variable is not set")

HEADERS = {"Authorization": f"Bearer {GITHUB_TOKEN}"}

GITHUB_API_URL = "https://api.github.com"

REPO_SNAPSHOT_QUERY = """
query RepoSnapshot($owner: String!, $name: String!, $since: GitTimestamp!) {
  repository(owner: $owner, name: $name) {
    name
    owner { login }
    pushedAt
    defaultBranchRef {
      name
      target {
        ... on Commit {
          totalCommits: history {
            totalCount
          }
          recentCommits: history(since: $since) {
            totalCount
          }
        }
      }
    }
  }
}
"""

def fetch_repo_data(owner, repo_name):
    since_date = (datetime.utcnow() - timedelta(days=90)).isoformat() + "Z"
    variables = {"owner": owner, "name": repo_name, "since": since_date}
    data = run_graphql_query(REPO_SNAPSHOT_QUERY, variables)
    repo = data.get("repository", None)
    if not repo:
        print(f"Repository {owner}/{repo_name} not found in GraphQL response.")
        return None

    pushed_at = repo.get("pushedAt") or ""

    dbr = repo.get("defaultBranchRef") or {}
    tgt = dbr.get("target") or {}

    total_commit_count = tgt.get("totalCommits", {}).get("totalCount", 0)
    commit_count_last_90_days = tgt.get("recentCommits", {}).get("totalCount", 0)

    # Fallback to REST if pushedAt missing
    if not pushed_at:
        try:
            rest = requests.get(f"{GITHUB_API_URL}/repos/{owner}/{repo_name}", headers=HEADERS, timeout=15)
            if rest.ok:
                pushed_at = rest.json().get("pushed_at") or ""
                print(f"[REST fallback] pushed_at for {owner}/{repo_name}: {pushed_at}")
            else:
                print(f"[REST fallback] Failed for {owner}/{repo_name} with status {rest.status_code}")
        except Exception as e:
            print(f"[REST fallback] Error fetching pushed_at for {owner}/{repo_name}: {e}")

    scored_repo = {
        "owner": owner,
        "name": repo_name,
        "full_name": f"{owner}/{repo_name}",
        "pushedAt": pushed_at,
        "commitCountLast90Days": commit_count_last_90_days,
        "totalCommitCount": total_commit_count,
    }

    print(f"fetch_repo_data for {owner}/{repo_name}: pushedAt={pushed_at}, last90={commit_count_last_90_days}, total={total_commit_count}")
    return scored_repo



def extract_comments_and_code(lines):
    comments = []
    code_lines = []
    in_multiline_comment = False

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("#") or stripped.startswith("//"):
            comments.append(line)
        elif stripped.startswith("/*") or stripped.startswith('"""') or stripped.startswith("'''"):
            in_multiline_comment = True
            comments.append(line)
        elif in_multiline_comment:
            comments.append(line)
            if "*/" in stripped or '"""' in stripped or "'''" in stripped:
                in_multiline_comment = False
        else:
            code_lines.append(line)

    snippet_text = "\n".join(comments) + "\n\n" + "\n".join(code_lines[:20])
    return snippet_text.strip()

def fetch_code_snippets(owner, repo_name, max_files=3, max_lines=50):
    valid_extensions = (".py", ".js", ".java", ".kt", ".cpp", ".c", ".ts", ".go", ".rb")
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"}
    url = f"https://api.github.com/repos/{owner}/{repo_name}/contents"
    snippets = []

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Failed to fetch root contents: {response.text}")
        return snippets

    files = response.json()
    count = 0
    for file_info in files:
        if count >= max_files:
            break
        if file_info.get("type") != "file":
            continue
        filename = file_info.get("name", "")
        if not filename.endswith(valid_extensions):
            continue

        try:
            file_resp = requests.get(file_info["url"], headers=headers)
            if file_resp.status_code != 200:
                continue
            content_data = file_resp.json()
            encoded_content = content_data.get("content", "")
            decoded_content = base64.b64decode(encoded_content).decode("utf-8", errors="ignore")

            lines = decoded_content.splitlines()[:max_lines]
            snippet_content = extract_comments_and_code(lines)

            snippets.append({"file_path": file_info.get("path"), "content": snippet_content})
            count += 1

        except Exception as e:
            print(f"Error processing file {filename}: {e}")
            continue

    print(f"Collected {len(snippets)} main file snippets for analysis")
    return snippets

def fetch_contributors_with_locations(owner, repo, top_n=10):
    """
    Fetch total contributor count and detailed info for top N contributors.
    """
    contributors_url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/contributors?per_page=100"
    all_contributors = []
    page = 1

    # Paginate to get all contributors
    while True:
        resp = requests.get(f"{contributors_url}&page={page}", headers=HEADERS)
        resp.raise_for_status()
        batch = resp.json()
        if not batch:
            break
        all_contributors.extend(batch)
        page += 1

    total_contributors = len(all_contributors)
    top_contributors = all_contributors[:top_n]

    detailed_contributors = []
    for contributor in top_contributors:
        username = contributor.get("login")
        user_url = f"{GITHUB_API_URL}/users/{username}"
        user_resp = requests.get(user_url, headers=HEADERS)
        user_resp.raise_for_status()
        user_data = user_resp.json()
        detailed_contributors.append({
            "login": username,
            "contributions": contributor.get("contributions"),
            "location": user_data.get("location"),
            "created_at": user_data.get("created_at")
        })

    return {
        "total_contributors": total_contributors,
        "top_contributors": detailed_contributors
    }


def fetch_readme(owner, repo_name, max_chars=10000, keywords=None):
    """
    Fetch README from GitHub, decode content,
    and return a snippet of relevant content filtered by keywords and length limit.
    If keywords is None, return first max_chars characters of README.

    :param owner: repo owner name
    :param repo_name: repo name
    :param max_chars: max chars to return
    :param keywords: list of lowercase keywords to filter lines
    :return: filtered README snippet string
    """
    url = f"{GITHUB_API_URL}/repos/{owner}/{repo_name}/readme"
    response = requests.get(url, headers=HEADERS)
    if response.status_code != 200:
        print(f"Failed to fetch README: {response.text}")
        return None
    data = response.json()
    content = data.get("content", "")
    encoding = data.get("encoding", "base64")
    if encoding == "base64":
        decoded = base64.b64decode(content).decode("utf-8", errors="ignore")
    else:
        decoded = content

    lines = decoded.splitlines()

    if keywords:
        # Filter lines containing any keyword
        filtered_lines = [line for line in lines if any(kw in line.lower() for kw in keywords)]
        snippet = "\n".join(filtered_lines)
    else:
        snippet = decoded

    if len(snippet) > max_chars:
        snippet = snippet[:max_chars]

    return snippet

def extract_links_from_text(text):
    url_pattern = re.compile(r'(https?://[^\s]+)')
    return url_pattern.findall(text)

def fetch_page_title_and_description(url):
    try:
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        content = resp.text

        # Extract <title>
        title_match = re.search(r'<title>(.*?)</title>', content, re.IGNORECASE | re.DOTALL)
        title = title_match.group(1).strip() if title_match else ""

        # Extract <meta name="description" content="...">
        description_match = re.search(r'<meta\s+name=["\']description["\']\s+content=["\'](.*?)["\']', content, re.IGNORECASE | re.DOTALL)
        description = description_match.group(1).strip() if description_match else ""

        return {"title": title, "description": description}
    except Exception as e:
        print(f"Error fetching page metadata for {url}: {e}")
        return {"title": "", "description": ""}
    
def fetch_pull_requests(owner, repo, state="all", per_page=100, max_items=100):
    prs = []
    page = 1
    while len(prs) < max_items:
        url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/pulls"
        params = {"state": state, "per_page": min(per_page, max_items - len(prs)), "page": page}
        resp = requests.get(url, headers=HEADERS, params=params)
        if resp.status_code != 200:
            print(f"Failed to fetch pull requests: {resp.status_code}, {resp.text}")
            break
        data = resp.json()
        if not data:
            break
        prs.extend(data)
        if len(data) < params["per_page"]:
            break
        page += 1

    return prs[:max_items]

def fetch_pr_reviews(owner, repo, pr_number, per_page=100, max_items=100):
    reviews = []
    page = 1
    while len(reviews) < max_items:
        url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/pulls/{pr_number}/reviews"
        params = {"per_page": min(per_page, max_items - len(reviews)), "page": page}
        resp = requests.get(url, headers=HEADERS, params=params)
        if resp.status_code != 200:
            print(f"Failed to fetch PR reviews: {resp.status_code}, {resp.text}")
            break
        data = resp.json()
        if not data:
            break
        reviews.extend(data)
        if len(data) < params["per_page"]:
            break
        page += 1

    return reviews[:max_items]


def fetch_issues(owner, repo, state="all", per_page=100, max_items=100):
    issues = []
    page = 1
    while len(issues) < max_items:
        url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/issues"
        params = {"state": state, "per_page": min(per_page, max_items - len(issues)), "page": page}
        resp = requests.get(url, headers=HEADERS, params=params)
        if resp.status_code != 200:
            print(f"Failed to fetch issues: {resp.status_code} - {resp.text}")
            break
        data = resp.json()
        if not data:
            break
        issues.extend(data)
        if len(data) < params["per_page"]:
            break
        page += 1

    return issues[:max_items]


def fetch_issue_comments(owner, repo, issue_number, per_page=100, max_items=100):
    comments = []
    page = 1
    while len(comments) < max_items:
        url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/issues/{issue_number}/comments"
        params = {"per_page": min(per_page, max_items - len(comments)), "page": page}
        resp = requests.get(url, headers=HEADERS, params=params)
        if resp.status_code != 200:
            print(f"Failed to fetch issue comments: {resp.status_code} - {resp.text}")
            break
        data = resp.json()
        if not data:
            break
        comments.extend(data)
        if len(data) < params["per_page"]:
            break
        page += 1

    return comments[:max_items]
