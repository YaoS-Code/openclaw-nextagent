---
name: web-search
description: Tavily Web Search — 联网搜索能力，支持多 API Key 轮转，限额自动切换
metadata:
  {
    "openclaw": {
      "emoji": "🔍",
      "always": true
    }
  }
---

# Web Search Skill (Tavily)

联网搜索能力。使用 Tavily Search API，支持 8 个 API Key 自动轮转。

## 使用方法

```bash
~/openclaw-services/tools/tavily-search.sh "搜索内容"
```

或直接 curl:

```bash
source ~/openclaw-services/tools/tavily-keys.sh
curl -s -X POST https://api.tavily.com/search \
  -H "Content-Type: application/json" \
  -d "{\"api_key\": \"$TAVILY_KEY\", \"query\": \"your query\", \"max_results\": 5}"
```

## 触发条件

- 用户说"搜一下"、"查查"、"search"、"最新消息"
- 需要实时信息（新闻、价格、天气、最新版本等）
- blog-fetcher 需要补充信息时
- 任何需要联网获取最新数据的场景

## API 参数

```json
{
  "api_key": "tvly-dev-xxx",
  "query": "搜索词",
  "search_depth": "basic",
  "max_results": 5,
  "include_answer": true,
  "include_raw_content": false
}
```

- `search_depth`: "basic" (快) 或 "advanced" (深度，用 2x 额度)
- `max_results`: 1-10
- `include_answer`: true 返回 AI 摘要
- `include_raw_content`: true 返回完整网页内容（慎用，很大）

## Key 管理

8 个 API Key 存在 `~/openclaw-services/tools/tavily-keys.sh`，自动轮转。
每个 key 每月 1000 次免费搜索。总共 8000 次/月。

如果返回 429 (rate limited) 或 401 (key exhausted)，自动切换下一个 key。

## 与 Blog Fetcher 集成

blog-fetcher 可以用 Tavily 搜索补充 RSS 没覆盖的来源：

```bash
# 搜索最新 AI 新闻
~/openclaw-services/tools/tavily-search.sh "latest AI model releases this week" | python3 -m json.tool
```
