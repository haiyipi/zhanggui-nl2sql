# app/utils/sql_utils.py
import re
import logging

logger = logging.getLogger(__name__)


def clean_sql(raw_sql: str) -> str:
    """
    从LLM返回的内容中提取纯净的SQL语句

    支持的输入格式:
    - ```sql\nSELECT ... \n```
    - ```\nSELECT ... \n```
    - 直接输出 SELECT ... ;
    """
    if not raw_sql:
        return ""

    sql = raw_sql.strip()

    # 情况1: 标准的 markdown 代码块 ```sql ... ```
    pattern1 = r'```(?:sql)?\s*\n(.*?)\n```'
    match = re.search(pattern1, sql, re.DOTALL | re.IGNORECASE)
    if match:
        sql = match.group(1).strip()
        logger.debug("从 ```sql ``` 块中提取SQL")

    # 情况2: 只有开头标记没有结尾（不常见，但处理一下）
    sql = re.sub(r'^```(?:sql)?\s*\n?', '', sql, flags=re.IGNORECASE)
    sql = re.sub(r'\n?```$', '', sql)

    # 情况3: 多余的空行和空格
    sql = '\n'.join(line.strip() for line in sql.split('\n') if line.strip())

    return sql


def is_valid_sql_basic(sql: str) -> bool:
    """基础SQL验证，防止空语句或明显错误的语句"""
    sql_upper = sql.upper().strip()

    # 必须包含SELECT/INSERT/UPDATE/DELETE/WITH之一
    sql_keywords = ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'WITH']
    if not any(sql_upper.startswith(kw) for kw in sql_keywords):
        return False

    # 不能是空字符串
    if len(sql) < 5:
        return False

    return True


def extract_and_clean_sql(raw_sql: str) -> str:
    """清洗并验证SQL的完整流程"""
    cleaned = clean_sql(raw_sql)

    if not cleaned:
        raise ValueError("提取的SQL为空，请检查LLM输出")

    if not is_valid_sql_basic(cleaned):
        raise ValueError(f"SQL格式无效: {cleaned[:100]}")

    return cleaned