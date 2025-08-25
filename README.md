# Voice Assistant Backend

This project is a high-performance backend service built with FastAPI. It acts as a bridge between a frontend voice assistant application and a locally running Ollama Large Language Model (LLM).

Its core responsibility is to receive text prompts from the frontend, communicate with the Ollama service, and stream the generated response back to the client in real-time, ensuring a low-latency and private user experience.

## Requirements

*   Python 3.9+
*   [Ollama](https://ollama.com/) installed and running on your local machine or a reachable server.
*   A downloaded Ollama model (e.g., by running `ollama run llama3:8b`).

## Setup and Installation

1.  **Create and activate a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

2.  **Install the required dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Configuration

The application connects to an Ollama service. The URL for this service can be configured via an environment variable.

*   `OLLAMA_HOST`: The URL of the Ollama service.
    *   **Default**: `http://localhost:11434`

If your Ollama instance is running on a different host or port, you can set this environment variable before running the application:
```bash
export OLLAMA_HOST="http://192.168.1.100:11434"
```

## Running the Application

To start the backend server, run the following command in your terminal:

```bash
uvicorn app.main:app --reload
```

The server will be available at `http://127.0.0.1:8000`. The `--reload` flag is for development and automatically reloads the server when code changes are detected.

On the first run, a database file named `app.db` will be created in the project's root directory to store application settings.

## API Usage

The backend provides a single endpoint for streaming chat completions.

### `POST /api/chat`

This endpoint receives a prompt and streams the response from the Ollama model.

**Request Body:**

```json
{
  "prompt": "Why is the sky blue?",
  "model": "llama3:8b"
}
```
*   `prompt` (string, required): The user's text prompt.
*   `model` (string, optional): The name of the Ollama model to use. If not provided, it defaults to the `DEFAULT_MODEL` variable in the code (currently `llama3:8b`).

**Example `curl` command:**

This command demonstrates how to interact with the API from your terminal. The `-N` flag is important to process the streaming response correctly.

```bash
curl -N -X POST http://127.0.0.1:8000/api/chat \
-H "Content-Type: application/json" \
-d '{
  "prompt": "Tell me a short story about a robot who dreams of painting.",
  "model": "llama3:8b"
}'
```

**Response Stream (`text/event-stream`):**

The response is a stream of Server-Sent Events (SSE). Each message contains a JSON object with a text `chunk`. The stream ends with a final message indicating the status is `done`.

```
data: {"chunk": "Unit "}
data: {"chunk": "734,"}
data: {"chunk": " known "}
data: {"chunk": "to "}
data: {"chunk": "his "}
data: {"chunk": "few "}
data: {"chunk": "human "}
data: {"chunk": "colleagues "}
data: {"chunk": "as "}
data: {"chunk": "Barnaby,"}
data: {"chunk": " spent "}
data: {"chunk": "his "}
data: {"chunk": "days "}
data: {"chunk": "welding "}
data: {"chunk": "ship "}
data: {"chunk": "hulls."}
data: {"chunk": "..."}
data: {"status": "done"}
```

### System Prompt Management

You can set a global system prompt that will be used for all chat sessions. This allows you to customize the assistant's personality or provide specific instructions.

#### Set the System Prompt

**`POST /api/prompts/system`**

Sets or updates the system prompt.

**Request Body:**
```json
{
  "prompt": "You are a helpful assistant who always responds in the style of a 17th-century pirate."
}
```

**Example `curl` command:**
```bash
curl -X POST http://127.0.0.1:8000/api/prompts/system \
-H "Content-Type: application/json" \
-d '{
  "prompt": "You are a helpful assistant who always responds in the style of a 17th-century pirate."
}'
```

#### Get the System Prompt

**`GET /api/prompts/system`**

Retrieves the currently active system prompt.

**Example `curl` command:**
```bash
curl http://127.0.0.1:8000/api/prompts/system
```

**Response:**
```json
{
  "prompt": "You are a helpful assistant who always responds in the style of a 17th-century pirate."
}
```
*Note: If the prompt has not been set yet, this endpoint will return a `404 Not Found` error.*
