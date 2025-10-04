import base64
import os
import re
from google import genai
from services.ingest.repo_fetcher import fetch_readme, extract_links_from_text, fetch_page_title_and_description
from services.scoring.database import get_cached_score, save_score


GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    import os
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY environment variable is not set")

client = genai.Client(api_key=GEMINI_API_KEY)

def parse_score_from_text(text):
    match = re.search(r"(\d+(\.\d+)?)", text)
    if match:
        return float(match.group(1))
    return None

def send_prompt_to_gemini(prompt):
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    return parse_score_from_text(response.text)



def get_documentation_score(owner, repo_name):
    """
    Comprehensive documentation score as weighted sum of:
    - Readme clarity (40%)
    - Examples/tutorials (30%)
    - Setup instructions (20%)
    - License & contribution guidelines (10%)
    Each scored separately by Gemini using focused prompts on filtered README snippets.
    """

    # Check for cached score first
    cached = get_cached_score(owner, repo_name)
    if cached and "documentation_score" in cached:
        return cached["documentation_score"]

    readme_content = fetch_readme(owner, repo_name)
    if not readme_content:
        return 0

    lines = [line.strip() for line in readme_content.splitlines() if line.strip()]

    def extract_section_by_keywords(keywords):
        snippet_lines = [line for line in lines if any(kw in line.lower() for kw in keywords)]
        if snippet_lines:
            return "\n".join(snippet_lines[:50])
        return "\n".join(lines[:50])

    clarity_keywords = ["description", "overview", "summary", "introduction", "purpose"]
    examples_keywords = ["example", "tutorial", "sample", "quick start", "demo"]
    setup_keywords = ["install", "setup", "configure", "prerequisite", "requirements"]
    license_contrib_keywords = ["license", "contributing", "contribution", "cla", "code of conduct"]

    prompt_template = (
        "You are an expert technical writer. Evaluate the following README snippet "
        "for {criterion_description}. Respond with a numeric score from 0 (poor) to 10 (excellent).\n\n"
    )

    clarity_snippet = extract_section_by_keywords(clarity_keywords)
    examples_snippet = extract_section_by_keywords(examples_keywords)
    setup_snippet = extract_section_by_keywords(setup_keywords)
    license_contrib_snippet = extract_section_by_keywords(license_contrib_keywords)

    clarity_score = send_prompt_to_gemini(prompt_template.format(criterion_description="clarity and understandability") + clarity_snippet)
    examples_score = send_prompt_to_gemini(prompt_template.format(criterion_description="examples and tutorials") + examples_snippet)
    setup_score = send_prompt_to_gemini(prompt_template.format(criterion_description="setup and installation instructions") + setup_snippet)
    license_contrib_score = send_prompt_to_gemini(prompt_template.format(criterion_description="license and contribution guidelines") + license_contrib_snippet)
    print(clarity_score, examples_score, setup_score, license_contrib_score)
    combined_score = (
        0.4 * clarity_score +
        0.3 * examples_score +
        0.2 * setup_score +
        0.1 * license_contrib_score
    )

    combined_score = round(combined_score, 2)

    # Save documentation score to cache
    cached = cached or {}
    cached["documentation_score"] = combined_score
    save_score(owner, repo_name, cached)

    return combined_score
