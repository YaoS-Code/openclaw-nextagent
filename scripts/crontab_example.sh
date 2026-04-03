#!/bin/bash
# Example crontab entries for YourPlatform OpenClaw setup
# Add to crontab with: crontab -e

# Blog auto-fetch + publish — 6AM Vancouver (13:00 UTC)
# 0 13 * * * cd ~/openclaw-services/blog_fetcher && python3 fetcher.py >> /tmp/blog-fetcher.log 2>&1 && python3 auto_publisher.py >> /tmp/blog-publisher.log 2>&1

# OpenClaw daily update analysis — 6:30AM Vancouver (13:30 UTC)
# 30 13 * * * cd ~/openclaw-services/blog_fetcher && python3 openclaw_blog_writer.py >> /tmp/openclaw-blog-writer.log 2>&1

# Self-improvement hot-knowledge promotion — 7AM Vancouver (14:00 UTC)
# 0 14 * * * curl -s -X POST http://localhost:18800/maintenance/promote-learnings >> /tmp/promote.log 2>&1

# Daily memory audit — 11PM UTC (4PM Vancouver)
# 0 23 * * * ~/.openclaw/workspace/scripts/daily_memory_audit.sh >> ~/.openclaw/workspace/logs/memory_audit.log 2>&1

# Memory maintenance (every 3 days) — archive + expire old memories
# 0 2 */3 * * curl -s -X POST http://localhost:18800/maintenance/archive && curl -s -X POST http://localhost:18800/maintenance/expire
