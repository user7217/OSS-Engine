from services.ingest.repo_fetcher import fetch_repo_data, fetch_code_snippets
from services.ingest.ecosyste_client import get_aggregated_code_quality_score
from services.scoring.maintenance import calculate_category_1_score
from services.scoring.community import calculate_category_3_score

def process_repo(owner: str, repo_name: str):
    """
    Fetches repo data, extracts code snippets, assesses maintenance, code quality, and community engagement,
    then returns a combined weighted score along with individual metrics.
    """
    # Fetch repository metadata once
    repo_data = fetch_repo_data(owner, repo_name)
    if not repo_data:
        raise ValueError(f"Repository {owner}/{repo_name} not found or inaccessible.")

    # Compute maintenance score (Category 1)
    maintenance_score = calculate_category_1_score(repo_data)

    # Fetch snippets from main source files (comments + code context)
    snippets = fetch_code_snippets(owner, repo_name)

    # Get overall code quality score from Gemini (Category 2)
    code_quality_score = get_aggregated_code_quality_score(snippets)

    # Compute community engagement score (Category 3)
    category_3_score = calculate_category_3_score(owner, repo_name)

    # Weighted combination of all categories for final scoring
    combined_score = round(
        0.5 * maintenance_score +
        0.2 * code_quality_score +
        0.3 * category_3_score,
        2
    )

    return {
        "owner": owner,
        "repo": repo_name,
        "maintenance_score": maintenance_score,
        "code_quality_score": code_quality_score,
        "community_engagement_score": category_3_score,
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
