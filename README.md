# AI Market Radar

AI Market Radar is a market intelligence platform that surfaces high-signal products and trends from multiple sources, enriches them with AI analysis, and presents them in a focused, decision-ready dashboard.

## What it does
- Multi-source ingestion: Pulls fresh items from community and product feeds, normalizes URLs, and merges duplicates across platforms while tracking source metadata and popularity metrics.
- AI scoring and summaries: Generates concise summaries, categories, tags, and impact scores so you can scan and rank opportunities quickly.
- Cross-platform signals: Aggregates appearances across platforms into a unified record with visit counts, metric history, and the most recent AI evaluation.
- Manual LLM evaluations: Trigger a deeper evaluation for any item (e.g., via DeepSeek) to capture product, investor, and market perspectives; each run is versioned and persisted.
- Timed refresh: Daily scheduled ingestion keeps the feed current without manual triggers.

## Design principles
- Signal over noise: De-duplicate aggressively, consolidate metrics, and highlight the freshest and most relevant items first.
- Explainability: Every item carries AI summaries, reasoning, tags, and optional long-form evaluations for deeper context.
- Actionable views: Structured data (scores, categories, platforms count, metric history) is surfaced to support quick triage and follow-up.
- Resilience: Background schedules and manual triggers both exist; evaluations fall back gracefully when external APIs are unavailable.

## How to run (local examples)
- Config
  - Set `DEEPSEEK_API_KEY` (and optionally `DEEPSEEK_MODEL`/`DEEPSEEK_BASE_URL`) to enable real LLM evaluations; without it, evaluations fall back to mock responses.
- Backend
  ```bash
  cd backend
  python -m venv venv
  source venv/bin/activate
  pip install -r requirements.txt
  uvicorn app.main:app --reload --port 8000
  ```
- Frontend
  ```bash
  cd frontend
  pnpm install
  pnpm dev
  ```

## Project structure
- `/backend`: API, ingestion, schedulers, AI evaluation, persistence.
- `/frontend`: Web UI for the intelligence dashboard and manual evaluations.
