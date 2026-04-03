---
name: self-improvement
description: 自学习系统 — 错误自动记录、纠正学习、热知识缓存、模式自动升级
metadata:
  {
    "openclaw": {
      "emoji": "🧬",
      "always": true
    }
  }
---

# Self-Improvement Skill

三层认知模型：下意识(0ms) → 热知识(5ms) → 冷知识(200ms)

## 热知识查询 (先查这个!)

```bash
# 快速查询——命中返回缓存答案，未命中返回 null
curl -s "http://localhost:18800/hot?q=你的问题"
```

被问 3 次以上的问题自动升温为热知识，下次直接从 Redis 返回。

## 记录学习

### 自动触发（你应该主动记录）

| 场景 | type | 操作 |
|------|------|------|
| 命令失败 | error | 立即记录 |
| 用户说"不对/错了/Actually" | correction | 立即记录 |
| 发现更好方法 | best_practice | 记录 |
| 知识过时 | knowledge_gap | 记录 |

```bash
curl -s -X POST http://localhost:18800/learnings \
  -H "Content-Type: application/json" \
  -d '{
    "type": "error",
    "summary": "简短描述",
    "details": "详细上下文",
    "area": "infra",
    "priority": "high",
    "pattern_key": "unique-pattern-id",
    "tags": ["tag1", "tag2"]
  }'
```

- `type`: error | correction | knowledge_gap | best_practice
- `area`: frontend | backend | infra | config | docs
- `priority`: low | medium | high | critical
- `pattern_key`: 用于去重——相同 pattern_key 会增加 recurrence 计数而不是创建新记录

## 查看/管理学习

```bash
# 查看待处理的错误
curl -s "http://localhost:18800/learnings?type=error&status=pending"

# 查看所有待处理
curl -s "http://localhost:18800/learnings?status=pending"

# 标记已解决
curl -s -X POST http://localhost:18800/learnings/<id>/resolve
```

## 模式升级

重复出现 3 次的问题自动升级：

```bash
# 手动触发升级检查
curl -s -X POST http://localhost:18800/maintenance/promote-learnings
```

升级目标：
- `error + infra` → your-website Skill 常见问题
- `best_practice` → AGENTS.md Rules
- `correction` → SOUL.md 行为指南

每日 7AM 自动运行升级检查（cron）。

## 规则

1. **命令失败** → 立即 `POST /learnings` (type=error)，用有意义的 pattern_key
2. **用户纠正** → 立即 `POST /learnings` (type=correction)
3. **重复问题** → 先 `GET /hot?q=xxx`，命中直接回答
4. **发现捷径** → `POST /learnings` (type=best_practice)
5. **每次任务完成后** → 评估是否有值得记录的学习
