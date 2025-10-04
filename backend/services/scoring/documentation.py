import base64
import os
import re
from google import genai
from services.ingest.repo_fetcher import fetch_readme, extract_links_from_text, fetch_page_title_and_description


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
    readme_content = fetch_readme(owner, repo_name)
    if not readme_content:
        return 0

    # Normalize README lines for filtering
    lines = [line.strip() for line in readme_content.splitlines() if line.strip()]
    text_lower = readme_content.lower()

    def extract_section_by_keywords(keywords):
        # Extract snippet lines that mention any keywords
        snippet_lines = [line for line in lines if any(kw in line.lower() for kw in keywords)]
        # Return snippet text or fallback to first 50 lines
        if snippet_lines:
            return "\n".join(snippet_lines[:50])
        return "\n".join(lines[:50])

    # Define keyword groups for each criterion
    clarity_keywords = ["description", "overview", "summary", "introduction", "purpose"]
    examples_keywords = ["example", "tutorial", "sample", "quick start", "demo"]
    setup_keywords = ["install", "setup", "configure", "prerequisite", "requirements"]
    license_contrib_keywords = ["license", "contributing", "contribution", "cla", "code of conduct"]

    # Compose prompts for each section
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

    # Weighted combination
    combined_score = (
        0.4 * clarity_score +
        0.3 * examples_score +
        0.2 * setup_score +
        0.1 * license_contrib_score
    )

    return round(combined_score, 2)