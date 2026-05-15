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
# Order matters: Error handler should be outermost to catch everything
app.add_middleware(RequestIDMiddleware)
app.add_middleware(RateLimitMiddleware)
app.middleware("http")(error_handler_middleware)

# Include Routes
app.include_router(router)

def find_available_port(start_port: int, max_attempts: int = 5) -> int:
    """Checks for an available port starting from start_port."""
    for port in range(start_port, start_port + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("0.0.0.0", port))
                return port
            except socket.error:
                logger.warning(f"Port {port} is in use, trying next...")
                continue
    raise RuntimeError(f"Could not find an available port after {max_attempts} attempts.")

if __name__ == "__main__":
    import sys

    try:
        requested_port = settings.SERVER_PORT
        if len(sys.argv) > 1 and sys.argv[1] == "--port":
            requested_port = int(sys.argv[2])

        final_port = find_available_port(requested_port)

        logger.info(f"API Banner: OB53 UNLIMITED - Active Regions: 14")
        logger.info(f"Serving on port: {final_port}")

        uvicorn.run(app, host="0.0.0.0", port=final_port)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        sys.exit(1)
