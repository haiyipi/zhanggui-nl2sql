# app/clients/mysql_client_manager.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.conf.app_config import DBConfig, app_config


class MysqlClientManager:
    def __init__(self, config: DBConfig):
        self.engine = None
        self.config = config
        self.session_factory = None

    def _get_url(self):
        return f'mysql+pymysql://{self.config.user}:{self.config.password}@{self.config.host}:{self.config.port}/{self.config.database}?charset=utf8mb4'

    def init(self):
        self.engine = create_engine(
            self._get_url(),
            pool_size=10,
            pool_pre_ping=True
        )
        self.session_factory = sessionmaker(
            self.engine,
            expire_on_commit=False,
            autoflush=True
        )

    def close(self):
        if self.engine:
            self.engine.dispose()


# 创建全局实例
meta_mysql_client_manager = MysqlClientManager(app_config.db_meta)
dw_mysql_client_manager = MysqlClientManager(app_config.db_dw)