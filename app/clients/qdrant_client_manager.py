# app/clients/qdrant_client_manager.py
from qdrant_client import QdrantClient  # 注意：用同步客户端
from app.conf.app_config import QdrantConfig, app_config


class QdrantClientManager:
    def __init__(self, config: QdrantConfig):
        self.client = None
        self.config = config

    def _get_url(self):
        return f'http://{self.config.host}:{self.config.port}'

    def init(self):
        self.client = QdrantClient(url=self._get_url())

    def close(self):
        if self.client:
            self.client.close()


qdrant_client_manager = QdrantClientManager(app_config.qdrant)