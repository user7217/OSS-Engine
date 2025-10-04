from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from services.ingest.repo_fetcher import fetch_repo_data, fetch_code_snippets
from services.ingest.ecosyste_client import get_aggregated_code_quality_score
from services.scoring.maintenance import calculate_category_1_score

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

    # Combine scores with weights
    combined_score = round(0.7 * maintenance_score + 0.3 * code_quality_score, 2)

    return {
        "repo": f"{req.owner}/{req.repo_name}",
        "score_category_1": maintenance_score,
        "code_quality_score": code_quality_score,
        "combined_score": combined_score,
        "num_snippets": len(snippets),
    }
