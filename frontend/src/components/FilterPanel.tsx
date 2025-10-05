import React from "react";
import Select from "react-select";

export type Filters = {
  keywords: string;
  language: string;
  topics: string[];
  minGoodFirstIssues: number;
  maxGoodFirstIssues: number;
  recentCommitDays: number;
};

type FilterPanelProps = {
  filters: Filters;
  languageOptions: string[];
  topicOptions: string[];
  onFiltersChange: (filters: Filters) => void;
  onSearchClick: (filters: Filters) => void;
};

const topicSelectOptions = (topicOptions: string[]) =>
  topicOptions.map(v => ({ label: v, value: v }));

const FilterPanel: React.FC<FilterPanelProps> = ({
  filters,
  onFiltersChange,
  languageOptions,
  topicOptions,
  onSearchClick,
}) => {
  return (
    <div className="google-filter-panel">
      <form
        className="google-search-form"
        onSubmit={e => {
          e.preventDefault();
          onSearchClick(filters);
        }}
      >
        <input
          type="text"
          placeholder="Search repositories"
          spellCheck={false}
          value={filters.keywords}
          onChange={e => onFiltersChange({ ...filters, keywords: e.target.value })}
          className="big-search-input"
        />
        <button className="big-search-button" type="submit">
          Search
        </button>
      </form>
      <div className="dropdown-row">
        <select
          className="google-dropdown"
          value={filters.language}
          onChange={e => onFiltersChange({ ...filters, language: e.target.value })}
        >
          <option value="">All Languages</option>
          {languageOptions.map(lang => (
            <option key={lang} value={lang}>{lang}</option>
          ))}
        </select>
        <div style={{ minWidth: 180, flex: 1, marginRight: 8, fontFamily: "inherit" }}>
          <Select
            isMulti
            name="topics"
            classNamePrefix="react-select"
            value={topicSelectOptions(topicOptions).filter(option =>
              filters.topics.includes(option.value),
            )}
            options={topicSelectOptions(topicOptions)}
            onChange={selected =>
              onFiltersChange({ ...filters, topics: (selected as any[]).map(o => o.value) })
            }
            placeholder="Topics"
            styles={{
              control: base => ({
                ...base,
                background: "#232635",
                borderRadius: 16,
                borderColor: "#34374b",
                color: "#e0e7ef",
                fontFamily: "inherit",
              }),
              menu: base => ({
                ...base,
                background: "#232635",
                color: "#e0e7ef",
                borderRadius: 14,
              }),
              multiValue: base => ({
                ...base,
                background: "#343f50",
                color: "#c7e3fe",
                borderRadius: 10,
              }),
              multiValueLabel: base => ({
                ...base,
                color: "#c7e3fe",
                fontWeight: 600,
              }),
            }}
          />
        </div>
        <select
          className="google-dropdown"
          value={filters.minGoodFirstIssues}
          onChange={e => onFiltersChange({ ...filters, minGoodFirstIssues: Number(e.target.value) })}
        >
          {[0, 1, 2, 3, 4, 5].map(v => (
            <option key={v} value={v}>{v}+</option>
          ))}
        </select>
        <select
          className="google-dropdown"
          value={filters.maxGoodFirstIssues}
          onChange={e => onFiltersChange({ ...filters, maxGoodFirstIssues: Number(e.target.value) })}
        >
          {[10, 50, 100, 500, 1000].map(v => (
            <option key={v} value={v}>{v}</option>
          ))}
        </select>
        <select
          className="google-dropdown"
          value={filters.recentCommitDays}
          onChange={e => onFiltersChange({ ...filters, recentCommitDays: Number(e.target.value) })}
        >
          {[30, 60, 90, 180].map(v => (
            <option key={v} value={v}>Last {v} days</option>
          ))}
        </select>
      </div>
    </div>
  );
};

export default FilterPanel;
