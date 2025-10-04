from services.ingest.repo_fetcher import fetch_repo_data, fetch_code_snippets
from services.ingest.ecosyste_client import get_aggregated_code_quality_score
from services.scoring.maintenance import calculate_category_1_score

def process_repo(owner: str, repo_name: str):
    """
    Fetches repo data, extracts code snippets, assesses maintenance and overall code quality,
    and returns a combined score.
    """
    # Fetch repository metadata
    repo_data = fetch_repo_data(owner, repo_name)
    if not repo_data:
        raise ValueError(f"Repository {owner}/{repo_name} not found or inaccessible.")

    # Compute maintenance score
    maintenance_score = calculate_category_1_score(repo_data)

    # Fetch snippets from main files (comments + code context)
    snippets = fetch_code_snippets(owner, repo_name)

    # Get the overall code quality score from Gemini
    code_quality_score = get_aggregated_code_quality_score(snippets)

    # Weighted combination
    combined_score = round(0.7 * maintenance_score + 0.3 * code_quality_score, 2)

    return {
        "owner": owner,
        "repo": repo_name,
        "maintenance_score": maintenance_score,
        "code_quality_score": code_quality_score,
        "combined_score": combined_score,
        "num_snippets": len(snippets),
    }

# CLI entry point for testing
if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("Usage: python main.py <owner> <repo>")
        sys.exit(1)
    owner = sys.argv[1]
    repo_name = sys.argv[2]
    result = process_repo(owner, repo_name)
    print(result)
