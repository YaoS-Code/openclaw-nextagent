---
name: blog-manager
description: NexAgent AI Blog 管理 — 创建/发布文章、触发自动抓取、审核草稿、语义搜索
metadata:
  {
    "openclaw": {
      "emoji": "📰",
      "always": true
    }
  }
---

# AI Blog 管理

> Blog 是 nextagent.ca 的子模块，前端在 `/zh/blog` 和 `/en/blog`。
> 整站架构见 `skills/nextagent-website/SKILL.md`。

API Base: `http://localhost:4001`
Bot Token: 同 openclaw_club_bot_token

## 分类

| Key | 名称 | 内容 |
|-----|------|------|
| models | AI 模型 | 开源/商业模型发布、论文 |
| tools | 工具生态 | MCP, GitHub 热门, 框架 |
| automation | AI 自动化 | 企业流程、电商、量化 |
| industry | 行业动态 | 北美/中国 AI、政策 |
| openclaw | OpenClaw | 更新、社区项目、Agent |
| insights | NexAgent 实战 | 宋老师经验分享、案例 |
| research | AI 研究 | ArXiv 论文、实验室博客、突破性发现 |
| creators | AI 创作者 | YouTube/Bilibili/Podcast 内容 |

## 文章管理

```bash
# 查看统计
curl -s http://localhost:4001/api/bot/blog/stats -H "X-Bot-Token: ${BOT_TOKEN}"

# 查看文章列表
curl -s http://localhost:4001/api/blog/posts
curl -s "http://localhost:4001/api/blog/posts?category=insights"

# 搜索 (keyword/semantic/hybrid)
curl -s "http://localhost:4001/api/blog/search?q=qwen&mode=hybrid"

# 创建文章 (宋老师手动)
curl -s -X POST http://localhost:4001/api/bot/blog/posts \
  -H "Content-Type: application/json" -H "X-Bot-Token: ${BOT_TOKEN}" \
  -d '{
    "title": "中文标题",
    "title_en": "English Title",
    "summary": "中文摘要",
    "summary_en": "English summary",
    "content_md": "# 正文 Markdown\n\n...",
    "content_en_md": "# English\n\n...",
    "category": "insights",
    "tags": ["claude", "automation"],
    "author": "Yao Song",
    "is_auto": false,
    "published": true
  }'

# 发布草稿
curl -s -X PUT http://localhost:4001/api/bot/blog/posts/<id> \
  -H "Content-Type: application/json" -H "X-Bot-Token: ${BOT_TOKEN}" \
  -d '{"published": true}'

# 删除
curl -s -X DELETE http://localhost:4001/api/bot/blog/posts/<id> -H "X-Bot-Token: ${BOT_TOKEN}"
```

## 自动抓取

```bash
# 手动触发一次
cd ~/openclaw-services/blog_fetcher && ~/openclaw-memory-service/venv/bin/python3 fetcher.py

# 查看抓取日志
tail -50 /tmp/blog-fetcher.log

# 定时任务 (已配置 cron: 每天 6AM Vancouver)
crontab -l | grep blog
```

数据来源: TechCrunch, The Verge, 机器之心, GitHub Trending, HuggingFace Trending, ClawHub (OpenClaw Skills), awesome-agent-skills (Claude Code)

自动文章默认 `published=false`（草稿），需要审核后发布。

## 宋老师发文流程

1. 宋老师口述或提供要点
2. 用 AI 扩写成中英文 Markdown
3. category=`insights`, author=`Yao Song`, is_auto=false
4. 直接 published=true
