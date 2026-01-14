#!/bin/bash

# ==========================================
# 智能打标便捷器 - 生产环境部署脚本
# ==========================================

set -e

echo "=========================================="
echo "  智能打标便捷器 - 生产环境部署"
echo "=========================================="
echo ""

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查函数
check_command() {
    if ! command -v $1 &> /dev/null; then
        echo -e "${RED}✗ $1 未安装${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ $1 已安装${NC}"
}

# 1. 检查依赖
echo "步骤 1/7: 检查系统依赖..."
check_command docker
check_command docker-compose
echo ""

# 2. 配置环境变量
echo "步骤 2/7: 配置环境变量..."
if [ ! -f .env.production ]; then
    if [ -f .env.production.example ]; then
        cp .env.production.example .env.production
        echo -e "${YELLOW}⚠ 已创建 .env.production，请编辑配置API Keys${NC}"
        echo -e "${YELLOW}按回车继续...${NC}"
        read
    else
        echo -e "${RED}✗ .env.production.example 文件不存在${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✓ .env.production 已存在${NC}"
fi
echo ""

# 3. 构建镜像
echo "步骤 3/7: 构建Docker镜像..."
docker-compose -f docker-compose.prod.yml build
echo ""

# 4. 停止旧服务
echo "步骤 4/7: 停止旧服务..."
docker-compose -f docker-compose.prod.yml down 2>/dev/null || true
echo ""

# 5. 启动服务
echo "步骤 5/7: 启动服务..."
docker-compose -f docker-compose.prod.yml up -d
echo ""

# 6. 等待服务启动
echo "步骤 6/7: 等待服务启动..."
sleep 5
echo ""

# 7. 健康检查
echo "步骤 7/7: 健康检查..."
if curl -sf http://localhost/health > /dev/null; then
    echo -e "${GREEN}✓ 后端服务正常${NC}"
else
    echo -e "${RED}✗ 后端服务异常${NC}"
fi

if curl -sf http://localhost:3000 > /dev/null; then
    echo -e "${GREEN}✓ 前端服务正常${NC}"
else
    echo -e "${YELLOW}⚠ 前端服务检查中...${NC}"
fi
echo ""

# 8. 显示服务状态
echo "=========================================="
echo "  服务状态"
echo "=========================================="
docker-compose -f docker-compose.prod.yml ps
echo ""

# 9. 访问信息
echo "=========================================="
echo "  部署完成！"
echo "=========================================="
echo ""
echo "访问地址："
echo "  • 前端: http://localhost"
echo "  • 后端API: http://localhost/api/"
echo "  • API文档: http://localhost/docs"
echo "  • 健康检查: http://localhost/health"
echo ""
echo "常用命令："
echo "  • 查看日志: docker-compose -f docker-compose.prod.yml logs -f"
echo "  • 停止服务: docker-compose -f docker-compose.prod.yml down"
echo "  • 重启服务: docker-compose -f docker-compose.prod.yml restart"
echo ""
echo -e "${GREEN}✓ 部署成功！${NC}"
