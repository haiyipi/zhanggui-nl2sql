# app/repositories/qdrant/metric_qdrant_repository.py
from qdrant_client import QdrantClient
from qdrant_client.http.models import VectorParams, Distance, PointStruct

from app.conf.app_config import app_config
from app.core.log import logger
from app.entities.metric_info import MetricInfo


class MetricQdrantRepository:
    COLLECTION_NAME = "metric_info_collection"

    def __init__(self, client: QdrantClient):
        self.client = client

    def ensure_collection(self):
        if not self.client.collection_exists(self.COLLECTION_NAME):
            self.client.create_collection(
                collection_name=self.COLLECTION_NAME,
                vectors_config=VectorParams(
                    size=app_config.qdrant.embedding_size,
                    distance=Distance.COSINE
                )
            )
            logger.info(f"创建集合: {self.COLLECTION_NAME}")

    def upsert(self, ids: list[str], embeddings: list[list[float]], payloads: list[dict], batch_size: int = 20):
        points = [
            PointStruct(id=id, vector=embedding, payload=payload)
            for id, embedding, payload in zip(ids, embeddings, payloads)
        ]

        total = len(points)
        for i in range(0, total, batch_size):
            batch = points[i:i + batch_size]
            self.client.upsert(
                collection_name=self.COLLECTION_NAME,
                points=batch
            )
            logger.debug(f"已插入 {min(i + batch_size, total)}/{total} 条向量")

        logger.info(f"成功插入 {total} 条向量到 {self.COLLECTION_NAME}")

    def search(self, embedding: list[float], score_threshold: float = 0.6, limit: int = 5) -> list[MetricInfo]:
        result = self.client.query_points(
            collection_name=self.COLLECTION_NAME,
            query=embedding,
            score_threshold=score_threshold,
            limit=limit
        )
        return [MetricInfo(**point.payload) for point in result.points]