from typing import List, Dict
from services.scoring.maintenance import calculate_category_1_score
from services.scoring.community import calculate_category_3_score
from services.scoring.documentation import get_documentation_score
from services.ingest.ecosyste_client import get_aggregated_code_quality_score
from services.ingest.repo_fetcher import fetch_code_snippets, fetch_contributors_with_locations


def batch_score_repositories(repos: List[Dict]) -> List[Dict]:
    scored_repos = []
    print(f"Starting batch scoring of {len(repos[:100])} repositories (top 100)")

    for idx, repo in enumerate(repos[:100], start=1):
        print(f"[{idx}/{min(100, len(repos))}] Scoring maintenance and community for {repo['full_name']}...")
        try:
            score_input = {
                "pushedAt": repo.get("pushedAt") or repo.get("pushed_at") or "",
                "commitCountLast90Days": repo.get("commitCountLast90Days") or 0,
                "totalCommitCount": repo.get("totalCommitCount") or 0,
                "pullRequests": repo.get("pullRequests", {}),
                "issues": repo.get("issues", {}),
                "ciPresent": repo.get("ciPresent", True),
                "testCoveragePercent": repo.get("testCoveragePercent", 80),
            }
            print(f"  Normalized maintenance inputs for {repo['full_name']}: pushedAt={score_input['pushedAt']}, last90={score_input['commitCountLast90Days']}, total={score_input['totalCommitCount']}")
            maint_score = calculate_category_1_score(score_input)

            contributors = fetch_contributors_with_locations(repo["owner"], repo["name"])
            comm_score = calculate_category_3_score(repo["owner"], repo["name"], contributors)
            print(f"  Maintenance: {maint_score}, Community: {comm_score}")
        except Exception as e:
            print(f"  Error scoring maintenance/community for {repo['full_name']}: {e}")
            maint_score, comm_score = 0, 0

        scored_repos.append({
            "repo": repo["full_name"],
            "owner": repo["owner"],
            "repo_name": repo["name"],
            "maintenance_score": maint_score,
            "community_score": comm_score,
            "documentation_score": None,
            "code_quality_score": None,
            "combined_score": 0,
            "good_first_issues_count": repo.get("good_first_issues_count", 0),
            "pushedAt": score_input["pushedAt"],
            "topics": repo.get("topics", []),
        })

    print("Scoring documentation and code quality for top 15 repositories")
    for i, r in enumerate(scored_repos[:15], start=1):
        print(f"[{i}/15] Scoring documentation and code quality for {r['repo']}...")
        try:
            doc_score = get_documentation_score(r["owner"], r["repo_name"])
            snippets = fetch_code_snippets(r["owner"], r["repo_name"])
            code_quality_score = get_aggregated_code_quality_score(snippets, r["owner"], r["repo_name"])
            print(f"  Documentation: {doc_score}, Code Quality: {code_quality_score}")
        except Exception as e:
            print(f"  Error scoring doc/code quality for {r['repo']}: {e}")
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

    print("Calculating combined score for remaining repositories (16-100)")
    for r in scored_repos[15:]:
        r["combined_score"] = round(
            0.6 * r["maintenance_score"] +
            0.4 * r["community_score"],
            2
        )

    print("Sorting repositories by combined score")
    scored_repos.sort(key=lambda x: x["combined_score"], reverse=True)

    print("Batch scoring complete")
    return scored_repos
