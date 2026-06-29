# app/repositories/mysql/meta/meta_mysql_repository.py
from abc import ABCMeta
from typing import List, Optional
from sqlalchemy import text, select
from sqlalchemy.dialects.mysql import insert

from app.entities.column_info import ColumnInfo
from app.entities.table_info import TableInfo
from app.entities.metric_info import MetricInfo
from app.entities.column_metric import ColumnMetric
from app.repositories.mysql.meta.mappers.column_info_mapper import ColumnInfoMapper
from app.repositories.mysql.meta.mappers.table_info_mapper import TableInfoMapper
from app.repositories.mysql.meta.mappers.metric_info_mapper import MetricInfoMapper
from app.repositories.mysql.meta.mappers.column_metric_mapper import ColumnMetricMapper
from app.models.column_info import ColumnInfoMySQL
from app.models.table_info import TableInfoMySQL
from app.models.metric_info import MetricInfoMySQL
from app.models.column_metric import ColumnMetricMySQL


class MetaMysqlRepository(metaclass=ABCMeta):
    def __init__(self, session):
        self.session = session

    def save_table_infos(self, table_infos: List[TableInfo]):
        if not table_infos:
            return
        values_list = []
        for table_info in table_infos:
            values_list.append({
                "id": table_info.id,
                "name": table_info.name,
                "role": table_info.role,
                "description": table_info.description
            })
        stmt = insert(TableInfoMySQL).values(values_list)
        update_stmt = stmt.on_duplicate_key_update(
            name=stmt.inserted.name,
            role=stmt.inserted.role,
            description=stmt.inserted.description
        )
        self.session.execute(update_stmt)

    def save_column_infos(self, column_infos: List[ColumnInfo]):
        if not column_infos:
            return
        values_list = []
        for column_info in column_infos:
            values_list.append({
                "id": column_info.id,
                "name": column_info.name,
                "type": column_info.type,
                "role": column_info.role,
                "examples": column_info.examples,
                "description": column_info.description,
                "alias": column_info.alias,
                "table_id": column_info.table_id
            })
        stmt = insert(ColumnInfoMySQL).values(values_list)
        update_stmt = stmt.on_duplicate_key_update(
            name=stmt.inserted.name,
            type=stmt.inserted.type,
            role=stmt.inserted.role,
            examples=stmt.inserted.examples,
            description=stmt.inserted.description,
            alias=stmt.inserted.alias,
            table_id=stmt.inserted.table_id
        )
        self.session.execute(update_stmt)

    def save_metric_infos(self, metric_infos: List[MetricInfo]):
        if not metric_infos:
            return
        values_list = []
        for metric_info in metric_infos:
            values_list.append({
                "id": metric_info.id,
                "name": metric_info.name,
                "description": metric_info.description,
                "relevant_columns": metric_info.relevant_columns,
                "alias": metric_info.alias
            })
        stmt = insert(MetricInfoMySQL).values(values_list)
        update_stmt = stmt.on_duplicate_key_update(
            name=stmt.inserted.name,
            description=stmt.inserted.description,
            relevant_columns=stmt.inserted.relevant_columns,
            alias=stmt.inserted.alias
        )
        self.session.execute(update_stmt)

    def save_column_metrics(self, column_metrics: List[ColumnMetric]):
        if not column_metrics:
            return
        values_list = []
        for column_metric in column_metrics:
            values_list.append({
                "column_id": column_metric.column_id,
                "metric_id": column_metric.metric_id
            })
        stmt = insert(ColumnMetricMySQL).values(values_list)
        update_stmt = stmt.on_duplicate_key_update(
            column_id=stmt.inserted.column_id,
            metric_id=stmt.inserted.metric_id
        )
        self.session.execute(update_stmt)

    def get_column_info_by_id(self, column_id: str) -> Optional[ColumnInfo]:
        result = self.session.execute(
            select(ColumnInfoMySQL).where(ColumnInfoMySQL.id == column_id)
        )
        model = result.scalar_one_or_none()
        if model:
            return ColumnInfoMapper.to_entity(model)
        return None

    def get_table_info_by_id(self, table_id: str) -> Optional[TableInfo]:
        result = self.session.execute(
            select(TableInfoMySQL).where(TableInfoMySQL.id == table_id)
        )
        model = result.scalar_one_or_none()
        if model:
            return TableInfoMapper.to_entity(model)
        return None

    def get_key_columns_by_table_id(self, table_id: str) -> List[ColumnInfo]:
        sql = text("""
            SELECT * FROM column_info
            WHERE table_id = :table_id
            AND role IN ('primary_key', 'foreign_key')
        """)
        result = self.session.execute(sql, {"table_id": table_id})
        rows = result.mappings().fetchall()
        return [ColumnInfo(**row) for row in rows]