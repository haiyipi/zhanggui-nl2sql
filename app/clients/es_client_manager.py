# app/clients/es_client_manager.py
from elasticsearch import Elasticsearch  # 同步客户端
from app.conf.app_config import ESConfig, app_config


class ESClientManager:
    def __init__(self, config: ESConfig):
        self.client = None
        self.config = config

    def _get_url(self):
        return f'http://{self.config.host}:{self.config.port}'

    def init(self):
        self.client = Elasticsearch(hosts=[self._get_url()])

    def close(self):
        if self.client:
            self.client.close()


es_client_manager = ESClientManager(app_config.es)