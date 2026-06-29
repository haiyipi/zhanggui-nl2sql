# app/clients/embedding_client_manager.py
import requests
from typing import List, Optional
from app.conf.app_config import EmbeddingConfig, app_config


class EmbeddingClientManager:
    def __init__(self, config: EmbeddingConfig):
        self.config = config
        self.session = None

    def _get_url(self) -> str:
        return f"http://{self.config.host}:{self.config.port}/embed"

    def init(self):
        self.session = requests.Session()

    def embed_query(self, text: str) -> List[float]:
        if self.session is None:
            raise RuntimeError("Client not initialized. Call `init()` first.")
        url = self._get_url()
        payload = {"inputs": [text]}
        response = self.session.post(url, json=payload)
        response.raise_for_status()
        result = response.json()
        if isinstance(result, list) and len(result) > 0:
            return result[0]
        else:
            raise ValueError(f"Unexpected response format: {result}")

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if self.session is None:
            raise RuntimeError("Client not initialized. Call `init()` first.")
        url = self._get_url()
        payload = {"inputs": texts}
        response = self.session.post(url, json=payload)
        response.raise_for_status()
        result = response.json()
        if isinstance(result, list):
            return result
        else:
            raise ValueError(f"Unexpected response format: {result}")

    def close(self):
        if self.session:
            self.session.close()


embedding_client_manager = EmbeddingClientManager(app_config.embedding)