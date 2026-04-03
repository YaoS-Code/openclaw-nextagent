---
name: cloudflare-deploy
description: 通过 Cloudflare Tunnel + Docker 部署项目到公网。创建 tunnel、配置域名、docker-compose 启动。
---

# Cloudflare Tunnel 部署

你可以通过 Cloudflare Tunnel 将本地 Docker 服务暴露到公网，无需公网 IP。

## 部署流程

### 1. 创建 Tunnel
```bash
cloudflared tunnel create <project-name>
# 会生成 credentials JSON 文件到 ~/.cloudflared/
```

### 2. 创建配置文件
```yaml
# ~/.cloudflared/<project-name>.yml
tunnel: <TUNNEL_ID>
credentials-file: /home/borui/.cloudflared/<TUNNEL_ID>.json

ingress:
  - hostname: <subdomain>.borui.org
    service: http://localhost:<PORT>
  - service: http_status:404
```

### 3. 配置 DNS
```bash
cloudflared tunnel route dns <project-name> <subdomain>.borui.org
```

### 4. 启动服务
```bash
# 启动应用（Docker）
cd ~/project-dir
docker compose up -d

# 启动 tunnel
cloudflared tunnel --config ~/.cloudflared/<project-name>.yml run &
```

### 5. 设为系统服务（可选）
```bash
sudo cloudflared service install --config ~/.cloudflared/<project-name>.yml
```

## Docker Compose 标准模式

生产部署用 `docker-compose.prod.yml`：
- 应用容器（Next.js / Node）
- 数据库容器（PostgreSQL）
- Nginx 反向代理（可选）

```bash
docker compose -f docker-compose.prod.yml up -d
```

## 注意事项

- Tunnel 名称用项目名
- 域名用 `*.borui.org` 子域名（除非主公另有指定）
- 数据库不暴露到公网
- 部署完成后测试 HTTPS 可达性
