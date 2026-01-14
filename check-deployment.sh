#!/bin/bash

# ==========================================
# 部署检查脚本
# ==========================================

echo "=========================================="
echo "  部署检查清单"
echo "=========================================="
echo ""

# 颜色
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

checks_passed=0
checks_total=0

check() {
    name=$1
    command=$2
    ((checks_total++))
    
    echo -n "检查 $name... "
    if eval "$command" &> /dev/null; then
        echo -e "${GREEN}✓ 通过${NC}"
        ((checks_passed++))
    else
        echo -e "${RED}✗ 失败${NC}"
    fi
}

# 1. Docker检查
echo "=== 1. 系统依赖检查 ==="
check "Docker" "command -v docker"
check "Docker Compose" "command -v docker-compose"
echo ""

# 2. 配置文件检查
echo "=== 2. 配置文件检查 ==="
check ".env.production" "test -f .env.production"
check ".env.production中GLM_API_KEY" "grep -q 'GLM_API_KEY=' .env.production && grep -q 'GLM_API_KEY=your_' .env.production && exit 1 || test -f .env.production"
check "docker-compose.prod.yml" "test -f docker-compose.prod.yml"
check "nginx/nginx.conf" "test -f nginx/nginx.conf"
echo ""

# 3. 服务状态检查
echo "=== 3. 服务状态检查 ==="
check "Nginx服务" "docker-compose -f docker-compose.prod.yml ps | grep nginx"
check "Frontend服务" "docker-compose -f docker-compose.prod.yml ps | grep frontend"
check "Backend服务" "docker-compose -f docker-compose.prod.yml ps | grep backend"
echo ""

# 4. 健康检查
echo "=== 4. 健康检查 ==="
check "Nginx可访问" "curl -sf http://localhost/"
check "后端健康检查" "curl -sf http://localhost/health"
check "前端可访问" "curl -sf http://localhost:3000"
check "API文档可访问" "curl -sf http://localhost/docs"
echo ""

# 5. 功能检查
echo "=== 5. 功能检查 ==="
check "对话列表API" "curl -sf http://localhost/api/v1/conversations"
check "批次列表API" "curl -sf http://localhost/api/v1/batches"
check "全局统计API" "curl -sf http://localhost/api/v1/conversations/stats/global"
echo ""

# 总结
echo "=========================================="
echo "  检查结果"
echo "=========================================="
echo "通过: $checks_passed / $checks_total"

if [ $checks_passed -eq $checks_total ]; then
    echo -e "${GREEN}✓ 所有检查通过！部署成功！${NC}"
    exit 0
else
    echo -e "${YELLOW}⚠ 有 $((checks_total - checks_passed)) 项检查未通过${NC}"
    echo ""
    echo "建议："
    echo "1. 查看日志: docker-compose -f docker-compose.prod.yml logs"
    echo "2. 重启服务: docker-compose -f docker-compose.prod.yml restart"
    echo "3. 重新部署: ./deploy.sh"
    exit 1
fi
