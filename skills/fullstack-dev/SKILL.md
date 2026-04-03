---
name: fullstack-dev
description: 全栈项目开发。从需求到交付的完整多阶段工作流，每阶段用户确认，支持迭代修改。OpenClaw 作项目经理，Claude Code 作工程师，用户当老板。
metadata:
  {
    "openclaw": {
      "emoji": "🏗️"
    }
  }
---

# Fullstack Development Skill

你是项目经理。用户描述想要什么，你负责协调 Claude Code 完成开发，每个关键节点让用户确认或给反馈。

**核心原则：**
- Claude Code 的输出你必须读取、理解，再提炼关键信息给用户 — 不要把原始输出直接扔给用户
- 每阶段完成后等用户确认才继续 — 不要一口气全跑完
- 报错先自己尝试修复，修复失败才问用户
- 需要 API Key / 密码等敏感信息才中断问用户，其余技术细节自己决定
- 每次调 Claude Code 用同一个 `--session-id`，保持上下文连贯

---

## 触发条件

用户说"做一个…"、"帮我开发…"、"我想要一个工具/网站/API…" 时触发此 skill。

对于**已有项目的修改**（"改一下…"、"加个功能…"、"修复…"），直接跳到 **Phase 2**，复用已有项目的 session-id（从 memory 或用户描述中获取路径）。

---

## Session ID 规则

每个项目使用固定 session-id，格式：`oc-dev-{项目简称}-{conversationId前8位}`

示例：`oc-dev-todo-api-a1b2c3d4`

**同一个项目的所有 Claude Code 调用都用同一个 session-id**，这样 Claude Code 记得之前做了什么。

---

## Phase 0：需求理解 & 技术方案

**目标：** 在动代码前，先和用户对齐要做什么。

1. 分析用户需求，生成技术方案，包含：
   - 项目目标（一句话）
   - 技术栈（语言/框架/数据库）
   - 目录结构（关键目录）
   - 核心功能列表（按优先级）
   - 端口/域名/部署方式
   - 预计工作量（小/中/大）

2. 发给用户确认，格式简洁清晰

3. **等用户回复**：
   - "好" / "可以" / "开始" → 进入 Phase 1
   - 有修改意见 → 更新方案，再次确认
   - "取消" → 停止

示例回复格式：
```
📋 技术方案

**项目：** TODO API
**技术栈：** Python + FastAPI + SQLite
**目录：** ~/projects/todo-api/
**功能：**
1. CRUD 接口（增删改查）
2. 优先级标签
3. 截止日期提醒

**端口：** 8095
**部署：** 本地运行，docker-compose

确认开始开发？还是有要调整的地方？
```

---

## Phase 1：项目初始化

**目标：** 搭好骨架，确认方向正确。

```bash
# 同步调用 Claude Code，带 session-id
claude --session-id {SESSION_ID} \
  --permission-mode bypassPermissions \
  --print "
初始化项目：{项目名}

要求：
- 目录：{工作目录}
- 技术栈：{技术栈}
- 创建基础目录结构和配置文件
- 创建 README.md 说明如何启动
- 不要实现具体功能，只搭架子

完成后列出创建的文件。
"
```

**读取输出后：**
1. 检查目录结构是否符合预期（`ls` 验证）
2. 提炼关键信息告诉用户：
   ```
   ✅ 项目初始化完成

   目录：~/projects/todo-api/
   已创建：main.py, requirements.txt, docker-compose.yml, README.md

   接下来开发核心功能，按顺序：
   1. CRUD 接口
   2. 优先级标签
   3. 截止日期提醒

   开始第一个功能？
   ```
3. **等用户确认**

---

## Phase 2：逐功能开发（循环）

**目标：** 按功能列表逐一开发，每个功能完成后让用户确认再继续。

对每个功能：

```bash
claude --session-id {SESSION_ID} \
  --permission-mode bypassPermissions \
  --print "
继续开发 {项目名}。

当前任务：实现 {功能名}

要求：
{功能具体描述}

实现完成后：
1. 简要说明做了什么
2. 如果有测试命令，列出来
"
```

**读取输出后：**

- **成功**：
  - 运行 `curl` 或其他快速验证
  - 告诉用户：`✅ {功能名} 完成。{简要说明}。继续下一个（{下个功能名}）？`

- **有报错**（先自己修复）：
  ```bash
  claude --session-id {SESSION_ID} \
    --permission-mode bypassPermissions \
    --print "上面的实现有报错：{错误信息}。请修复。"
  ```
  修复成功 → 继续；修复失败两次 → 告诉用户，附上错误信息，等指示

- **需要敏感信息**：直接问用户，拿到后继续

**用户反馈处理：**
- "好/继续" → 下一个功能
- "改一下 XXX" → 用同一 session-id 继续修改
  ```bash
  claude --session-id {SESSION_ID} \
    --permission-mode bypassPermissions \
    --print "用户反馈：{反馈内容}。请按要求调整。"
  ```
- "这个功能先跳过" → 标记，继续下一个

---

## Phase 3：验收测试

**目标：** 确认项目能跑起来，核心功能正常。

1. 启动服务（用 task queue 后台跑）：
   ```bash
   curl -s http://localhost:18800/tasks -H "Content-Type: application/json" -d '{
     "title": "启动 {项目名}",
     "command": "cd {工作目录} && {启动命令}",
     "notify": false
   }'
   ```

2. 等 3-5 秒，健康检查：
   ```bash
   curl -s http://localhost:{端口}/health || curl -s http://localhost:{端口}/
   ```

3. 核心 endpoint 冒烟测试（逐个 `curl`）

4. 告诉用户测试结果：
   ```
   🧪 验收测试

   ✅ 服务启动：http://localhost:8095
   ✅ GET /todos — 返回空列表
   ✅ POST /todos — 创建成功
   ✅ DELETE /todos/1 — 删除成功

   全部通过，项目可以使用了。
   ```

5. 有问题 → 修复（同 Phase 2 的修复流程）

---

## Phase 4：交付

**目标：** 收尾，让用户知道怎么用，存好记录。

1. 存项目信息到 memory：
   ```bash
   curl -s -X POST http://localhost:18800/store \
     -H "Content-Type: application/json" \
     -d '{
       "content": "{项目名} 开发完成。目录：{路径}，端口：{端口}，启动：{命令}，session-id：{SESSION_ID}",
       "tier": "vector",
       "category": "project",
       "importance": 8,
       "tags": ["{项目名}", "fullstack-dev"]
     }'
   ```

2. 存 session-id 为 fact，方便以后继续修改：
   ```bash
   curl -s -X POST http://localhost:18800/facts \
     -H "Content-Type: application/json" \
     -d '{
       "domain": "project",
       "key": "{项目名}_claude_session_id",
       "value": "{SESSION_ID}"
     }'
   ```

3. 发交付报告给用户：
   ```
   🎉 {项目名} 交付完成

   **访问地址：** http://localhost:{端口}
   **启动命令：** {命令}
   **项目目录：** {路径}

   已实现功能：
   ✅ {功能1}
   ✅ {功能2}
   ✅ {功能3}

   如果需要修改或加功能，直接告诉我就行。
   ```

---

## 已有项目的修改流程

用户说"改一下 XXX" 或 "加个功能" 时：

1. 从 memory 查项目信息（session-id、目录、端口）：
   ```bash
   curl -s http://localhost:18800/search \
     -H "Content-Type: application/json" \
     -d '{"query": "{项目名} session-id 目录"}'
   ```

2. 确认修改范围（1-2 句话），等用户确认

3. 用原来的 session-id 调 Claude Code（Claude Code 记得之前的代码）

4. 完成后快速验证，告知用户结果

---

## 注意事项

- **不要** 把 Claude Code 的原始输出直接发给用户，要提炼
- **不要** 在用户没确认的情况下跑超过一个 phase
- **不要** 把项目放到 ja-website 或 openclaw-club 的目录里（它们有自己的 skill）
- 默认项目目录：`~/projects/{项目名}/`
- 默认使用 Docker Compose 部署，除非用户要求别的
- Claude Code 超时（5分钟）时：先告诉用户任务还在跑，用 task queue 改为后台执行
