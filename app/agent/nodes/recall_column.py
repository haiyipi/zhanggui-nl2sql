# app/agent/nodes/recall_column.py
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langgraph.runtime import Runtime
from app.agent.context import DataAgentContext
from app.agent.llm import llm
from app.agent.state import DataAgentState
from app.core.log import logger
from app.entities.column_info import ColumnInfo
from app.prompt.prompt_loader import load_prompt


def recall_column(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    writer = runtime.stream_writer
    writer({"type": "progress", "step": "召回字段", "status": "running"})

    query = state["query"]
    keywords = state["keywords"]
    embedding_client = runtime.context["embedding_client"]
    column_qdrant_repository = runtime.context["column_qdrant_repository"]

    try:
        # 使用 LLM 扩展关键词
        prompt = PromptTemplate(
            template=load_prompt("extend_keywords_for_column_recall"),
            input_variables=["query"]
        )
        chain = prompt | llm | JsonOutputParser()
        result = chain.invoke({"query": query})

        # 合并原始关键词和扩展关键词
        keywords = list(set(keywords + result))
        logger.info(f"召回字段信息扩展关键词：{keywords}")

        # 向量检索
        retrieved_columns_map: dict[str, ColumnInfo] = {}
        for keyword in keywords:
            embedding = embedding_client.embed_query(keyword)
            payloads: list[ColumnInfo] = column_qdrant_repository.search(embedding)
            for payload in payloads:
                if payload.id not in retrieved_columns_map:
                    retrieved_columns_map[payload.id] = payload

        retrieved_columns = list(retrieved_columns_map.values())

        writer({"type": "progress", "step": "召回字段", "status": "success"})
        logger.info(f"召回字段信息：{list(retrieved_columns_map.keys())}")

        return {"retrieved_columns": retrieved_columns}

    except Exception as e:
        writer({"type": "progress", "step": "召回字段", "status": "error"})
        logger.error(f"召回字段信息失败: {str(e)}")
        raise