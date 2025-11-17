# Docker 部署指南

## 快速开始

### 使用 Docker Compose（推荐）

```bash
# 构建并启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

### 使用 Docker 命令

```bash
# 构建镜像
docker build -t jarvis:latest .

# 运行容器
docker run -d \
  --name jarvis \
  -p 8000:8000 \
  -v $(pwd)/jarvis.db:/app/jarvis.db \
  -v $(pwd)/data/excel_rules:/app/data/excel_rules \
  jarvis:latest

# 查看日志
docker logs -f jarvis

# 停止容器
docker stop jarvis
docker rm jarvis
```

## 数据持久化

Docker Compose 配置会自动挂载以下目录：

- `./jarvis.db` - SQLite 数据库文件
- `./data/excel_rules` - Excel 规则配置文件

确保这些目录存在并有正确的权限。

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

