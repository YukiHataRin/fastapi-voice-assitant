from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import the chat router
from app.routers import chat

# --- FastAPI App Initialization ---
# This is the main application instance that Uvicorn will run.
app = FastAPI(
    title="Voice Assistant Backend",
    description="A backend service to proxy requests to an Ollama LLM.",
    version="1.0.0",
)

# --- CORS Middleware ---
# For development, we allow all origins.
# In a production environment, this should be restricted to the frontend's domain.
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Include Routers ---
# Include the chat router. All routes defined in chat.router will be prefixed with /api.
# So, the endpoint POST /chat in the router becomes POST /api/chat.
app.include_router(chat.router, prefix="/api")

# --- Root Endpoint ---
@app.get("/")
async def read_root():
    return {"message": "Voice Assistant Backend is running."}
