import httpx
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.models import ChatRequest
from app.services import stream_ollama_response_generator
from app.config import OLLAMA_HOST, DEFAULT_MODEL

router = APIRouter()

# FastAPI automatically handles request validation for the ChatRequest model.
# A 422 Unprocessable Entity response will be returned for invalid data.
@router.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """
    The API endpoint for handling chat requests.
    It connects to the Ollama service and streams the response back to the client.
    """
    model_to_use = request.model if request.model else DEFAULT_MODEL
    ollama_api_url = f"{OLLAMA_HOST}/api/chat"
    payload = {
        "model": model_to_use,
        "messages": [{"role": "user", "content": request.prompt}],
        "stream": True,
    }

    # Using a long timeout for the client as the stream can be long-running
    client = httpx.AsyncClient(timeout=None)

    try:
        # Initiate the streaming request to the Ollama service
        response_stream = await client.stream("POST", ollama_api_url, json=payload)
    except httpx.ConnectError:
        await client.aclose()
        raise HTTPException(
            status_code=503, detail="Service Unavailable: Could not connect to Ollama."
        )

    # We create a wrapper generator to ensure the httpx client is closed properly
    # after the streaming response has finished.
    async def generator_wrapper():
        try:
            # Pass the raw response stream to the service-layer generator
            async for chunk in stream_ollama_response_generator(response_stream):
                yield chunk
        finally:
            # This block will execute after the generator is exhausted,
            # ensuring the client is always closed.
            await client.aclose()

    return StreamingResponse(generator_wrapper(), media_type="text/event-stream")
