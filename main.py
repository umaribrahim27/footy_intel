from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv
import os
import time
import json
import logging
from datetime import datetime

load_dotenv()

app = FastAPI()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

# logging setup
logging.basicConfig(
    filename="logs.json",
    level=logging.INFO,
    format="%(message)s"
)

class QuestionRequest(BaseModel):
    question: str

def log_request(question: str, answer: str, tokens: int, latency: float, status: str):
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "question": question,
        "answer_preview": answer[:100],
        "tokens_used": tokens,
        "latency_seconds": round(latency, 3),
        "status": status
    }
    logging.info(json.dumps(entry))

@app.get("/")
def root():
    return {"message": "footy_bot is alive"}

@app.post("/ask")
def ask(request: QuestionRequest):
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    start = time.time()

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a football analysis assistant. Answer questions about football stats, players, and tactics."},
                {"role": "user", "content": request.question}
            ]
        )
        answer = response.choices[0].message.content
        tokens = response.usage.total_tokens
        latency = time.time() - start

        log_request(request.question, answer, tokens, latency, "success")

        return {
            "question": request.question,
            "answer": answer,
            "tokens_used": tokens,
            "latency_seconds": round(latency, 3)
        }

    except Exception as e:
        latency = time.time() - start
        log_request(request.question, str(e), 0, latency, "error")
        raise HTTPException(status_code=500, detail=str(e))