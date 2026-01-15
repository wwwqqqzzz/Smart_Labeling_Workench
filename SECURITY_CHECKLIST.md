# 🔐 安全检查清单 - GitHub 公开仓库

## ⚠️ 重要警告

**您的仓库是公开的，任何人都可见！提交前必须检查敏感信息！**

---

## ✅ 安全状态检查

当前检查结果：
- ✅ `.env` 文件未被 git 追踪
- ✅ `.gitignore` 已正确配置
- ✅ 没有敏感文件被追踪

---

## 🚫 绝对不能提交的文件

### 1. 环境变量文件（包含 API 密钥）

```bash
# ❌ 绝对不能提交
.env
.env.local
.env.production
frontend/.env.local
```

**这些文件包含**：
- `GLM_API_KEY` - 智谱 AI 密钥
- `OPENAI_API_KEY` - OpenAI API 密钥
- `DATABASE_URL` - 数据库连接信息
- 其他敏感配置

### 2. 数据库文件

```bash
# ❌ 不能提交
data/*.db
*.db-journal
conversations.db
```

### 3. SSL 证书

```bash
# ❌ 不能提交
*.pem
*.key
*.crt
ssl/
nginx/ssl/
```

### 4. 临时/日志文件

```bash
# ❌ 不能提交
*.log
.cache/
__pycache__/
.pytest_cache/
```

---

## ✅ 可以提交的文件

### 1. 示例配置文件（不包含真实密钥）

```bash
✅ .env.example
✅ .env.production.example
✅ frontend/.env.local.example
```

**这些文件应该包含**：
```bash
# API Keys
GLM_API_KEY=your_glm_api_key_here
OPENAI_API_KEY=your_openai_api_key_here

# Database
DATABASE_URL=sqlite:///./data/conversations.db
```

### 2. 代码文件

```bash
✅ *.py
✅ *.ts
✅ *.tsx
✅ *.json
✅ *.md
```

### 3. 配置文件

```bash
✅ requirements.txt
✅ package.json
✅ docker-compose.yml
✅ Dockerfile
✅ railway.json
✅ nixpacks.toml
```

---

## 🔍 提交前安全检查

### 检查命令 1：查看将要提交的文件

```bash
cd "/Users/wang/项目/Smart Labeling Workbench"

# 查看当前状态
git status

# 查看暂存区的文件
git diff --cached --name-only

# 查看暂存区的内容
git diff --cached
```

### 检查命令 2：搜索敏感信息

```bash
# 检查是否有 API 密钥被提交
git grep "GLM_API_KEY"
git grep "OPENAI_API_KEY"
git grep "sk-"
git grep "a82735f90df14d3c9ea555ed2583c574"

# 如果返回结果，说明密钥已被提交！需要删除！
```

### 检查命令 3：验证 .gitignore

```bash
# 检查 .env 是否被忽略（应该无输出）
git check-ignore -v .env
git check-ignore -v .env.local
git check-ignore -v frontend/.env.local

# 如果有输出，说明已被正确忽略
# 如果无输出，说明会被提交！需要添加到 .gitignore！
```

---

## 📝 推荐的 .gitignore 配置

您的项目已包含完整的 `.gitignore` 配置，涵盖了：

```gitignore
# 环境变量
.env
.env.local
.env.production
.env.*.local

# 数据
data/
*.db
*.db-journal

# SSL 证书
*.pem
*.key
*.crt
ssl/

# Railway 配置
railway.env
.vercel/env.local
```

---

## 🚨 如果已经提交了敏感信息

### 紧急处理步骤

```bash
# 1. 立即删除敏感文件
git rm --cached .env
git rm --cached .env.local

# 2. 提交删除
git commit -m "Remove sensitive files"

# 3. 推送到远程
git push origin main

# 4. 撤销历史记录（如果密钥已在历史中）
# ⚠️ 警告：这会重写 Git 历史！
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch .env" \
  --prune-empty --tag-name-filter cat -- --all

# 5. 强制推送
git push origin --force --all

# 6. 立即更换 API 密钥！
# 访问智谱 AI 和 OpenAI 控制台，重新生成密钥
```

---

## 🛡️ 永久安全建议

### 1. 提交前清单

```bash
# 每次提交前运行
cd "/Users/wang/项目/Smart Labeling Workbench"

# ✅ 检查敏感文件
git status | grep "\.env"

# ✅ 检查暂存区
git diff --cached | grep -i "api_key\|secret\|password"

# ✅ 确认 .gitignore 生效
git check-ignore -v .env .env.local
```

### 2. 使用 Pre-commit Hook

创建 `.git/hooks/pre-commit`：

```bash
#!/bin/bash
# 检查是否尝试提交 .env 文件
if git diff --cached --name-only | grep -E "\.env$|\.env\.local$"; then
  echo "❌ 错误：不能提交 .env 文件！"
  echo "请将 .env 添加到 .gitignore"
  exit 1
fi
```

启用：
```bash
chmod +x .git/hooks/pre-commit
```

### 3. Railway/Vercel 部署安全

**永远在平台的控制台中配置环境变量，不要在代码中硬编码！**

Railway:
- 项目 → Variables → 添加环境变量

Vercel:
- 项目 → Settings → Environment Variables → 添加

---

## 📊 当前安全状态总结

| 检查项 | 状态 | 说明 |
|--------|------|------|
| `.env` 文件 | ✅ 已忽略 | 不会被提交 |
| `.env.local` | ✅ 已忽略 | 不会被提交 |
| 数据库文件 | ✅ 已忽略 | data/ 目录已忽略 |
| SSL 证书 | ✅ 已忽略 | *.pem, *.key 已忽略 |
| 敏感文件追踪 | ✅ 安全 | 无敏感文件被追踪 |

---

## ✅ 可以安全推送

**当前状态：安全！可以提交以下文件：**

```bash
# 推荐提交的文件
git add .gitignore
git add README.md
git add CLAUDE.md
git add RAILWAY_DEPLOYMENT.md
git add railway.json
git add nixpacks.toml
git add backend/
git add frontend/
git add docs/

# ❌ 不要添加
# git add .env           # 包含真实密钥
# git add .env.local     # 包含本地配置
# git add data/          # 数据库文件
```

---

## 🎯 快速推送命令

```bash
cd "/Users/wang/项目/Smart Labeling Workbench"

# 1. 添加所有文件（.env 会自动被 .gitignore 排除）
git add .

# 2. 检查将要提交的文件
git status

# 3. 确认没有 .env 文件后提交
git commit -m "Initial commit: Smart Labeling Workbench"

# 4. 推送到 GitHub
git remote add origin https://github.com/wwwqqqzzz/Smart_Labeling_Workench.git
git push -u origin main
```

---

## 📞 如果发现安全问题

1. **立即更换 API 密钥**（智谱 AI、OpenAI）
2. **从 Git 历史中删除**（使用 filter-branch）
3. **联系 GitHub 支持**（如果已在公开仓库）
4. **检查访问日志**（API 使用情况）

---

**最后检查**：
- ✅ 已确认 `.env` 不在 git 追踪中
- ✅ 已确认 `.gitignore` 配置正确
- ✅ 可以安全推送到公开仓库

**祝部署顺利！🎉**
