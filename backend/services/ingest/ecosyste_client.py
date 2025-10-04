import os
from google import genai
import re
from services.scoring.database import get_cached_score, save_score

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY environment variable is not set")

client = genai.Client(api_key=GEMINI_API_KEY)

def parse_score_from_text(text):
    match = re.search(r"(\d+(\.\d+)?)", text)
    if match:
        return float(match.group(1))
    return None

def get_aggregated_code_quality_score(snippets, owner=None, repo_name=None):
    """
    Calculates aggregated code quality score using Gemini AI on code snippets.
    If owner and repo_name provided, caches results by repo key.
    """
    if owner and repo_name:
        cached = get_cached_score(owner, repo_name)
        if cached and "code_quality_score" in cached:
            return cached["code_quality_score"]

    if not snippets:
        return 0

    combined_content = "\n\n".join([f"// File: {s['file_path']}\n{s['content']}" for s in snippets])

    standard_prompt = (
        "You are a software quality expert. Assess the overall code quality "
        "based on the following combined code snippets from the main files of a repository. "
        "Evaluate readability, structure, correctness, maintainability, and best practices.\n"
        "Provide a normalized score from 0 (poor) to 10 (excellent). Reply with only the numeric score."
    )

    input_text = f"{standard_prompt}\n\n{combined_content}"

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=input_text
    )

    score = parse_score_from_text(response.text)
    score = score if score is not None else 0

    if owner and repo_name:
        cached = cached or {}
        cached["code_quality_score"] = score
        save_score(owner, repo_name, cached)

    return score
