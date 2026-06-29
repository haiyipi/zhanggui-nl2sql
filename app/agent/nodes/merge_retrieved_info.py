# app/agent/nodes/merge_retrieved_info.py
from langgraph.runtime import Runtime
from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState, TableInfoState, MetricInfoState, ColumnInfoState
from app.core.log import logger
from app.entities.column_info import ColumnInfo
from app.entities.table_info import TableInfo


def merge_retrieved_info(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    writer = runtime.stream_writer
    writer({"type": "progress", "step": "合并召回信息", "status": "running"})

    retrieved_columns = state["retrieved_columns"]
    retrieved_values = state["retrieved_values"]
    retrieved_metrics = state["retrieved_metrics"]
    meta_mysql_repository = runtime.context["meta_mysql_repository"]

    try:
        retrieved_columns_map: dict[str, ColumnInfo] = {c.id: c for c in retrieved_columns}

        # 1. 将指标信息的相关字段加入字段信息列表
        for retrieved_metric in retrieved_metrics:
            for relevant_column in retrieved_metric.relevant_columns:
                if relevant_column not in retrieved_columns_map:
                    column_info = meta_mysql_repository.get_column_info_by_id(relevant_column)
                    if column_info:
                        retrieved_columns_map[relevant_column] = column_info

        # 2. 将字段取值合并到字段信息列表
        for retrieved_value in retrieved_values:
            column_id = retrieved_value.column_id
            column_value = retrieved_value.value
            if column_id not in retrieved_columns_map:
                column_info = meta_mysql_repository.get_column_info_by_id(column_id)
                if column_info:
                    retrieved_columns_map[column_id] = column_info
            if column_value not in retrieved_columns_map[column_id].examples:
                retrieved_columns_map[column_id].examples.append(column_value)

        # 3. 按表分组
        table_to_columns_map: dict[str, list[ColumnInfo]] = {}
        for column in retrieved_columns_map.values():
            table_id = column.table_id
            if table_id not in table_to_columns_map:
                table_to_columns_map[table_id] = []
            table_to_columns_map[table_id].append(column)

        # 4. 添加主外键字段
        for table_id in table_to_columns_map:
            key_columns = meta_mysql_repository.get_key_columns_by_table_id(table_id)
            existing_column_ids = [c.id for c in table_to_columns_map[table_id]]
            for key_column in key_columns:
                if key_column.id not in existing_column_ids:
                    table_to_columns_map[table_id].append(key_column)

        # 5. 转换为 TableInfoState
        table_infos: list[TableInfoState] = []
        for table_id, columns in table_to_columns_map.items():
            table: TableInfo = meta_mysql_repository.get_table_info_by_id(table_id)
            if table:
                columns_state = [
                    ColumnInfoState(
                        name=c.name, type=c.type, role=c.role,
                        examples=c.examples, description=c.description, alias=c.alias
                    )
                    for c in columns
                ]
                table_infos.append(TableInfoState(
                    name=table.name, role=table.role,
                    description=table.description, columns=columns_state
                ))

        # 6. 转换为 MetricInfoState
        metric_infos = [
            MetricInfoState(
                name=m.name, description=m.description,
                relevant_columns=m.relevant_columns, alias=m.alias
            )
            for m in retrieved_metrics
        ]

        writer({"type": "progress", "step": "合并召回信息", "status": "success"})
        logger.info(f"合并召回信息: 表信息-{[t['name'] for t in table_infos]}, 指标信息-{[m['name'] for m in metric_infos]}")

        return {"table_infos": table_infos, "metric_infos": metric_infos}

    except Exception as e:
        writer({"type": "progress", "step": "合并召回信息", "status": "error"})
        logger.error(f"合并召回信息失败: {str(e)}")
        raise