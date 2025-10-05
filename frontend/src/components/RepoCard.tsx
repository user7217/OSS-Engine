import React from "react";

type RepoCardProps = {
  repo: {
    repo: string;
    combined_score: number;
    maintenance_score: number;
    community_score: number;
    code_quality_score: number | null;
    documentation_score: number | null;
  };
};

const getScoreClass = (score: number | null) => {
  if (score === null) return "";
  if (score >= 8) return "score-green";
  if (score >= 5) return "score-yellow";
  return "score-red";
};

const RepoCard: React.FC<RepoCardProps> = ({ repo }) => {
  const repoUrl = `https://github.com/${repo.repo}`;

  return (
    <a
      href={repoUrl}
      target="_blank"
      rel="noopener noreferrer"
      className="repo-card-link"
      aria-label={`Open GitHub repository ${repo.repo} in new tab`}
      style={{ textDecoration: "none", color: "inherit", display: "block" }}
    >
      <div className="repo-card" tabIndex={0}>
        <h3 className="repo-name">{repo.repo}</h3>

        <div className="score-row">
          <div className="score-label">Combined</div>
          <div className={`score-value ${getScoreClass(repo.combined_score)}`}>{repo.combined_score}</div>
        </div>

        <div className="score-row">
          <div className="score-label">Maintenance</div>
          <div className={`score-value ${getScoreClass(repo.maintenance_score)}`}>{repo.maintenance_score}</div>
        </div>

        <div className="score-row">
          <div className="score-label">Community</div>
          <div className={`score-value ${getScoreClass(repo.community_score)}`}>{repo.community_score}</div>
        </div>

        <div className="score-row">
          <div className="score-label">Code Quality</div>
          <div className={`score-value ${getScoreClass(repo.code_quality_score)}`}>{repo.code_quality_score ?? "N/A"}</div>
        </div>

        <div className="score-row">
          <div className="score-label">Documentation</div>
          <div className={`score-value ${getScoreClass(repo.documentation_score)}`}>{repo.documentation_score ?? "N/A"}</div>
        </div>
      </div>
    </a>
  );
};

export default RepoCard;
