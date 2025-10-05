import axios from "axios";
import { RepoScoreResult } from "../types/RepoScoreResult";

export interface FilterCriteria {
  keywords?: string;
  language?: string;
  min_good_first_issues?: number;
  max_good_first_issues?: number;
  topics?: string[];
  recent_commit_days?: number;
}

const API_BASE = process.env.REACT_APP_API_BASE || "http://localhost:8000";

export async function fetchReposWithScores(filters: FilterCriteria): Promise<RepoScoreResult[]> {
  const response = await axios.post<RepoScoreResult[]>(`${API_BASE}/search_and_score`, filters);
  return response.data;
}
