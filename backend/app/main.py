from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.v1 import conversations, tags, export, recommendations, batches, admin
import importlib

# 导入import模块（import是Python关键字，需要使用importlib）
import_api = importlib.import_module('app.api.v1.import')

# 创建FastAPI应用
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    debug=settings.DEBUG,
    docs_url="/docs",
    redoc_url="/redoc"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(conversations.router, prefix="/api/v1", tags=["conversations"])
app.include_router(tags.router, prefix="/api/v1", tags=["tags"])
app.include_router(import_api.router, prefix="/api/v1/import", tags=["import"])
app.include_router(export.router, prefix="/api/v1/export", tags=["export"])
app.include_router(recommendations.router, prefix="/api/v1/recommendations", tags=["recommendations"])
app.include_router(batches.router, prefix="/api/v1", tags=["batches"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["admin"])


@app.get("/")
async def root():
    """健康检查"""
    return {
        "message": "智能打标便捷器API",
        "version": settings.VERSION,
        "status": "running"
    }


@app.get("/health")
async def health():
    """健康检查"""
    return {"status": "healthy"}
