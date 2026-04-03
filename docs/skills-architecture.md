# Skills Architecture: 5-Layer Design

## Why Not Just Use ClawHub?

ClawHub is great for general-purpose skills. Custom skills let you:
1. Encode your specific business logic
2. Connect to your own APIs/services
3. Define routing rules in AGENTS.md
4. Keep private data private

## The 5-Layer Model

### Layer 1 — Memory & Learning (Foundation)
Shared by all other skills. Install these first.

- `memory-system/` — pgvector search + structured facts
- `self-improvement/` — error recording, correction learning, hot-knowledge cache

### Layer 2 — Platform Core (Your Products)
Skills that manage platforms you own.

Example: website management skill, course platform skill, CRM skill.
One skill per platform. All calls through Bot Token + REST API.

### Layer 3 — Content Operations (Automation)
News scraping, AI writing, auto-publishing.

- `blog-fetcher/` — multi-source scraper → Claude writes → publishes
- `blog-manager/` — CRUD for blog posts

### Layer 4 — Productivity Integration (External SaaS)
One skill per tool you use daily.

- `google-workspace/` — Gmail, Calendar, Drive, Sheets
- `github-contributor/` — Git operations
- `reminder/` — timed reminders + iCal
- `task-queue/` — async Claude Code tasks
- `cloudflare-deploy/` — Cloudflare Tunnel deployment

### Layer 5 — Private Business Skills (Never Publish)
Skills tightly coupled to your specific business.
Time-clock systems, proprietary CRMs, client-specific workflows — keep these local.

## AGENTS.md as Router

The Skills Index table in AGENTS.md maps natural-language intent to skill file paths.
The LLM reads this table and knows which SKILL.md to load for any request.
