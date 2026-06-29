# app/agent/graph.py
import asyncio
import sys
from pathlib import Path

from langgraph.constants import START, END
from langgraph.graph import StateGraph

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.agent.state import DataAgentState
from app.agent.context import DataAgentContext

# 从 nodes 目录导入节点
from app.agent.nodes.extract_keywords import extract_keywords
from app.agent.nodes.recall_column import recall_column
from app.agent.nodes.recall_metric import recall_metric
from app.agent.nodes.recall_value import recall_value
from app.agent.nodes.merge_retrieved_info import merge_retrieved_info
from app.agent.nodes.filter_table import filter_table
from app.agent.nodes.filter_metric import filter_metric
from app.agent.nodes.add_extra_context import add_extra_context
from app.agent.nodes.generate_sql import generate_sql
from app.agent.nodes.validate_sql import validate_sql
from app.agent.nodes.correct_sql import correct_sql
from app.agent.nodes.execute_sql import execute_sql


def build_graph():
    """构建智能体工作流图"""
    graph_builder = StateGraph(state_schema=DataAgentState, context_schema=DataAgentContext)

    # 添加节点
    graph_builder.add_node("extract_keywords", extract_keywords)
    graph_builder.add_node("recall_column", recall_column)
    graph_builder.add_node("recall_value", recall_value)
    graph_builder.add_node("recall_metric", recall_metric)
    graph_builder.add_node("merge_retrieved_info", merge_retrieved_info)
    graph_builder.add_node("filter_metric", filter_metric)
    graph_builder.add_node("filter_table", filter_table)
    graph_builder.add_node("add_extra_context", add_extra_context)
    graph_builder.add_node("generate_sql", generate_sql)
    graph_builder.add_node("validate_sql", validate_sql)
    graph_builder.add_node("correct_sql", correct_sql)
    graph_builder.add_node("execute_sql", execute_sql)

    # 添加边
    graph_builder.add_edge(START, "extract_keywords")
    graph_builder.add_edge("extract_keywords", "recall_column")
    graph_builder.add_edge("extract_keywords", "recall_value")
    graph_builder.add_edge("extract_keywords", "recall_metric")
    graph_builder.add_edge("recall_column", "merge_retrieved_info")
    graph_builder.add_edge("recall_value", "merge_retrieved_info")
    graph_builder.add_edge("recall_metric", "merge_retrieved_info")
    graph_builder.add_edge("merge_retrieved_info", "filter_table")
    graph_builder.add_edge("merge_retrieved_info", "filter_metric")
    graph_builder.add_edge("filter_table", "add_extra_context")
    graph_builder.add_edge("filter_metric", "add_extra_context")
    graph_builder.add_edge("add_extra_context", "generate_sql")
    graph_builder.add_edge("generate_sql", "validate_sql")

    # 条件边
    graph_builder.add_conditional_edges(
        "validate_sql",
        lambda state: "execute_sql" if state.get("error") is None else "correct_sql",
        {"execute_sql": "execute_sql", "correct_sql": "correct_sql"}
    )

    graph_builder.add_edge("correct_sql", "execute_sql")
    graph_builder.add_edge("execute_sql", END)

    return graph_builder.compile()


# 创建全局图实例
graph = build_graph()


# ==================== 测试代码 ====================
if __name__ == "__main__":
    from app.clients.embedding_client_manager import embedding_client_manager
    from app.clients.qdrant_client_manager import qdrant_client_manager
    from app.clients.es_client_manager import es_client_manager
    from app.clients.mysql_client_manager import meta_mysql_client_manager, dw_mysql_client_manager
    from app.repositories.es.value_es_repository import ValueEsRepository
    from app.repositories.mysql.meta.meta_mysql_repository import MetaMysqlRepository
    from app.repositories.mysql.dw.dw_mysql_repository import DWMYSQLRepository
    from app.repositories.qdrant.column_qdrant_repository import ColumnQdrantRepository
    from app.repositories.qdrant.metric_qdrant_repository import MetricQdrantRepository

    async def test_agent():
        print("=" * 60)
        print("初始化客户端...")
        print("=" * 60)

        # 初始化所有客户端
        await embedding_client_manager.init()
        await qdrant_client_manager.init()
        await es_client_manager.init()
        await meta_mysql_client_manager.init()
        await dw_mysql_client_manager.init()

        # 创建 Repository
        column_qdrant_repo = ColumnQdrantRepository(qdrant_client_manager.client)
        metric_qdrant_repo = MetricQdrantRepository(qdrant_client_manager.client)
        value_es_repo = ValueEsRepository(es_client_manager.client)

        async with meta_mysql_client_manager.session_factory() as meta_session:
            async with dw_mysql_client_manager.session_factory() as dw_session:
                meta_mysql_repo = MetaMysqlRepository(meta_session)
                dw_mysql_repo = DWMYSQLRepository(dw_session)

                # 构建上下文
                context: DataAgentContext = {
                    "embedding_client": embedding_client_manager,
                    "column_qdrant_repository": column_qdrant_repo,
                    "value_es_repository": value_es_repo,
                    "metric_qdrant_repository": metric_qdrant_repo,
                    "meta_mysql_repository": meta_mysql_repo,
                    "dw_mysql_repository": dw_mysql_repo
                }

                # 初始状态
                initial_state: DataAgentState = {
                    "query": "GMV最高的商品是什么",
                    "keywords": [],
                    "retrieved_columns": [],
                    "retrieved_values": [],
                    "retrieved_metrics": [],
                    "table_infos": [],
                    "metric_infos": [],
                    "date_info": {},
                    "db_info": {},
                    "sql": "",
                    "error": ""
                }

                print(f"\n用户问题: {initial_state['query']}\n")
                print("=" * 60)
                print("开始执行智能体工作流...")
                print("=" * 60)

                # 运行智能体
                async for chunk in graph.astream(
                    input=initial_state,
                    context=context,
                    stream_mode="custom"
                ):
                    print(chunk)

        # 关闭客户端
        await embedding_client_manager.close()
        await qdrant_client_manager.close()
        await es_client_manager.close()
        await meta_mysql_client_manager.close()
        await dw_mysql_client_manager.close()

    asyncio.run(test_agent())