# Migration Guide: Official OpenClaw → YourPlatform Setup

See the [blog post](https://your-domain.com/blog) for the full illustrated guide.

## Overview

Official OpenClaw gives you a powerful agent framework with SQLite-backed session memory.
This setup adds:
1. Persistent memory via PostgreSQL + pgvector
2. Custom skill layers for your business
3. Persona definition (SOUL.md + IDENTITY.md)
4. Native systemd deployment (no Docker)

## Quick Steps

1. Install OpenClaw: `npm install -g openclaw && openclaw onboard`
2. Configure Discord channel
3. Set default model to Claude Sonnet (Anthropic API)
4. Set up PostgreSQL 17 + pgvector (see database-setup.md)
5. Deploy Memory Service (see agentic-memory repo)
6. Install custom skills: copy `skills/` to `~/.openclaw/workspace/skills/`
7. Create workspace files: copy `workspace/` templates to `~/.openclaw/workspace/`
8. Set up systemd services (see systemd/)
9. Configure crontab (see scripts/crontab_example.sh)

## Version Compatibility

| OpenClaw Version | Notes |
|---|---|
| v2026.4.x | Current, fully compatible |
| v2026.3.31 | Breaking: nodes.run removed, use exec host=node |
| v2026.3.22 | Breaking: Plugin SDK path changed to openclaw/plugin-sdk/* |

Full changelog and impact analysis: see your-domain.com blog.
