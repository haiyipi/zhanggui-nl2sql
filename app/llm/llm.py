# app/agent/llm.py
from langchain.chat_models import init_chat_model
from app.conf.app_config import app_config

llm = init_chat_model(
    model=app_config.llm.model_name,      # 从配置文件读取: qwen-max
    model_provider="openai",
    api_key=app_config.llm.api_key,       # 从配置文件读取
    base_url=app_config.llm.base_url,     # 从配置文件读取
    temperature=0.8
)