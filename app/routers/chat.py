import httpx
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.models import ChatRequest
from app.services import stream_ollama_response_generator
from app.config import OLLAMA_HOST, DEFAULT_MODEL

router = APIRouter()

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

    client = httpx.AsyncClient(timeout=None)

    # Manually create the stream context so we can handle connection errors
    # before we start sending a response to our client.
    stream_context = client.stream("POST", ollama_api_url, json=payload)

    try:
        # Manually enter the async context. This is where the connection is made.
        response_stream = await stream_context.__aenter__()
    except httpx.ConnectError:
        # If connection fails, close the client and raise a 503 error.
        await client.aclose()
        raise HTTPException(
            status_code=503, detail="Service Unavailable: Could not connect to Ollama."
        )
    except Exception as e:
        # Handle other potential startup errors.
        await client.aclose()
        raise HTTPException(
            status_code=500, detail=f"An unexpected error occurred: {e}"
        )

    # This wrapper generator is now responsible for ensuring the stream context
    # and the client are properly closed.
    async def generator_wrapper():
        try:
            # Pass the raw response stream to the service-layer generator
            async for chunk in stream_ollama_response_generator(response_stream):
                yield chunk
        finally:
            # Ensure the stream context is exited and the client is closed.
            # The arguments to __aexit__ are exception type, value, and traceback.
            # Passing None indicates no exception occurred within the stream's processing.
            await stream_context.__aexit__(None, None, None)
            await client.aclose()

    return StreamingResponse(generator_wrapper(), media_type="text/event-stream")
