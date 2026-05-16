import uvicorn
import logging
import socket
import sys
from fastapi import FastAPI
from contextlib import asynccontextmanager
from api.routes import router
from api.middleware import RequestIDMiddleware, RateLimitMiddleware, error_handler_middleware
from core.transport import transport
from config.settings import settings

# Setup logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handles startup and shutdown events."""
    logger.info(f"Starting Free Fire API (Version {settings.OB_VERSION})...")
    yield
    logger.info("Shutting down Free Fire API...")
    await transport.close()

app = FastAPI(
    title="Free Fire UID Verification API",
    description="The definitive API for fetching player data across all 14 regions.",
    version="3.0.0",
    lifespan=lifespan
)

# Add Middleware (error_handler as outermost)
app.middleware("http")(error_handler_middleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(RequestIDMiddleware)

# Include Routes
app.include_router(router)

def find_available_port(start_port: int, max_retries: int = 5) -> int:
    """Attempts to find an available port starting from start_port."""
    for port in range(start_port, start_port + max_retries):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("0.0.0.0", port))
                return port
            except socket.error:
                logger.warning(f"Port {port} is in use, trying next...")
                continue
    return start_port # Let uvicorn fail if no port found

if __name__ == "__main__":
    port = settings.SERVER_PORT
    if len(sys.argv) > 1 and sys.argv[1] == "--port":
        port = int(sys.argv[2])

    # Port conflict resolution
    actual_port = find_available_port(port)
    if actual_port != port:
        logger.info(f"Requested port {port} was busy. Using {actual_port} instead.")

    logger.info(f"API Banner: OB53 UNLIMITED - Active Regions: 14")
    uvicorn.run(app, host="0.0.0.0", port=actual_port)
