import json
import httpx

async def stream_ollama_response_generator(response_stream: httpx.Response):
    """
    An async generator that processes an httpx.Response stream from Ollama,
    yielding Server-Sent Events (SSE) formatted strings.

    This function handles parsing the JSON lines, extracting the content,
    and formatting it for the client. It also handles in-stream errors
    from the Ollama API.
    """
    try:
        # Raise an exception for bad status codes (4xx or 5xx)
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

        # Send the final 'done' status message once the loop is complete
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
        # Ensure the stream is always closed
        await response_stream.aclose()
