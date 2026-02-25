from pydantic import BaseModel
from typing import Optional

class Cluster(BaseModel):
    id: Optional[str] = None
    model: Optional[str] = None
    members: Optional[list[str]] = None
    centroid: Optional[float] = None

class MessageResponse(BaseModel):
    message: str