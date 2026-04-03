#!/usr/bin/env python3
"""
Blog Auto Publisher v4 — Reads fetcher output, generates articles via Anthropic SDK, publishes.
Runs after fetcher.py in cron: `fetcher.py && auto_publisher.py`
"""

import json
import os
import sys
import time
import re
import logging
import urllib.request
from datetime import datetime
from pathlib import Path

from dotenv import dotenv_values
import anthropic

# Load environment from openclaw-services/.env
_env = dotenv_values(Path(__file__).resolve().parent.parent / ".env")

def _get(key: str, fallback: str = "") -> str:
    return _env.get(key) or os.getenv(key, fallback)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
BOT_TOKEN = _get("BOT_TOKEN")
ANTHROPIC_API_KEY = _get("ANTHROPIC_API_KEY")

BLOG_API = "http://127.0.0.1:4001/api/bot/blog/posts"
FETCHER_OUTPUT = "/tmp/blog-raw-{date}.json"
MAX_ARTICLES = 6

CATEGORIES = [
    "industry", "research", "models", "tools",
    "creators", "automation", "openclaw", "healthtech", "edtech",
]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("auto_publisher")


# ---------------------------------------------------------------------------
# AI Content Generation via Anthropic SDK
# ---------------------------------------------------------------------------

ARTICLE_PROMPT_TEMPLATE = """你是凌骁，NexAgent AI Blog 的主笔。根据以下新闻信息，写一篇中英双语博客文章。

原文信息：
标题：{title}
摘要：{summary}
来源：{source}
分类：{category}
URL：{url}

要求：
- 不照搬原文，要有自己的观点和解读
- 中文正文 200-400 字，Markdown 格式
- 英文正文 150-300 词，Markdown 格式
- 标题要 SEO 友好（含关键词）
- 标签 3-5 个（英文小写，连字符分隔）

直接输出一个 JSON 对象，不要任何前言、解释或代码块，格式：
{{"title":"中文标题","title_en":"English Title","summary":"中文摘要50字以内","summary_en":"English summary","content_md":"# 中文正文\\n\\n...","content_en_md":"# English\\n\\n...","tags":["tag1","tag2"]}}"""


def generate_article(client: anthropic.Anthropic, item: dict, max_retries: int = 3) -> dict | None:
    """Generate article using Anthropic SDK with retry logic."""
    prompt = ARTICLE_PROMPT_TEMPLATE.format(
        title=item.get("title", ""),
        summary=item.get("summary", "")[:300],
        source=item.get("source", ""),
        category=item.get("category", ""),
        url=item.get("link", ""),
    )

    for attempt in range(max_retries):
        try:
            message = client.messages.create(
                model="claude-haiku-4-5",
                max_tokens=2048,
                messages=[{"role": "user", "content": prompt}]
            )
            text = message.content[0].text.strip()
            # Strip markdown fences if present
            text = re.sub(r"^```json\s*", "", text)
            text = re.sub(r"\s*```$", "", text.strip())
            # Extract JSON object
            m = re.search(r'\{.*\}', text, re.DOTALL)
            if m:
                text = m.group(0)
            return json.loads(text)

        except anthropic.RateLimitError:
            wait = 60 * (attempt + 1)
            log.warning("Rate limited, waiting %ds (attempt %d/%d)", wait, attempt + 1, max_retries)
            time.sleep(wait)
        except anthropic.APIError as e:
            log.warning("API error (attempt %d/%d): %s", attempt + 1, max_retries, e)
            time.sleep(10)
        except json.JSONDecodeError as e:
            log.warning("JSON parse error: %s", e)
            return None
        except Exception as e:
            log.warning("Generation failed: %s", e)
            return None

    log.error("Exhausted retries for: %s", item.get("title", "?"))
    return None


# ---------------------------------------------------------------------------
# Article Selection
# ---------------------------------------------------------------------------

def select_articles(items: list[dict], max_count: int = MAX_ARTICLES) -> list[dict]:
    """Select best articles, 1 per category, priority order."""
    by_cat: dict[str, list[dict]] = {}
    for item in items:
        cat = item.get("category", "industry")
        by_cat.setdefault(cat, []).append(item)

    selected = []
    priority = ["models", "tools", "openclaw", "healthtech", "edtech", "industry", "research"]
    remaining = [c for c in CATEGORIES if c not in priority]

    for cat in priority + remaining:
        if len(selected) >= max_count:
            break
        candidates = by_cat.get(cat, [])
        if candidates:
            selected.append(candidates[0])

    # Fill up to max from remaining
    if len(selected) < max_count:
        for cat in sorted(by_cat.keys(), key=lambda c: len(by_cat[c]), reverse=True):
            for item in by_cat[cat][1:]:
                if len(selected) >= max_count:
                    break
                if item not in selected:
                    selected.append(item)
                    break

    return selected


# ---------------------------------------------------------------------------
# Publishing
# ---------------------------------------------------------------------------

def publish_article(article_data: dict, source_item: dict) -> dict | None:
    """Publish a generated article to the blog API."""
    payload = {
        "title": article_data.get("title", source_item.get("title", "")),
        "title_en": article_data.get("title_en", ""),
        "summary": article_data.get("summary", ""),
        "summary_en": article_data.get("summary_en", ""),
        "content_md": article_data.get("content_md", ""),
        "content_en_md": article_data.get("content_en_md", ""),
        "category": source_item.get("category", "industry"),
        "tags": article_data.get("tags", []),
        "source_url": source_item.get("link", ""),
        "source_name": source_item.get("source", ""),
        "author": "凌骁",
        "is_auto": True,
        "published": True,
    }

    try:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(
            BLOG_API,
            data=body,
            headers={
                "Content-Type": "application/json",
                "X-Bot-Token": BOT_TOKEN,
            },
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
            log.info("Published: [%s] %s (id=%s)", payload["category"], payload["title"], result.get("id"))
            return result
    except Exception as e:
        log.error("Failed to publish '%s': %s", payload["title"], e)
        return None


# ---------------------------------------------------------------------------
# DB dedup via API
# ---------------------------------------------------------------------------

def get_existing_urls() -> set:
    """Fetch all existing source_urls from blog API to deduplicate."""
    try:
        req = urllib.request.Request(f"{BLOG_API.replace('/bot/blog/posts', '/blog/posts')}?limit=200")
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        urls = {p["source_url"] for p in data.get("posts", []) if p.get("source_url")}
        log.info("Fetched %d existing source_urls from blog API", len(urls))
        return urls
    except Exception as e:
        log.warning("Could not fetch existing URLs: %s", e)
        return set()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    today = datetime.now().strftime("%Y%m%d")
    input_file = FETCHER_OUTPUT.format(date=today)

    if not os.path.exists(input_file):
        log.error("Fetcher output not found: %s", input_file)
        sys.exit(1)

    if not BOT_TOKEN:
        log.error("BOT_TOKEN not set in .env")
        sys.exit(1)

    if not ANTHROPIC_API_KEY:
        log.error("ANTHROPIC_API_KEY not set in .env")
        sys.exit(1)

    # Init Anthropic client
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    log.info("Anthropic SDK client ready (claude-haiku-4-5)")

    # Load fetcher data
    with open(input_file, encoding="utf-8") as f:
        raw_items = json.load(f)
    log.info("Loaded %d items from %s", len(raw_items), input_file)

    # Dedup against existing blog posts
    existing_urls = get_existing_urls()
    raw_items = [r for r in raw_items if r.get("link") not in existing_urls]
    log.info("After dedup: %d new items to consider", len(raw_items))

    if not raw_items:
        log.info("No new items to publish. Done.")
        return

    # Select best articles
    selected = select_articles(raw_items)
    log.info("Selected %d articles for publishing", len(selected))

    # Generate and publish
    stats = {"success": 0, "failed": 0, "categories": {}}

    for i, item in enumerate(selected, 1):
        cat = item.get("category", "industry")
        log.info("[%d/%d] Generating: %s (%s)", i, len(selected), item.get("title", "?")[:60], cat)

        article = generate_article(client, item)
        if article is None:
            log.error("AI generation failed for: %s", item.get("title", "?"))
            stats["failed"] += 1
            continue

        result = publish_article(article, item)
        if result:
            stats["success"] += 1
            stats["categories"][cat] = stats["categories"].get(cat, 0) + 1
        else:
            stats["failed"] += 1

        # Pause between API calls to avoid rate limits
        if i < len(selected):
            time.sleep(15)

    # Summary
    log.info("=" * 50)
    log.info("Auto-publish complete: %d success, %d failed", stats["success"], stats["failed"])
    for cat, count in stats["categories"].items():
        log.info("  %s: %d articles", cat, count)
    log.info("=" * 50)


if __name__ == "__main__":
    main()
