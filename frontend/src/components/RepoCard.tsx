import React from "react";
import { RepoScoreResult } from "../types/RepoScoreResult";

interface Props {
  repo: RepoScoreResult;
  isTop15: boolean;
}

const RepoCard: React.FC<Props> = ({ repo, isTop15 }) => {
  return (
    <div
      style={{
        border: "1px solid #ddd",
        borderRadius: 8,
        padding: 16,
        marginBottom: 12,
        boxShadow: "1px 1px 5px rgba(0,0,0,0.1)",
      }}
    >
      <h3>
        <a href={`https://github.com/${repo.owner}/${repo.repo_name}`} target="_blank" rel="noreferrer">
          {repo.repo}
        </a>
      </h3>
      <p>
        <b>Good First Issues:</b> {repo.good_first_issues_count} |{" "}
        <b>Last Commit:</b> {repo.pushed_at ? new Date(repo.pushed_at).toLocaleDateString() : "N/A"}
      </p>

      <p>
        <b>Maintenance score:</b> {repo.maintenance_score.toFixed(2)} |{" "}
        <b>Community score:</b> {repo.community_score.toFixed(2)}
      </p>

      {isTop15 && (
        <>
          <p>
            <b>Documentation score:</b>{" "}
            {repo.documentation_score !== null && repo.documentation_score !== undefined
              ? repo.documentation_score.toFixed(2)
              : "N/A"}
          </p>
          <p>
            <b>Code Quality score:</b>{" "}
            {repo.code_quality_score !== null && repo.code_quality_score !== undefined
              ? repo.code_quality_score.toFixed(2)
              : "N/A"}
          </p>
        </>
      )}

      <p>
        <b>Combined score:</b> {repo.combined_score.toFixed(2)}
      </p>

      <p>
        <b>Topics:</b>{" "}
        {repo.topics && repo.topics.length > 0
          ? repo.topics.join(", ")
          : "None"}
      </p>
    </div>
  );
};

export default RepoCard;
