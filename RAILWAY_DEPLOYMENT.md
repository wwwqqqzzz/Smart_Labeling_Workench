
# Railway.app 亚洲节点部署指南

## 🚀 5分钟快速部署到公网（免费方案）

---

## 方案对比

| 平台 | 免费额度 | 亚洲节点 | Docker支持 | 自动HTTPS | 推荐度 |
|------|---------|---------|-----------|----------|--------|
| **Railway.app** | $5/月 | ✅ 新加坡/日本 | ✅ | ✅ | ⭐⭐⭐⭐⭐ |
| Render.com | 有限 | ✅ 新加坡 | ✅ | ✅ | ⭐⭐⭐⭐ |
| Fly.io | $5/月 | ✅ 香港/新加坡 | ✅ | ✅ | ⭐⭐⭐⭐ |
| Vercel | 100GB带宽 | 全球CDN | ⚠️ 仅前端 | ✅ | ⭐⭐⭐⭐⭐ |

**推荐**：Railway.app（最佳平衡）

---

## 部署步骤

### 第一步：准备代码

#### 1. 推送代码到 GitHub

```bash
cd "/Users/wang/项目/Smart Labeling Workbench"

# 初始化 Git（如果还没有）
git init
git add .
git commit -m "Ready for Railway deployment"

# 在 GitHub 创建新仓库后
git remote add origin https://github.com/你的用户名/smart-labeling-workbench.git
git branch -M main
git push -u origin main
```

#### 2. 检查必需文件

确保以下文件存在：
- ✅ `requirements.txt` - 后端依赖
- ✅ `nixpacks.toml` - Railway 构建配置
- ✅ `railway.json` - Railway 部署配置
- ✅ `backend/app/main.py` - FastAPI 入口
- ✅ `.env.example` - 环境变量模板

---

### 第二步：在 Railway 创建项目

#### 1. 登录 Railway

访问 https://railway.app/ 并使用 GitHub 登录

#### 2. 创建新项目

```
New Project → Deploy from GitHub repo → 选择你的仓库
```

Railway 会自动检测并创建服务

---

### 第三步：配置环境变量

在 Railway 控制台：

1. 点击你的项目
2. 选择 **Variables** 标签
3. 添加以下环境变量：

```bash
# 必需
GLM_API_KEY=你的智谱API密钥
OPENAI_API_KEY=你的OpenAI API密钥（用于RAG）
DATABASE_URL=sqlite:///./data/conversations.db
PORT=8000

# 可选
DEBUG=false
LOG_LEVEL=INFO
```

---

### 第四步：配置后端服务

#### 1. 选择 Backend 服务

Railway 会自动识别 Python 项目

#### 2. 设置根目录

如果 Railway 没有自动识别，手动设置：
- **Root Directory**: `backend`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT`

#### 3. 配置健康检查

在 **Settings** → **Healthcheck** 中：
- **Path**: `/health`
- **Interval**: 30s
- **Timeout**: 10s
- **Retry**: 3

---

### 第五步：配置前端服务（可选）

#### 方案A：独立部署前端（推荐用于生产）

创建新的 Railway 服务：

1. **New Service** → **Deploy from GitHub repo** → 选择同一仓库
2. **Root Directory**: `frontend`
3. **Build Command**: `npm run build`
4. **Start Command**: `npm start`
5. **环境变量**：
   ```bash
   NEXT_PUBLIC_API_URL=https://你的后端域名.railway.app
   ```

#### 方案B：前端部署到 Vercel（更快的CDN）

1. 访问 https://vercel.com
2. 导入你的 GitHub 仓库
3. 设置 **Root Directory** 为 `frontend`
4. 添加环境变量：`NEXT_PUBLIC_API_URL`
5. 点击 **Deploy**

---

### 第六步：获取公网域名

部署完成后，Railway 会自动分配域名：

```
https://你的项目名.up.railway.app
```

例如：
- **后端**: `https://smart-labeling-backend.up.railway.app`
- **前端**: `https://smart-labeling-frontend.up.railway.app`

#### 自定义域名（可选）

1. 在 Railway 项目的 **Settings** → **Domains**
2. 点击 **Add Domain**
3. 输入你的域名（如 `label.yourdomain.com`）
4. 配置 DNS CNAME 记录指向 Railway

---

## 验证部署

### 1. 检查后端健康状态

```bash
# 替换为你的 Railway 域名
curl https://你的项目名.up.railway.app/health
```

预期返回：
```json
{"status": "healthy"}
```

### 2. 访问 API 文档

浏览器打开：
```
https://你的项目名.up.railway.app/docs
```

### 3. 初始化数据库

Railway 控制台 → 选择服务 → **Diagnose** → **New Terminal**：

```bash
python scripts/init_db.py
```

### 4. 导入测试数据（可选）

```bash
python scripts/import_excel.py
```

---

## 成本估算

### Railway 免费额度（$5/月）

- **512 MB RAM**
- **1 GB 存储**
- **有限的带宽**
- **适合**: 开发测试、小规模使用

### 超出免费额度后

- **按量计费**: ~$0.00028/GB-hour
- **预计月费**:
  - 小规模使用（<1000次API调用/天）: $0-5
  - 中等使用（~10000次API调用/天）: $10-20
  - 高频使用（>50000次API调用/天）: $50+

### 成本优化建议

1. **仅部署后端到 Railway**，前端用 Vercel（完全免费）
2. **使用定时休眠**：非工作时间自动休眠
3. **优化数据库查询**：减少资源占用
4. **启用缓存**：减少重复 API 调用

---

## 监控和维护

### 查看日志

Railway 控制台 → 选择服务 → **Deployments** → 点击日志

### 设置告警

Railway 控制台 → **Settings** → **Notifications**:
- CPU 使用率 > 80%
- 内存使用 > 90%
- 服务崩溃重启

### 数据库备份

定期导出 SQLite 数据库：

```bash
# 在 Railway 终端中
cp /app/data/conversations.db /app/data/backup_$(date +%Y%m%d).db
# 下载到本地
railway cp /app/data/backup_20250115.db ./backup/
```

---

## 故障排查

### 问题1：服务无法启动

**检查**:
1. 环境变量是否正确设置
2. `requirements.txt` 是否包含所有依赖
3. 端口是否使用 `$PORT` 变量

**解决**:
```bash
# 查看构建日志
railway logs

# 重启服务
railway restart
```

### 问题2：API 请求失败

**检查**:
1. CORS 配置是否包含前端域名
2. `NEXT_PUBLIC_API_URL` 是否正确
3. 后端健康检查是否通过

**解决**:
在 `backend/app/main.py` 中添加 Railway 域名到 CORS：
```python
allow_origins=[
    "http://localhost:3000",
    "https://你的前端域名.vercel.app"
]
```

### 问题3：数据库连接失败

**原因**: Railway 每次部署会重置文件系统

**解决**: 使用持久化卷或改用 Railway PostgreSQL
```python
# 改用 Railway 提供的 PostgreSQL
DATABASE_URL=postgresql://user:pass@host/dbname
```

---

## 备选方案：Fly.io（备选）

如果 Railway 不满足需求，可以尝试 Fly.io：

### 快速开始

```bash
# 安装 Fly CLI
curl -L https://fly.io/install.sh | sh

# 登录
fly auth login

# 初始化项目
fly launch

# 部署到亚洲节点（新加坡）
fly deploy --region hkg

# 获取域名
fly apps list
```

---

## 下一步

部署完成后：

1. ✅ **配置自定义域名**（可选）
2. ✅ **设置数据库备份**
3. ✅ **配置监控告警**
4. ✅ **优化性能和成本**
5. ✅ **分享给用户测试**

---

## 技术支持

- **Railway 文档**: https://docs.railway.app/
- **Railway 社区**: https://community.railway.app/
- **项目文档**: [CLAUDE.md](CLAUDE.md)
- **问题反馈**: GitHub Issues

---

**祝部署顺利！🎉**

部署成功后，你将获得一个类似这样的公网访问地址：
```
后端: https://smart-labeling-backend.up.railway.app
前端: https://smart-labeling.vercel.app
```
