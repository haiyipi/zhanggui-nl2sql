# app/repositories/mysql/dw/dw_mysql_repository.py
import re
from sqlalchemy import text


class DWMYSQLRepository:
    def __init__(self, session):
        self.session = session

    def get_column_types(self, table_name: str) -> dict:
        sql = f'SHOW COLUMNS FROM {table_name}'
        result = self.session.execute(text(sql))
        rows = result.fetchall()
        return {row[0]: row[1] for row in rows}

    def get_column_values(self, table_name: str, column_name: str, limit: int = 100) -> list:
        sql = f'SELECT DISTINCT {column_name} FROM {table_name} LIMIT {limit}'
        result = self.session.execute(text(sql))
        return [row[0] for row in result.fetchall()]

    def get_db_info(self):
        result = self.session.execute(text("SELECT VERSION()"))
        version = result.scalar()
        dialect = self.session.get_bind().dialect.name
        return {"version": version, "dialect": dialect}

    def validate_sql(self, sql):
        self.session.execute(text(f"EXPLAIN {sql}"))

    def execute_sql(self, sql):
        # 清理 Markdown 标记
        cleaned_sql = re.sub(r'```.*?\n', '', sql, flags=re.DOTALL)
        cleaned_sql = re.sub(r'\n```', '', cleaned_sql)
        result = self.session.execute(text(cleaned_sql))
        return [dict(row) for row in result.mappings().fetchall()]