from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx


OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
DEFAULT_MODEL = "qwen2.5:0.5b"


class GenerateRequest(BaseModel):
    prompt: str
    model: str = DEFAULT_MODEL


class GenerateResponse(BaseModel):
    model: str
    response: str


app = FastAPI(title="LLM Spam POC", version="1.0.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/generate", response_model=GenerateResponse)
async def generate(payload: GenerateRequest) -> GenerateResponse:
    request_body = {
        "model": payload.model,
        "prompt": payload.prompt,
        "stream": False,
    }

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(OLLAMA_URL, json=request_body)
            response.raise_for_status()
            data = response.json()
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Ollama request failed: {exc}") from exc

    text = data.get("response")
    if not isinstance(text, str):
        raise HTTPException(status_code=502, detail="Invalid response from Ollama")

    return GenerateResponse(model=payload.model, response=text)
