from pydantic import BaseModel

class BatchCreateResponse(BaseModel):
    batch_id: str

class BatchStatusResponse(BaseModel):
    batch_id: str
    status: str
    total: int
    ok: int
    error: int
    progress: float

class BatchRunResponse(BaseModel):
    batch_id: str
    status: str
