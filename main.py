# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

from app.api.routers.query_router import query_router
from app.api.lifespan import lifespan

# 获取前端目录路径
frontend_path = Path(__file__).parent / "frontend"

app = FastAPI(
    title="Data Agent API",
    description="问数智能体服务",
    version="1.0.0",
    lifespan=lifespan
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册 API 路由
app.include_router(query_router)

# 托管前端静态文件
if frontend_path.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")


    @app.get("/")
    async def serve_frontend():
        """访问根路径时返回前端页面"""
        return FileResponse(str(frontend_path / "index.html"))

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)