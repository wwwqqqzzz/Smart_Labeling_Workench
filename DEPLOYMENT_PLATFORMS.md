# 公网部署平台对比 - 完整项目部署

## 🚨 当前问题

Railway 免费层构建时间限制约 **20 分钟**，而完整项目（包含 RAG 依赖）需要 **15-25 分钟**构建，经常超时。

---

## 📊 平台对比

| 平台 | 免费额度 | 构建时间限制 | 亚洲节点 | Docker支持 | 推荐度 |
|------|---------|-------------|---------|-----------|--------|
| **Railway** | $5/月 | ~20分钟 | ✅ 新加坡/日本 | ✅ | ⭐⭐⭐ |
| **Render** | 750小时/月 | ~30分钟 | ✅ 新加坡 | ✅ | ⭐⭐⭐⭐⭐ |
| **Fly.io** | $5/月 | ~60分钟 | ✅ 香港/新加坡 | ✅ | ⭐⭐⭐⭐⭐ |
| **Zeabur** | 按量计费 | ~60分钟 | ✅ 香港/日本/新加坡 | ✅ | ⭐⭐⭐⭐⭐ |
| **Hetzner** + 自建 | €5/月 | 无限制 | ❌ 德国 | ✅ | ⭐⭐⭐ |

---

## 🏆 推荐方案：Render.com（最适合）

### 为什么选择 Render？

✅ **更长的构建时间**：30-60 分钟（足够安装大型依赖）
✅ **免费额度充足**：750 小时/月（约 31 天全天运行）
✅ **亚洲节点**：新加坡区域
✅ **Docker 支持**：直接使用现有 Dockerfile
✅ **自动 HTTPS**：无需配置
✅ **GitHub 集成**：推送自动部署
✅ **持久化存储**：免费 1GB（足够 SQLite 数据库）

---

## 🚀 Render 部署步骤（5分钟）

### 第一步：准备配置文件

我已经为您创建了 `Dockerfile`，可以直接使用。

### 第二步：在 Render 创建服务

1. **访问** https://render.com
2. **Sign Up** → 使用 GitHub 登录
3. **New** → **Web Service**
4. **连接 GitHub 仓库**：选择 `wwwqqqzzz/Smart_Labeling_Workench`
5. **配置服务**：

```
Name: smart-labeling-backend
Region: Singapore (推荐亚洲节点)
Branch: main
Runtime: Docker
Dockerfile Path: ./Dockerfile
```

### 第三步：配置环境变量

在 **Environment** 部分添加：

```bash
GLM_API_KEY=a82735f90df14d3c9ea555ed2583c574.Vl6VEVFaKNg7dipH
OPENAI_API_KEY=你的密钥（可选）
DATABASE_URL=sqlite:///./data/conversations.db
PORT=8000
```

### 第四步：部署

点击 **Create Web Service**，Render 会自动：
1. 拉取代码
2. 构建 Docker 镜像（30-60 分钟，有足够时间）
3. 部署到新加坡节点
4. 分配公网 URL：`https://smart-labeling-backend.onrender.com`

### 第五步：初始化数据库

部署成功后，使用 Render Shell：
1. 进入服务 → **Shell** 标签
2. 运行：
```bash
cd backend
python scripts/init_db.py
```

---

## 🎯 备选方案：Fly.io（推荐）

### 为什么选择 Fly.io？

✅ **全球边缘网络**：香港、新加坡、日本节点
✅ **超长构建时间**：最多 60 分钟
✅ **免费额度**：$5/月
✅ **性能强劲**：独占 CPU，不像 Railway 共享
✅ **灵活部署**：支持 Dockerfile

### Fly.io 部署步骤

```bash
# 1. 安装 Fly CLI
curl -L https://fly.io/install.sh | sh

# 2. 登录
fly auth login

# 3. 初始化项目
cd "/Users/wang/项目/Smart Labeling Workbench"
fly launch

# 4. 选择区域
# Singapore (sin) 或 Hong Kong (hkg)

# 5. 部署
fly deploy --region hkg

# 6. 设置环境变量
fly secrets set GLM_API_KEY=a82735f90df14d3c9ea555ed2583c574.Vl6VEVFaKNg7dipH

# 7. 初始化数据库
fly ssh console
cd backend && python scripts/init_db.py
```

---

## 🎁 备选方案：Zeabur（推荐，亚洲友好）

### 为什么选择 Zeabur？

✅ **亚洲优化**：专为亚洲用户设计
✅ **多区域**：香港、日本、新加坡、台湾
✅ **超长构建**：60+ 分钟
✅ **简单易用**：界面友好，中文支持
✅ **按量计费**：只为使用量付费

### Zeabur 部署步骤

1. **访问** https://zeabur.com
2. **GitHub 登录**
3. **New Project** → 选择仓库
4. **选择区域**：香港/新加坡
5. **配置环境变量**
6. **部署**

---

## 💡 最终推荐

### 如果您想要：
- **最简单**：选择 **Render**（界面友好，配置简单）
- **最稳定**：选择 **Fly.io**（性能强，全球边缘网络）
- **亚洲最优**：选择 **Zeabur**（专为亚洲优化）
- **继续尝试 Railway**：使用优化的 Dockerfile（但可能还会超时）

---

## 🔧 当前优化的 Dockerfile

我已经更新了 `Dockerfile`，使用清华镜像加速：

```dockerfile
# 使用清华镜像加速 pip 安装
RUN pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
```

这能将安装速度提升 **3-5 倍**，但 Railway 的构建时间限制仍然是瓶颈。

---

## 📝 总结建议

| 需求 | 推荐平台 | 理由 |
|------|---------|------|
| 快速部署 | Render | 界面简单，构建时间长 |
| 亚洲访问 | Zeabur | 香港节点，延迟低 |
| 性能优先 | Fly.io | 独占CPU，全球CDN |
| 学习目的 | Railway | 文档丰富，社区活跃 |

---

**我的建议：使用 Render.com**，最简单可靠，构建时间足够，免费额度充足。

需要我帮您配置 Render 部署吗？
