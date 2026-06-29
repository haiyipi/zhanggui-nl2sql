# app/api/dependencies.py
from app.services.query_service import QueryService
from app.clients.mysql_client_manager import meta_mysql_client_manager, dw_mysql_client_manager
from app.clients.qdrant_client_manager import qdrant_client_manager
from app.clients.es_client_manager import es_client_manager
from app.clients.embedding_client_manager import embedding_client_manager
from app.repositories.mysql.meta.meta_mysql_repository import MetaMysqlRepository
from app.repositories.mysql.dw.dw_mysql_repository import DWMYSQLRepository
from app.repositories.qdrant.column_qdrant_repository import ColumnQdrantRepository
from app.repositories.qdrant.metric_qdrant_repository import MetricQdrantRepository
from app.repositories.es.value_es_repository import ValueEsRepository


def get_query_service():
    # 同步获取 session
    meta_session = meta_mysql_client_manager.session_factory()
    dw_session = dw_mysql_client_manager.session_factory()

    meta_repo = MetaMysqlRepository(meta_session)
    dw_repo = DWMYSQLRepository(dw_session)
    column_repo = ColumnQdrantRepository(qdrant_client_manager.client)
    metric_repo = MetricQdrantRepository(qdrant_client_manager.client)
    value_repo = ValueEsRepository(es_client_manager.client)

    return QueryService(
        meta_mysql_repo=meta_repo,
        dw_mysql_repo=dw_repo,
        column_qdrant_repo=column_repo,
        metric_qdrant_repo=metric_repo,
        value_es_repo=value_repo,
        embedding_client=embedding_client_manager
    )