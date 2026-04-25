import uvicorn
import logging
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
    # Session is lazily initialized in transport.session, but we could pre-warm it here
    yield
    logger.info("Shutting down Free Fire API...")
    await transport.close()

app = FastAPI(
    title="Free Fire UID Verification API",
    description="The definitive API for fetching player data across all 14 regions.",
    version="3.0.0",
    lifespan=lifespan
)

# Add Middleware
app.add_middleware(RequestIDMiddleware)
app.add_middleware(RateLimitMiddleware)
app.middleware("http")(error_handler_middleware)

# Include Routes
app.include_router(router)

def find_available_port(start_port: int, max_retries: int = 5) -> int:
    """FM-09: Finds an available port starting from start_port."""
    import socket
    port = start_port
    for _ in range(max_retries):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("0.0.0.0", port))
                return port
            except OSError:
                logger.warning(f"Port {port} is occupied. Retrying on {port + 1}...")
                port += 1

    raise OSError(f"Could not find an available port after {max_retries} attempts.")

if __name__ == "__main__":
    import sys

    port = settings.SERVER_PORT
    if len(sys.argv) > 1 and sys.argv[1] == "--port":
        port = int(sys.argv[2])

    try:
        port = find_available_port(port)
    except OSError as e:
        logger.error(str(e))
        sys.exit(1)

    logger.info(f"API Banner: OB53 UNLIMITED - Active Regions: 14")
    logger.info(f"Starting server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
