#!/usr/bin/env python3
"""
OpenClaw Daily Update Blog Writer
每天从 GitHub 抓取 OpenClaw 最新 releases 和 commits，
结合本地定制化配置，生成个性化升级分析文章，发布到 NexAgent Blog。
"""

import json
import os
import sys
import time
import re
import logging
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta
from pathlib import Path

from dotenv import dotenv_values
import anthropic

# ── Config ──────────────────────────────────────────────────────────────────

_env = dotenv_values(Path(__file__).resolve().parent.parent / ".env")

def _get(key, fallback=""):
    return _env.get(key) or os.getenv(key, fallback)

BOT_TOKEN       = _get("BOT_TOKEN")
ANTHROPIC_KEY   = _get("ANTHROPIC_API_KEY")
BLOG_API        = "http://127.0.0.1:4001/api/bot/blog/posts"
GITHUB_API      = "https://api.github.com"
REPO            = "openclaw/openclaw"
WORKSPACE       = Path.home() / ".openclaw/workspace"
SKILLS_DIR      = WORKSPACE / "skills"
STATE_FILE      = Path("/tmp/openclaw-blog-writer-state.json")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("openclaw_blog_writer")


# ── GitHub Helpers ───────────────────────────────────────────────────────────

def gh_get(path: str) -> dict | list | None:
    url = f"{GITHUB_API}/{path.lstrip('/')}"
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json", "User-Agent": "NexAgent-Blog/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())
    except Exception as e:
        log.warning("GitHub API error (%s): %s", url, e)
        return None


def get_latest_release() -> dict | None:
    """Get the latest release from openclaw/openclaw."""
    data = gh_get(f"repos/{REPO}/releases?per_page=3")
    if not data or not isinstance(data, list):
        return None
    return data[0] if data else None


def get_recent_commits(since_hours: int = 26) -> list[dict]:
    """Get commits from the last N hours."""
    since = (datetime.now(timezone.utc) - timedelta(hours=since_hours)).strftime("%Y-%m-%dT%H:%M:%SZ")
    data = gh_get(f"repos/{REPO}/commits?per_page=20&since={since}")
    if not data or not isinstance(data, list):
        return []
    return data


def get_all_releases(per_page: int = 5) -> list[dict]:
    data = gh_get(f"repos/{REPO}/releases?per_page={per_page}")
    return data if isinstance(data, list) else []


# ── Local Context ────────────────────────────────────────────────────────────

def get_local_context() -> str:
    """Collect our local OpenClaw customization context for the AI prompt."""
    ctx_parts = []

    # Current version
    try:
        import subprocess
        ver = subprocess.run(["openclaw", "--version"], capture_output=True, text=True, timeout=5)
        ctx_parts.append(f"当前版本: {ver.stdout.strip()}")
    except Exception:
        ctx_parts.append("当前版本: 未知")

    # Installed skills
    skills = sorted([d.name for d in SKILLS_DIR.iterdir() if d.is_dir()]) if SKILLS_DIR.exists() else []
    ctx_parts.append(f"已安装 Skills ({len(skills)}): {', '.join(skills)}")

    # AGENTS.md key sections (roles, rules)
    agents_path = WORKSPACE / "AGENTS.md"
    if agents_path.exists():
        content = agents_path.read_text()[:3000]
        ctx_parts.append(f"AGENTS.md (节选):\n{content}")

    # SOUL.md
    soul_path = WORKSPACE / "SOUL.md"
    if soul_path.exists():
        ctx_parts.append(f"SOUL.md:\n{soul_path.read_text()[:500]}")

    # Key environment / services
    ctx_parts.append("""服务架构:
- Next.js 前端 (PM2, port 3000)
- Flask 后端 (systemd oc-api, port 4001)
- PostgreSQL 17 + pgvector (原生 systemd)
- Memory Service FastAPI + bge-m3 (port 18800)
- Nginx + Cloudflare Tunnel
- 无 Docker（2026-04-02 全面迁移到原生部署）
- 频道: Discord DM + 群聊""")

    return "\n\n".join(ctx_parts)


# ── State: avoid publishing duplicate releases ───────────────────────────────

def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            pass
    return {"published_releases": [], "last_commit_sha": None}


def save_state(state: dict):
    STATE_FILE.write_text(json.dumps(state, indent=2))


# ── AI Article Generation ────────────────────────────────────────────────────

PROMPT_TEMPLATE = """你是凌骁，NexAgent AI Blog 主笔，同时也是宋老师 OpenClaw 实例的专属 AI 助手。

今天需要你写一篇 OpenClaw 版本更新博客，分析新版本对**我们这个特定配置**的实际影响。

## OpenClaw 最新更新信息

{update_info}

## 我们的本地定制化配置

{local_context}

## 写作要求

**中文版（300-500字）：**
- 概述本次更新的核心变化
- **重点分析哪些更新直接影响我们的配置**（逐条对应：哪个 skill 受影响？AGENTS.md 需要改什么？服务架构需要调整吗？）
- 如果某个变更与我们无关，直接说"对我们无影响"，不要水文
- 给出具体的升级建议和操作步骤（如果有）
- 语气：直接、专业，凌骁风格（不废话）

**英文版（200-350词）：**
- English equivalent, same focus on our specific setup impact
- Technical and concise

**标题：** 要体现版本号和核心亮点

输出纯 JSON，不要任何代码块包裹，格式：
{{"title":"中文标题","title_en":"English Title","summary":"中文摘要（50字内）","summary_en":"English summary","content_md":"# 中文正文\\n\\n...","content_en_md":"# English\\n\\n...","tags":["openclaw","update","版本更新"]}}"""


def generate_article(client: anthropic.Anthropic, update_info: str, local_context: str) -> dict | None:
    prompt = PROMPT_TEMPLATE.format(update_info=update_info, local_context=local_context)

    for attempt in range(3):
        try:
            msg = client.messages.create(
                model="claude-haiku-4-5",
                max_tokens=3000,
                messages=[{"role": "user", "content": prompt}],
            )
            text = msg.content[0].text.strip()
            text = re.sub(r"^```json\s*", "", text)
            text = re.sub(r"\s*```$", "", text.strip())
            m = re.search(r'\{.*\}', text, re.DOTALL)
            if m:
                text = m.group(0)
            return json.loads(text)
        except anthropic.RateLimitError:
            wait = 60 * (attempt + 1)
            log.warning("Rate limited, waiting %ds", wait)
            time.sleep(wait)
        except json.JSONDecodeError as e:
            log.warning("JSON parse error (attempt %d): %s", attempt + 1, e)
            if attempt == 2:
                return None
        except Exception as e:
            log.warning("Generation error (attempt %d): %s", attempt + 1, e)
            if attempt == 2:
                return None
        time.sleep(5)
    return None


# ── Publishing ───────────────────────────────────────────────────────────────

def publish(article: dict, source_url: str, tags_extra: list[str] = []) -> bool:
    tags = list(set(article.get("tags", []) + ["openclaw", "版本更新"] + tags_extra))
    payload = {
        "title":       article.get("title", "OpenClaw 更新"),
        "title_en":    article.get("title_en", "OpenClaw Update"),
        "summary":     article.get("summary", ""),
        "summary_en":  article.get("summary_en", ""),
        "content_md":  article.get("content_md", ""),
        "content_en_md": article.get("content_en_md", ""),
        "category":    "openclaw",
        "tags":        tags,
        "source_url":  source_url,
        "source_name": "OpenClaw GitHub",
        "author":      "NexAgent AI",
        "is_auto":     True,
        "published":   True,
    }
    try:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(
            BLOG_API, data=body,
            headers={"Content-Type": "application/json", "X-Bot-Token": BOT_TOKEN},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
            log.info("Published: %s (id=%s)", payload["title"], result.get("id"))
            return True
    except Exception as e:
        log.error("Publish failed: %s", e)
        return False


# ── Main ─────────────────────────────────────────────────────────────────────

def build_release_update_info(release: dict, commits: list[dict]) -> str:
    lines = []

    tag = release.get("tag_name", "unknown")
    name = release.get("name", tag)
    published = release.get("published_at", "")[:10]
    body = release.get("body", "").strip()

    lines.append(f"## Release: {name} ({tag})")
    lines.append(f"发布时间: {published}")
    lines.append(f"Release URL: {release.get('html_url', '')}")
    if body:
        lines.append(f"\n### Release Notes:\n{body[:2000]}")

    if commits:
        lines.append(f"\n### 最近 {len(commits)} 个 Commits:")
        for c in commits[:15]:
            sha = c.get("sha", "")[:7]
            msg = c.get("commit", {}).get("message", "").split("\n")[0][:100]
            date = c.get("commit", {}).get("author", {}).get("date", "")[:10]
            lines.append(f"- [{sha}] {date} {msg}")

    return "\n".join(lines)


def build_commits_only_update_info(commits: list[dict]) -> str:
    """When no new release, summarize daily commits."""
    lines = ["## 今日 OpenClaw 代码更新（无新 Release）"]
    lines.append(f"Commits 数量: {len(commits)}")
    for c in commits[:15]:
        sha = c.get("sha", "")[:7]
        msg = c.get("commit", {}).get("message", "").split("\n")[0][:100]
        date = c.get("commit", {}).get("author", {}).get("date", "")[:10]
        lines.append(f"- [{sha}] {date} {msg}")
    return "\n".join(lines)


def main():
    log.info("OpenClaw Blog Writer starting...")

    if not BOT_TOKEN or not ANTHROPIC_KEY:
        log.error("Missing BOT_TOKEN or ANTHROPIC_API_KEY")
        sys.exit(1)

    state = load_state()
    client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
    local_context = get_local_context()

    # Fetch latest release
    release = get_latest_release()
    commits = get_recent_commits(since_hours=26)

    log.info("Latest release: %s", release.get("tag_name") if release else "none")
    log.info("Recent commits: %d", len(commits))

    # Check if this release was already published
    published_releases = state.get("published_releases", [])
    last_commit_sha = state.get("last_commit_sha")

    has_new_release = release and release.get("tag_name") not in published_releases
    has_new_commits = commits and (not last_commit_sha or commits[0].get("sha") != last_commit_sha)

    if not has_new_release and not has_new_commits:
        log.info("No new updates since last run. Skipping.")
        return

    # Build update info
    if has_new_release:
        update_info = build_release_update_info(release, commits)
        source_url = release.get("html_url", f"https://github.com/{REPO}/releases")
        tag_extras = [release.get("tag_name", "")]
        log.info("Writing article for new release: %s", release.get("tag_name"))
    else:
        # Commits-only update — only write if >= 3 commits
        if len(commits) < 3:
            log.info("Only %d commits, too few for an article. Skipping.", len(commits))
            return
        update_info = build_commits_only_update_info(commits)
        source_url = f"https://github.com/{REPO}/commits"
        tag_extras = []
        log.info("Writing article for %d daily commits", len(commits))

    # Generate article
    log.info("Generating article via Claude...")
    article = generate_article(client, update_info, local_context)
    if not article:
        log.error("Article generation failed")
        sys.exit(1)

    # Publish
    ok = publish(article, source_url, tag_extras)
    if not ok:
        log.error("Publishing failed")
        sys.exit(1)

    # Update state
    if has_new_release:
        published_releases.append(release["tag_name"])
        # Keep only last 10
        state["published_releases"] = published_releases[-10:]
    if commits:
        state["last_commit_sha"] = commits[0].get("sha")
    save_state(state)

    log.info("Done. Article published successfully.")


if __name__ == "__main__":
    main()
