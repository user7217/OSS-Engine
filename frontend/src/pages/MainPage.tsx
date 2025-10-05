import React, { useState } from "react";
import FilterPanel, { Filters } from "../components/FilterPanel";
import ResultsList from "../components/ResultsList";
import LoadingShuffledCards from "../components/LoadingShuffledCards";

const languageOptions = ["Python", "JavaScript", "Java", "Kotlin", "C++", "TypeScript", "Go", "Ruby"];
const topicOptions = ["machine-learning", "android", "web", "devops", "data-science", "security", "mobile"];
const initialFilters: Filters = {
  keywords: "",
  language: "",
  topics: [],
  minGoodFirstIssues: 0,
  maxGoodFirstIssues: 1000,
  recentCommitDays: 90,
};

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || "";

const MainPage: React.FC = () => {
  const [filters, setFilters] = useState<Filters>(initialFilters);
  const [repos, setRepos] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  const handleSearch = (searchFilters: Filters) => {
    console.log("Submitting search:", searchFilters);
    setLoading(true);
    fetch(`${BACKEND_URL}/search_and_score`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        keywords: searchFilters.keywords,
        language: searchFilters.language,
        topics: searchFilters.topics,
        min_good_first_issues: searchFilters.minGoodFirstIssues,
        max_good_first_issues: searchFilters.maxGoodFirstIssues,
        recent_commit_days: searchFilters.recentCommitDays,
      }),
    })
      .then(res => {
        console.log("HTTP response", res);
        if (!res.ok) throw new Error("Server error " + res.status);
        return res.json();
      })
      .then(data => setRepos(data))
      .catch(err => {
        console.error("Search error:", err);
        setRepos([]);
      })
      .finally(() => setLoading(false));
  };

  return (
    <div className="main-page">
      <FilterPanel filters={filters} onFiltersChange={setFilters} onSearchClick={handleSearch} languageOptions={languageOptions} topicOptions={topicOptions} />
      {loading ? <LoadingShuffledCards /> : <ResultsList repos={repos} loading={loading} />}
    </div>
  );
};

export default MainPage;
