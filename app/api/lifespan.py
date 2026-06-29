# app/api/lifespan.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.clients.mysql_client_manager import meta_mysql_client_manager, dw_mysql_client_manager
from app.clients.qdrant_client_manager import qdrant_client_manager
from app.clients.embedding_client_manager import embedding_client_manager
from app.clients.es_client_manager import es_client_manager
from app.core.log import logger
import asyncio


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动（在事件循环中运行同步代码）
    logger.info("正在启动服务，初始化客户端...")

    # 同步初始化（用 run_in_executor 避免阻塞）
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, meta_mysql_client_manager.init)
    await loop.run_in_executor(None, dw_mysql_client_manager.init)
    await loop.run_in_executor(None, qdrant_client_manager.init)
    await loop.run_in_executor(None, embedding_client_manager.init)
    await loop.run_in_executor(None, es_client_manager.init)

    logger.info("所有客户端初始化完成，服务已就绪")

    yield

    # 关闭
    logger.info("正在关闭服务，清理客户端连接...")
    await loop.run_in_executor(None, meta_mysql_client_manager.close)
    await loop.run_in_executor(None, dw_mysql_client_manager.close)
    await loop.run_in_executor(None, qdrant_client_manager.close)
    await loop.run_in_executor(None, embedding_client_manager.close)
    await loop.run_in_executor(None, es_client_manager.close)
    logger.info("所有客户端已关闭，服务已停止")