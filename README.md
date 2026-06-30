# 📊 掌柜问数 — 企业级 NL2SQL 智能问数系统

> 让业务专员用自然语言查询数据仓库，3 秒内获取准确的成交数据，无需等待数据分析师编写 SQL

## 📌 项目背景

会小二是全国最大的酒店会议推荐平台。业务专员在为客户推荐会议场地时，需频繁查询合作酒店的历史成交记录与订房率。传统方式依赖数据分析师编写 SQL 脚本，响应周期长达数小时，严重影响客户响应速度与成交转化。

## 🎯 项目目标

- 打造自然语言驱动的自助查询工具
- 使业务专员能在数秒内获取准确数据
- 提升推荐效率与客户满意度

## 🧠 核心流程
用户提问："统计去年北京地区五星级酒店的成交总额"
↓

关键词抽取（jieba分词 + LLM扩展）
→ 提取："北京"、"五星级"、"成交总额"
↓

三路并发召回
├── Qdrant 向量召回 → 匹配到 order_amount（成交金额）
├── Qdrant 向量召回 → 匹配到 hotel_level（酒店等级）
└── Elasticsearch 全文检索 → 匹配到 region = '北京'
↓

信息合并 → 确定涉及表（dim_hotel + fact_order）
↓

LLM 过滤 → 只保留相关的表和字段
↓

添加上下文（当前日期、数据库版本）
↓

LLM 生成 SQL
↓

EXPLAIN 验证语法合法性
├── 合法 → 执行并返回结果
└── 不合法 → LLM 自动修正，最多重试3次
# 1. 配置环境变量
cp .env.example .env
# 填写 OPENAI_API_KEY 等

# 2. 启动 Docker 服务
docker-compose up -d

# 3. 构建元数据知识库
python -m app.scripts.build_meta_knowledge -c ./conf/meta_config.yaml

# 4. 启动 API 服务

📁 项目结构
uvicorn main:app --host 0.0.0.0 --port 8000
data-agent/
├── app/
│   ├── agent/          # 智能体工作流（12 个 LangGraph 节点）
│   ├── api/            # FastAPI 接口
│   ├── clients/        # 外部服务客户端
│   ├── conf/           # 配置类
│   ├── entities/       # 业务实体类
│   ├── models/         # ORM 模型
│   ├── repositories/   # 数据访问层
│   ├── scripts/        # 脚本工具
│   └── services/       # 业务逻辑层
├── conf/               # 配置文件
├── prompts/            # 提示词模板
└── docker/             # Docker 部署配置

