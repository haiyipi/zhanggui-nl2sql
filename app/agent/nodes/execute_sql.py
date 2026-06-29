# app/agent/nodes/execute_sql.py
from langgraph.runtime import Runtime
from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState
from app.core.log import logger


def execute_sql(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    """执行SQL并返回结果"""
    writer = runtime.stream_writer
    writer({"type": "progress", "step": "执行SQL", "status": "running"})

    sql = state["sql"]
    dw_mysql_repository = runtime.context["dw_mysql_repository"]

    try:
        result = dw_mysql_repository.execute_sql(sql)

        # ✅ 添加这两行：发送 SQL 消息
        writer({"type": "sql", "data": sql})
        writer({"type": "result", "data": result})
        writer({"type": "progress", "step": "执行SQL", "status": "success"})

        logger.info(f"执行SQL结果: {result}")

        return {"result": result}

    except Exception as e:
        writer({"type": "progress", "step": "执行SQL", "status": "error"})
        logger.error(f"执行SQL失败:{str(e)}")
        raise