# Database Setup: SQLite → PostgreSQL 17 + pgvector

Official OpenClaw uses SQLite. This setup replaces it with PostgreSQL 17 for persistent vector memory and business data.

## Architecture

```
PostgreSQL: my_agent_db (single database, multiple schemas)
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
sudo -u postgres psql -c "CREATE USER db_admin WITH PASSWORD 'yourpassword';"
sudo -u postgres psql -c "CREATE DATABASE my_agent_db OWNER db_admin;"

# Enable pgvector
psql -h 127.0.0.1 -U db_admin -d my_agent_db -c "CREATE EXTENSION IF NOT EXISTS vector;"

# Create memory schema (all memory-related tables)
psql -h 127.0.0.1 -U db_admin -d my_agent_db -f sql/memory_schema.sql

# Create blog schema (optional, if using blog system)
psql -h 127.0.0.1 -U db_admin -d my_agent_db -f sql/blog_schema.sql
```

## Environment Config

```env
DATABASE_URL=postgresql://db_admin:yourpassword@127.0.0.1:5432/my_agent_db
REDIS_URL=redis://localhost:6379/0
```

## systemd ordering

Ensure all services have `After=postgresql.service` in their `[Unit]` section.

## Backup

```bash
# Daily backup at 3AM
0 3 * * * pg_dump -h 127.0.0.1 -U db_admin my_agent_db | gzip > ~/backups/$(date +%Y%m%d).sql.gz
```
