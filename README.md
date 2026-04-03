# openclaw-nextagent

**Custom OpenClaw setup** — persistent memory with pgvector, 17 custom skills, Discord-native agent, Claude Sonnet 4.6.

> A complete, production-running customization of [OpenClaw](https://github.com/openclaw/openclaw) deployed on a Linux laptop as a full AI assistant + content platform.

[![OpenClaw](https://img.shields.io/badge/OpenClaw-v2026.4.1-cyan)](https://github.com/openclaw/openclaw)
[![Claude](https://img.shields.io/badge/Model-Claude_Sonnet_4.6-orange)](https://anthropic.com)
[![PostgreSQL](https://img.shields.io/badge/DB-PostgreSQL_17+pgvector-blue)](https://github.com/pgvector/pgvector)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## What This Is

Official OpenClaw gives you a powerful AI assistant framework. This repo shows how we took it further:

| Official OpenClaw | This Setup (NexAgent 凌骁) |
|---|---|
| Session-only memory (SQLite) | Persistent pgvector memory + structured facts |
| Generic assistant | Named persona (凌骁) with SOUL.md + IDENTITY.md |
| ClawHub skill ecosystem | 17 custom vertical skills |
| Multi-channel support | Discord-native (DM + guild moderation) |
| npm/Docker deployment | Native systemd, zero Docker |
| openclaw.json config | Multi-layer: AGENTS.md + SOUL.md + IDENTITY.md |

---

## Architecture

```
Discord (DM + Guild)
        │
   OpenClaw Agent (凌骁 / Líng Xiāo)
        │
        ├── AGENTS.md          ← skill routing + exec policy + memory rules
        ├── SOUL.md            ← persona baseline
        ├── IDENTITY.md        ← name, timezone, language
        │
        ├── Memory Service (FastAPI :18800)
        │       ├── PostgreSQL 17 + pgvector  ← semantic vector search
        │       ├── Structured facts store    ← domain/key/value
        │       └── Redis                     ← hot-knowledge cache
        │
        ├── Business Backend (Flask :4001)
        │       ├── Blog system (NexAgent AI Blog)
        │       ├── Course platform (OpenClaw Club)
        │       └── Discord moderation log
        │
        └── Frontend (Next.js :3000, nginx, Cloudflare Tunnel)
                └── nextagent.ca
```

---

## Repository Structure

```
openclaw-nextagent/
├── README.md
├── docs/
│   ├── migration-guide.md       ← Full migration: official → this setup
│   ├── database-setup.md        ← SQLite → PostgreSQL migration
│   └── skills-architecture.md  ← How to design your own skill layers
├── workspace/
│   ├── AGENTS.md                ← Template (redacted private sections)
│   ├── SOUL.md                  ← Persona template
│   └── IDENTITY.md              ← Identity template
├── skills/
│   ├── memory-system/           ← pgvector memory skill
│   ├── self-improvement/        ← learning + hot-knowledge cache
│   ├── blog-manager/            ← blog CRUD skill (generic)
│   ├── blog-fetcher/            ← daily news → Claude writes → publish
│   ├── reminder/                ← reminders + iCal subscriptions
│   ├── task-queue/              ← async Claude Code tasks
│   ├── google-workspace/        ← Gmail/Calendar/Drive
│   ├── github-contributor/      ← Git operations
│   ├── tavily-search/           ← real-time web search
│   ├── web-search/              ← DuckDuckGo search
│   ├── cloudflare-deploy/       ← Cloudflare Tunnel deployment
│   ├── fullstack-dev/           ← end-to-end project workflow
│   └── games/                  ← mini-games
├── sql/
│   ├── memory_schema.sql        ← Complete memory DB schema
│   └── blog_schema.sql          ← Blog posts table with pgvector
├── systemd/
│   ├── oc-api.service           ← Flask backend service
│   └── openclaw-memory.service  ← Memory service
└── scripts/
    ├── blog_fetcher/
    │   ├── fetcher.py           ← Multi-source news scraper
    │   ├── auto_publisher.py    ← Claude writes + publishes articles
    │   └── openclaw_blog_writer.py ← Daily OpenClaw update analysis
    └── daily_memory_audit.sh    ← Nightly memory maintenance
```

---

## Quick Start

### 1. Install OpenClaw
```bash
npm install -g openclaw
openclaw onboard   # choose Anthropic, enter API key
```

### 2. Set up PostgreSQL + pgvector
```bash
sudo apt install postgresql-17 postgresql-17-pgvector
sudo -u postgres psql -c "CREATE USER db_admin WITH PASSWORD 'yourpass';"
sudo -u postgres psql -c "CREATE DATABASE my_agent_db OWNER db_admin;"
psql -h 127.0.0.1 -U db_admin -d my_agent_db -c "CREATE EXTENSION vector;"
psql -h 127.0.0.1 -U db_admin -d my_agent_db -f sql/memory_schema.sql
```

### 3. Deploy Memory Service
```bash
git clone https://github.com/YaoS-Code/agentic-memory
cd agentic-memory/memory-service
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
# Configure DB connection in config.py or .env
./venv/bin/uvicorn main:app --host 127.0.0.1 --port 18800
```

### 4. Install skills
```bash
cp -r skills/ ~/.openclaw/workspace/skills/
cp workspace/AGENTS.md ~/.openclaw/workspace/AGENTS.md
cp workspace/SOUL.md ~/.openclaw/workspace/SOUL.md
```

### 5. Configure Discord
```bash
openclaw configure --section channels
# Select Discord, enter Bot Token
```

### 6. Set systemd services (optional, replaces Docker)
```bash
sudo cp systemd/*.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable oc-api openclaw-memory
sudo systemctl start oc-api openclaw-memory
```

---

## Key Design Decisions

### Why PostgreSQL instead of SQLite?
- **Vector search**: pgvector HNSW enables semantic memory search across all past conversations
- **Persistence**: memories survive restarts, accumulate over time with configurable decay
- **Scale**: concurrent connections, JSONB, GIN indexes for fast full-text search

### Why Discord-only?
We run a Discord community (OpenClaw Club). Discord gives us guild management, role-based access, slash commands, and button approvals — more than enough for a team setup.

### Why systemd instead of Docker?
Running on a thin laptop (7.4GB RAM). Native systemd saves ~2GB RAM vs Docker overhead, starts faster, and has simpler dependency ordering.

### Why AGENTS.md instead of plugins.json?
AGENTS.md is a markdown file the LLM reads directly. It serves as routing table + permission policy + memory rules + self-learning rules in one human-readable place. No separate config format to learn.

---

## Version Compatibility

| This setup version | OpenClaw | Claude Model |
|---|---|---|
| Current | v2026.4.1 | claude-sonnet-4-6 |
| Previous | v2026.3.28 | claude-sonnet-4-5 |

See [docs/migration-guide.md](docs/migration-guide.md) for full version changelog and impact analysis.
Also see the [NexAgent Blog](https://nextagent.ca/zh/blog) for illustrated migration write-ups.

---

## Related

- [agentic-memory](https://github.com/YaoS-Code/agentic-memory) — The memory service used by this setup
- [OpenClaw](https://github.com/openclaw/openclaw) — The underlying agent framework
- [NexAgent](https://nextagent.ca) — Where this all runs in production

---

## License

MIT — use freely, customize to your needs.
