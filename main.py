import os
import json
import httpx
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional


# --- API Data Models ---
class ChatRequest(BaseModel):
    prompt: str
    model: Optional[str] = None


# --- Configuration ---
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
DEFAULT_MODEL = "llama3:8b"

# --- FastAPI App Initialization ---
app = FastAPI()

# --- CORS Middleware ---
# In a production environment, you should restrict the origins to your frontend's domain.
# For example: origins = ["https://your-frontend-domain.com"]
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- API Endpoints ---

# FastAPI automatically handles request validation and will return a 422 Unprocessable Entity
# response if the request body does not match the ChatRequest model.
@app.post("/api/chat")
async def api_chat(request: ChatRequest):
    """
    The main endpoint to handle chat requests.
    It streams the response from the Ollama model.
    """
    model_to_use = request.model if request.model else DEFAULT_MODEL
    # We use the /api/chat endpoint for better future compatibility with conversation history
    ollama_api_url = f"{OLLAMA_HOST}/api/chat"
    payload = {
        "model": model_to_use,
        "messages": [{"role": "user", "content": request.prompt}],
        "stream": True,
    }

    client = httpx.AsyncClient(timeout=None)

    try:
        response_stream = await client.stream("POST", ollama_api_url, json=payload)
    except httpx.ConnectError:
        await client.aclose()
        raise HTTPException(
            status_code=503, detail="Service Unavailable: Could not connect to Ollama."
        )

    async def response_generator():
        try:
            response_stream.raise_for_status()
            async for line in response_stream.aiter_lines():
                if line:
                    try:
                        data = json.loads(line)
                        # For /api/chat, the content is in message.content
                        message = data.get("message", {})
                        if message.get("content"):
                            chunk = message["content"]
                            yield f"data: {json.dumps({'chunk': chunk})}\n\n"

                        # Break the loop if Ollama signals it's done
                        if data.get("done"):
                            break
                    except json.JSONDecodeError:
                        print(f"Warning: Received non-JSON line from Ollama: {line}")
            # Send the final 'done' status message
            yield f"data: {json.dumps({'status': 'done'})}\n\n"
        except httpx.HTTPStatusError as e:
            # If Ollama returns an error status (e.g., 404 for a model not found),
            # we can't change the HTTP status of our response anymore since the headers have already been sent.
            # Instead, we send a custom error message within the event stream to the client.
            print(f"Error from Ollama API: {e}")
            error_payload = json.dumps(
                {
                    "status": "error",
                    "message": f"Ollama API Error: {e.response.text}",
                }
            )
            yield f"data: {error_payload}\n\n"
        finally:
            # Ensure the stream and client are always closed
            await response_stream.aclose()
            await client.aclose()

    return StreamingResponse(response_generator(), media_type="text/event-stream")
