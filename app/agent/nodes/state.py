# app/agent/state.py
from typing import TypedDict, List, Optional
from app.entities.column_info import ColumnInfo
from app.entities.metric_info import MetricInfo
from app.entities.value_info import ValueInfo


class ColumnInfoState(TypedDict):
    name: str
    type: str
    role: str
    examples: list
    description: str
    alias: list[str]


class TableInfoState(TypedDict):
    name: str
    role: str
    description: str
    columns: List[ColumnInfoState]


class MetricInfoState(TypedDict):
    name: str
    description: str
    relevant_columns: list[str]
    alias: list[str]


class DateInfoState(TypedDict):
    date: str
    weekday: str
    quarter: str


class DBInfoState(TypedDict):
    dialect: str
    version: str


class DataAgentState(TypedDict):
    query: str  # 用户查询
    keywords: List[str]  # 用户查询的关键字
    retrieved_columns: List[ColumnInfo]  # 召回的字段信息
    retrieved_values: List[ValueInfo]  # 召回的值信息
    retrieved_metrics: List[MetricInfo]  # 召回的指标信息
    table_infos: List[TableInfoState]  # 合并后的表信息
    metric_infos: List[MetricInfoState]  # 合并后的指标信息
    date_info: DateInfoState  # 日期信息
    db_info: DBInfoState  # 数据库信息
    sql: str  # 生成的SQL
    error: str  # 验证SQL时的错误信息