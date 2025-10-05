import React from "react";
import { RepoScoreResult } from "../types/RepoScoreResult";
import RepoCard from "./RepoCard";

interface Props {
  repos: RepoScoreResult[];
}

const ResultsList: React.FC<Props> = ({ repos }) => {
  return (
    <div>
      {repos.map((repo, idx) => (
        <RepoCard key={repo.repo} repo={repo} isTop15={idx < 15} />
      ))}
    </div>
  );
};

export default ResultsList;
