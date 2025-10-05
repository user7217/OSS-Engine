import React from "react";
import RepoCard from "./RepoCard";

type ResultsListProps = { repos: any[]; loading: boolean; };

const ResultsList: React.FC<ResultsListProps> = ({ repos, loading }) => {
  if (loading) return <div className="loading">Loading repositories...</div>;
  if (repos.length === 0)
    return <div className="no-results">No repositories match your criteria.</div>;
  return (
    <div className="repo-cards-container">
      {repos.map((repo) => <RepoCard key={repo.repo} repo={repo} />)}
    </div>
  );
};

export default ResultsList;
