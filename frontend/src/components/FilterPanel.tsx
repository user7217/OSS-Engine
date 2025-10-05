import React, { useState } from "react";

interface Props {
  onApplyFilters: (filters: {
    keywords: string;
    language: string;
    minGoodFirstIssues: number;
    maxGoodFirstIssues: number;
    topics: string;
    recentCommitDays: number;
  }) => void;
}

const FilterPanel: React.FC<Props> = ({ onApplyFilters }) => {
  const [keywords, setKeywords] = useState("");
  const [language, setLanguage] = useState("");
  const [minGoodFirstIssues, setMinGoodFirstIssues] = useState(0);
  const [maxGoodFirstIssues, setMaxGoodFirstIssues] = useState(1000);
  const [topics, setTopics] = useState("");
  const [recentCommitDays, setRecentCommitDays] = useState(90);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onApplyFilters({
      keywords,
      language,
      minGoodFirstIssues,
      maxGoodFirstIssues,
      topics,
      recentCommitDays,
    });
  };

  return (
    <form onSubmit={handleSubmit} style={{ marginBottom: 20 }}>
      <div>
        <label>Keywords: </label>
        <input
          type="text"
          value={keywords}
          onChange={(e) => setKeywords(e.target.value)}
          placeholder="Search keywords"
        />
      </div>
      <div>
        <label>Language: </label>
        <input
          type="text"
          value={language}
          onChange={(e) => setLanguage(e.target.value)}
          placeholder="e.g. Python, JavaScript"
        />
      </div>
      <div>
        <label>Good First Issues (min): </label>
        <input
          type="number"
          min={0}
          value={minGoodFirstIssues}
          onChange={(e) => setMinGoodFirstIssues(Number(e.target.value))}
        />
      </div>
      <div>
        <label>Good First Issues (max): </label>
        <input
          type="number"
          min={0}
          value={maxGoodFirstIssues}
          onChange={(e) => setMaxGoodFirstIssues(Number(e.target.value))}
        />
      </div>
      <div>
        <label>Topics (comma separated): </label>
        <input
          type="text"
          value={topics}
          onChange={(e) => setTopics(e.target.value)}
          placeholder="e.g. machine-learning, web"
        />
      </div>
      <div>
        <label>Commit recency (days): </label>
        <input
          type="number"
          min={1}
          max={365}
          value={recentCommitDays}
          onChange={(e) => setRecentCommitDays(Number(e.target.value))}
        />
      </div>
      <button type="submit" style={{ marginTop: 10 }}>
        Search
      </button>
    </form>
  );
};

export default FilterPanel;
