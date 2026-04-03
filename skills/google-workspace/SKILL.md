---
name: google-workspace
description: Access Gmail, Google Calendar, Drive, Sheets, Docs, Tasks via gws CLI and local API
metadata:
  {
    "openclaw": {
      "emoji": "📧",
      "always": true,
      "requires": { "bins": ["gws"] }
    }
  }
---

# Google Workspace

## Sheets — Create & Write (use local API, fastest)

```bash
# Create new sheet and write rows (one call does everything)
curl -s http://localhost:18800/sheets/create -H "Content-Type: application/json" -d '{
  "title": "Sheet Title",
  "rows": [["Header1","Header2","Header3"],["val1","val2","val3"],["val4","val5","val6"]]
}'
# Returns: {"sheet_id":"...", "url":"https://docs.google.com/...", "rows_written": N}

# Append rows to existing sheet
curl -s http://localhost:18800/sheets/append -H "Content-Type: application/json" -d '{
  "sheet_id": "SHEET_ID",
  "rows": [["new1","new2","new3"]]
}'
```

## Gmail

```bash
# List recent emails
gws gmail users messages list --params '{"userId":"me","maxResults":5}' 2>&1 | grep -v keyring

# Read email
gws gmail users messages get --params '{"userId":"me","id":"MSG_ID","format":"full"}' 2>&1 | grep -v keyring

# Send email
gws gmail +send --to "email@example.com" --subject "Subject" --body "Body text"

# Reply
gws gmail +reply --message-id "MSG_ID" --body "Reply text"
```

## Calendar (create events — for reading schedule use /reminders/today)

```bash
# Create event
gws calendar +insert --summary "Meeting" --start "2026-03-28T10:00:00" --end "2026-03-28T11:00:00"
```

## Drive

```bash
# List files
gws drive files list --params '{"pageSize":10}' 2>&1 | grep -v keyring

# Upload file
gws drive +upload --file "/path/to/file"
```

## Notes

- User email: songYOUR_USER499@gmail.com
- All gws commands: add `2>&1 | grep -v keyring` to suppress log noise
- For Sheets: always use the local API (`/sheets/create`, `/sheets/append`) — it's simpler and faster than gws CLI
