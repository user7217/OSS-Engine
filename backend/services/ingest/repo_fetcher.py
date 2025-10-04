from .github_graphql_client import run_graphql_query
from datetime import datetime, timedelta

REPO_SNAPSHOT_QUERY = """
query RepoSnapshot($owner: String!, $name: String!, $since: GitTimestamp!) {
  repository(owner: $owner, name: $name) {
    nameWithOwner
    stargazerCount
    pushedAt
    defaultBranchRef {
      target {
        ... on Commit {
          history(since: $since) {
            totalCount
          }
        }
      }
    }
    pullRequestsTotal: pullRequests(states: [OPEN, MERGED, CLOSED]) {
      totalCount
    }
    pullRequestsMerged: pullRequests(states: MERGED) {
      totalCount
    }
    issuesTotal: issues(states: [OPEN, CLOSED]) {
      totalCount
    }
    issuesClosed: issues(states: CLOSED) {
      totalCount
    }
  }
}
"""

def fetch_repo_data(owner, repo_name):
    since_date = (datetime.utcnow() - timedelta(days=90)).isoformat() + "Z"  # last 90 days
    variables = {
        "owner": owner,
        "name": repo_name,
        "since": since_date,
    }
    data = run_graphql_query(REPO_SNAPSHOT_QUERY, variables)
    repo = data.get("repository", None)
    if repo:
        commit_count_last_90_days = repo.get("defaultBranchRef", {}) \
                                       .get("target", {}) \
                                       .get("history", {}) \
                                       .get("totalCount", 0)
        repo["commitCountLast90Days"] = commit_count_last_90_days
    print(repo)
    return repo
