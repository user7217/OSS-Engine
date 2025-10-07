from typing import List, Dict
from services.ingest.repo_fetcher import fetch_repo_data, fetch_code_snippets, fetch_contributors_with_locations
from services.scoring.maintenance import calculate_category_1_score
from services.scoring.community import calculate_category_3_score
from services.scoring.documentation import get_documentation_score
from services.ingest.ecosyste_client import get_aggregated_code_quality_score


def batch_score_repositories(repos: List[Dict]) -> List[Dict]:
    scored_repos = []
    print(f"Starting batch scoring of {len(repos[:100])} repositories (top 100)", flush=True)

    for idx, repo in enumerate(repos[:100], start=1):
        full_name = repo.get("full_name") or f"{repo.get('owner')}/{repo.get('name')}"
        print(f"[{idx}/{min(100, len(repos))}] Scoring maintenance and community for {full_name}...", flush=True)

        try:
            # Fetch detailed repo data for scoring
            full_repo_data = fetch_repo_data(repo["owner"], repo["name"])
            if not full_repo_data:
                print(f"  Warning: fetch_repo_data returned None for {full_name}, skipping", flush=True)
                continue

            score_input = {
                "pushedAt": full_repo_data.get("pushedAt") or full_repo_data.get("pushed_at") or "",
                "commitCountLast90Days": full_repo_data.get("commitCountLast90Days") or 0,
                "totalCommitCount": full_repo_data.get("totalCommitCount") or 0,
                "pullRequests": full_repo_data.get("pullRequests", {}),
                "issues": full_repo_data.get("issues", {}),
                "ciPresent": full_repo_data.get("ciPresent", True),
                "testCoveragePercent": full_repo_data.get("testCoveragePercent", 80),
            }
            print(f"  Normalized maintenance inputs for {full_name}: pushedAt={score_input['pushedAt']}, last90={score_input['commitCountLast90Days']}, total={score_input['totalCommitCount']}", flush=True)

            maint_score = calculate_category_1_score(score_input)

            contributors = fetch_contributors_with_locations(repo["owner"], repo["name"])
            comm_score = calculate_category_3_score(repo["owner"], repo["name"], contributors)

            print(f"  Maintenance: {maint_score}, Community: {comm_score}", flush=True)
        except Exception as e:
            print(f"  Error scoring maintenance/community for {full_name}: {e}", flush=True)
            maint_score, comm_score = 0, 0

        scored_repos.append({
            "repo": full_name,
            "owner": repo["owner"],
            "repo_name": repo["name"],
            "maintenance_score": maint_score,
            "community_score": comm_score,
            "documentation_score": None,
            "code_quality_score": None,
            "combined_score": 0,
            "good_first_issues_count": repo.get("good_first_issues_count", 0),
            "pushedAt": score_input.get("pushedAt", ""),
            "topics": repo.get("topics", []),
        })

    print("Scoring documentation and code quality for top 15 repositories", flush=True)
    for i, r in enumerate(scored_repos[:15], start=1):
        print(f"[{i}/15] Scoring documentation and code quality for {r['repo']}...", flush=True)
        try:
            doc_score = get_documentation_score(r["owner"], r["repo_name"])
            snippets = fetch_code_snippets(r["owner"], r["repo_name"])
            code_quality_score = get_aggregated_code_quality_score(snippets, r["owner"], r["repo_name"])
            print(f"  Documentation: {doc_score}, Code Quality: {code_quality_score}", flush=True)
        except Exception as e:
            print(f"  Error scoring doc/code quality for {r['repo']}: {e}", flush=True)
            doc_score, code_quality_score = 0, 0

        r["documentation_score"] = doc_score
        r["code_quality_score"] = code_quality_score
        r["combined_score"] = round(
            0.4 * r["maintenance_score"] +
            0.25 * r["community_score"] +
            0.25 * code_quality_score +
            0.10 * doc_score,
            2
        )

    print("Calculating combined score for remaining repositories (16-100)", flush=True)
    for r in scored_repos[15:]:
        r["combined_score"] = round(
            0.6 * r["maintenance_score"] +
            0.4 * r["community_score"],
            2
        )

    print("Sorting repositories by combined score", flush=True)
    scored_repos.sort(key=lambda x: x["combined_score"], reverse=True)

    print("Batch scoring complete", flush=True)
    return scored_repos

