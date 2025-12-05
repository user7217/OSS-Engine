# ==============================================================================
# 1. SETUP & CONFIGURATION
# ==============================================================================
import os  # Access environment variables
import requests  # Make HTTP requests
from datetime import datetime, timedelta  # Handle date and time
import base64  # Decode base64 content
import re  # Use regular expressions
from services.ingest.github_graphql_client import run_graphql_query  # Custom GraphQL client
from concurrent.futures import ThreadPoolExecutor, as_completed  # Run tasks concurrently

# --- Globals & Constants ---
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")  # Get GitHub token from environment
if not GITHUB_TOKEN:  # Check if token exists
    raise RuntimeError("GITHUB_TOKEN environment variable is not set")  # Error if token is missing

HEADERS = {"Authorization": f"Bearer {GITHUB_TOKEN}"}  # Set auth headers for requests
GITHUB_API_URL = "https://api.github.com"  # Base URL for GitHub REST API

# --- GraphQL Queries ---
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

# ==============================================================================
# 2. GITHUB API FETCHING FUNCTIONS
# ==============================================================================

def fetch_repo_data(owner, repo_name):
    """Fetch repo metadata via GraphQL with REST fallback"""
    from datetime import timezone, datetime, timedelta  # Local imports for date/time
    import requests  # Local import for fallback

    since_date = (datetime.now(timezone.utc) - timedelta(days=90)).isoformat().replace("+00:00", "Z")  # Calculate date 90 days ago
    variables = {"owner": owner, "name": repo_name, "since": since_date}  # Set variables for GraphQL query
    data = run_graphql_query(REPO_SNAPSHOT_QUERY, variables)  # Execute GraphQL query
    repo = data.get("repository", None)  # Extract repo data from response
    if not repo:  # Handle case where repo is not found
        print(f"Repository {owner}/{repo_name} not found in GraphQL response", flush=True)
        return None  # Exit if no repo data

    pushed_at = repo.get("pushedAt")  # Get last push timestamp

    dbr = repo.get("defaultBranchRef") or {}  # Safely get default branch reference
    tgt = dbr.get("target") or {}  # Safely get target commit

    total_commit_count = tgt.get("totalCommits", {}).get("totalCount", 0)  # Get total commit count
    commit_count_last_90_days = tgt.get("recentCommits", {}).get("totalCount", 0)  # Get recent commit count

    # Fallback to REST API if pushedAt is missing from GraphQL
    if not pushed_at:
        try:
            rest = requests.get(f"{GITHUB_API_URL}/repos/{owner}/{repo_name}", headers=HEADERS, timeout=15)  # Make REST API call
            if rest.ok:  # Check for successful response
                pushed_at = rest.json().get("pushed_at") or ""  # Extract pushed_at from JSON
                print(f"[REST fallback] pushed_at for {owner}/{repo_name}: {pushed_at}", flush=True)
            else:
                print(f"[REST fallback] Failed for {owner}/{repo_name} with status {rest.status_code}", flush=True)  # Log REST API failure
        except Exception as e:
            print(f"[REST fallback] Error fetching pushed_at for {owner}/{repo_name}: {e}", flush=True)  # Log any exceptions

    scored_repo = {
        "owner": owner,
        "name": repo_name,
        "full_name": f"{owner}/{repo_name}",
        "pushedAt": pushed_at,
        "commitCountLast90Days": commit_count_last_90_days,
        "totalCommitCount": total_commit_count,
    }

    print(scored_repo, flush=True)  # Print the final repo data
    print("-----", flush=True)  # Print a separator
    return scored_repo  # Return the collected repo data

def analyze_repo_structure(owner: str, repo_name: str, max_depth=2, max_items=300):
    """Fetch a limited snapshot of the repo structure safely."""
    base_url = f"https://api.github.com/repos/{owner}/{repo_name}/contents"
    structure = []
    total_requests = 0

    def walk(path="", depth=0):
        nonlocal total_requests
        if depth > max_depth or len(structure) >= max_items:
            return
        if total_requests > 50:  # hard safety cap
            print("Reached max API requests limit")
            return

        try:
            resp = requests.get(
                f"{base_url}/{path}" if path else base_url,
                headers=HEADERS,
                params={"per_page": 100},
                timeout=8,
            )
        except requests.exceptions.Timeout:
            print(f"Timeout fetching {path}")
            return

        total_requests += 1
        if resp.status_code != 200:
            print(f"Failed to fetch {path}: {resp.status_code}")
            return

        for item in resp.json():
            if len(structure) >= max_items:
                return
            structure.append({"type": item["type"], "path": item["path"]})
            if item["type"] == "dir":
                walk(item["path"], depth + 1)

    walk()
    print(f"Fetched {len(structure)} items from repo structure.")
    return structure
 # Return the complete list of files and directories

def fetch_code_snippets(owner: str, repo_name: str, max_files=5, max_lines=80):
    """Fetch code snippets from the most important files in a repo"""
    valid_exts = (".py", ".js", ".java", ".kt", ".cpp", ".c", ".ts", ".go", ".rb")  # Allowed file extensions
    skip_files = {"main.py", "app.py", "index.js", "server.js", "__init__.py"}  # Common entry-point files to skip

    structure = analyze_repo_structure(owner, repo_name)  # Get the repository file structure
    if not structure: return [], ""  # Return empty if structure analysis fails

    # Rank files by importance using a scoring system
    ranked_files = []
    for item in structure:  # Iterate over all files/dirs
        if item["type"] != "file": continue  # Skip directories
        path = item["path"]
        name = os.path.basename(path)  # Get the filename
        if not name.endswith(valid_exts) or name in skip_files: continue  # Skip invalid or explicitly skipped files
        score = 0  # Initialize score
        if any(x in path for x in ["/src", "/core", "/lib", "/services", "/models", "/controllers"]): score += 3  # Higher score for core directories
        if any(x in path for x in ["/tests", "/venv", "/migrations", "/node_modules", "/build", "/dist"]): score -= 3  # Lower score for non-source directories
        if name in skip_files: score -= 5  # Heavily penalize skipped filenames
        ranked_files.append((score, path))  # Add scored file to the list

    ranked_files.sort(reverse=True, key=lambda x: x[0])  # Sort files by score descending
    selected_files = [p for _, p in ranked_files[:max_files]]  # Select top N files

    snippets = []  # Initialize list for code snippets
    for path in selected_files:  # Loop through selected files
        file_url = f"https://api.github.com/repos/{owner}/{repo_name}/contents/{path}"  # API URL for file content
        file_resp = requests.get(file_url, headers=HEADERS)  # Fetch file content
        if file_resp.status_code != 200: continue  # Skip if fetch fails
        data = file_resp.json()  # Parse JSON response
        encoded = data.get("content", "")  # Get base64 encoded content
        try:
            decoded = base64.b64decode(encoded).decode("utf-8", errors="ignore")  # Decode content
        except:
            continue  # Skip if decoding fails
        lines = decoded.splitlines()[:max_lines]  # Get the first N lines of the file
        snippets.append({"file_path": path, "content": "\n".join(lines), "defs": count_defs(decoded)})  # Add snippet to list

    structure_summary = summarize_structure(structure)  # Generate a summary of the repo structure
    return snippets, structure_summary  # Return snippets and summary

def fetch_readme(owner, repo_name, max_chars=10000, keywords=None):
    """Fetch and decode the README, optionally filtering by keywords"""
    url = f"{GITHUB_API_URL}/repos/{owner}/{repo_name}/readme"  # README API endpoint
    response = requests.get(url, headers=HEADERS)  # Fetch README data
    if response.status_code != 200:  # Handle failed request
        print(f"Failed to fetch README: {response.text}")
        return None
    data = response.json()  # Parse JSON response
    content = data.get("content", "")  # Get base64 content
    encoding = data.get("encoding", "base64")  # Get content encoding
    if encoding == "base64":
        decoded = base64.b64decode(content).decode("utf-8", errors="ignore")  # Decode if base64
    else:
        decoded = content  # Use content directly if not encoded

    lines = decoded.splitlines()  # Split content into lines

    if keywords:
        # Filter lines that contain any of the specified keywords
        filtered_lines = [line for line in lines if any(kw in line.lower() for kw in keywords)]
        snippet = "\n".join(filtered_lines)  # Join filtered lines back into a string
    else:
        snippet = decoded  # Use the full decoded content if no keywords

    if len(snippet) > max_chars:
        snippet = snippet[:max_chars]  # Truncate snippet if it exceeds max length

    return snippet  # Return the final README snippet

def fetch_contributors_with_locations(owner, repo, top_n=10):
    """Fetch total contributors and detailed info for the top N"""
    contributors_url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/contributors?per_page=100"  # API URL for contributors
    all_contributors = []  # List to store all contributors
    page = 1  # Start at page 1 for pagination

    # Paginate through all contributors
    while True:
        resp = requests.get(f"{contributors_url}&page={page}", headers=HEADERS)  # Fetch a page of contributors
        resp.raise_for_status()  # Raise an error for bad responses
        batch = resp.json()  # Parse JSON
        if not batch: break  # Exit loop if no more contributors
        all_contributors.extend(batch)  # Add batch to the list
        page += 1  # Go to the next page

    total_contributors = len(all_contributors)  # Get total count
    top_contributors = all_contributors[:top_n]  # Select top N contributors

    detailed_contributors = []  # List for detailed info
    for contributor in top_contributors:  # Loop through top contributors
        username = contributor.get("login")  # Get username
        user_url = f"{GITHUB_API_URL}/users/{username}"  # API URL for user details
        user_resp = requests.get(user_url, headers=HEADERS)  # Fetch user data
        user_resp.raise_for_status()  # Check for errors
        user_data = user_resp.json()  # Parse user data
        detailed_contributors.append({  # Append detailed info to the list
            "login": username,
            "contributions": contributor.get("contributions"),
            "location": user_data.get("location"),
            "created_at": user_data.get("created_at")
        })

    return {"total_contributors": total_contributors, "top_contributors": detailed_contributors}  # Return final data

def fetch_pull_requests(owner, repo, state="all", per_page=100, max_items=100):
    """Fetch pull requests from a repository, with pagination"""
    prs = []  # Initialize list for pull requests
    page = 1  # Start pagination at page 1
    while len(prs) < max_items:  # Loop until max items are fetched
        url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/pulls"  # PRs API endpoint
        params = {"state": state, "per_page": min(per_page, max_items - len(prs)), "page": page}  # Set request parameters
        resp = requests.get(url, headers=HEADERS, params=params)  # Fetch a page of PRs
        if resp.status_code != 200:  # Handle failed request
            print(f"Failed to fetch pull requests: {resp.status_code}, {resp.text}")
            break
        data = resp.json()  # Parse JSON response
        if not data: break  # Exit if page is empty
        prs.extend(data)  # Add fetched PRs to the list
        if len(data) < params["per_page"]: break  # Exit if it's the last page
        page += 1  # Go to next page

    return prs[:max_items]  # Return PRs, ensuring not to exceed max_items

def fetch_pr_reviews(owner, repo, pr_number, per_page=100, max_items=100):
    """Fetch reviews for a specific pull request, with pagination"""
    reviews = []  # Initialize list for reviews
    page = 1  # Start pagination at page 1
    while len(reviews) < max_items:  # Loop until max items are fetched
        url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/pulls/{pr_number}/reviews"  # PR reviews API endpoint
        params = {"per_page": min(per_page, max_items - len(reviews)), "page": page}  # Set request parameters
        resp = requests.get(url, headers=HEADERS, params=params)  # Fetch a page of reviews
        if resp.status_code != 200:  # Handle failed request
            print(f"Failed to fetch PR reviews: {resp.status_code}, {resp.text}")
            break
        data = resp.json()  # Parse JSON response
        if not data: break  # Exit if page is empty
        reviews.extend(data)  # Add fetched reviews to the list
        if len(data) < params["per_page"]: break  # Exit if it's the last page
        page += 1  # Go to next page

    return reviews[:max_items]  # Return reviews, capped at max_items

def fetch_issues(owner, repo, state="all", per_page=100, max_items=100):
    """Fetch issues from a repository, with pagination"""
    issues = []  # Initialize list for issues
    page = 1  # Start pagination at page 1
    while len(issues) < max_items:  # Loop until max items are fetched
        url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/issues"  # Issues API endpoint
        params = {"state": state, "per_page": min(per_page, max_items - len(issues)), "page": page}  # Set request parameters
        resp = requests.get(url, headers=HEADERS, params=params)  # Fetch a page of issues
        if resp.status_code != 200:  # Handle failed request
            print(f"Failed to fetch issues: {resp.status_code} - {resp.text}")
            break
        data = resp.json()  # Parse JSON response
        if not data: break  # Exit if page is empty
        issues.extend(data)  # Add fetched issues to the list
        if len(data) < params["per_page"]: break  # Exit if it's the last page
        page += 1  # Go to next page
    print(f"Fetched {len(issues)} issues for {owner}/{repo}", flush=True)  # Log number of fetched issues

    return issues[:max_items]  # Return issues, capped at max_items

def fetch_issue_comments(owner, repo, issue_number, per_page=100, max_items=100):
    """Fetch issue comments concurrently using a thread pool"""
    comments = []  # Initialize list for comments
    max_per_page = 100  # Max items per page allowed by API
    total_pages = (max_items + max_per_page - 1) // max_per_page  # Calculate total pages to fetch

    def fetch_page(page):  # Helper function to fetch a single page of comments
        url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/issues/{issue_number}/comments"  # Comments API endpoint
        params = {"per_page": per_page, "page": page}  # Set request parameters
        resp = requests.get(url, headers=HEADERS, params=params)  # Fetch page
        if resp.status_code == 200:  # Check for success
            return resp.json()  # Return JSON data
        else:
            print(f"Failed to fetch page {page}: {resp.status_code} - {resp.text}", flush=True)  # Log failures
            return []  # Return empty list on failure

    with ThreadPoolExecutor(max_workers=5) as executor:  # Create a thread pool
        futures = [executor.submit(fetch_page, page) for page in range(1, total_pages+1)]  # Submit all page fetches
        for future in as_completed(futures):  # Process futures as they complete
            data = future.result()  # Get result from future
            if data:
                comments.extend(data)  # Add fetched comments to the list
            if len(comments) >= max_items:  # Stop if max items reached
                break

    comments = comments[:max_items]  # Ensure list does not exceed max_items
    print(f"Fetched {len(comments)} comments for issue #{issue_number} in {owner}/{repo}", flush=True)  # Log total comments fetched
    return comments[:max_items]  # Return the final list of comments

# ==============================================================================
# 3. DATA PROCESSING & UTILITY FUNCTIONS
# ==============================================================================

def count_defs(code: str) -> int:
    """Count function/class definitions in a code string"""
    return code.count("def ") + code.count("class ") + code.count("function ")  # Sum counts of definition keywords

def summarize_structure(structure, max_items=50):
    """Score and summarize the repo structure to find important files/dirs"""
    important_dirs = {"src", "core", "lib", "models", "services", "controllers", "utils"}  # Keywords for important directories
    skip_dirs = {"test", "tests", "venv", "node_modules", "dist", "build", "migrations"}  # Keywords for directories to ignore

    def score_path(path):  # Helper function to calculate a score for a given path
        path_lower = path.lower()  # Convert path to lowercase for case-insensitive matching
        score = 0  # Initialize score
        if any(d in path_lower for d in important_dirs): score += 3  # Increase score for important dirs
        if any(word in path_lower for word in ("api", "engine", "backend", "production")): score += 2  # Increase score for other key terms
        if any(d in path_lower for d in skip_dirs): score -= 5  # Decrease score for unimportant dirs
        if path_lower.endswith((".py", ".js", ".ts", ".java")): score += 1  # Slightly increase score for code files
        return score  # Return the calculated score

    # Score each item in the structure and sort by score in descending order
    scored = sorted([(item["path"], item["type"], score_path(item["path"])) for item in structure], key=lambda x: x[2], reverse=True)

    dirs = [f"{p} (score={s})" for p, t, s in scored if t == "dir"][:max_items]  # Get top N directories
    files = [f"{p} (score={s})" for p, t, s in scored if t == "file"][:max_items]  # Get top N files

    # Format the summary string
    return ("Top Directories:\n" + "\n".join(dirs) + "\n\nTop Files:\n" + "\n".join(files))

def extract_links_from_text(text):
    """Find all URLs in a given string using regex"""
    url_pattern = re.compile(r'(https?://[^\s]+)')  # Regex pattern for URLs
    return url_pattern.findall(text)  # Return all found URLs

def fetch_page_title_and_description(url):
    """Scrape a URL to extract its title and meta description"""
    try:
        resp = requests.get(url, timeout=5)  # Fetch page content with a timeout
        resp.raise_for_status()  # Check for HTTP errors
        content = resp.text  # Get page HTML

        # Extract the <title> tag content
        title_match = re.search(r'<title>(.*?)</title>', content, re.IGNORECASE | re.DOTALL)
        title = title_match.group(1).strip() if title_match else ""  # Get title or empty string

        # Extract the meta description content
        description_match = re.search(r'<meta\s+name=["\']description["\']\s+content=["\'](.*?)["\']', content, re.IGNORECASE | re.DOTALL)
        description = description_match.group(1).strip() if description_match else ""  # Get description or empty string

        return {"title": title, "description": description}  # Return extracted metadata
    except Exception as e:
        print(f"Error fetching page metadata for {url}: {e}")  # Log any errors
        return {"title": "", "description": ""}  # Return empty on failure