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
    query: str  # ✅ 必须存在
    keywords: List[str]
    retrieved_columns: List[ColumnInfo]
    retrieved_values: List[ValueInfo]
    retrieved_metrics: List[MetricInfo]
    table_infos: List[dict]
    metric_infos: List[dict]
    date_info: dict
    db_info: dict
    sql: str
    error: str
    result: List[dict]

