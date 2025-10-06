
---

# OSS Engine 🚀

[![License: MIT](https://img.shields.io/badge/License-MIT-green)](LICENSE) [![Python](https://img.shields.io/badge/Python-3.9%2B-blue)](https://www.python.org/) [![Node.js](https://img.shields.io/badge/Node.js-16%2B-green)](https://nodejs.org/) [![GitHub Stars](https://img.shields.io/github/stars/yourusername/oss-engine)]()

**OSS Engine** is a web platform to **discover, filter, and score open-source repositories** based on multiple quality metrics: maintenance, community engagement, documentation, and code quality. Find the best repos to contribute to or use, powered by **GitHub APIs**, **Gemini AI**, and custom scoring logic.

---

## 🌟 Features

* **Advanced search & filter**

  * Keywords in repo name & description
  * Primary programming language
  * Number of open “good first issues”
  * Recent commit activity
  * Topics/tags

* **Scoring pipeline**

  * Batch scores top 100 repos by maintenance & community metrics
  * Top 15 repos scored further for documentation & code quality
  * Caching of scores for performance

* **Interactive frontend**

  * Filter panel with multi-criteria options
  * Repo cards showing key metrics & scores
  * Responsive React TypeScript UI

---

## 🏗 Architecture

**Backend (FastAPI)**

* `services.ingest.repo_searcher`: GitHub REST & GraphQL search & filtering
* `services.scoring`: Modules for maintenance, community, documentation, code quality
* `services.api`: Exposes endpoints:

  * `/score`: Score a single repo
  * `/search_and_score`: Filter repos and batch score top results
* **Database**: JSON cache (`score_cache.json`)

**Frontend (React + TypeScript)**

* `FilterPanel`: Multi-criteria filters
* `ResultsList` & `RepoCard`: Display repo info & scores
* Uses `REACT_APP_API_BASE` to connect to backend

---

## 🛠 Getting Started

### Prerequisites

* Node.js >=16, npm or yarn
* Python 3.9+
* GitHub personal access token with repo read access
* Gemini AI API key

### Backend Setup

```bash
cd backend
export GITHUB_TOKEN=your_github_token
export GEMINI_API_KEY=your_gemini_api_key
pip install -r requirements.txt
uvicorn services.api:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup

```bash
cd frontend
echo "REACT_APP_API_BASE=http://localhost:8000" > .env
npm install
npm start
```

Open: [http://localhost:3000](http://localhost:3000)

---

## 🎯 Usage

1. Use filter panel to set keywords, language, issues, topics, commit recency
2. Click **Search** to retrieve scored repositories
3. View results in cards with scores and highlights
4. Top 15 repos show extended scores: documentation & code quality

---

## 📊 Example API

**Request:**

```http
GET /score?owner=octocat&repo=Hello-World
```

**Response:**

```json
{
  "repo": "octocat/Hello-World",
  "community_score": 7.8,
  "maintenance_score": 8.2,
  "documentation_score": 6.5,
  "code_quality_score": 7.0
}
```

---

## 🛡 Environment Variables

| Variable             | Description                  | Required      |
| -------------------- | ---------------------------- | ------------- |
| `GITHUB_TOKEN`       | GitHub personal access token | ✅             |
| `GEMINI_API_KEY`     | Gemini AI API key            | ✅             |
| `REACT_APP_API_BASE` | Backend API URL              | Frontend only |

---

## 🐛 Troubleshooting

* **CORS errors**: Ensure `CORSMiddleware` is enabled with correct origins
* **GitHub API limits**: Check token quota or enable caching
* **Missing dependencies**: Verify `npm install` & `pip install`
* **React errors**: Ensure `tsconfig.json` has `"esModuleInterop": true` and `.tsx` extensions

---

## 💡 Contributing

Contributions welcome!

1. Fork the repo
2. Create a branch: `git checkout -b feature/your-feature`
3. Commit: `git commit -m "Add your feature"`
4. Push: `git push origin feature/your-feature`
5. Open a Pull Request

---

## 🔖 Tags

**#OpenSource #GitHub #React #FastAPI #Python #TypeScript #AI #Community #RepoScoring #OSS**

---

## 📸 Preview

![FilterPanel](./assets/filter-panel.png)
![RepoCard](./assets/repo-card.png)

---

## 📝 License

MIT License © 2025 OSS Engine Contributors

---