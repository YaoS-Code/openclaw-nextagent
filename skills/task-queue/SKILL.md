---
name: task-queue
description: Submit complex or long-running tasks to Claude Code in background. Notify on completion via Discord.
metadata:
  {
    "openclaw": {
      "emoji": "⚡",
      "always": true
    }
  }
---

# Async Task Queue

For tasks that are **complex** (multi-step, multi-file, need analysis) or **slow** (>10s), delegate to Claude Code in background.

## When to Use

- **Multi-step tasks**: search + analyze + write to Sheet/file
- **Code tasks**: website changes, refactoring, bug fixes, PR reviews
- **Heavy operations**: builds, deployments, data processing
- **Anything you can't do in 1-2 tool calls**

## Submit Task

```bash
curl -s http://localhost:18800/tasks -H "Content-Type: application/json" -d '{
  "title": "DESCRIPTION",
  "command": "SHELL COMMAND",
  "notify": true
}'
```

## Common Patterns

### Delegate to Claude Code (most common)
```bash
curl -s http://localhost:18800/tasks -H "Content-Type: application/json" -d '{
  "title": "TASK DESCRIPTION",
  "command": "cd /home/jaadmin/WORKDIR && claude --permission-mode bypassPermissions --print \"DETAILED TASK PROMPT\"",
  "notify": true
}'
```

### Search + Write to Google Sheet (compound task)
```bash
curl -s http://localhost:18800/tasks -H "Content-Type: application/json" -d '{
  "title": "Research X and export to Sheet",
  "command": "claude --permission-mode bypassPermissions --print \"Search for X, organize findings as JSON rows, then call: curl -s http://localhost:18800/sheets/create -H Content-Type:application/json -d with title and rows array. Return the Sheet URL.\"",
  "notify": true
}'
```

### Website changes
```bash
curl -s http://localhost:18800/tasks -H "Content-Type: application/json" -d '{
  "title": "Fix/add feature on ja-website",
  "command": "cd /home/jaadmin/ja-website && claude --permission-mode bypassPermissions --print \"TASK. Read Documentation/BACKEND.md for API spec. Read packages/database/prisma/schema.prisma for DB schema.\"",
  "notify": true
}'
```

### Deploy
```bash
curl -s http://localhost:18800/tasks -H "Content-Type: application/json" -d '{
  "title": "Rebuild and restart website",
  "command": "cd /home/jaadmin/ja-website/deploy && docker compose -f docker-compose.prod.yml build ja-api ja-web && docker compose -f docker-compose.prod.yml restart ja-api ja-web",
  "notify": true
}'
```

## Check Status

```bash
curl -s http://localhost:18800/tasks
curl -s http://localhost:18800/tasks/TASK_ID
```

## Multi-Phase Project Tasks (session_id)

For projects where multiple background tasks share context (e.g. deploy → migrate → restart),
use the same `session_id` so Claude Code remembers what it already did:

```bash
# Phase 1: build
curl -s http://localhost:18800/tasks -H "Content-Type: application/json" -d '{
  "title": "Build project X",
  "command": "cd /home/jaadmin/projects/x && claude --permission-mode bypassPermissions --print \"Build the project\"",
  "session_id": "oc-dev-x-a1b2c3d4",
  "notify": true
}'

# Phase 2 (after phase 1 completes): same session_id — Claude Code remembers the build
curl -s http://localhost:18800/tasks -H "Content-Type: application/json" -d '{
  "title": "Run migrations for project X",
  "command": "cd /home/jaadmin/projects/x && claude --permission-mode bypassPermissions --print \"Run the DB migrations\"",
  "session_id": "oc-dev-x-a1b2c3d4",
  "notify": true
}'
```

The `session_id` is automatically injected before `--permission-mode` in the command.
Use format `oc-dev-{project}-{8-char-id}` for easy identification.

## After Submitting

Say "已提交后台任务，完成后会通知你" then continue chatting normally. **Never wait for task completion.**
