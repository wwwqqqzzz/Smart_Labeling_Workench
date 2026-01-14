# 快速部署指南

## 🚀 5分钟快速部署到生产环境

### 前置要求

- Docker 20.10+
- Docker Compose 2.0+
- 服务器：2核CPU + 4GB内存（最小配置）

### 部署步骤

#### 1. 克隆项目

```bash
git clone <repository-url>
cd Smart-Labeling-Workbench
```

#### 2. 配置环境变量

```bash
# 复制环境变量模板
cp .env.production.example .env.production

# 编辑配置（必需）
vim .env.production
```

**最少配置**：
```bash
GLM_API_KEY=你的智谱API密钥
NEXT_PUBLIC_API_URL=http://你的域名或IP
BACKEND_CORS_ORIGINS=["http://你的域名或IP"]
```

#### 3. 一键部署

```bash
# 给脚本执行权限
chmod +x deploy.sh

# 运行部署
./deploy.sh
```

#### 4. 访问应用

打开浏览器访问：
- **应用主页**: http://你的域名或IP
- **API文档**: http://你的域名或IP/docs

---

## 📋 详细部署文档

完整的部署指南请查看：
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - 生产环境完整部署文档
- **[docs/08-部署指南.md](docs/08-部署指南.md)** - 详细的部署说明

---

## 🔧 常用命令

```bash
# 查看服务状态
docker-compose -f docker-compose.prod.yml ps

# 查看日志
docker-compose -f docker-compose.prod.yml logs -f

# 停止服务
docker-compose -f docker-compose.prod.yml down

# 重启服务
docker-compose -f docker-compose.prod.yml restart
```

---

## 🐛 遇到问题？

1. **端口被占用**
   ```bash
   # 检查端口
   netstat -tlnp | grep -E ':(80|8000|3000)'
   
   # 修改docker-compose.prod.yml中的端口映射
   ```

2. **API请求失败**
   ```bash
   # 检查环境变量
   docker-compose -f docker-compose.prod.yml exec backend env | grep API
   
   # 查看后端日志
   docker-compose -f docker-compose.prod.yml logs backend
   ```

3. **服务无法启动**
   ```bash
   # 查看详细日志
   docker-compose -f docker-compose.prod.yml logs
   
   # 重建镜像
   docker-compose -f docker-compose.prod.yml build --no-cache
   ```

---

## 📞 技术支持

详细文档：
- [部署指南](DEPLOYMENT.md)
- [开发者文档](docs/07-开发者文档.md)
- [故障排查](docs/08-部署指南.md#故障排查)
