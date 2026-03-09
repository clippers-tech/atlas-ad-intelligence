# ATLAS — Autonomous Ad Intelligence System

Internal ad intelligence, automation, and attribution system for:
- **Lumina Web3** (Web3 marketing agency)
- **Lumina Clippers** (Content distribution)
- **OpenClaw Agency** (AI consultancy)

## Architecture

- **Frontend:** Next.js 14+ / TypeScript / Tremor charts
- **Backend:** Python FastAPI / Celery / PostgreSQL / Redis
- **Integrations:** Meta Marketing API, Calendly, Stripe, Telegram, Claude AI, Apify

## Quick Start

```bash
cp .env.example .env
# Fill in your API keys in .env
docker-compose up --build
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Funnel

Ad Click → Landing Page → Calendly Book → Sales Call → Proposal → Close → Revenue
