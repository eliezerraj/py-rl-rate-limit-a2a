from pydantic import BaseModel
from typing import Optional

class Tenant(BaseModel):
    id: str
    message: Optional[str] = None
    data: Optional['Data'] = None
    cluster: Optional['Cluster'] = None

class Data(BaseModel):
    mean: Optional[float] = None
    std: Optional[float] = None
    min: Optional[float] = None    
    max: Optional[float] = None
    n_slope: Optional[float] = None
    mad: Optional[float] = None

class Cluster(BaseModel):
    id: Optional[str] = None
    model: Optional[str] = None
    members: Optional[list[str]] = None
    centroid: Optional[float] = None

class MessageResponse(BaseModel):
    message: str