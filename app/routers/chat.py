import httpx
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud
from app.database import get_db
from app.models import ChatRequest
from app.services import stream_ollama_response_generator
from app.config import OLLAMA_HOST, DEFAULT_MODEL
from .prompts import SYSTEM_PROMPT_KEY

router = APIRouter()

@router.post("/chat")
async def chat_endpoint(
    request: ChatRequest, db: AsyncSession = Depends(get_db)
):
    """
    The API endpoint for handling chat requests.
    It fetches the system prompt, combines it with the user prompt,
    connects to the Ollama service, and streams the response.
    """
    model_to_use = request.model if request.model else DEFAULT_MODEL

    # Prepare the messages payload for Ollama
    messages = []

    # Fetch the system prompt from the database.
    system_prompt_setting = await crud.get_setting(db, key=SYSTEM_PROMPT_KEY)
    if system_prompt_setting and system_prompt_setting.value:
        messages.append({"role": "system", "content": system_prompt_setting.value})

    # Add the user's prompt to the payload.
    messages.append({"role": "user", "content": request.prompt})

    ollama_api_url = f"{OLLAMA_HOST}/api/chat"
    payload = {
        "model": model_to_use,
        "messages": messages,
        "stream": True,
    }

    client = httpx.AsyncClient(timeout=None)

    stream_context = client.stream("POST", ollama_api_url, json=payload)

    try:
        response_stream = await stream_context.__aenter__()
    except httpx.ConnectError:
        await client.aclose()
        raise HTTPException(
            status_code=503, detail="Service Unavailable: Could not connect to Ollama."
        )
    except Exception as e:
        await client.aclose()
        raise HTTPException(
            status_code=500, detail=f"An unexpected error occurred: {e}"
        )

    async def generator_wrapper():
        try:
            async for chunk in stream_ollama_response_generator(response_stream):
                yield chunk
        finally:
            await stream_context.__aexit__(None, None, None)
            await client.aclose()

    return StreamingResponse(generator_wrapper(), media_type="text/event-stream")
