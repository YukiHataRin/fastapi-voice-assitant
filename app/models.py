from pydantic import BaseModel
from typing import Optional


class ChatRequest(BaseModel):
    prompt: str
    model: Optional[str] = None
