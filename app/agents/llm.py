from langchain_openai import ChatOpenAI
from app.core.config import settings


def get_llm() -> ChatOpenAI:
    return ChatOpenAI(
        openai_api_base="https://api.groq.com/openai/v1",
        openai_api_key=settings.GROQ_API_KEY,
        temperature=0,
        model_name="llama-3.3-70b-versatile",
        top_p=1,
        max_retries=3,
        request_timeout=60,
    )
