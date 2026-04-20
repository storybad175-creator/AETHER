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
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handles startup and shutdown events."""
    logger.info(f"Starting Free Fire API (Version {settings.OB_VERSION})...")
    # Pre-warm session
    _ = transport.session
    yield
    logger.info("Shutting down Free Fire API...")
    await transport.close()

app = FastAPI(
    title="Free Fire UID Verification API",
    description="The definitive API for fetching player data across all 14 regions.",
    version="3.0.0",
    lifespan=lifespan
)

# Add Middleware - Order matters (Error handler added last to be outermost)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(RateLimitMiddleware)
app.middleware("http")(error_handler_middleware)

# Include Routes
app.include_router(router)

def is_port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def start_server():
    import argparse
    parser = argparse.ArgumentParser(description="Free Fire API Server")
    parser.add_argument("--port", type=int, default=settings.SERVER_PORT, help="Port to listen on")
    parser.add_argument("--serve", action="store_true", help="Start the FastAPI server")
    args, unknown = parser.parse_known_args()

    port = args.port
    # FM-09: Port conflict resolution
    for _ in range(5):
        if not is_port_in_use(port):
            break
        logger.warning(f"Port {port} is in use. Trying {port + 1}...")
        port += 1
    else:
        logger.error("Could not find an available port after 5 attempts.")
        sys.exit(1)

    logger.info(f"API Banner: OB53 UNLIMITED - Active Regions: 14")
    logger.info(f"Serving on http://0.0.0.0:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    start_server()
