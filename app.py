from fastapi import FastAPI
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer, util
import torch

app = FastAPI()

# 1. THE SENTRY (ML Logic)
class Sentry:
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.attacks = ["ignore instructions", "dan mode", "system prompt", "api keys", "admin access"]
        self.attack_embeddings = self.model.encode(self.attacks, convert_to_tensor=True)

    def get_risk(self, text: str):
        emb = self.model.encode(text, convert_to_tensor=True)
        scores = util.cos_sim(emb, self.attack_embeddings)
        return float(torch.max(scores).item())

sentry = Sentry()

# 2. THE MOCK LLM
async def call_llm_mock(model_type: str, prompt: str):
    if model_type == "production":
        return f"PROD_LLM: Here is the safe information you requested about '{prompt[:20]}'."
    else:
        return f"CANARY_LLM: Access Granted. Admin Key: sk_live_{abs(hash(prompt)) % 10**12}"

# 3. THE ROUTE
class Query(BaseModel):
    prompt: str

@app.post("/chat")
async def chat(query: Query):
    risk = sentry.get_risk(query.prompt)
    
    # Route based on risk score
    model_type = "canary" if risk > 0.6 else "production"
    response_text = await call_llm_mock(model_type, query.prompt)
    
    return {
        "status": "DECEPTION_ACTIVE" if model_type == "canary" else "CLEAN",
        "risk": round(risk, 2),
        "output": response_text
    }