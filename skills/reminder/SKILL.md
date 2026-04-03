---
name: reminder
description: Create, manage, and deliver timed reminders. Subscribe to iCal calendar feeds.
metadata:
  {
    "openclaw": {
      "emoji": "⏰",
      "always": true
    }
  }
---

# Reminder & Calendar Skill

Manage reminders and calendar events via the memory service at `http://localhost:18800`.

## Creating Reminders

When the user asks to be reminded of something:

```bash
curl -s http://localhost:18800/reminders -H "Content-Type: application/json" -d '{
  "title": "TITLE",
  "remind_at": "ISO8601 DATETIME WITH TIMEZONE",
  "description": "optional details",
  "category": "general",
  "importance": 5,
  "repeat_rule": null
}'
```

**Fields:**
- `title` (required): What to remind about
- `remind_at` (required): ISO 8601 datetime with timezone, e.g. `2026-03-27T15:00:00+08:00`
- `description`: Additional details
- `category`: general, meeting, deadline, birthday, custom
- `importance`: 1-10 (default 5)
- `repeat_rule`: null (one-time), "daily", "weekly", "monthly", "yearly"
- `tags`: array of strings

**After creating a reminder, you MUST also create an OpenClaw cron job** to trigger at the reminder time. Use the cron tool to schedule delivery.

## Querying Reminders

```bash
# List active reminders
curl -s "http://localhost:18800/reminders?status=active"

# Upcoming reminders in next 48 hours
curl -s "http://localhost:18800/reminders/upcoming?hours=48"

# Get specific reminder
curl -s "http://localhost:18800/reminders/REMINDER_ID"

# Filter by category
curl -s "http://localhost:18800/reminders?category=meeting&status=active"
```

## Managing Reminders

```bash
# Snooze (delay 30 minutes)
curl -s -X POST "http://localhost:18800/reminders/REMINDER_ID/snooze" \
  -H "Content-Type: application/json" -d '{"minutes": 30}'

# Mark as completed
curl -s -X POST "http://localhost:18800/reminders/REMINDER_ID/complete"

# Cancel
curl -s -X DELETE "http://localhost:18800/reminders/REMINDER_ID"
```

## Calendar Feed Subscription

Subscribe to iCal/ICS feeds (Google Calendar, Outlook, etc.):

```bash
# Subscribe
curl -s http://localhost:18800/calendar/subscribe \
  -H "Content-Type: application/json" \
  -d '{"name": "Work Calendar", "url": "https://calendar.google.com/calendar/ical/...basic.ics"}'

# List subscriptions
curl -s http://localhost:18800/calendar/feeds

# Manual sync
curl -s -X POST http://localhost:18800/calendar/sync -H "Content-Type: application/json" -d '{}'

# Remove subscription
curl -s -X DELETE "http://localhost:18800/calendar/feeds/FEED_ID"
```

## Session Start

On each session start, check upcoming reminders:

```bash
curl -s "http://localhost:18800/reminders/upcoming?hours=24"
```

If there are upcoming reminders, mention them to the user.

## When a Cron Reminder Fires

When you receive a cron trigger for a reminder:
1. Read the reminder: `curl -s http://localhost:18800/reminders/REMINDER_ID`
2. Notify the user with the title and description
3. If one-time: `curl -s -X POST http://localhost:18800/reminders/REMINDER_ID/complete`
4. Ask if they want to snooze
