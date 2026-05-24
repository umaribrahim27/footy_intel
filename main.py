from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

class QuestionRequest(BaseModel):
    question: str

@app.get("/")
def root():
    return {"message": "footy_bot is alive"}

@app.post("/ask")
def ask(request: QuestionRequest):
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a football analysis assistant. Answer questions about football stats, players, and tactics."},
                {"role": "user", "content": request.question}
            ]
        )
        answer = response.choices[0].message.content
        return {"question": request.question, "answer": answer}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))