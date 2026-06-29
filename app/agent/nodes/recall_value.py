# app/agent/nodes/recall_value.py
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langgraph.runtime import Runtime
from app.agent.context import DataAgentContext
from app.agent.llm import llm
from app.agent.state import DataAgentState
from app.core.log import logger
from app.entities.value_info import ValueInfo
from app.prompt.prompt_loader import load_prompt


def recall_value(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    writer = runtime.stream_writer
    writer({"type": "progress", "step": "召回字段取值", "status": "running"})

    query = state["query"]
    keywords = state["keywords"]
    value_es_repository = runtime.context["value_es_repository"]

    try:
        prompt = PromptTemplate(
            template=load_prompt("extend_keywords_for_value_recall"),
            input_variables=["query"]
        )
        chain = prompt | llm | JsonOutputParser()
        result = chain.invoke({"query": query})

        keywords = list(set(keywords + result))
        logger.info(f"召回字段取值扩展关键词：{keywords}")

        values_map: dict[str, ValueInfo] = {}
        for keyword in keywords:
            values: list[ValueInfo] = value_es_repository.search(keyword)
            for value in values:
                if value.id not in values_map:
                    values_map[value.id] = value

        retrieved_values = list(values_map.values())

        writer({"type": "progress", "step": "召回字段取值", "status": "success"})
        logger.info(f"召回字段取值：{list(values_map.keys())}")

        return {"retrieved_values": retrieved_values}

    except Exception as e:
        writer({"type": "progress", "step": "召回字段取值", "status": "error"})
        logger.error(f"召回字段取值失败: {str(e)}")
        raise