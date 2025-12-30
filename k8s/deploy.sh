#!/bin/bash

# Jarvis Kubernetes 部署脚本

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 配置
NAMESPACE="jarvis"
IMAGE_NAME="${IMAGE_NAME:-jarvis:latest}"
DEPLOY_FILE="${DEPLOY_FILE:-jarvis.yaml}"

echo -e "${GREEN}🚀 开始部署 Jarvis 到 Kubernetes...${NC}"

# 检查 kubectl
if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}❌ 未找到 kubectl，请先安装 kubectl${NC}"
    exit 1
fi

# 检查是否连接到集群
if ! kubectl cluster-info &> /dev/null; then
    echo -e "${RED}❌ 无法连接到 Kubernetes 集群，请检查 kubeconfig${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Kubernetes 集群连接正常${NC}"

# 选择部署文件
DEPLOY_FILE="${DEPLOY_FILE:-jarvis.yaml}"

# 检查文件是否存在
if [ ! -f "$DEPLOY_FILE" ]; then
    echo -e "${RED}❌ 部署文件 $DEPLOY_FILE 不存在${NC}"
    echo -e "${YELLOW}可用文件: jarvis.yaml, jarvis-full.yaml${NC}"
    exit 1
fi

# 更新部署文件中的镜像地址（如果提供了）
if [ -n "$IMAGE_NAME" ] && [ "$IMAGE_NAME" != "jarvis:latest" ]; then
    echo -e "${YELLOW}📝 更新镜像地址为: $IMAGE_NAME${NC}"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s|image:.*jarvis.*|image: $IMAGE_NAME|g" "$DEPLOY_FILE"
    else
        # Linux
        sed -i "s|image:.*jarvis.*|image: $IMAGE_NAME|g" "$DEPLOY_FILE"
    fi
fi

# 部署所有资源
echo -e "${GREEN}📦 部署所有资源...${NC}"
kubectl apply -f "$DEPLOY_FILE"

# 等待 PVC 就绪
echo -e "${YELLOW}⏳ 等待 PVC 就绪...${NC}"
kubectl wait --for=condition=Bound pvc/jarvis-data -n "$NAMESPACE" --timeout=60s || true

# 等待 Pod 就绪
echo -e "${YELLOW}⏳ 等待 Pod 启动...${NC}"
kubectl wait --for=condition=ready pod -l app=jarvis -n "$NAMESPACE" --timeout=120s || true

# 显示部署状态
echo ""
echo -e "${GREEN}✅ 部署完成！${NC}"
echo ""
echo -e "${GREEN}📊 部署状态:${NC}"
kubectl get all -n "$NAMESPACE"

echo ""
echo -e "${GREEN}📝 Pod 日志:${NC}"
POD_NAME=$(kubectl get pods -n "$NAMESPACE" -l app=jarvis -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")
if [ -n "$POD_NAME" ]; then
    echo "使用以下命令查看日志:"
    echo "  kubectl logs -f $POD_NAME -n $NAMESPACE"
fi

echo ""
echo -e "${GREEN}🌐 访问方式:${NC}"
echo "1. 集群内部访问:"
echo "   http://jarvis.$NAMESPACE.svc.cluster.local:8000"
echo ""
echo "2. 端口转发（本地访问）:"
echo "   kubectl port-forward svc/jarvis 8000:8000 -n $NAMESPACE"
echo "   然后访问: http://localhost:8000"
echo ""
echo "3. 如果需要外部访问，可以使用以下方式之一:"
echo "   - 应用 NodePort Service: kubectl apply -f service-nodeport.yaml"
echo "   - 应用 Ingress: kubectl apply -f ingress.yaml（需要先配置域名）"

