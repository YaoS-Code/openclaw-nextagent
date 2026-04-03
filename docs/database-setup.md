# Database Setup: SQLite → PostgreSQL 17 + pgvector

Official OpenClaw uses SQLite. This setup replaces it with PostgreSQL 17 for persistent vector memory and business data.

## Architecture

```
PostgreSQL: openclaw_club (single database, multiple schemas)
├── public.*           — Business tables (blog, courses, users)
├── memory.*           — Vector memories + structured facts (from schema.sql)
├── skill_reminder.*   — Reminders + iCal calendar subscriptions
└── skill_task.*       — Async task queue
```

## Installation

```bash
# Ubuntu 24.04
sudo apt install -y postgresql-17 postgresql-17-pgvector

# Create DB and user
sudo -u postgres psql -c "CREATE USER oc_admin WITH PASSWORD 'yourpassword';"
sudo -u postgres psql -c "CREATE DATABASE openclaw_club OWNER oc_admin;"

# Enable pgvector
psql -h 127.0.0.1 -U oc_admin -d openclaw_club -c "CREATE EXTENSION IF NOT EXISTS vector;"

# Create memory schema (all memory-related tables)
psql -h 127.0.0.1 -U oc_admin -d openclaw_club -f sql/memory_schema.sql

# Create blog schema (optional, if using blog system)
psql -h 127.0.0.1 -U oc_admin -d openclaw_club -f sql/blog_schema.sql
```

## Environment Config

```env
DATABASE_URL=postgresql://oc_admin:yourpassword@127.0.0.1:5432/openclaw_club
REDIS_URL=redis://localhost:6379/0
```

## systemd ordering

Ensure all services have `After=postgresql.service` in their `[Unit]` section.

## Backup

```bash
# Daily backup at 3AM
0 3 * * * pg_dump -h 127.0.0.1 -U oc_admin openclaw_club | gzip > ~/backups/$(date +%Y%m%d).sql.gz
```
