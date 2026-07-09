from datetime import datetime

from pydantic import BaseModel


class NodeHeartbeat(BaseModel):
    node_id: str
    hostname: str
    role: str
    site: str = "madrid"
    ip: str


class NodeResponse(BaseModel):
    node_id: str
    hostname: str
    role: str
    site: str
    ip: str
    status: str
    last_seen: datetime

    class Config:
        from_attributes = True
