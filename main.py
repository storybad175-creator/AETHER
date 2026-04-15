import uvicorn
import argparse
from fastapi import FastAPI
from contextlib import asynccontextmanager
from api.routes import router
from api.middleware import RequestIDMiddleware, RateLimitMiddleware, error_handler_middleware
from core.transport import transport
from config.settings import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize shared session
    await transport.get_session()
    yield
    # Graceful shutdown
    await transport.close()

app = FastAPI(
    title="Free Fire UID Verification API",
    version="3.0.0",
    lifespan=lifespan
)

# Register Middlewares
app.add_middleware(RequestIDMiddleware)
app.add_middleware(RateLimitMiddleware)
app.middleware("http")(error_handler_middleware)

# Register Routes
app.include_router(router)

def start_server(port: int = None):
    port = port or settings.SERVER_PORT
    uvicorn.run(app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FF API Server")
    parser.add_argument("--port", type=int, help="Port to run the server on")
    parser.add_argument("--serve", action="store_true", help="Start the FastAPI server")
    args = parser.parse_args()

    if args.serve or not any(vars(args).values()):
        start_server(args.port)
