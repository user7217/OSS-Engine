from services.ingest.repo_fetcher import fetch_repo_data, fetch_code_snippets
from services.ingest.ecosyste_client import get_aggregated_code_quality_score
from services.scoring.maintenance import calculate_category_1_score
from services.scoring.community import calculate_category_3_score
from services.scoring.documentation import get_documentation_score

def process_repo(owner: str, repo_name: str):
    repo_data = fetch_repo_data(owner, repo_name)
    if not repo_data:
        raise ValueError(f"Repository {owner}/{repo_name} not found or inaccessible.")

    maintenance_score = calculate_category_1_score(repo_data)
    snippets = fetch_code_snippets(owner, repo_name)
    code_quality_score = get_aggregated_code_quality_score(snippets)
    community_score = calculate_category_3_score(owner, repo_name)
    documentation_score = get_documentation_score(owner, repo_name)

    combined_score = round(
        0.4 * maintenance_score +
        0.25 * code_quality_score +
        0.25 * community_score +
        0.10 * documentation_score,
        2
    )

    highlights = []
    special_mentions = []
    threshold_high = 8.0
    threshold_low = 5.0

    scores_dict = {
        "Maintenance": maintenance_score,
        "Code Quality": code_quality_score,
        "Community": community_score,
        "Documentation": documentation_score,
    }

    for cat, score in scores_dict.items():
        if score >= threshold_high:
            highlights.append(cat)
        elif score < threshold_low:
            special_mentions.append(f"Weak in {cat}")

    return {
        "owner": owner,
        "repo": repo_name,
        "maintenance_score": maintenance_score,
        "code_quality_score": code_quality_score,
        "community_engagement_score": community_score,
        "documentation_score": documentation_score,
        "combined_score": combined_score,
        "top_highlights": highlights,
        "special_mentions": special_mentions,
        "num_snippets": len(snippets),
    }

# CLI entry point
if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("Usage: python main.py <owner> <repo>")
        exit(1)
    owner = sys.argv[1]
    repo_name = sys.argv[2]

    result = process_repo(owner, repo_name)
    print(result)
