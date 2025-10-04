from services.scoring.database import get_cached_score, save_score
from services.ingest.repo_fetcher import fetch_repo_data, fetch_code_snippets
from services.ingest.ecosyste_client import get_aggregated_code_quality_score
from services.scoring.maintenance import calculate_category_1_score
from services.scoring.community import calculate_category_3_score
from services.scoring.documentation import get_documentation_score

def process_repo(owner: str, repo_name: str):
    # Check cache first
    cached = get_cached_score(owner, repo_name)
    if cached:
        return cached

    # Cache miss - full fetch and scoring
    repo_data = fetch_repo_data(owner, repo_name)
    if not repo_data:
        raise ValueError(f"Repository {owner}/{repo_name} not found or inaccessible.")

    snippets = fetch_code_snippets(owner, repo_name)
    maintenance_score = calculate_category_1_score(repo_data)
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

    result = {
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

    save_score(owner, repo_name, result)
    return result
