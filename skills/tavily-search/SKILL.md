---
name: tavily-search
description: 使用 Tavily API 搜索实时新闻和网页内容。用于 blog-fetcher 抓取真实新闻、验证文章内容、以及任何需要实时信息的场景。
metadata:
  {
    "openclaw": {
      "emoji": "🔍",
      "always": true
    }
  }
---

# Tavily Search Skill

实时搜索引擎，替代 RSS 作为 blog-fetcher 的主要新闻来源。5 个 API key 轮换使用。

## 获取 API Key（轮换）

```python
import json, urllib.request, random

facts = json.loads(urllib.request.urlopen('http://localhost:18800/facts').read())
keys = next(f['value'] for f in facts if f['key'] == 'tavily_api_keys')
if isinstance(keys, str):
    keys = json.loads(keys)
api_key = random.choice(keys)
```

## 基础搜索

```python
import json, urllib.request

def tavily_search(query, api_key, max_results=5, search_depth="advanced", topic="news", days=3):
    payload = json.dumps({
        "api_key": api_key,
        "query": query,
        "search_depth": search_depth,
        "topic": topic,
        "days": days,
        "max_results": max_results,
        "include_answer": False,
        "include_raw_content": False,
        "include_images": False
    }).encode()
    req = urllib.request.Request(
        "https://api.tavily.com/search",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read())
```

返回结构：
```json
{
  "results": [
    {
      "title": "...",
      "url": "...",
      "content": "...(snippet)...",
      "score": 0.95,
      "published_date": "2026-03-31"
    }
  ]
}
```

## Blog Fetcher 推荐查询列表

每日抓取时按类别搜索：

```python
QUERIES = [
    # industry - 通用 AI 行业
    ("latest AI news today site:techcrunch.com OR site:venturebeat.com OR site:theverge.com", "industry"),
    ("Anthropic Claude OR OpenAI GPT OR Google Gemini news this week", "industry"),
    # models - 新模型发布
    ("new AI model released 2026 open source LLM", "models"),
    ("HuggingFace trending model release this week", "models"),
    # tools - 开发工具
    ("OpenClaw AI assistant news", "openclaw"),
    ("Claude MCP tool agent framework GitHub 2026", "tools"),
    # healthtech - 医疗医美
    ("AI healthcare medical aesthetics skincare diagnosis 2026", "healthtech"),
    ("AI telehealth digital health funding 2026", "healthtech"),
    # edtech - 教育
    ("AI education tutoring students learning 2026", "edtech"),
    ("AI coding education AP CS programming students", "edtech"),
]
```

## 使用规则

1. **轮换 key**：每次搜索随机选一个 key，不要固定用第一个
2. **429 处理**：遇到 429 换下一个 key 重试，最多换 3 次
3. **结合 web_fetch**：搜到好标题后，用 web_fetch 读原文，**不要凭记忆补内容**
4. **去重**：同一 URL 不重复发布（查 blog_posts.source_url）

## 完整 Blog Fetch 流程

```python
# 1. 轮换获取 key
api_key = random.choice(keys)

# 2. 按类别搜索
results = tavily_search("AI healthcare AI diagnosis 2026", api_key, topic="news", days=3)

# 3. 取 score 最高的结果
best = max(results["results"], key=lambda x: x.get("score", 0))

# 4. web_fetch 读原文（用Your Agent的 web_fetch 工具）
# 然后基于原文内容写文章，不自己补

# 5. 发布到 blog API
```

## 429 轮换逻辑

```python
def tavily_search_with_fallback(query, keys, **kwargs):
    random.shuffle(keys_copy := keys[:])
    for key in keys_copy:
        try:
            return tavily_search(query, key, **kwargs)
        except urllib.error.HTTPError as e:
            if e.code == 429:
                continue
            raise
    raise Exception("All Tavily keys exhausted")
```
