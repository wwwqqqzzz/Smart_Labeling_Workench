#!/bin/bash

# 智能打标便捷器 - Railway 一键部署脚本

set -e

echo "================================"
echo "🚀 智能打标便捷器 - Railway 部署"
echo "================================"
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 步骤 1: 推送到 GitHub
echo -e "${YELLOW}步骤 1/3: 推送代码到 GitHub${NC}"
echo "----------------------------------------"

# 检查是否已配置远程仓库
if git remote get-url origin &>/dev/null; then
    echo "✅ 远程仓库已配置: $(git remote get-url origin)"
else
    echo "❌ 未配置远程仓库"
    read -p "请输入 GitHub 仓库 URL: " repo_url
    git remote add origin $repo_url
fi

# 推送代码
echo "📤 正在推送代码到 GitHub..."
if git push -u origin main; then
    echo -e "${GREEN}✅ 代码推送成功！${NC}"
else
    echo -e "${RED}❌ 推送失败，可能需要身份验证${NC}"
    echo ""
    echo "请手动执行以下命令："
    echo "  cd \"$(pwd)\""
    echo "  git push -u origin main"
    echo ""
    echo "或者使用 SSH（推荐）："
    echo "  git remote set-url origin git@github.com:wwwqqqzzz/Smart_Labeling_Workench.git"
    echo "  git push -u origin main"
    exit 1
fi

echo ""
echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}✅ 代码已成功推送到 GitHub！${NC}"
echo -e "${GREEN}================================${NC}"
echo ""

# 步骤 2: Railway 部署指引
echo -e "${YELLOW}步骤 2/3: 在 Railway.app 创建项目${NC}"
echo "----------------------------------------"
echo "请按照以下步骤操作："
echo ""
echo "1️⃣  打开 https://railway.app/"
echo "2️⃣  使用 GitHub 登录"
echo "3️⃣  点击 'New Project'"
echo "4️⃣  选择 'Deploy from GitHub repo'"
echo "5️⃣  选择仓库: wwwqqqzzz/Smart_Labeling_Workench"
echo "6️⃣  Railway 会自动检测并创建服务"
echo ""
read -p "按 Enter 键继续（完成上述步骤后）..."

# 步骤 3: 配置环境变量
echo ""
echo -e "${YELLOW}步骤 3/3: 配置环境变量${NC}"
echo "----------------------------------------"
echo "在 Railway 项目中添加以下环境变量："
echo ""
echo "必需的环境变量："
echo "  GLM_API_KEY=你的智谱API密钥"
echo "  OPENAI_API_KEY=你的OpenAI API密钥"
echo "  DATABASE_URL=sqlite:///./data/conversations.db"
echo "  PORT=8000"
echo ""
echo "获取 API Keys："
echo "  • 智谱 AI: https://open.bigmodel.cn/usercenter/apikeys"
echo "  • OpenAI: https://platform.openai.com/api-keys"
echo ""
echo "📖 详细步骤请参考: RAILWAY_DEPLOYMENT.md"
echo ""

# 等待用户确认部署
echo -e "${YELLOW}等待 Railway 部署完成...${NC}"
echo "部署完成后，Railway 会提供公网访问地址："
echo "  • 后端: https://你的项目名.up.railway.app"
echo "  • API 文档: https://你的项目名.up.railway.app/docs"
echo ""

# 完成
echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}🎉 部署指引完成！${NC}"
echo -e "${GREEN}================================${NC}"
echo ""
echo "下一步："
echo "  1. 在 Railway 控制台配置环境变量"
echo "  2. 等待自动部署完成"
echo "  3. 访问分配的公网地址"
echo "  4. 初始化数据库（在 Railway 终端运行）"
echo ""
echo "💡 提示：使用 Railway 终端初始化数据库"
echo "  python scripts/init_db.py"
echo ""
