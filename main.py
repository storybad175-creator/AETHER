import uvicorn
import logging
import argparse
from fastapi import FastAPI
from contextlib import asynccontextmanager
from api.routes import router
from api.middleware import RequestIDMiddleware, RateLimitMiddleware, error_handler_middleware
from core.transport import transport
from config.settings import settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info(f"Starting Free Fire API (Version {settings.OB_VERSION})")
    yield
    # Shutdown
    logger.info("Shutting down...")
    await transport.close()

app = FastAPI(
    title="Free Fire UID Verification API",
    description="Multi-region player data extraction API for OB53",
    version="3.0.0",
    lifespan=lifespan
)

# Add Middleware
app.middleware("http")(error_handler_middleware)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(RateLimitMiddleware)

# Include Routes
app.include_router(router, prefix="/api/v1")

def main():
    parser = argparse.ArgumentParser(description="FF API Server")
    parser.add_argument("--port", type=int, default=settings.SERVER_PORT, help="Port to run the server on")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind to")
    args = parser.parse_args()

    logger.info(f"API Server listening on {args.host}:{args.port}")
    uvicorn.run(app, host=args.host, port=args.port, log_level=settings.LOG_LEVEL.lower())

if __name__ == "__main__":
    main()
