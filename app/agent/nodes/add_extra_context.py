# app/agent/nodes/add_extra_context.py
from datetime import datetime
from langgraph.runtime import Runtime
from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState, DateInfoState
from app.core.log import logger


def add_extra_context(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    writer = runtime.stream_writer
    writer({"type": "progress", "step": "添加额外上下文信息", "status": "running"})

    dw_mysql_repository = runtime.context["dw_mysql_repository"]

    try:
        today = datetime.today()
        date_info = DateInfoState(
            date=today.strftime("%Y-%m-%d"),
            weekday=today.strftime("%A"),
            quarter=f"Q{(today.month - 1) // 3 + 1}"
        )

        db_info = dw_mysql_repository.get_db_info()

        writer({"type": "progress", "step": "添加额外上下文信息", "status": "success"})
        logger.info(f"额外上下文信息：数据库信息-{db_info} 日期信息-{date_info}")

        return {"date_info": date_info, "db_info": db_info}

    except Exception as e:
        writer({"type": "progress", "step": "添加额外上下文信息", "status": "error"})
        logger.error(f"添加上下文失败:{str(e)}")
        raise