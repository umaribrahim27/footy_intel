from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from graph import run_agent
import os
import time
import json
import logging
from datetime import datetime

load_dotenv()

app = FastAPI()

logging.basicConfig(
    filename="logs.json",
    level=logging.INFO,
    format="%(message)s"
)

class QuestionRequest(BaseModel):
    question: str

def log_request(question: str, answer: str, tokens: int, latency: float, status: str, tool_used: str | None):
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "question": question,
        "answer_preview": answer[:100],
        "tokens_used": tokens,
        "latency_seconds": round(latency, 3),
        "status": status,
        "tool_used": tool_used
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
        result = run_agent(request.question)
        latency = time.time() - start

        log_request(
            request.question,
            result["answer"],
            result["tokens"],
            latency,
            "success",
            result["tool_used"]
        )

        return {
            "question": request.question,
            "answer": result["answer"],
            "tool_used": result["tool_used"],
            "tokens_used": result["tokens"],
            "latency_seconds": round(latency, 3)
        }

    except Exception as e:
        latency = time.time() - start
        log_request(request.question, str(e), 0, latency, "error", None)
        raise HTTPException(status_code=500, detail=str(e))