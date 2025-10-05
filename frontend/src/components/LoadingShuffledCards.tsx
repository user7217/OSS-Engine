import React, { useState, useEffect } from "react";
import RepoCard from "./RepoCard";

const MOCK_REPOS = [
  { repo: "facebook/react", combined_score: 9, maintenance_score: 9, community_score: 10, code_quality_score: 9, documentation_score: 8 },
  { repo: "tensorflow/tensorflow", combined_score: 8, maintenance_score: 7, community_score: 9, code_quality_score: 8, documentation_score: 7 },
  { repo: "apache/spark", combined_score: 7, maintenance_score: 7, community_score: 8, code_quality_score: 7, documentation_score: 6 },
  { repo: "nestjs/nest", combined_score: 8, maintenance_score: 8, community_score: 7, code_quality_score: 7, documentation_score: 8 },
  { repo: "microsoft/vscode", combined_score: 9, maintenance_score: 9, community_score: 9, code_quality_score: 8, documentation_score: 9 },
];

const LoadingShuffledCards: React.FC = () => {
  const [visibleRepos, setVisibleRepos] = useState(MOCK_REPOS);

  useEffect(() => {
    const interval = setInterval(() => {
      setVisibleRepos((prev) => {
        if (prev.length <= 1) {
          clearInterval(interval);
          return prev;
        }
        const indexToRemove = Math.floor(Math.random() * prev.length);
        return prev.filter((_, idx) => idx !== indexToRemove);
      });
    }, 1500);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="repo-cards-container">
      {visibleRepos.map((repo) => (
        <RepoCard key={repo.repo} repo={repo} />
      ))}
    </div>
  );
};

export default LoadingShuffledCards;
