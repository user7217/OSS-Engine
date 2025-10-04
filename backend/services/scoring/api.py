from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from services.ingest.repo_fetcher import fetch_repo_data
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
    score = calculate_category_1_score(repo_data)
    return {"repo": f"{req.owner}/{req.repo_name}", "score_category_1": score}
