---
name: blog-fetcher
description: 每日自动抓取 AI 新闻，生成中英文博客文章并发布到 Your Blog。Your Agent自己用 Claude 写文章。
metadata:
  {
    "openclaw": {
      "emoji": "📡",
      "always": true
    }
  }
---

# Blog Auto-Fetcher Skill

每日从多个来源抓取 AI 新闻，**你（Your Agent）直接用 Claude 写文章**，发布到 Your Blog。

## 触发条件

- 定时触发（cron 每日 6AM Vancouver）
- the operator说"抓新闻"、"更新blog"、"fetch news"

## 数据来源

**主来源：Tavily 实时搜索（优先）**
见 `skills/tavily-search/SKILL.md`，按类别搜索，内容实时、准确。

**备用来源：RSS（Tavily 失败时 fallback）**

| # | 来源 | 类型 | 分类 | 垂直领域 |
|---|------|------|------|----------|
| 1 | TechCrunch AI | RSS | industry | 综合科技 |
| 2 | The Verge AI | RSS | industry | 综合科技 |
| 3 | VentureBeat AI | RSS | industry | 综合科技 |
| 4 | Wired AI（主feed+AI过滤） | RSS | industry | 综合科技 |
| 5 | GitHub Trending (AI) | API | tools | 开发工具 |
| 6 | HuggingFace Trending | API | models | 模型 |
| 7 | MobiHealthNews | RSS | healthtech | 医疗/医美 |
| 8 | Healthcare IT News | RSS | healthtech | 医疗/医美 |
| 9 | EdSurge | RSS | edtech | 教育 |
| 10 | eLearning Industry | RSS | edtech | 教育 |

## 执行流程

### Step 1: 用 Tavily 搜索实时新闻（主流程）

```bash
~/openclaw-memory-service/venv/bin/python3 /tmp/blog_fetch.py
```

脚本会按 industry/openclaw/models/healthtech/edtech/tools 六个类别搜索，结果存入 `/tmp/blog-raw-new.json`。

**重要：搜到标题后必须用 web_fetch 读原文，禁止凭记忆写内容。**

### Step 1b: RSS Fallback（仅 Tavily 全部失败时）

```bash
cd ~/openclaw-services/blog_fetcher && ~/openclaw-memory-service/venv/bin/python3 -c "
import feedparser, json, re, urllib.request

results = []

# RSS feeds
for url, source, cat in [
    ('https://techcrunch.com/category/artificial-intelligence/feed/', 'TechCrunch', 'industry'),
    ('https://www.theverge.com/rss/ai-artificial-intelligence/index.xml', 'The Verge', 'industry'),
    ('https://venturebeat.com/category/ai/feed/', 'VentureBeat', 'industry'),
    ('https://www.wired.com/feed/rss', 'Wired', 'industry'),  # 全量 RSS，需过滤 AI 关键词
    # 医疗/医美
    ('https://www.mobihealthnews.com/rss.xml', 'MobiHealthNews', 'healthtech'),
    ('https://www.healthcareitnews.com/rss/all', 'Healthcare IT News', 'healthtech'),
    # 教育
    ('https://edsurge.com/feed', 'EdSurge', 'edtech'),
    ('https://www.elearningindustry.com/feed', 'eLearning Industry', 'edtech'),
]:
    feed = feedparser.parse(url)
    for e in feed.entries[:3]:
        summary = re.sub(r'<[^>]+>', '', e.get('summary', ''))[:200]
        results.append({'title': e.title, 'summary': summary, 'link': e.link, 'source': source, 'category': cat})

# 过滤 Wired 全量 RSS，只保留含 AI 关键词的条目
AI_KEYWORDS = ['ai', 'artificial intelligence', 'machine learning', 'llm', 'chatgpt', 'claude', 'gemini', 'openai', 'robot', 'automation']
results = [r for r in results if r['source'] != 'Wired' or any(kw in (r['title'] + r['summary']).lower() for kw in AI_KEYWORDS)]

# GitHub trending AI repos
try:
    from datetime import datetime, timedelta, timezone
    since = (datetime.now(timezone.utc) - timedelta(days=7)).strftime('%Y-%m-%d')
    req = urllib.request.Request(f'https://api.github.com/search/repositories?q=stars:>100+topic:ai+pushed:>{since}&sort=stars&order=desc&per_page=3')
    req.add_header('Accept', 'application/vnd.github+json')
    with urllib.request.urlopen(req, timeout=15) as resp:
        for repo in json.loads(resp.read()).get('items', []):
            results.append({'title': repo['full_name'], 'summary': (repo.get('description') or '')[:200], 'link': repo['html_url'], 'source': 'GitHub', 'category': 'tools', 'stars': repo['stargazers_count']})
except: pass

print(json.dumps(results, indent=2, ensure_ascii=False))
"
```

### Step 2: 去重

对每条数据，检查 source_url 是否已存在：

```bash
psql -h 127.0.0.1 -U db_admin -d my_agent_db -t -c "SELECT count(*) FROM blog_posts WHERE source_url = '<link>';"
```

如果已存在，跳过。

### Step 3: 选文策略

**每天按类别各选 1 篇，共发 5-6 篇左右：**

| 类别 | 来源 | 优先级 |
|------|------|--------|
| industry | TechCrunch / The Verge / VentureBeat / Wired | 选最有观点价值的 1 篇 |
| models | HuggingFace / 技术博客 | 选最值得关注的新模型 1 篇 |
| tools | GitHub Trending / awesome-agent-skills | 选 1 篇，见下方规则 |
| openclaw | ClawHub / GitHub OpenClaw相关 | 有则优先，没有跳过 |
| healthtech | MobiHealthNews / Healthcare IT News | AI在医疗/医美应用，选 1 篇 |
| edtech | EdSurge / EdWeek | AI在教育应用，选 1 篇 |

**垂直行业选文重点（医疗/医美/教育）：**
- 医美/医疗：AI 皮肤诊断、AI 辅助手术、智能问诊、医美咨询机器人、医疗影像 AI
- 教育：AI 辅导、自适应学习、作业批改自动化、AP/IB AI 工具、编程教育 AI
- 优先选有实际产品落地或研究结论的，不选泛泛而谈的"AI将改变XX"

**GitHub/tools 选文规则（重要）：**
- 凡是与 **OpenClaw、Claude、Anthropic** 相关的 repo 或 skill，**优先选，可以额外多选 1 篇**
- 其次选近期 stars 增长快、有实际用途的项目
- 纯 star 数高但没新鲜内容的老项目（AutoGPT、n8n 等）跳过
- awesome-agent-skills 的 commit 除非有实质内容，否则跳过

**不选的情况：**
- 纯民调/调查数据，没有实际技术/产品内容（除非结论特别有洞见）
- 融资新闻但没有技术亮点
- 已有同类文章（同一周内发过类似话题）

### Step 3b: 你来写文章

**必须先 web_fetch 读原文**，禁止凭已有知识补充内容（特别是版本号、价格、数字类信息）。

对选中的每条新闻，你（Your Agent）自己写：
- 中文标题 + 英文标题
- 中文摘要 (50字) + 英文摘要
- 中文正文 (200-400字 Markdown 评论/解读) + 英文正文
- 分类: models / tools / automation / industry / openclaw / insights
- 标签: 3-5个

**质量要求：**
- 不照搬原文，要有自己的观点
- 标题要 SEO 友好（包含关键词）
- 中英文都要自然流畅
- 每篇 200-400 字，不要灌水

### Step 4: 发布

```bash
BOT_TOKEN=$(curl -s http://localhost:18800/facts | python3 -c "import json,sys;[print(f['value']) for f in json.load(sys.stdin) if f['key']=='my_agent_db_bot_token']" 2>/dev/null)

curl -s -X POST http://localhost:4001/api/bot/blog/posts \
  -H "Content-Type: application/json" \
  -H "X-Bot-Token: ${BOT_TOKEN}" \
  -d @/tmp/blog-post.json
```

文章 JSON 格式:
```json
{
  "title": "中文标题",
  "title_en": "English Title",
  "summary": "中文摘要",
  "summary_en": "English summary",
  "content_md": "# 正文\n\n...",
  "content_en_md": "# English\n\n...",
  "category": "industry",
  "tags": ["ai", "news"],
  "source_url": "https://原文链接",
  "source_name": "TechCrunch",
  "author": "Your Agent",
  "is_auto": true,
  "published": true
}
```

## 分类规则

| 关键词 | 分类 |
|--------|------|
| arxiv, paper, research, experiment | research |
| youtube, video, podcast, creator, bilibili | creators |
|--------|------|
| model, LLM, GPT, Claude, Gemini, Qwen | models |
| tool, MCP, skill, framework, GitHub | tools |
| automation, workflow, agent, 电商 | automation |
| funding, startup, policy, 融资 | industry |
| OpenClaw, ClawHub, skill registry | openclaw |
| YourPlatform, 实战, case study | insights |
| medical, health, clinic, skincare, aesthetic, 医美, 医疗, 皮肤 | healthtech |
| education, learning, student, tutor, school, AP, IB, 教育, 学习 | edtech |
