from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import time

# Import routers
from app.routers import chat, prompts
from app.database import engine, Base

# --- FastAPI App Initialization ---
# This is the main application instance that Uvicorn will run.
app = FastAPI(
    title="Voice Assistant Backend",
    description="A backend service to proxy requests to an Ollama LLM.",
    version="1.0.0",
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()

    response = await call_next(request)

    process_time = (time.time() - start_time) * 1000
    formatted_process_time = '{0:.2f}'.format(process_time)

    # 這裡的 request.client.host 會是真實 IP
    client_host = request.client.host

    # 模仿 Uvicorn 的日誌格式
    print(f'INFO:     {client_host} - "{request.method} {request.url.path}" {response.status_code} - {formatted_process_time}ms')

    return response

# --- Database Initialization ---
# This event handler will run when the application starts.
@app.on_event("startup")
async def on_startup():
    # Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

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
app.include_router(prompts.router, prefix="/api")

# --- Root Endpoint ---
@app.get("/")
async def read_root():
    return {"message": "Voice Assistant Backend is running."}
