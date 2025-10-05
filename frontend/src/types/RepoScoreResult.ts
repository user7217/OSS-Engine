export interface RepoScoreResult {
  repo: string;
  owner: string;
  repo_name: string;
  maintenance_score: number;
  community_score: number;
  documentation_score?: number | null;
  code_quality_score?: number | null;
  combined_score: number;
  good_first_issues_count: number;
  pushed_at?: string;
  topics: string[];
}
