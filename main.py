import uvicorn
import logging
import socket
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

# Add Middleware
# Note: error_handler_middleware is added via .middleware() to ensure it's the outermost
app.add_middleware(RequestIDMiddleware)
app.add_middleware(RateLimitMiddleware)
app.middleware("http")(error_handler_middleware)

# Include Routes
app.include_router(router)

def is_port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def run_server():
    import sys
    port = settings.SERVER_PORT
    if len(sys.argv) > 1 and sys.argv[1] == "--port":
        port = int(sys.argv[2])

    # FM-09: Port conflict resolution
    attempts = 0
    max_attempts = 5
    while is_port_in_use(port) and attempts < max_attempts:
        logger.warning(f"Port {port} is in use. Trying {port + 1}...")
        port += 1
        attempts += 1

    if attempts == max_attempts:
        logger.error(f"Could not find an open port after {max_attempts} attempts.")
        sys.exit(1)

    logger.info(f"API Banner: OB53 UNLIMITED - Active Regions: 14")
    logger.info(f"Serving on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    run_server()
