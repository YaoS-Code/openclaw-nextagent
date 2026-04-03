---
name: github-contributor
description: GitHub 代码贡献能力。通过 token 认证进行 git 操作：clone、commit、push、创建分支。用于奉孝和庞统。
---

# GitHub Contributor

你通过 GitHub Personal Access Token 与项目仓库交互。Token 存放在 `~/.openclaw/` 的 `.env.*` 文件中。

## 项目 Token 映射

| 项目 | Token 环境变量 | .env 文件 | Repo |
|------|---------------|-----------|------|
| agentic-memory | `WOLONG_GITHUB_TOKEN` | `~/.openclaw/.env.wolong` | `YaoS-Code/agentic-memory` |
| openclaw-tutorials | `WOLONG_GITHUB_TOKEN` | `~/.openclaw/.env.wolong` | `YaoS-Code/openclaw-tutorials` |
| wolong-hall | `WOLONG_GITHUB_TOKEN` | `~/.openclaw/.env.wolong` | `YaoS-Code/wolong-hall` |
| secondhand-mvp | `SECONDHAND_GITHUB_TOKEN` | `~/.openclaw/.env.secondhand` | `YaoS-Code/secondhand-mvp` |
| tesla-accessories | `TESLA_GITHUB_TOKEN` | `~/.openclaw/.env.tesla` | `YaoS-Code/tesla-accessories` |

> **注意**: `WOLONG_GITHUB_TOKEN` 对 YaoS-Code 下所有 repo 有 admin 权限，可以用于任何项目。

## Git 操作模板

### Clone（首次）
```bash
# 先读取 token
source ~/.openclaw/.env.wolong  # 或 .env.secondhand
git clone https://x-access-token:$WOLONG_GITHUB_TOKEN@github.com/YaoS-Code/wolong-hall.git
```

### 日常操作
```bash
# 拉取最新
cd <project-dir> && git pull

# 创建功能分支
git checkout -b feat/<description>

# 提交
git add <files>
git commit -m "feat: <description>"

# 推送
source ~/.openclaw/.env.wolong  # 确保 token 可用
git push origin feat/<description>
```

### 创建 PR（通过 GitHub API）
```bash
source ~/.openclaw/.env.wolong
curl -X POST \
  -H "Authorization: Bearer $WOLONG_GITHUB_TOKEN" \
  -H "Accept: application/vnd.github+json" \
  https://api.github.com/repos/YaoS-Code/wolong-hall/pulls \
  -d '{"title":"...","body":"...","head":"feat/...","base":"main"}'
```

## 工作规则

1. **功能分支**：永远不要直接 push 到 main。创建 `feat/`、`fix/`、`docs/` 分支。
2. **提 PR**：代码完成后创建 PR，在 Discord @ 孔明 review。
3. **不要 merge**：merge 权限在孔明，你只管提 PR。
4. **Commit message 规范**：`feat:` / `fix:` / `docs:` / `refactor:` 前缀。

## 项目列表

参见 workspace 中的 `PROJECTS.md`。
