# ATLAS — Autonomous Ad Intelligence System

Internal ad intelligence, automation, and attribution system for:
- **Lumina Web3** (Web3 marketing agency)
- **Lumina Clippers** (Content distribution)
- **OpenClaw Agency** (AI consultancy)

## Architecture

- **Frontend:** Next.js 14+ / TypeScript / Tremor charts
- **Backend:** Python FastAPI / APScheduler / PostgreSQL
- **AI Insights:** Anthropic Claude (Sonnet 4.6) for ad performance analysis
- **Integrations:** Meta Marketing API, Calendly, Stripe, Telegram, Apify
- **Scheduler:** In-process APScheduler with 5 automated tasks (every 4 hours)

## Quick Start

```bash
cp .env.example .env
# Fill in your API keys in .env (including ANTHROPIC_API_KEY)
docker-compose up --build
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Scheduler Status: http://localhost:8000/api/scheduler/status

## Scheduled Automations

| Task | Interval | Description |
|------|----------|-------------|
| Meta Data Sync | Every 4h at :00 | Pull campaigns, ad sets, ads & metrics |
| Rules Evaluation | Every 4h at :15 | Evaluate automation rules against metrics |
| Competitor Ad Fetch | Every 4h at :30 | Fetch competitor ads via Apify |
| Health Check | Every 4h at :45 | Verify system health and data freshness |
| AI Insights | Every 4h at :50 | Generate Claude-powered performance insights |

## Funnel

Ad Click → Landing Page → Calendly Book → Sales Call → Proposal → Close → Revenue

