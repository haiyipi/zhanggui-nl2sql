# app/agent/llm.py
from langchain.chat_models import init_chat_model
from app.conf.app_config import app_config

llm = init_chat_model(
    model=app_config.llm.model_name,      # qwen3-max
    model_provider="openai",               # 修正：使用 openai 作为 provider
    api_key=app_config.llm.api_key,       # 从配置读取，不要硬编码
    base_url=app_config.llm.base_url,     # 使用配置中的 base_url
    temperature=0.7                       # 修正：温度范围 0-2，推荐 0-1
)