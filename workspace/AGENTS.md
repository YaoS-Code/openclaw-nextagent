# AGENTS.md — Template

Timezone: YOUR_TIMEZONE (e.g. America/Vancouver)

> Customize this file for your own setup. Replace all YOUR_* placeholders.
> The Skills Index table is the most important part — it tells the LLM which SKILL.md to load for each type of request.

## Session Startup

Only run these if the user's first message is about schedule/tasks/memory:
1. `curl -s http://localhost:18800/recall -H "Content-Type: application/json" -d '{"context": "topic"}'`
2. `curl -s http://localhost:18800/reminders/today`

For quick questions, skip startup checks.

## Skills Index

| Intent | Skill |
|---|---|
| Website / platform management | `skills/your-platform/SKILL.md` |
| Blog / content management | `skills/blog-manager/SKILL.md` |
| News auto-fetch + publish | `skills/blog-fetcher/SKILL.md` |
| Reminders / calendar | `skills/reminder/SKILL.md` |
| Memory / preferences | `skills/memory-system/SKILL.md` |
| Google Workspace | `skills/google-workspace/SKILL.md` |
| Background tasks | `skills/task-queue/SKILL.md` |
| Full-stack dev | `skills/fullstack-dev/SKILL.md` |
| Cloudflare deployment | `skills/cloudflare-deploy/SKILL.md` |
| GitHub contribution | `skills/github-contributor/SKILL.md` |
| Web search | `skills/web-search/SKILL.md` |
| Real-time news search | `skills/tavily-search/SKILL.md` |
| Self-learning | `skills/self-improvement/SKILL.md` |
| Credentials | Memory facts (`curl localhost:18800/facts`) |
| Casual / translation / Q&A | Just respond |

## Rules

### Memory

Unified memory — PostgreSQL + pgvector + bge-m3. One entry point searches everything.

**Search: always use `memory_search` first**
- Searches workspace files + pgvector conversations simultaneously
- For anything like "what did we do before" → memory_search, no curl
- `memory_get` to read specific file lines after search

**Write: use curl** (only these cases need curl)
```bash
# Store structured fact
curl -s -X POST http://localhost:18800/facts \
  -H "Content-Type: application/json" \
  -d '{"domain":"user","key":"preference","value":"..."}'

# Store conversation memory
curl -s -X POST http://localhost:18800/store \
  -H "Content-Type: application/json" \
  -d '{"content":"...","category":"decision"}'

# Force workspace re-index (after editing workspace files)
curl -s -X POST http://localhost:18800/workspace/sync -d '{"force":true}'
```

**Simple rule: search → memory_search, write → curl**

### Exec Policy

Discord sessions have full exec access. Use directly — no need to route through task-queue.

### Security

- Never expose API keys/tokens in group chats
- Memory is isolated by user_id
- Only the owner's DM can execute shell commands

### Self-Learning Rules

1. Command fails → `POST /learnings` (type=error, pattern_key)
2. User corrects → `POST /learnings` (type=correction)
3. Better method found → `POST /learnings` (type=best_practice)

### General

- Be concise. Execute then present results.
- Ask before external actions (emails, public posts)

## Auto Memory & Compaction

**Auto-extract** — After significant exchanges:
```bash
curl -s -X POST http://localhost:18800/extract \
  -H "Content-Type: application/json" \
  -d '{"messages": [...], "auto_store": true}'
```

**Auto-compact** — When conversations get long (>20 messages):
```bash
curl -s -X POST http://localhost:18800/compact \
  -H "Content-Type: application/json" \
  -d '{"messages": [...]}'
```
