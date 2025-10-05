***

# OSS Engine - Open Source Project Discoverability and Scoring

A web application to discover, filter, and score open-source repositories based on multiple quality metrics such as maintenance, community engagement, documentation, and code quality. It includes a FastAPI backend for data fetching and scoring, and a React TypeScript frontend for interactive search and display.

***

## Features

- Search and filter repositories by:
  - Keywords in name and description
  - Primary programming language
  - Number of open “good first issues”
  - Recent commit activity
  - Topics/tags
- Batch scoring pipeline:
  - Scores top 100 filtered repos by maintenance and community engagement
  - Further scores top 15 by documentation and code quality
- Caching of computed scores for performance
- Interactive React frontend with filter panel and cards showing key metrics and scores

***

## Architecture

### Backend (FastAPI)

- `services.ingest.repo_searcher` - Advanced GitHub repo search and filtering using GitHub REST/GraphQL API
- `services.scoring` - Scoring modules for maintenance, community, documentation, and code quality using Gemini AI and custom logic
- `services.api` - FastAPI app exposing:
  - `/score` endpoint: Scores a single repo
  - `/search_and_score` endpoint: Filter repos and batch score top results
- Database: JSON file caching scores (`score_cache.json`)

### Frontend (React + TypeScript)

- FilterPanel: Multi-criteria filter form
- ResultsList & RepoCard: Displays repo info and scores in card layout
- Uses environment variable `REACT_APP_API_BASE` to connect to backend API

***

## Getting Started

### Prerequisites

- Node.js >=16, npm or yarn
- Python 3.9+
- GitHub personal access token with repo read access
- Gemini API key (set as `GEMINI_API_KEY` environment variable)

***

### Backend Setup

1. Clone repository and navigate to backend folder:

   ```bash
   cd backend
   ```

2. Create `.env` file or export GitHub and Gemini tokens:

   ```bash
   export GITHUB_TOKEN=your_github_token
   export GEMINI_API_KEY=your_gemini_api_key
   ```

3. Install Python dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Run FastAPI server:

   ```bash
   uvicorn services.api:app --reload --host 0.0.0.0 --port 8000
   ```

***

### Frontend Setup

1. Navigate to frontend folder:

   ```bash
   cd frontend
   ```

2. Create `.env` file with backend URL:

   ```
   REACT_APP_API_BASE=http://localhost:8000
   ```

3. Install dependencies:

   ```bash
   npm install
   ```

4. Start React development server:

   ```bash
   npm start
   ```

5. Open browser at http://localhost:3000

***

## Usage

- Use the filter panel to enter keywords, language, good first issue counts, topics, and commit recency.
- Click **Search** to query backend and retrieve scored repositories.
- View results displayed as cards with all relevant scores and highlights.
- Top 15 repos show extended scores including documentation and code quality.

***

## Environment Variables

| Variable        | Description                       | Required  |
|-----------------|---------------------------------|-----------|
| GITHUB_TOKEN    | GitHub API personal access token| Yes       |
| GEMINI_API_KEY  | Gemini AI API key                | Yes       |
| REACT_APP_API_BASE | Backend API URL for frontend  | Frontend only |

***

## Troubleshooting

- **CORS errors:** Make sure CORS middleware is enabled in backend with correct origins.
- **API rate limits:** GitHub API enforces limits; ensure your token has sufficient quota or implement caching.
- **Missing or failed dependencies:** Double-check `npm install` and `pip install` steps.
- **React errors about JSX or imports:** Verify `tsconfig.json` includes `"esModuleInterop": true` and `.tsx` extensions.

***

## Contributing

Contributions welcome! Please fork the repo and submit pull requests with improvements or bug fixes.

***

## License

MIT License © 2025 OSS Engine Contributors

***
