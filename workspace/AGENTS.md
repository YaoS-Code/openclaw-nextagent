# AGENTS.md — Template

Timezone: YOUR_TIMEZONE (e.g. America/Vancouver)

> Customize this file for your own setup. Remove or replace private sections.

## Session Startup

Only run these if the user's first message is about schedule/tasks/memory:
1. `curl -s http://localhost:18800/recall -H "Content-Type: application/json" -d '{"context": "topic"}'`
2. `curl -s http://localhost:18800/reminders/today`

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

**Search: always use `memory_search` first**
- Searches workspace files + pgvector conversations simultaneously
- For anything like "what did we do before" → memory_search, no curl

**Write: use curl**
\`\`\`bash
# Store structured fact
curl -s -X POST http://localhost:18800/facts \
  -H "Content-Type: application/json" \
  -d '{"domain":"user","key":"preference","value":"..."}'

# Store conversation memory
curl -s -X POST http://localhost:18800/store \
  -H "Content-Type: application/json" \
  -d '{"content":"...","category":"decision"}'
\`\`\`

### Exec Policy

Discord sessions have full exec access. Use directly — no need to route through task-queue.

### Self-Learning Rules

1. Command fails → `POST /learnings` (type=error, pattern_key)
2. User corrects → `POST /learnings` (type=correction)
3. Better method found → `POST /learnings` (type=best_practice)
