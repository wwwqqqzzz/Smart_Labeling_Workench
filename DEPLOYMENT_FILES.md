# 部署相关文件说明

## 📁 部署文件列表

### 核心配置文件

1. **docker-compose.prod.yml**
   - 生产环境Docker Compose配置
   - 包含：Nginx、Frontend、Backend服务
   - 优化：健康检查、资源限制、自动重启

2. **.env.production.example**
   - 生产环境变量模板
   - 包含所有必需的配置项
   - 需要复制为.env.production并填写实际值

3. **nginx/nginx.conf**
   - Nginx反向代理配置
   - 路由配置、负载均衡、Gzip压缩
   - SSL配置模板（HTTPS）

### Docker镜像文件

4. **backend/Dockerfile.prod**
   - 后端生产环境Dockerfile
   - 多阶段构建、镜像优化
   - 非root用户运行、健康检查

5. **frontend/Dockerfile.prod**
   - 前端生产环境Dockerfile
   - Next.js standalone输出
   - 优化的生产构建

### 部署脚本

6. **deploy.sh**
   - 一键部署脚本
   - 自动检查依赖、构建镜像、启动服务
   - 健康检查、状态显示

7. **check-deployment.sh**
   - 部署检查脚本
   - 检查服务状态、健康检查
   - 功能验证

### 文档文件

8. **DEPLOYMENT.md**
   - 完整的生产环境部署指南
   - 手动部署步骤、SSL配置、故障排查

9. **QUICK_START.md**
   - 5分钟快速部署指南
   - 最小化配置、快速上手

10. **docs/08-部署指南.md**
    - 详细的部署文档
    - 包含开发环境和生产环境

## 🚀 快速开始

### 最快部署方式（推荐）

```bash
# 1. 配置环境变量
cp .env.production.example .env.production
vim .env.production  # 填入GLM_API_KEY等必需配置

# 2. 一键部署
chmod +x deploy.sh
./deploy.sh

# 3. 检查部署
chmod +x check-deployment.sh
./check-deployment.sh
```

### 手动部署（高级用户）

```bash
# 1. 构建镜像
docker-compose -f docker-compose.prod.yml build

# 2. 启动服务
docker-compose -f docker-compose.prod.yml up -d

# 3. 查看状态
docker-compose -f docker-compose.prod.yml ps

# 4. 查看日志
docker-compose -f docker-compose.prod.yml logs -f
```

## 📋 部署前检查清单

### 必需配置

- [ ] GLM_API_KEY已配置
- [ ] NEXT_PUBLIC_API_URL已配置
- [ ] BACKEND_CORS_ORIGINS已配置
- [ ] 端口80/443未被占用

### 可选配置

- [ ] SSL证书已配置（HTTPS）
- [ ] PostgreSQL已配置（生产数据库）
- [ ] Redis已配置（缓存）
- [ ] 防火墙规则已设置

### 部署后验证

运行检查脚本：
```bash
./check-deployment.sh
```

或手动验证：
- [ ] 前端可以访问
- [ ] 后端API正常响应
- [ ] API文档可以访问
- [ ] 健康检查正常

## 🔧 配置说明

### 环境变量详解

**GLM_API_KEY**（必需）
- 智谱AI的API密钥
- 用于AI标签推荐功能
- 获取地址：https://open.bigmodel.cn/

**NEXT_PUBLIC_API_URL**（必需）
- 前端访问后端的地址
- 示例：http://your-domain.com
- 使用Nginx代理时用域名或IP

**BACKEND_CORS_ORIGINS**（必需）
- 允许的前端域名列表
- JSON数组格式
- 示例：["http://localhost","http://your-domain.com"]

**DATABASE_URL**（可选）
- 数据库连接字符串
- 默认：SQLite（无需配置）
- 生产建议：PostgreSQL

### Nginx配置说明

**默认配置**：
- HTTP端口：80
- HTTPS端口：443（需要SSL证书）
- 前端代理：/
- 后端API代理：/api/
- API文档：/docs

**自定义配置**：
编辑 `nginx/nginx.conf`，修改：
- 端口映射
- SSL证书路径
- 超时时间
- 缓存策略

## 📊 服务架构

```
Internet
    ↓
[Nginx :80/:443]
    ↓
    ├─→ [Frontend :3000]  Next.js应用
    └─→ [Backend :8000]   FastAPI应用
            ↓
        [SQLite DB]       数据存储
```

## 🔍 故障排查

### 常见问题

1. **端口被占用**
   ```bash
   # 检查端口
   netstat -tlnp | grep :80
   
   # 修改docker-compose.prod.yml中的端口
   ports:
     - "8080:80"  # 使用8080端口
   ```

2. **环境变量未加载**
   ```bash
   # 检查环境变量
   docker-compose -f docker-compose.prod.yml config
   
   # 重新加载
   docker-compose -f docker-compose.prod.yml down
   docker-compose -f docker-compose.prod.yml up -d
   ```

3. **服务无法启动**
   ```bash
   # 查看详细日志
   docker-compose -f docker-compose.prod.yml logs -f
   
   # 重建镜像
   docker-compose -f docker-compose.prod.yml build --no-cache
   docker-compose -f docker-compose.prod.yml up -d
   ```

### 日志位置

- Nginx日志：`nginx/logs/`
- Docker日志：`docker-compose logs`
- 应用日志：容器内 `/app/logs/`

## 📞 获取帮助

- 完整文档：[DEPLOYMENT.md](DEPLOYMENT.md)
- 快速开始：[QUICK_START.md](QUICK_START.md)
- 详细指南：[docs/08-部署指南.md](docs/08-部署指南.md)
- 检查部署：`./check-deployment.sh`

## 🔄 更新部署

```bash
# 1. 备份数据
docker-compose -f docker-compose.prod.yml exec backend \
  cp /app/data/conversations.db /app/data/backup.db

# 2. 拉取最新代码
git pull

# 3. 重建并启动
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d

# 4. 验证部署
./check-deployment.sh
```

## 🎯 生产环境建议

1. **使用PostgreSQL**：更稳定、更安全
2. **配置SSL证书**：启用HTTPS加密
3. **设置防火墙**：只开放80/443端口
4. **定期备份**：每日备份数据库
5. **监控告警**：配置日志监控和性能监控
6. **负载均衡**：多实例部署提高可用性
