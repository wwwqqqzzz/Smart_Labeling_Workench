# 生产环境部署指南

## 快速部署

### 1. 准备工作

确保服务器已安装：
- Docker 20.10+
- Docker Compose 2.0+

### 2. 配置环境变量

```bash
# 复制环境变量模板
cp .env.production.example .env.production

# 编辑配置文件，填入必需的API Keys
vim .env.production
```

**必需配置**：
```bash
GLM_API_KEY=your_glm_api_key_here
NEXT_PUBLIC_API_URL=http://your-domain.com
BACKEND_CORS_ORIGINS=["http://your-domain.com","https://your-domain.com"]
```

### 3. 一键部署

```bash
# 运行部署脚本
chmod +x deploy.sh
./deploy.sh
```

### 4. 访问应用

部署完成后访问：
- **前端**: http://your-domain.com
- **后端API**: http://your-domain.com/api/
- **API文档**: http://your-domain.com/docs

## 手动部署（不使用脚本）

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

## 配置SSL证书（可选）

### 使用Let's Encrypt免费证书

```bash
# 1. 安装certbot
apt-get update
apt-get install certbot

# 2. 获取证书
certbot certonly --standalone -d your-domain.com

# 3. 复制证书
mkdir -p nginx/ssl
cp /etc/letsencrypt/live/your-domain.com/fullchain.pem nginx/ssl/
cp /etc/letsencrypt/live/your-domain.com/privkey.pem nginx/ssl/

# 4. 修改nginx/nginx.conf，启用HTTPS配置
# 取消HTTPS server块的注释

# 5. 重启nginx
docker-compose -f docker-compose.prod.yml restart nginx
```

## 常用命令

### 服务管理

```bash
# 查看服务状态
docker-compose -f docker-compose.prod.yml ps

# 查看日志
docker-compose -f docker-compose.prod.yml logs -f

# 重启服务
docker-compose -f docker-compose.prod.yml restart

# 停止服务
docker-compose -f docker-compose.prod.yml down

# 更新服务
git pull
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d
```

### 数据库管理

```bash
# 进入后端容器
docker-compose -f docker-compose.prod.yml exec backend bash

# 初始化数据库
python scripts/init_db.py

# 数据库迁移
python scripts/migrate_add_batch.py

# 导入Excel
python scripts/import_excel.py

# 退出容器
exit
```

## 监控和维护

### 日志查看

```bash
# 实时日志
docker-compose -f docker-compose.prod.yml logs -f

# 查看特定服务日志
docker-compose -f docker-compose.prod.yml logs -f backend
docker-compose -f docker-compose.prod.yml logs -f frontend
docker-compose -f docker-compose.prod.yml logs -f nginx
```

### 健康检查

```bash
# 后端健康检查
curl http://localhost/health

# 前端健康检查
curl http://localhost:3000

# API测试
curl http://localhost/api/v1/
```

### 数据备份

```bash
# 备份数据库
docker-compose -f docker-compose.prod.yml exec backend \
  cp /app/data/conversations.db /app/data/backup_$(date +%Y%m%d).db

# 备份到本地
docker cp smartlabelingworkbench-backend-1:/app/data ./backup
```

## 性能优化

### 后端优化

- 工作进程数：设置为CPU核心数 * 2 + 1
- 超时时间：AI分析需要较长时间，建议60秒
- 缓存：Redis缓存RAG结果

### 前端优化

- Next.js自动优化构建
- Nginx启用Gzip压缩
- 静态资源CDN加速

## 故障排查

### 服务无法启动

```bash
# 查看详细日志
docker-compose -f docker-compose.prod.yml logs

# 检查端口占用
netstat -tlnp | grep -E ':(80|443|3000|8000)'

# 重建镜像
docker-compose -f docker-compose.prod.yml build --no-cache
```

### API请求失败

```bash
# 检查环境变量
docker-compose -f docker-compose.prod.yml exec backend env | grep API

# 检查后端日志
docker-compose -f docker-compose.prod.yml logs backend

# 测试API
curl http://localhost:8000/health
```

### 性能问题

```bash
# 查看资源使用
docker stats

# 限制资源使用
# 在docker-compose.prod.yml中添加：
# deploy:
#   resources:
#     limits:
#       cpus: '2'
#       memory: 2G
```

## 安全建议

1. **修改默认密码**（如使用数据库）
2. **配置防火墙**：只开放80/443端口
3. **启用HTTPS**：使用SSL证书
4. **定期更新**：保持系统和依赖最新
5. **数据备份**：定期备份数据库
6. **监控告警**：配置日志监控和告警

## 生产环境检查清单

部署前检查：

- [ ] API Keys已配置
- [ ] CORS白名单已设置
- [ ] DEBUG=false（生产环境）
- [ ] 数据库已初始化
- [ ] SSL证书已配置（如需要）
- [ ] 防火墙规则已设置
- [ ] 备份策略已配置
- [ ] 监控已配置

部署后验证：

- [ ] 前端可以访问
- [ ] 后端API正常响应
- [ ] API文档可以访问
- [ ] Excel导入功能正常
- [ ] AI推荐功能正常
- [ ] 健康检查正常
- [ ] 日志正常记录

## 支持

如遇到问题，请查看：
- 系统日志: `docker-compose -f docker-compose.prod.yml logs`
- API文档: http://your-domain.com/docs
- 开发文档: [docs/08-部署指南.md](docs/08-部署指南.md)
