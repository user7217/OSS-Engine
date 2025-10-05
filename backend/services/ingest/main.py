from typing import Dict, Any
from services.scoring.database import get_cached_score, save_score
from services.ingest.repo_fetcher import fetch_repo_data, fetch_code_snippets
from services.ingest.ecosyste_client import get_aggregated_code_quality_score
from services.scoring.maintenance import calculate_category_1_score
from services.scoring.community import calculate_category_3_score
from services.scoring.documentation import get_documentation_score


def process_repo(owner: str, repo_name: str) -> Dict[str, Any]:
    print(f"Processing repository {owner}/{repo_name}...")

    # Check cache first
    cached = get_cached_score(owner, repo_name)
    if cached:
        print(f"  Cache hit for {owner}/{repo_name}. Returning cached scores.")
        return cached

    # Cache miss - full fetch and scoring
    repo_data = fetch_repo_data(owner, repo_name)
    if not repo_data:
        raise ValueError(f"Repository {owner}/{repo_name} not found or inaccessible.")

    print(f"  Fetched repo data: keys = {list(repo_data.keys())}")

    snippets = fetch_code_snippets(owner, repo_name)
    print(f"  Fetched {len(snippets)} code snippets")

    try:
        maintenance_score = calculate_category_1_score(repo_data)
    except Exception as e:
        maintenance_score = 0
        print(f"Error calculating maintenance score: {e}")

    try:
        code_quality_score = get_aggregated_code_quality_score(snippets)
    except Exception as e:
        code_quality_score = 0
        print(f"Error calculating code quality score: {e}")

    try:
        community_score = calculate_category_3_score(owner, repo_name)
    except Exception as e:
        community_score = 0
        print(f"Error calculating community score: {e}")

    try:
        documentation_score = get_documentation_score(owner, repo_name)
    except Exception as e:
        documentation_score = 0
        print(f"Error calculating documentation score: {e}")

    combined_score = round(
        0.4 * maintenance_score +
        0.25 * code_quality_score +
        0.25 * community_score +
        0.10 * documentation_score,
        2
    )
    print(f"  Combined score: {combined_score}")

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
    print(f"  Saved scores for {owner}/{repo_name} in cache.")
    return result
