# Jarvis Kubernetes 部署指南

本文档说明如何将 Jarvis 应用部署到 Kubernetes 集群。

## 前置要求

1. 已安装并配置 Kubernetes 集群（v1.20+）
2. 已安装 `kubectl` 命令行工具
3. 已构建 Docker 镜像并推送到镜像仓库（或使用本地镜像）
4. 跳板机是 K8s 集群的节点，或者可以通过 hostPath 访问跳板机上的文件
5. 在跳板机上准备好 `jarvis.db` 文件和 `data` 目录

## 快速部署

### 1. 构建并推送镜像

首先需要构建 Docker 镜像并推送到镜像仓库：

```bash
# 方式1: 使用原始 Dockerfile（使用华为云镜像源）
docker build -t your-registry/jarvis:latest -f Dockerfile .

# 方式2: 使用 K8s 版本 Dockerfile（使用公共镜像）
docker build -t your-registry/jarvis:latest -f Dockerfile.k8s .

# 推送到镜像仓库
docker push your-registry/jarvis:latest
```

**注意**: 
- 如果使用华为云环境，可以使用原始的 `Dockerfile`
- 如果使用其他环境或公共镜像仓库，建议使用 `Dockerfile.k8s`
- 构建多平台镜像（可选）：
  ```bash
  docker buildx build --platform linux/amd64,linux/arm64 \
    -t your-registry/jarvis:latest \
    -f Dockerfile.k8s \
    --push .
  ```

如果使用私有镜像仓库，需要先创建 Secret：

```bash
kubectl create secret docker-registry regcred \
  --docker-server=your-registry.com \
  --docker-username=your-username \
  --docker-password=your-password \
  --docker-email=your-email \
  -n jarvis
```

然后在 `jarvis.yaml` 或 `jarvis-full.yaml` 中的 Deployment 部分添加：

```yaml
spec:
  template:
    spec:
      imagePullSecrets:
      - name: regcred
```

### 2. 修改配置

根据实际情况修改以下文件：

- **jarvis.yaml** 或 **jarvis-full.yaml**: 
  - 修改 Deployment 中的镜像地址
  - 修改 ConfigMap 中的应用配置（如需要）
  - **重要：配置 hostPath 和节点选择**
  - 修改 Deployment 中的 `hostPath.path` 为跳板机上 `jarvis.db` 的实际路径
  - 修改 Deployment 中的 `hostPath.path` 为跳板机上数据目录的实际路径
  - 修改 Deployment 中的 `nodeName` 或 `nodeSelector` 以指定跳板机节点
  - 修改 Ingress 的域名和 Ingress Controller 类型（如使用 jarvis-full.yaml）

**示例配置：**

```yaml
spec:
  template:
    spec:
      # 方式1: 使用 nodeName 直接指定节点
      nodeName: jump-server  # 跳板机节点名
      
      # 或方式2: 使用 nodeSelector 通过标签选择
      # nodeSelector:
      #   kubernetes.io/hostname: jump-server
      
      volumes:
      - name: jarvis-db
        hostPath:
          path: /data/jarvis/jarvis.db  # 跳板机上数据库文件路径
          type: FileOrCreate
      - name: jarvis-data
        hostPath:
          path: /data/jarvis/data  # 跳板机上数据目录路径
          type: DirectoryOrCreate
```

### 3. 部署应用

#### 方式一：使用合并的 YAML 文件（推荐）

**重要：部署前请确保已修改 hostPath 路径和节点选择器**

```bash
# 基础部署（包含 Namespace, ConfigMap, Deployment, Service）
kubectl apply -f jarvis.yaml

# 完整部署（包含所有资源，包括 NodePort 和 Ingress）
kubectl apply -f jarvis-full.yaml
```


### 4. 验证部署

```bash
# 查看命名空间
kubectl get ns jarvis

# 查看 Pod 状态
kubectl get pods -n jarvis

# 查看 Pod 日志
kubectl logs -f deployment/jarvis -n jarvis

# 查看 Service
kubectl get svc -n jarvis

# 查看 Pod 所在节点（确认是否调度到跳板机）
kubectl get pods -n jarvis -o wide
```

### 5. 访问应用

根据选择的暴露方式访问：

- **ClusterIP**: 在集群内部访问 `http://jarvis.jarvis.svc.cluster.local:8000`
- **NodePort**: 通过任意节点 IP + 端口访问 `http://<node-ip>:30080`
- **Ingress**: 通过配置的域名访问 `http://jarvis.example.com`

## 配置说明

### ConfigMap

ConfigMap 包含应用的环境变量配置，可以根据需要修改 `jarvis.yaml` 或 `jarvis-full.yaml` 中的 ConfigMap 部分。

主要配置项：
- `APP_NAME`: 应用名称
- `DEBUG`: 调试模式（生产环境建议设为 false）
- `DATABASE_URL`: 数据库连接字符串
- `MORNING_REMINDER_TIME`: 每日提醒时间
- `ENABLE_LOGGING`: 是否启用日志

### HostPath 存储

使用 hostPath 挂载跳板机上的文件：
- 数据库文件 (`jarvis.db`) - 挂载为文件
- Excel 规则配置 (`data/excel_rules/`) - 挂载为目录

**配置说明：**
- `type: FileOrCreate` - 如果数据库文件不存在，会自动创建
- `type: DirectoryOrCreate` - 如果数据目录不存在，会自动创建
- 需要确保 Pod 调度到跳板机节点（通过 `nodeName` 或 `nodeSelector`）
- 需要确保跳板机节点上的路径有正确的权限

### Deployment

Deployment 配置了：
- 副本数：1（单实例部署）
- 资源限制：内存 512Mi，CPU 500m
- 健康检查：liveness 和 readiness probe
- 数据卷挂载：数据库和配置目录

### Service

提供了两种 Service 类型：
- **ClusterIP**: 集群内部访问（默认）
- **NodePort**: 通过节点端口外部访问（端口 30080）

### Ingress

如果需要通过域名访问，可以使用 Ingress。需要根据实际的 Ingress Controller 类型修改注解。

## 扩缩容

如果需要扩展应用实例：

```bash
# 扩展副本数
kubectl scale deployment jarvis --replicas=3 -n jarvis

# 查看副本状态
kubectl get pods -n jarvis
```

**注意**: 由于使用 SQLite 数据库，多个实例之间无法共享数据库文件。如果需要多实例部署，建议：
1. 使用外部数据库（如 PostgreSQL）
2. 修改 `DATABASE_URL` 配置为 PostgreSQL 连接字符串
3. 确保所有实例连接到同一个数据库

## 数据备份

由于数据文件存储在跳板机上，备份可以直接在跳板机上操作：

### 备份数据库

```bash
# 在跳板机上执行
cp /path/to/jarvis.db /path/to/jarvis.db.backup

# 或使用 sqlite3 导出
sqlite3 /path/to/jarvis.db ".backup /path/to/jarvis.db.backup"
```

### 备份数据目录

```bash
# 在跳板机上执行
tar czf /path/to/jarvis-data-backup.tar.gz /path/to/jarvis-data/
```

### 从 Pod 内备份（可选）

```bash
# 获取 Pod 名称
POD_NAME=$(kubectl get pods -n jarvis -l app=jarvis -o jsonpath='{.items[0].metadata.name}')

# 备份数据库
kubectl exec -n jarvis $POD_NAME -- sqlite3 /app/jarvis.db ".backup /app/jarvis.db.backup"

# 复制到本地
kubectl cp jarvis/$POD_NAME:/app/jarvis.db.backup ./jarvis.db.backup
```

## 故障排查

### Pod 无法启动

```bash
# 查看 Pod 状态
kubectl describe pod -n jarvis -l app=jarvis

# 查看 Pod 日志
kubectl logs -n jarvis -l app=jarvis
```

### 无法访问服务

```bash
# 检查 Service
kubectl get svc -n jarvis

# 检查 Endpoints
kubectl get endpoints -n jarvis jarvis

# 测试服务连通性（在集群内）
kubectl run -it --rm debug --image=curlimages/curl --restart=Never -- curl http://jarvis.jarvis.svc.cluster.local:8000/api/health
```

### 数据持久化问题

```bash
# 检查 Pod 是否调度到正确的节点
kubectl get pods -n jarvis -o wide

# 检查节点上的文件是否存在
# 在跳板机上执行：
ls -la /path/to/jarvis.db
ls -la /path/to/jarvis-data/

# 检查文件权限
# 确保 K8s 节点上的路径有读写权限
# 如果使用非 root 用户运行容器，可能需要调整权限
```

## 升级应用

```bash
# 更新镜像
kubectl set image deployment/jarvis jarvis=your-registry/jarvis:v1.1.0 -n jarvis

# 查看滚动更新状态
kubectl rollout status deployment/jarvis -n jarvis

# 如果需要回滚
kubectl rollout undo deployment/jarvis -n jarvis
```

## 卸载应用

```bash
# 删除所有资源（数据文件保留在跳板机上）
kubectl delete -f jarvis.yaml

# 或使用完整版本
kubectl delete -f jarvis-full.yaml

# 注意：删除应用不会删除跳板机上的数据文件
# 数据文件仍然保留在跳板机的 hostPath 路径中
# 如需删除数据，需要手动在跳板机上删除文件
```

## 生产环境建议

1. **使用外部数据库**: 将 SQLite 替换为 PostgreSQL 或 MySQL，支持多实例部署
2. **配置资源限制**: 根据实际负载调整 CPU 和内存限制
3. **启用日志收集**: 配置日志收集系统（如 ELK、Loki）
4. **配置监控**: 添加 Prometheus 监控和告警
5. **使用 Secret**: 敏感信息（如数据库密码）使用 Secret 而不是 ConfigMap
6. **配置 TLS**: 在 Ingress 中启用 HTTPS
7. **备份策略**: 定期备份数据库和数据文件
8. **高可用**: 如需高可用，使用外部数据库并部署多个实例

