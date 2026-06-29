# app/repositories/es/value_es_repository.py
from dataclasses import asdict
from typing import List
from elasticsearch import Elasticsearch  # 同步客户端

from app.entities.value_info import ValueInfo


class ValueEsRepository:
    index_name = 'value_index'

    INDEX_MAPPINGS = {
        "dynamic": False,
        "properties": {
            "id": {"type": "keyword"},
            "value": {
                "type": "text",
                "analyzer": "ik_max_word",
                "search_analyzer": "ik_max_word"
            },
            "column_id": {"type": "keyword"}
        }
    }

    def __init__(self, client: Elasticsearch):
        self.client = client

    def ensure_index(self):
        if not self.client.indices.exists(index=self.index_name):
            self.client.indices.create(
                index=self.index_name,
                mappings=self.INDEX_MAPPINGS
            )

    def index(self, value_infos: List[ValueInfo], batch_size: int = 20):
        for i in range(0, len(value_infos), batch_size):
            batch_value_infos = value_infos[i:i + batch_size]
            batch_operations = []

            for value_info in batch_value_infos:
                batch_operations.append({"index": {"_index": self.index_name}})
                batch_operations.append(asdict(value_info))

            self.client.bulk(operations=batch_operations)

    def search(self, keyword: str, limit: int = 10) -> List[ValueInfo]:
        result = self.client.search(
            index=self.index_name,
            query={"match": {"value": keyword}},
            size=limit
        )
        return [ValueInfo(**hit["_source"]) for hit in result["hits"]["hits"]]