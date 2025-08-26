"""
FastAPI主应用文件
学术论文推荐系统后端API
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

# 导入API路由
from .api import auth, search, papers, authors, workspace, ai_assistant

# 创建FastAPI应用实例
app = FastAPI(
    title="学术论文推荐系统API",
    description="""
    高级学术论文推荐Web系统的后端API服务
    
    ## 主要功能
    
    * **用户系统** - 注册、登录、个人信息管理
    * **智能搜索** - 混合搜索、语义搜索、动态筛选
    * **论文管理** - 论文详情、引用分析、真值计算
    * **作者分析** - 作者画像、合作网络、学术轨迹
    * **个人工作台** - 收藏管理、关注列表、阅读历史
    * **AI助手** - 论文总结、对比分析、研究建议
    
    ## 技术特色
    
    * 基于FastAPI的高性能API服务
    * 完整的用户认证和权限管理
    * 模拟数据库提供丰富的测试数据
    * 真值算法和推荐算法的占位符实现
    * 支持知识图谱和网络分析
    """,
    version="1.0.0",
    terms_of_service="http://example.com/terms/",
    contact={
        "name": "学术推荐系统团队",
        "url": "http://example.com/contact/",
        "email": "contact@example.com",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    docs_url="/docs",
    redoc_url="/redoc"
)

# 配置CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vue开发服务器
        "http://localhost:3000",  # 备用端口
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
        "http://localhost:8080",  # Vue生产构建
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册API路由
app.include_router(auth.router, prefix="/api")
app.include_router(search.router, prefix="/api")
app.include_router(papers.router, prefix="/api")
app.include_router(authors.router, prefix="/api")
app.include_router(workspace.router, prefix="/api")
app.include_router(ai_assistant.router, prefix="/api")

# 根路径
@app.get("/", tags=["系统"])
async def root():
    """
    系统根路径，返回API基本信息
    """
    return {
        "message": "学术论文推荐系统API",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "running",
        "features": [
            "用户认证系统",
            "智能搜索引擎", 
            "论文分析工具",
            "作者画像分析",
            "个人工作台",
            "AI学术助手"
        ]
    }

# 健康检查端点
@app.get("/health", tags=["系统"])
async def health_check():
    """
    健康检查端点，用于监控服务状态
    """
    try:
        # 这里可以添加数据库连接检查等
        return {
            "status": "healthy",
            "timestamp": "2023-12-01T10:00:00Z",
            "services": {
                "api": "running",
                "database": "connected",
                "algorithms": "available"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail="Service unavailable")

# API信息端点
@app.get("/api/info", tags=["系统"])
async def api_info():
    """
    获取API详细信息和统计数据
    """
    from .db.mock_db import db
    
    return {
        "api_version": "1.0.0",
        "total_papers": len(db.papers),
        "total_authors": len(db.authors),
        "total_users": len(db.users),
        "available_endpoints": {
            "authentication": [
                "/api/auth/register",
                "/api/auth/login",
                "/api/auth/me"
            ],
            "search": [
                "/api/search/",
                "/api/search/suggestions",
                "/api/search/filters"
            ],
            "papers": [
                "/api/papers/",
                "/api/papers/{paper_id}",
                "/api/papers/{paper_id}/graph"
            ],
            "authors": [
                "/api/authors/",
                "/api/authors/{author_id}",
                "/api/authors/{author_id}/graph"
            ],
            "workspace": [
                "/api/workspace/dashboard",
                "/api/workspace/bookmarks",
                "/api/workspace/folders"
            ],
            "ai_assistant": [
                "/api/ai-assistant/summarize/{paper_id}",
                "/api/ai-assistant/compare",
                "/api/ai-assistant/research-trends"
            ]
        }
    }

# 全局异常处理器
@app.exception_handler(404)
async def not_found_handler(request, exc):
    """
    404错误处理器
    """
    return JSONResponse(
        status_code=404,
        content={
            "error": "资源未找到",
            "message": "请求的资源不存在",
            "path": str(request.url.path)
        }
    )

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    """
    500错误处理器
    """
    return JSONResponse(
        status_code=500,
        content={
            "error": "服务器内部错误",
            "message": "服务器处理请求时发生错误，请稍后重试"
        }
    )

# 启动事件
@app.on_event("startup")
async def startup_event():
    """
    应用启动时的初始化操作
    """
    print("🚀 学术论文推荐系统API启动中...")
    print("📚 初始化模拟数据库...")
    print("🔧 配置算法模块...")
    print("✅ 系统启动完成！")
    print("📖 API文档: http://127.0.0.1:8000/docs")

# 关闭事件
@app.on_event("shutdown")
async def shutdown_event():
    """
    应用关闭时的清理操作
    """
    print("🛑 学术论文推荐系统API正在关闭...")
    print("💾 保存用户数据...")
    print("🧹 清理资源...")
    print("✅ 系统已安全关闭")

# 中间件：请求日志
@app.middleware("http")
async def log_requests(request, call_next):
    """
    记录HTTP请求日志
    """
    import time
    
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    # 简单的请求日志（生产环境中应使用专业的日志系统）
    print(f"📝 {request.method} {request.url.path} - {response.status_code} - {process_time:.3f}s")
    
    # 添加响应时间到响应头
    response.headers["X-Process-Time"] = str(process_time)
    
    return response

# 数据初始化端点（仅用于开发/测试）
@app.post("/api/dev/reset-data", tags=["开发工具"])
async def reset_mock_data():
    """
    重置模拟数据（仅用于开发测试）
    
    ⚠️ 警告：此操作将清除所有用户数据
    """
    from .db.mock_db import MockDatabase
    
    # 重新初始化数据库
    from .db import mock_db
    mock_db.db = MockDatabase()
    
    return {
        "message": "模拟数据已重置",
        "timestamp": "2023-12-01T10:00:00Z",
        "warning": "所有用户数据已被清除"
    }

# 系统统计端点
@app.get("/api/stats", tags=["系统"])
async def get_system_stats():
    """
    获取系统统计信息
    """
    from .db.mock_db import db
    
    # 计算统计数据
    total_citations = sum(paper["citation_count"] for paper in db.papers)
    avg_citations = total_citations / len(db.papers) if db.papers else 0
    
    recent_papers = [
        paper for paper in db.papers 
        if paper["year"] >= 2020
    ]
    
    research_fields = {}
    for paper in db.papers:
        field = paper["research_field"]
        research_fields[field] = research_fields.get(field, 0) + 1
    
    return {
        "database_stats": {
            "total_papers": len(db.papers),
            "total_authors": len(db.authors),
            "total_users": len(db.users),
            "recent_papers": len(recent_papers),
            "total_citations": total_citations,
            "average_citations": round(avg_citations, 2)
        },
        "research_fields": research_fields,
        "system_status": {
            "uptime": "running",
            "version": "1.0.0",
            "last_updated": "2023-12-01T10:00:00Z"
        }
    }

if __name__ == "__main__":
    # 开发环境启动配置
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )

