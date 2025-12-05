import os
import json
import re
from google import genai
from services.scoring.database import get_cached_score, save_score

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY environment variable is not set")

client = genai.Client(api_key=GEMINI_API_KEY)


def parse_score_from_text(text):
    """Extract a numeric score from text."""
    numbers = re.findall(r"\b\d+(?:\.\d+)?\b", text)
    return float(numbers[-1]) if numbers else None


def get_aggregated_code_quality_score(snippets, structure_summary=None, owner=None, repo_name=None):
    """
    Analyze code and folder structure using Gemini.
    Returns weighted score: 0.8*code + 0.2*structure.
    """

    # --- Safety check ---
    if not snippets or not isinstance(snippets, list) or not all(isinstance(s, dict) for s in snippets):
        print("Invalid snippets format:", snippets)
        return 0

    # --- Cache check ---
    if owner and repo_name:
        cached = get_cached_score(owner, repo_name)
        if cached and "code_quality_score" in cached:
            return cached["code_quality_score"]
    else:
        cached = {}

    # --- Combine code snippets ---
    combined_content = "\n\n".join([
        f"// File: {s['file_path']}\n{s['content']}"
        for s in snippets
    ])
    if len(combined_content) > 15000:
        combined_content = combined_content[:15000]

    # --- Build Gemini prompt ---
    prompt = f"""
You are a senior software quality auditor.

1. Rate **code quality** (clarity, maintainability, efficiency) out of 10.
2. Rate **folder structure** (organization, logical grouping, separation of concerns) out of 10.
3. Provide short reasoning for both.
4. Compute **final score** = 0.8*code + 0.2*folder structure.
5. Respond strictly in JSON:
{{
  "code_quality": <number>,
  "folder_structure": <number>,
  "final_score": <number>,
  "reasoning": "<short explanation>"
}}

Folder structure summary:
{structure_summary or "(No structure provided)"}

Code snippets:
{combined_content}
"""

    # --- Query Gemini ---
    final_score = 0
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        if hasattr(response, "text") and response.text:
            try:
                result = json.loads(response.text)
                final_score = float(result.get("final_score", 0))
                print("Gemini JSON:", result)
            except json.JSONDecodeError:
                print("Gemini response not JSON. Raw text:", response.text)
                final_score = parse_score_from_text(response.text) or 0
        else:
            print("Gemini returned empty response")
    except Exception as e:
        print(f"Error querying Gemini model: {e}")
        final_score = 0

    # --- Cache ---
    if owner and repo_name:
        cached["code_quality_score"] = final_score
        save_score(owner, repo_name, cached)

    return final_score
