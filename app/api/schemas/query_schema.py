from fastapi.openapi.models import Schema
from pydantic import BaseModel


class QuerySchema(BaseModel):
    query:str