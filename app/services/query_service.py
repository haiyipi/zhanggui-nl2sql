# app/services/query_service.py
import json
from decimal import Decimal
from datetime import date, datetime
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain.chat_models import init_chat_model

from app.agent.graph import graph
from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState
from app.conf.app_config import app_config
from app.core.log import logger


class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, (date, datetime)):
            return obj.isoformat()
        return super().default(obj)


class QueryService:
    def __init__(self, meta_mysql_repo, dw_mysql_repo, column_qdrant_repo,
                 metric_qdrant_repo, value_es_repo, embedding_client):
        self.meta_mysql_repo = meta_mysql_repo
        self.dw_mysql_repo = dw_mysql_repo
        self.column_qdrant_repo = column_qdrant_repo
        self.metric_qdrant_repo = metric_qdrant_repo
        self.value_es_repo = value_es_repo
        self.embedding_client = embedding_client

    def _explain_result(self, query: str, sql: str, result) -> str:
        """将 SQL 结果转换为自然语言"""
        try:
            llm = init_chat_model(
                model=app_config.llm.model_name,
                model_provider="openai",
                api_key=app_config.llm.api_key,
                base_url=app_config.llm.base_url,
                temperature=0.3
            )

            prompt = PromptTemplate(
                template="""你是一个数据分析专家。请用自然语言回答用户的问题。

用户问题：{query}

查询结果：
{result}

请用通俗易懂的中文回答，不要输出 JSON 或 SQL。
如果是数字，保留两位小数，超过1000加千分位分隔符。
如果有多个结果，用列表形式呈现。
回答要简洁、准确、友好。

请回答：""",
                input_variables=["query", "result"]
            )

            chain = prompt | llm | StrOutputParser()

            result_str = json.dumps(result, ensure_ascii=False, default=str)[:3000]
            explanation = chain.invoke({
                "query": query,
                "result": result_str
            })

            return explanation.strip()

        except Exception as e:
            logger.error(f"解释失败: {e}")
            return f"查询结果：{json.dumps(result, ensure_ascii=False, cls=CustomJSONEncoder)}"

    def query(self, query_text: str):
        context: DataAgentContext = {
            "embedding_client": self.embedding_client,
            "column_qdrant_repository": self.column_qdrant_repo,
            "value_es_repository": self.value_es_repo,
            "metric_qdrant_repository": self.metric_qdrant_repo,
            "meta_mysql_repository": self.meta_mysql_repo,
            "dw_mysql_repository": self.dw_mysql_repo
        }

        initial_state: DataAgentState = {
            "query": query_text,
            "keywords": [],
            "retrieved_columns": [],
            "retrieved_values": [],
            "retrieved_metrics": [],
            "table_infos": [],
            "metric_infos": [],
            "date_info": {},
            "db_info": {},
            "sql": "",
            "error": "",
            "result": []
        }

        final_result = None
        final_sql = None

        for chunk in graph.stream(
            input=initial_state,
            context=context,
            stream_mode="custom"
        ):
            if isinstance(chunk, dict):
                if chunk.get("type") == "result":
                    final_result = chunk.get("data")
                if chunk.get("type") == "sql":
                    final_sql = chunk.get("data")

            yield f"data: {json.dumps(chunk, ensure_ascii=False, cls=CustomJSONEncoder)}\n\n"

        logger.info(f"DEBUG: final_result = {final_result}")
        logger.info(f"DEBUG: final_sql = {final_sql}")

        if final_result:
            explanation = self._explain_result(query_text, final_sql or "", final_result)
            yield f"data: {json.dumps({'type': 'explanation', 'data': explanation}, ensure_ascii=False, cls=CustomJSONEncoder)}\n\n"
        else:
            logger.info("DEBUG: final_result 为空，跳过解释生成")