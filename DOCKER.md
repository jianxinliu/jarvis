# Docker 部署指南

## 快速开始

### 使用 Docker Compose（推荐）

```bash
# 构建并启动服务（后台运行，推荐）
docker-compose up -d

# 或者前台运行（可以看到实时日志，按 Ctrl+C 停止）
docker-compose up

# 查看日志
docker-compose logs -f

# 查看最近 100 行日志
docker-compose logs --tail=100 -f

# 查看服务状态
docker-compose ps

# 重启服务
docker-compose restart

# 停止服务（保留容器）
docker-compose stop

# 停止并删除服务（删除容器）
docker-compose down

# 停止并删除服务，同时删除数据卷（谨慎使用）
docker-compose down -v
```

### 使用 Docker 命令

```bash
# 构建镜像（当前平台）
docker build -t jarvis:latest .

# 构建指定平台的镜像（例如 ARM64）
docker build --platform linux/arm64 -t jarvis:latest .

# 运行容器（必须挂载数据库文件和规则目录）
docker run -d \
  --name jarvis \
  --platform linux/amd64 \  # 指定运行平台
  -p 8000:8000 \
  -v $(pwd)/jarvis.db:/app/jarvis.db \  # 必须挂载，否则数据会丢失
  -v $(pwd)/data/excel_rules:/app/data/excel_rules \  # 必须挂载，否则规则会丢失
  jarvis:latest
```

### 多平台构建

如果需要构建支持多个平台的镜像（例如同时支持 AMD64 和 ARM64）：

```bash
# 启用 buildx（如果未启用）
docker buildx create --use --name multiarch

# 构建多平台镜像
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t jarvis:latest \
  --load .  # 使用 --load 加载到本地，或使用 --push 推送到仓库

# 查看支持的平台
docker buildx imagetools inspect jarvis:latest
```

## 平台支持

### 支持的平台

- **linux/amd64** - Intel/AMD 64位架构（x86_64）
- **linux/arm64** - ARM 64位架构（Apple Silicon、ARM 服务器）

### 在 docker-compose.yml 中指定平台

在 `docker-compose.yml` 中，可以通过 `platform` 字段指定运行平台：

```yaml
services:
  jarvis:
    platform: linux/amd64  # 或 linux/arm64
    # ... 其他配置
```

### 在 Apple Silicon (M1/M2) Mac 上运行

如果使用 Apple Silicon Mac，可以：

1. **使用 ARM64 平台**（推荐，性能更好）：
   ```yaml
   platform: linux/arm64
   ```

2. **使用 AMD64 平台**（通过模拟，性能较慢）：
   ```yaml
   platform: linux/amd64
   ```

## 数据持久化

**重要**: 以下数据必须挂载到宿主机，否则容器重启或删除时数据会丢失！

Docker Compose 配置会自动挂载以下目录：

- `./jarvis.db` - SQLite 数据库文件（**必须挂载**）
- `./data/excel_rules` - Excel 规则配置文件（**必须挂载**，保存的规则会存储在此目录）

### 使用 Docker 命令运行时的挂载

使用 `docker run` 命令时，必须使用 `-v` 参数挂载数据库文件和规则目录：

```bash
docker run -d \
  --name jarvis \
  -p 8000:8000 \
  -v $(pwd)/jarvis.db:/app/jarvis.db \  # 必须挂载数据库文件
  -v $(pwd)/data/excel_rules:/app/data/excel_rules \  # 必须挂载规则目录
  jarvis:latest
```

### 使用命名卷（可选）

如果需要使用 Docker 命名卷而不是绑定挂载：

```yaml
volumes:
  jarvis_db:
    driver: local
  jarvis_rules:
    driver: local

services:
  jarvis:
    volumes:
      - jarvis_db:/app/jarvis.db
      - jarvis_rules:/app/data/excel_rules
```

### 备份数据

由于数据库文件和规则目录已挂载到宿主机，可以直接备份：

```bash
# 备份数据库
cp jarvis.db jarvis.db.backup

# 或使用 sqlite3 导出
sqlite3 jarvis.db .dump > jarvis_backup.sql

# 备份规则配置
tar -czf excel_rules_backup.tar.gz data/excel_rules/
```

## 环境变量

可以通过环境变量配置应用：

```yaml
environment:
  - DEBUG=false
  - HOST=0.0.0.0
  - PORT=8000
  - DATABASE_URL=sqlite:///./jarvis.db
```

## 健康检查

容器包含健康检查配置，可以通过以下命令查看：

```bash
docker inspect jarvis | grep Health -A 10
```

## 访问应用

启动后，访问以下地址：

- 前端界面: http://localhost:8000
- API 文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/api/health

## 故障排查

### 查看容器日志

```bash
docker-compose logs jarvis
```

### 进入容器调试

```bash
docker exec -it jarvis /bin/bash
```

### 检查数据库

```bash
docker exec -it jarvis sqlite3 /app/jarvis.db
```

