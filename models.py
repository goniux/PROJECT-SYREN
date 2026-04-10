from pydantic import BaseModel

class PromptRequest(BaseModel):
    prompt: str

class SecurityResponse(BaseModel):
    status: str
    risk: float
    output: str