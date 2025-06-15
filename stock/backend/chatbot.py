from fastapi import APIRouter
from pydantic import BaseModel
from dotenv import load_dotenv
import os
import openai

load_dotenv()
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))  # ✅ 새로운 방식

chat_router = APIRouter()

class ChatRequest(BaseModel):
    messages: list  # [{"role": "user", "content": "Hello"}]

@chat_router.post("/api/chat")
async def chat_with_ai(req: ChatRequest):
    try:
        response = client.chat.completions.create(  # ✅ 새 방식
            model="gpt-3.5-turbo",
            messages=req.messages,
            temperature=0.7,
        )
        return {"reply": response.choices[0].message.content.strip()}
    except Exception as e:
        return {"reply": f"AI 응답 중 오류 발생: {e}"}
