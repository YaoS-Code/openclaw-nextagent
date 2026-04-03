---
name: memory-system
description: Tiered memory system with vector search, structured facts, and file storage
metadata:
  {
    "openclaw": {
      "emoji": "🧠",
      "always": true
    }
  }
---

# Memory System

You have access to a persistent, tiered memory system via a local API at `http://localhost:18800`. Use it to remember important information across sessions.

## Memory Tiers

| Tier | Use For | Storage |
|------|---------|---------|
| `cache` | Casual chat, transient context | Redis (expires in 4h) |
| `vector` | Important info, skills, decisions, insights | PostgreSQL + pgvector (with decay) |
| `fact` | Structured data: contacts, preferences, schedules | PostgreSQL JSONB |
| `file` | Photos, documents, audio | MinIO object storage |

## When to Store Memories

- User says "remember that..." → **vector** (importance 7+)
- Contact info, dates, preferences → **fact**
- Key decision or project insight → **vector** (category: decision/insight)
- Skill or technique learned → **vector** (category: skill, importance 8+)
- Photo/file shared → **file**
- General chat, small talk → **cache** or don't store

## Tools

### memory_store — Save a memory

```bash
curl -s http://localhost:18800/store -H "Content-Type: application/json" -d '{
  "content": "the text to remember",
  "tier": "vector",
  "category": "general",
  "importance": 5,
  "tags": ["tag1", "tag2"],
  "source": "chat",
  "source_ref": "session-id"
}'
```

**Parameters:**
- `content` (required): The text to store
- `tier`: "cache", "vector", "fact" (auto-classified if omitted)
- `category`: "general", "skill", "insight", "decision", "project", "conversation_highlight"
- `importance`: 1-10 (default 5). Higher = longer retention
- `tags`: Array of string tags
- For fact tier, also provide `domain`, `key`, `value`

### memory_search — Find memories

```bash
curl -s http://localhost:18800/search -H "Content-Type: application/json" -d '{
  "query": "what to search for",
  "max_results": 5,
  "tiers": ["vector", "fact"]
}'
```

**Parameters:**
- `query` (required): Search text (works in Chinese and English)
- `max_results`: 1-20 (default 5)
- `tiers`: Which tiers to search (default: ["vector", "fact"])
- `categories`: Filter by category
- `min_importance`: Minimum importance level
- `token_budget`: Max tokens for results (default 8000)

### memory_recall — Session startup context

Call this at the start of each session to load relevant context:

```bash
curl -s http://localhost:18800/recall -H "Content-Type: application/json" -d '{
  "context": "brief description of current conversation topic"
}'
```

Returns user profile facts and relevant recent memories, budget-capped.

### fact_store — Save structured data

```bash
curl -s http://localhost:18800/facts -H "Content-Type: application/json" -d '{
  "domain": "preference",
  "key": "editor",
  "value": {"name": "vim", "theme": "dark"},
  "source": "user_stated"
}'
```

**Domains:** preference, contact, schedule, project, skill, health, finance, custom

### fact_query — Query structured data

```bash
curl -s "http://localhost:18800/facts?domain=preference"
curl -s "http://localhost:18800/facts?search=vim"
```

### file_store — Upload a file

```bash
curl -s http://localhost:18800/files/upload \
  -F "file=@/path/to/photo.jpg" \
  -F "description=Photo of the office setup" \
  -F "tags=office,setup"
```

### file_search — Find files

```bash
curl -s http://localhost:18800/files/search -H "Content-Type: application/json" -d '{
  "query": "office photo",
  "mime_type": "image/jpeg",
  "max_results": 5
}'
```

## Memory Decay

Memories decay over time based on category:
- conversation_highlight: 14 days half-life
- general: 30 days
- project: 45 days
- insight: 60 days
- decision: 90 days
- skill: 180 days

Higher importance and frequent access slow decay. Use importance 8-10 for permanent-ish memories.

## Session Workflow

1. **On session start**: Call `/recall` with conversation context
2. **During conversation**: Store important information as you learn it
3. **When user asks to remember**: Store with appropriate tier and importance
4. **When you need context**: Call `/search` with relevant query
