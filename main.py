import uvicorn
import argparse
from fastapi import FastAPI
from api.routes import router
from api.middleware import RequestIDMiddleware, RateLimitMiddleware, error_handler_middleware
from core.transport import transport
from config.settings import settings
from contextlib import asynccontextmanager
import logging

logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info(f"Starting Free Fire API (Version {settings.ob_version})")
    await transport.get_session()
    yield
    # Shutdown
    logger.info("Shutting down...")
    await transport.close()

app = FastAPI(
    title="Free Fire UID Verification API",
    version="3.0.0",
    lifespan=lifespan
)

# Middleware (Order matters: outermost first)
app.middleware("http")(error_handler_middleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(RequestIDMiddleware)

app.include_router(router)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FF API Server")
    parser.add_argument("--serve", action="store_true", help="Start the FastAPI server")
    parser.add_argument("--port", type=int, default=settings.server_port, help="Port to run the server on")
    args = parser.parse_args()

    if args.serve:
        uvicorn.run("main:app", host="0.0.0.0", port=args.port, reload=False)
    else:
        print("Use --serve to start the server or use cli.py for command line interface.")
