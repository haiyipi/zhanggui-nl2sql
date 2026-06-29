# app/agent/nodes/recall_metric.py
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langgraph.runtime import Runtime
from app.agent.context import DataAgentContext
from app.agent.llm import llm
from app.agent.state import DataAgentState
from app.core.log import logger
from app.entities.metric_info import MetricInfo
from app.prompt.prompt_loader import load_prompt


def recall_metric(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    writer = runtime.stream_writer
    writer({"type": "progress", "step": "召回指标", "status": "running"})

    query = state["query"]
    keywords = state["keywords"]
    embedding_client = runtime.context["embedding_client"]
    metric_qdrant_repository = runtime.context["metric_qdrant_repository"]

    try:
        prompt = PromptTemplate(
            template=load_prompt("extend_keywords_for_metric_recall"),
            input_variables=["query"]
        )
        chain = prompt | llm | JsonOutputParser()
        result = chain.invoke({"query": query})

        keywords = list(set(keywords + result))
        logger.info(f"召回指标信息扩展关键词：{keywords}")

        retrieved_metrics_map: dict[str, MetricInfo] = {}
        for keyword in keywords:
            embedding = embedding_client.embed_query(keyword)
            payloads: list[MetricInfo] = metric_qdrant_repository.search(embedding)
            for payload in payloads:
                if payload.id not in retrieved_metrics_map:
                    retrieved_metrics_map[payload.id] = payload

        retrieved_metrics = list(retrieved_metrics_map.values())

        writer({"type": "progress", "step": "召回指标", "status": "success"})
        logger.info(f"召回指标信息：{list(retrieved_metrics_map.keys())}")

        return {"retrieved_metrics": retrieved_metrics}

    except Exception as e:
        writer({"type": "progress", "step": "召回指标", "status": "error"})
        logger.error(f"召回指标信息失败: {str(e)}")
        raise