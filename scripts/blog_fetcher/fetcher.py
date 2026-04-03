"""Your Blog Raw Fetcher v3 — 24 sources across 9 categories."""

import feedparser
import json
import urllib.request
import urllib.error
import re
import os
import subprocess
from datetime import datetime, timedelta, timezone

TOOLS_DIR = os.path.expanduser('~/openclaw-services/tools')

# ── RSS Sources ───────────────────────────────────────────

RSS_SOURCES = [
    # (url, source_name, category, language, max_entries)
    # Industry News
    ('https://techcrunch.com/category/artificial-intelligence/feed/', 'TechCrunch', 'industry', 'en', 5),
    ('https://www.theverge.com/rss/ai-artificial-intelligence/index.xml', 'The Verge', 'industry', 'en', 5),
    ('https://venturebeat.com/category/ai/feed/', 'VentureBeat', 'industry', 'en', 3),
    # Research & Papers
    ('https://rss.arxiv.org/rss/cs.AI+cs.CL+cs.LG', 'ArXiv', 'research', 'en', 5),
    ('https://deepmind.google/blog/rss.xml', 'DeepMind', 'research', 'en', 2),
    ('https://importai.substack.com/feed', 'Import AI', 'research', 'en', 2),
    # Models (Lab Blogs)
    ('https://openai.com/blog/rss.xml', 'OpenAI Blog', 'models', 'en', 2),
    ('https://blog.google/technology/ai/rss/', 'Google AI Blog', 'models', 'en', 2),
    # Tools & Ecosystem
    ('https://www.latent.space/feed', 'Latent Space', 'tools', 'en', 2),
    ('https://www.producthunt.com/feed?category=ai', 'Product Hunt', 'tools', 'en', 3),
    # Chinese
    ('https://www.jiqizhixin.com/rss', '机器之心', 'industry', 'zh', 3),
]

# ── Reddit Sources ────────────────────────────────────────

REDDIT_SOURCES = [
    ('https://www.reddit.com/r/MachineLearning/top/.rss?t=day&limit=5', 'r/MachineLearning', 'research'),
    ('https://www.reddit.com/r/LocalLLaMA/top/.rss?t=day&limit=5', 'r/LocalLLaMA', 'models'),
]

# ── YouTube AI Creators ───────────────────────────────────

YOUTUBE_CHANNELS = [
    # (channel_id, creator_name)
    ('UChpleBmo18P08aKCIgti38g', 'Matt Wolfe'),
    ('UCsBjURrPoezykLs9EqgamOA', 'Fireship'),
    ('UCbfYPyITQ-7l4upoX8nvctg', 'Two Minute Papers'),
    ('UCZHmQk67mSJgfCCTn7xBfew', 'Yannic Kilcher'),
]

# ── Tavily Search Queries ─────────────────────────────────

TAVILY_QUERIES = [
    ('latest AI model releases open source 2026', 'models', 2),
    ('OpenClaw ClawHub new skills MCP agent', 'openclaw', 2),
    ('AI automation enterprise workflow tools', 'automation', 2),
    ('Claude Anthropic GPT OpenAI Gemini latest news', 'industry', 2),
    ('中国 AI 大模型 最新消息', 'industry', 2),
    ('AI quantitative trading Amazon automation', 'automation', 2),
]


# ── Helpers ───────────────────────────────────────────────

def tavily_search(query, max_results=3):
    """Search via Tavily with key rotation."""
    try:
        result = subprocess.run(
            [f'{TOOLS_DIR}/tavily-search.sh', query, str(max_results)],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            return json.loads(result.stdout)
        return None
    except Exception as ex:
        print(f'    Tavily error: {ex}')
        return None


def clean_html(text):
    """Strip HTML tags."""
    return re.sub(r'<[^>]+>', '', text).strip()


# ── Fetchers ──────────────────────────────────────────────

def fetch_rss():
    """Fetch from all RSS feeds."""
    print('\n--- RSS Feeds ---')
    results = []
    for url, source, cat, lang, limit in RSS_SOURCES:
        try:
            feed = feedparser.parse(url)
            count = min(len(feed.entries), limit)
            print(f'  {source}: {len(feed.entries)} entries, taking {count}')
            for e in feed.entries[:limit]:
                title = clean_html(e.get('title', ''))
                summary = clean_html(e.get('summary', e.get('description', '')))[:300]
                link = e.get('link', '')
                if title and link:
                    results.append({
                        'title': title,
                        'summary': summary,
                        'link': link,
                        'source': source,
                        'category': cat,
                        'language': lang,
                    })
        except Exception as ex:
            print(f'  {source}: ERROR {ex}')
    return results


def fetch_reddit():
    """Fetch top daily posts from AI subreddits."""
    print('\n--- Reddit ---')
    results = []
    for url, source, cat in REDDIT_SOURCES:
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'OpenClaw-BlogBot/1.0'})
            feed = feedparser.parse(urllib.request.urlopen(req, timeout=15).read())
            count = min(len(feed.entries), 5)
            print(f'  {source}: {len(feed.entries)} entries, taking {count}')
            for e in feed.entries[:5]:
                title = clean_html(e.get('title', ''))
                link = e.get('link', '')
                summary = clean_html(e.get('summary', ''))[:300]
                if title and link:
                    results.append({
                        'title': title,
                        'summary': summary,
                        'link': link,
                        'source': source,
                        'category': cat,
                    })
        except Exception as ex:
            print(f'  {source}: ERROR {ex}')
    return results


def fetch_youtube():
    """Fetch latest videos from AI YouTube creators."""
    print('\n--- YouTube Creators ---')
    results = []
    for channel_id, creator in YOUTUBE_CHANNELS:
        try:
            url = f'https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}'
            feed = feedparser.parse(url)
            # Only take videos from last 7 days
            cutoff = datetime.now(timezone.utc) - timedelta(days=7)
            recent = []
            for e in feed.entries[:3]:
                published = e.get('published_parsed')
                if published:
                    pub_dt = datetime(*published[:6], tzinfo=timezone.utc)
                    if pub_dt > cutoff:
                        recent.append(e)
            print(f'  {creator}: {len(recent)} new videos (last 7 days)')
            for e in recent[:2]:
                title = e.get('title', '')
                link = e.get('link', '')
                summary = e.get('summary', e.get('media_description', ''))
                if isinstance(summary, dict):
                    summary = summary.get('content', '')
                summary = clean_html(str(summary))[:300]
                if title and link:
                    results.append({
                        'title': f'{creator}: {title}',
                        'summary': summary,
                        'link': link,
                        'source': f'YouTube ({creator})',
                        'category': 'creators',
                    })
        except Exception as ex:
            print(f'  {creator}: ERROR {ex}')
    return results


def fetch_github_trending():
    """Fetch trending AI repos."""
    print('\n--- GitHub Trending ---')
    results = []
    try:
        since = (datetime.now(timezone.utc) - timedelta(days=7)).strftime('%Y-%m-%d')
        url = f'https://api.github.com/search/repositories?q=stars:>100+topic:ai+pushed:>{since}&sort=stars&order=desc&per_page=5'
        req = urllib.request.Request(url, headers={'Accept': 'application/vnd.github+json'})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
        for repo in data.get('items', [])[:3]:
            print(f'  {repo["full_name"]} ({repo["stargazers_count"]} stars)')
            results.append({
                'title': repo['full_name'],
                'summary': (repo.get('description') or '')[:300],
                'link': repo['html_url'],
                'source': 'GitHub',
                'category': 'tools',
                'stars': repo['stargazers_count'],
                'language': repo.get('language', ''),
            })
    except Exception as ex:
        print(f'  ERROR: {ex}')
    return results


def fetch_huggingface():
    """Fetch trending models."""
    print('\n--- HuggingFace Trending ---')
    results = []
    try:
        url = 'https://huggingface.co/api/trending'
        req = urllib.request.Request(url, headers={'Accept': 'application/json'})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
        items = data.get('recentlyTrending', data if isinstance(data, list) else [])
        for item in items[:3]:
            repo_id = item.get('repoData', {}).get('id', '') if isinstance(item, dict) else str(item)
            if repo_id:
                print(f'  {repo_id}')
                results.append({
                    'title': repo_id,
                    'summary': f'Trending model on HuggingFace: {repo_id}',
                    'link': f'https://huggingface.co/{repo_id}',
                    'source': 'HuggingFace',
                    'category': 'models',
                })
    except Exception as ex:
        print(f'  ERROR: {ex}')
    return results


def fetch_tavily():
    """Use Tavily web search for supplementary coverage."""
    print('\n--- Tavily Search ---')
    results = []
    for query, cat, limit in TAVILY_QUERIES:
        print(f'  "{query[:50]}..."')
        data = tavily_search(query, limit)
        if data and 'results' in data:
            for r in data['results'][:limit]:
                url = r.get('url', '')
                title = r.get('title', '')
                if title and url:
                    results.append({
                        'title': title,
                        'summary': r.get('content', '')[:300],
                        'link': url,
                        'source': 'Tavily Search',
                        'category': cat,
                        'tavily_answer': data.get('answer', ''),
                    })
    return results


# ── Dedup ─────────────────────────────────────────────────

def dedup_within_batch(results):
    """Remove duplicates within the batch by URL."""
    seen = set()
    unique = []
    for r in results:
        key = r.get('link', '')
        if key and key not in seen:
            seen.add(key)
            unique.append(r)
    dropped = len(results) - len(unique)
    if dropped:
        print(f'Batch dedup: removed {dropped} duplicates')
    return unique


def dedup_against_db(results):
    """Remove items already in the database."""
    try:
        import psycopg
        conn = psycopg.connect('postgresql://db_admin:YOUR_DB_PASSWORD@127.0.0.1:5432/my_agent_db')
        with conn.cursor() as cur:
            cur.execute('SELECT source_url FROM blog_posts WHERE source_url IS NOT NULL')
            existing = {row[0] for row in cur.fetchall()}
        conn.close()
        before = len(results)
        results = [r for r in results if r.get('link') and r['link'] not in existing]
        print(f'DB dedup: {before} -> {len(results)} ({before - len(results)} already exist)')
        return results
    except Exception as ex:
        print(f'DB dedup failed: {ex}')
        return results


# ── Main ──────────────────────────────────────────────────

if __name__ == '__main__':
    print(f'{"="*60}')
    print(f'Your Blog Raw Fetcher v3 — {datetime.now().isoformat()}')
    print(f'{"="*60}')

    all_items = []
    all_items.extend(fetch_rss())
    all_items.extend(fetch_reddit())
    all_items.extend(fetch_youtube())
    all_items.extend(fetch_github_trending())
    all_items.extend(fetch_huggingface())
    all_items.extend(fetch_tavily())

    print(f'\nTotal fetched: {len(all_items)}')

    all_items = dedup_within_batch(all_items)
    all_items = dedup_against_db(all_items)

    # Summary by category
    from collections import Counter
    cats = Counter(r['category'] for r in all_items)
    print(f'\nBy category:')
    for cat, count in cats.most_common():
        print(f'  {cat}: {count}')

    if all_items:
        outfile = f'/tmp/blog-raw-{datetime.now().strftime("%Y%m%d")}.json'
        with open(outfile, 'w') as f:
            json.dump(all_items, f, indent=2, ensure_ascii=False)
        print(f'\nSaved {len(all_items)} items to {outfile}')
        print('Ready for OpenClaw (Your Agent) to process and publish.')
    else:
        print('\nNo new items to process.')
