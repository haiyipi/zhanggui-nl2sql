# app/agent/nodes/generate_sql.py
import yaml
import re
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langgraph.runtime import Runtime
from app.agent.context import DataAgentContext
from app.agent.llm import llm
from app.agent.state import DataAgentState
from app.core.log import logger
from app.prompt.prompt_loader import load_prompt


def generate_sql(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    """生成SQL语句"""
    writer = runtime.stream_writer
    writer({"type": "progress", "step": "生成SQL", "status": "running"})

    query = state["query"]
    table_infos = state["table_infos"]
    metric_infos = state["metric_infos"]
    date_info = state["date_info"]
    db_info = state["db_info"]

    try:
        prompt = PromptTemplate(
            template=load_prompt("generate_sql"),
            input_variables=["query", "table_infos", "metric_infos", "date_info", "db_info"]
        )
        chain = prompt | llm | StrOutputParser()

        result = chain.invoke({
            "query": query,
            "table_infos": yaml.dump(table_infos, allow_unicode=True, sort_keys=False),
            "metric_infos": yaml.dump(metric_infos, allow_unicode=True, sort_keys=False),
            "date_info": yaml.dump(date_info, allow_unicode=True, sort_keys=False),
            "db_info": yaml.dump(db_info, allow_unicode=True, sort_keys=False)
        })

        # 清理 SQL 语句，移除 Markdown 标记
        cleaned_sql = re.sub(r'^```(?:sql)?\s*|\s*```$', '', result.strip(), flags=re.IGNORECASE)

        writer({"type": "progress", "step": "生成SQL", "status": "success"})
        logger.info(f"生成的SQL: {cleaned_sql}")

        return {"sql": cleaned_sql}

    except Exception as e:
        writer({"type": "progress", "step": "生成SQL", "status": "error"})
        logger.error(f"生成SQL失败: {str(e)}")
        raise