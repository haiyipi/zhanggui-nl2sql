import argparse
import asyncio
from pathlib import Path

from app.clients.embedding_client_manager import embedding_client_manager
from app.clients.es_client_manager import es_client_manager
from app.clients.mysql_client_manager import meta_mysql_client_manager, dw_mysql_client_manager
from app.clients.qdrant_client_manager import qdrant_client_manager
from app.core.log import logger
from app.repositories.es.value_es_repository import ValueEsRepository
from app.repositories.mysql.meta.meta_mysql_repository import MetaMysqlRepository
from app.repositories.mysql.dw.dw_mysql_repository import DWMYSQLRepository  # 修正这里
from app.repositories.qdrant.column_qdrant_repository import ColumnQdrantRepository
from app.repositories.qdrant.metric_qdrant_repository import MetricQdrantRepository
from app.services.meta_knowledge_service import MetaKnowledgeService

async def build(config_path: Path):
    await meta_mysql_client_manager.init()
    await dw_mysql_client_manager.init()
    await qdrant_client_manager.init()
    await embedding_client_manager.init()
    await es_client_manager.init()

    async with meta_mysql_client_manager.session_factory() as meta_session:
        async with dw_mysql_client_manager.session_factory() as dw_session:
            meta_mysql_repository = MetaMysqlRepository(meta_session)
            dw_mysql_repository = DWMYSQLRepository(dw_session)
            column_qdrant_repository = ColumnQdrantRepository(qdrant_client_manager.client)
            value_es_repository = ValueEsRepository(es_client_manager.client)
            metric_qdrant_repository = MetricQdrantRepository(qdrant_client_manager.client)

            # build_meta_knowledge.py 第 34-39 行
            meta_knowledge_service = MetaKnowledgeService(
                meta_mysql_repository,
                dw_mysql_repository,
                column_qdrant_repository,
                embedding_client=embedding_client_manager,  # 去掉 .client
                value_es_repository=value_es_repository,
                metric_qdrant_repository=metric_qdrant_repository
            )
            await meta_knowledge_service.build(config_path)

    await meta_mysql_client_manager.close()
    await dw_mysql_client_manager.close()
    await qdrant_client_manager.close()
    await embedding_client_manager.close()
    await es_client_manager.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--conf', required=True, help='配置文件路径')
    args = parser.parse_args()
    config_path = args.conf
    logger.info(f"使用配置文件: {config_path}")
    asyncio.run(build(Path(config_path)))


