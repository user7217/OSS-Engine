from .github_graphql_client import run_graphql_query

REPO_SNAPSHOT_QUERY = """
query RepoSnapshot($owner: String!, $name: String!) {
  repository(owner: $owner, name: $name) {
    nameWithOwner
    stargazerCount
    pushedAt
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
    variables = {"owner": owner, "name": repo_name}
    data = run_graphql_query(REPO_SNAPSHOT_QUERY, variables)
    return data.get("repository", None)
