import React, { useState } from "react";
import FilterPanel from "../components/FilterPanel";
import ResultsList from "../components/ResultsList";
import { RepoScoreResult } from "../types/RepoScoreResult";
import { fetchReposWithScores, FilterCriteria } from "../services/api";

const MainPage: React.FC = () => {
  const [repos, setRepos] = useState<RepoScoreResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleApplyFilters = async (filtersInput: {
    keywords: string;
    language: string;
    minGoodFirstIssues: number;
    maxGoodFirstIssues: number;
    topics: string;
    recentCommitDays: number;
  }) => {
    setLoading(true);
    setError(null);
    setRepos([]);

    // Convert comma separated topics string to array
    const topicsArray = filtersInput.topics
      .split(",")
      .map((t) => t.trim())
      .filter((t) => t.length > 0);

    const filters: FilterCriteria = {
      keywords: filtersInput.keywords || undefined,
      language: filtersInput.language || undefined,
      min_good_first_issues: filtersInput.minGoodFirstIssues,
      max_good_first_issues: filtersInput.maxGoodFirstIssues,
      topics: topicsArray.length > 0 ? topicsArray : undefined,
      recent_commit_days: filtersInput.recentCommitDays,
    };

    try {
      const data = await fetchReposWithScores(filters);
      setRepos(data);
    } catch (e) {
      setError("Failed to fetch data. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: 900, margin: "auto", padding: 20 }}>
      <h1>Repository Discoverability & Scoring</h1>
      <FilterPanel onApplyFilters={handleApplyFilters} />
      {loading && <p>Loading repositories...</p>}
      {error && <p style={{ color: "red" }}>{error}</p>}
      <ResultsList repos={repos} />
    </div>
  );
};

export default MainPage;
