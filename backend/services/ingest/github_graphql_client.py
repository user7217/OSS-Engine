import os
import requests

GITHUB_GRAPHQL_URL = "https://api.github.com/graphql"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN") or "ghp_xxx_replace_me"

headers = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/json",
    "User-Agent": "oss-discoverability-ingest"
}

def run_graphql_query(query: str, variables: dict):
    response = requests.post(
        GITHUB_GRAPHQL_URL,
        json={"query": query, "variables": variables},
        headers=headers,
        timeout=30
    )
    response.raise_for_status()
    data = response.json()
    if "errors" in data:
        raise Exception(f"GraphQL errors: {data['errors']}")
    return data["data"]
