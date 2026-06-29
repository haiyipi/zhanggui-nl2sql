import uuid
from pathlib import Path
from typing import List, Optional
from dataclasses import asdict

from omegaconf import OmegaConf

from app.conf.meta_config import MetaConfig
from app.core.log import logger
from app.entities.column_info import ColumnInfo
from app.entities.table_info import TableInfo
from app.entities.metric_info import MetricInfo
from app.entities.column_metric import ColumnMetric
from app.entities.value_info import ValueInfo
from app.repositories.mysql.meta.meta_mysql_repository import MetaMysqlRepository
from app.repositories.mysql.dw.dw_mysql_repository import DWMYSQLRepository
from app.repositories.qdrant.column_qdrant_repository import ColumnQdrantRepository
from app.repositories.es.value_es_repository import ValueEsRepository
from app.repositories.qdrant.metric_qdrant_repository import MetricQdrantRepository


class MetaKnowledgeService:
    def __init__(
            self,
            meta_mysql_repository: MetaMysqlRepository,
            dw_mysql_repository: DWMYSQLRepository,
            column_qdrant_repository: ColumnQdrantRepository,
            embedding_client,
            value_es_repository: ValueEsRepository,
            metric_qdrant_repository: MetricQdrantRepository
    ):
        self.meta_mysql_repository = meta_mysql_repository
        self.dw_mysql_repository = dw_mysql_repository
        self.column_qdrant_repository = column_qdrant_repository
        self.embedding_client = embedding_client
        self.value_es_repository = value_es_repository
        self.metric_qdrant_repository = metric_qdrant_repository

    # ==================== 主流程 ====================

    async def build(self, config_path: Path):
        # 1. 读取配置文件
        context = OmegaConf.load(config_path)
        schema = OmegaConf.structured(MetaConfig)
        meta_config: MetaConfig = OmegaConf.to_object(OmegaConf.merge(schema, context))

        logger.info(f"加载配置文件完成")

        # 2. 处理表信息
        if meta_config.tables:
            table_infos: list[TableInfo] = []
            column_infos: list[ColumnInfo] = []

            for table in meta_config.tables:
                table_id = f"T_{table.name}"

                table_info = TableInfo(
                    id=table_id,
                    name=table.name,
                    role=table.role,
                    description=table.description
                )
                table_infos.append(table_info)

                column_types = await self.dw_mysql_repository.get_column_types(table.name)

                for column in table.columns:
                    column_value = await self.dw_mysql_repository.get_column_values(table.name, column.name)

                    column_info = ColumnInfo(
                        id=f'{table.name}.{column.name}',
                        name=column.name,
                        type=column_types.get(column.name, 'unknown'),
                        role=column.role,
                        examples=column_value,
                        description=column.description,
                        alias=column.alias,
                        table_id=table_id
                    )
                    column_infos.append(column_info)

            # 保存到数据库
            async with self.meta_mysql_repository.session.begin():
                await self.meta_mysql_repository.save_table_infos(table_infos)
                await self.meta_mysql_repository.save_column_infos(column_infos)

            logger.info(f"保存 {len(table_infos)} 个表和 {len(column_infos)} 个字段到 meta 数据库")

            # 2.2 对字段信息建立向量索引
            await self.column_qdrant_repository.ensure_collection()
            points: list[dict] = []

            for column_info in column_infos:
                points.append({
                    'id': uuid.uuid4().hex,
                    'embedding_text': column_info.name,
                    'payload': asdict(column_info)
                })
                points.append({
                    'id': uuid.uuid4().hex,
                    'embedding_text': column_info.description,
                    'payload': asdict(column_info)
                })
                for alias in column_info.alias:
                    points.append({
                        "id": uuid.uuid4().hex,
                        "embedding_text": alias,
                        "payload": asdict(column_info)
                    })

            # 向量化
            embedding_texts = [point['embedding_text'] for point in points]
            embeddings: list[list[float]] = []
            embedding_batch_size = 20

            for i in range(0, len(embedding_texts), embedding_batch_size):
                batch = embedding_texts[i:i + embedding_batch_size]
                batch_embeddings = await self.embedding_client.embed_documents(batch)
                embeddings.extend(batch_embeddings)

            ids = [point['id'] for point in points]
            payloads = [point['payload'] for point in points]

            await self.column_qdrant_repository.upsert(ids, embeddings, payloads)
            logger.info(f"为 {len(column_infos)} 个字段建立了向量索引")

            # 2.3 对指定的维度字段取值建立全文索引
            await self.value_es_repository.ensure_index()
            value_infos: list[ValueInfo] = []

            for table in meta_config.tables:
                for column in table.columns:
                    if column.sync:
                        current_column_values = await self.dw_mysql_repository.get_column_values(
                            table.name, column.name, 100000
                        )
                        new_infos = [
                            ValueInfo(
                                id=f"{table.name}.{column.name}.{value}",
                                value=value,
                                column_id=f"{table.name}.{column.name}"
                            )
                            for value in current_column_values
                        ]
                        value_infos.extend(new_infos)

            await self.value_es_repository.index(value_infos)
            logger.info(f"为字段取值建立了全文索引，共 {len(value_infos)} 条")

        # 3. 处理指标信息
        if meta_config.metrics:
            # 3.1 将指标信息保存到 meta 数据库中
            metric_infos, column_metrics = await self._save_metrics_to_meta_db(meta_config)

            # 3.2 对指标信息建立向量索引
            await self.metric_qdrant_repository.ensure_collection()
            points: list[dict] = []

            for metric_info in metric_infos:
                points.append({
                    'id': uuid.uuid4().hex,
                    'embedding_text': metric_info.name,
                    'payload': asdict(metric_info)
                })
                points.append({
                    'id': uuid.uuid4().hex,
                    'embedding_text': metric_info.description,
                    'payload': asdict(metric_info)
                })
                for alias in metric_info.alias:
                    points.append({
                        "id": uuid.uuid4().hex,
                        "embedding_text": alias,
                        "payload": asdict(metric_info)
                    })

            # 向量化
            embedding_texts = [point['embedding_text'] for point in points]
            embeddings: list[list[float]] = []
            embedding_batch_size = 20

            for i in range(0, len(embedding_texts), embedding_batch_size):
                batch = embedding_texts[i:i + embedding_batch_size]
                batch_embeddings = await self.embedding_client.embed_documents(batch)
                embeddings.extend(batch_embeddings)

            ids = [point['id'] for point in points]
            payloads = [point['payload'] for point in points]

            await self.metric_qdrant_repository.upsert(ids, embeddings, payloads)
            logger.info(f"为 {len(metric_infos)} 个指标建立了向量索引")

        logger.info("元数据知识库构建完成")

    # ==================== 辅助方法 ====================

    async def _save_metrics_to_meta_db(self, meta_config: MetaConfig):
        """保存指标信息到数据库"""
        metric_infos: list[MetricInfo] = []
        column_metrics: list[ColumnMetric] = []

        for metric in meta_config.metrics:
            # metric -> MetricInfo
            metric_info = MetricInfo(
                id=metric.name,
                name=metric.name,
                description=metric.description,
                relevant_columns=metric.relevant_columns,
                alias=metric.alias
            )
            metric_infos.append(metric_info)

            for column in metric.relevant_columns:
                column_metric = ColumnMetric(
                    column_id=column,
                    metric_id=metric.name
                )
                column_metrics.append(column_metric)

        async with self.meta_mysql_repository.session.begin():
            await self.meta_mysql_repository.save_metric_infos(metric_infos)
            await self.meta_mysql_repository.save_column_metrics(column_metrics)

        logger.info(f"保存 {len(metric_infos)} 个指标到 meta 数据库")

        return metric_infos, column_metrics