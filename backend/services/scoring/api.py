from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from services.ingest.repo_fetcher import fetch_repo_data, fetch_code_snippets
from services.ingest.ecosyste_client import get_aggregated_code_quality_score
from services.scoring.maintenance import calculate_category_1_score
from services.scoring.community import calculate_category_3_score

app = FastAPI()

class RepoRequest(BaseModel):
    owner: str
    repo_name: str

@app.post("/score")
async def score_repo(req: RepoRequest):
    repo_data = fetch_repo_data(req.owner, req.repo_name)
    if not repo_data:
        raise HTTPException(status_code=404, detail="Repository not found or access denied")

    # Calculate maintenance score
    maintenance_score = calculate_category_1_score(repo_data)

    # Fetch code snippets (comments + context)
    snippets = fetch_code_snippets(req.owner, req.repo_name)

    # Get single aggregated code quality score from Gemini
    code_quality_score = get_aggregated_code_quality_score(snippets)

    # Calculate community engagement score
    community_score = calculate_category_3_score(req.owner, req.repo_name)

    # Combine scores with updated weights (example: 50% maintenance, 20% code quality, 30% community)
    combined_score = round(
        0.5 * maintenance_score +
        0.2 * code_quality_score +
        0.3 * community_score,
        2
    )

    return {
        "repo": f"{req.owner}/{req.repo_name}",
        "score_category_1": maintenance_score,
        "code_quality_score": code_quality_score,
        "community_engagement_score": community_score,
        "combined_score": combined_score,
        "num_snippets": len(snippets),
    }
