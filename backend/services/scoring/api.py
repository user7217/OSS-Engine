from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from services.scoring.database import get_cached_score, save_score
from services.ingest.repo_fetcher import (
    fetch_repo_data,
    fetch_code_snippets,
)
from services.ingest.ecosyste_client import get_aggregated_code_quality_score
from services.scoring.maintenance import calculate_category_1_score
from services.scoring.community import calculate_category_3_score
from services.scoring.documentation import get_documentation_score
from services.scoring.enhanced_scoring import batch_score_repositories
from services.ingest.repo_searcher import search_repos


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # your frontend URL here, or ["*"] to allow all origins
    allow_credentials=True,
    allow_methods=["*"],   # allow all HTTP methods (GET, POST, OPTIONS, etc.)
    allow_headers=["*"],   # allow all headers
)


class RepoRequest(BaseModel):
    owner: str
    repo_name: str


@app.post("/score")
def score_repo(req: RepoRequest):
    print(f"Received /score request for repo {req.owner}/{req.repo_name}", flush=True)
    # First check cache
    cached = get_cached_score(req.owner, req.repo_name)
    if cached:
        print(f"Cache hit for {req.owner}/{req.repo_name}, returning cached data.", flush=True)
        return cached

    # Perform full scoring if cache miss
    repo_data = fetch_repo_data(req.owner, req.repo_name)
    if not repo_data:
        print(f"Repository {req.owner}/{req.repo_name} not found or access denied", flush=True)
        raise HTTPException(status_code=404, detail="Repository not found or access denied")
    print(f"Fetched repo data keys: {list(repo_data.keys())}", flush=True)

    snippets = fetch_code_snippets(req.owner, req.repo_name)
    print(f"Fetched {len(snippets)} snippets", flush=True)

    maintenance_score = calculate_category_1_score(repo_data)
    code_quality_score = get_aggregated_code_quality_score(snippets)
    community_score = calculate_category_3_score(req.owner, req.repo_name)
    documentation_score = get_documentation_score(req.owner, req.repo_name)

    combined_score = round(
        0.4 * maintenance_score +
        0.25 * code_quality_score +
        0.25 * community_score +
        0.10 * documentation_score,
        2
    )
    print(f"Computed combined score: {combined_score}", flush=True)

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
        "repo": f"{req.owner}/{req.repo_name}",
        "score_category_1": maintenance_score,
        "code_quality_score": code_quality_score,
        "community_engagement_score": community_score,
        "documentation_score": documentation_score,
        "combined_score": combined_score,
        "top_highlights": highlights,
        "special_mentions": special_mentions,
        "num_snippets": len(snippets),
    }

    save_score(req.owner, req.repo_name, result)
    print(f"Saved scored data for {req.owner}/{req.repo_name} in cache", flush=True)
    return result


class FilterCriteria(BaseModel):
    keywords: Optional[str] = None
    language: Optional[str] = None
    min_good_first_issues: Optional[int] = 0
    max_good_first_issues: Optional[int] = 1000
    topics: Optional[List[str]] = []
    recent_commit_days: Optional[int] = 90


@app.post("/search_and_score")
def search_and_score(filters: FilterCriteria):
    print("Received /search_and_score request with filters:", filters.dict(), flush=True)
    try:
        repos = search_repos(
            keywords=filters.keywords,
            language=filters.language,
            min_good_first_issues=filters.min_good_first_issues or 0,
            max_good_first_issues=filters.max_good_first_issues or 1000,
            topics=filters.topics or [],
            recent_commit_days=filters.recent_commit_days or 90,
            max_repos=150,
        )
        print(f"Found {len(repos)} repos matching filters", flush=True)
    except Exception as e:
        print("Search repos error:", e, flush=True)
        raise HTTPException(status_code=500, detail=f"Error searching repositories: {e}")

    if not repos:
        print("No repos found matching search criteria", flush=True)
        return []

    try:
        scored_repos = batch_score_repositories(repos)
        print(f"Scored {len(scored_repos)} repositories successfully", flush=True)
    except Exception as e:
        print("Batch scoring error:", e, flush=True)
        raise HTTPException(status_code=500, detail=f"Error scoring repositories: {e}")

    return scored_repos
