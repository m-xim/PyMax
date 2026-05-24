from pydantic import BaseModel


class InitData(BaseModel):
    query_id: str
    url: str
