# app/agent/nodes/filter_metric.py
import yaml
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langgraph.runtime import Runtime
from app.agent.context import DataAgentContext
from app.agent.llm import llm
from app.agent.state import DataAgentState
from app.core.log import logger
from app.prompt.prompt_loader import load_prompt


def filter_metric(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    writer = runtime.stream_writer
    writer({"type": "progress", "step": "过滤指标", "status": "running"})

    query = state["query"]
    metric_infos = state["metric_infos"]

    try:
        prompt = PromptTemplate(
            template=load_prompt("filter_metric_info"),
            input_variables=["query", "metric_infos"]
        )
        chain = prompt | llm | JsonOutputParser()

        result = chain.invoke({
            "query": query,
            "metric_infos": yaml.dump(metric_infos, allow_unicode=True, sort_keys=False)
        })

        for metric_info in metric_infos[:]:
            if metric_info["name"] not in result:
                metric_infos.remove(metric_info)

        writer({"type": "progress", "step": "过滤指标", "status": "success"})
        logger.info(f"过滤后的指标: {[m['name'] for m in metric_infos]}")

        return {"metric_infos": metric_infos}

    except Exception as e:
        writer({"type": "progress", "step": "过滤指标", "status": "error"})
        logger.error(f"过滤指标失败:{str(e)}")
        raise