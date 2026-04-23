import uvicorn
import logging
import sys
import socket
from fastapi import FastAPI
from contextlib import asynccontextmanager
from api.routes import router
from api.middleware import RequestIDMiddleware, RateLimitMiddleware, error_handler_middleware
from core.transport import transport
from config.settings import settings

# Setup logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL, logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handles startup and shutdown events for the FastAPI application."""
    logger.info(f"Starting Free Fire API - APEX v3.0 UNLIMITED (Version {settings.OB_VERSION})")
    logger.info(f"Supported Regions: 14 | Cache TTL: {settings.CACHE_TTL_SECONDS}s")

    yield

    logger.info("Gracefully shutting down Free Fire API...")
    await transport.close()

app = FastAPI(
    title="Free Fire UID Verification API",
    description="The definitive production-ready API for fetching player data across all 14 Garena regions.",
    version="3.0.0",
    lifespan=lifespan
)

# Middleware configuration (Order matters: outermost first)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(RateLimitMiddleware)
# Error handler as the outermost layer to catch all exceptions
app.middleware("http")(error_handler_middleware)

# Include API routes
app.include_router(router)

def is_port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def start_server():
    port = settings.SERVER_PORT

    # FM-09: Fastapi Port Conflict Resolution
    max_retries = 5
    for i in range(max_retries):
        if not is_port_in_use(port):
            break
        logger.warning(f"Port {port} is already in use. Retrying on {port + 1}...")
        port += 1
    else:
        logger.error(f"Could not find an available port after {max_retries} attempts.")
        sys.exit(1)

    logger.info(f"Binding to 0.0.0.0:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level=settings.LOG_LEVEL.lower())

if __name__ == "__main__":
    # Check for --serve flag or just start if no CLI args
    if len(sys.argv) > 1 and sys.argv[1] == "--cli":
        print("Please run cli.py for command line interface.")
        sys.exit(0)

    start_server()
