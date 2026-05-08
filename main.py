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
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handles startup and shutdown events."""
    logger.info(f"🚀 Starting Free Fire API (Version {settings.OB_VERSION})...")
    logger.info(f"🌍 Active Regions: {settings.OB_VERSION} UNLIMITED - 14 Regions Loaded")
    yield
    logger.info("🛑 Shutting down Free Fire API...")
    await transport.close()

app = FastAPI(
    title="Free Fire UID Verification API",
    description="The definitive API for fetching player data across all 14 regions.",
    version="3.0.0",
    lifespan=lifespan
)

# Add Middleware (Ordering matters)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(RateLimitMiddleware)
# Error handler as the outermost layer to catch middleware exceptions too
app.middleware("http")(error_handler_middleware)

# Include Routes
app.include_router(router)

def find_available_port(start_port: int, max_attempts: int = 5) -> int:
    """Attempts to find an available port starting from start_port."""
    for port in range(start_port, start_port + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("0.0.0.0", port))
                return port
            except OSError:
                logger.warning(f"Port {port} is in use. Trying next...")
    return start_port

if __name__ == "__main__":
    import sys
    port = settings.SERVER_PORT

    if len(sys.argv) > 1 and sys.argv[1] == "--port":
        port = int(sys.argv[2])
    else:
        port = find_available_port(port)

    print(f"\n✨ Server running on http://0.0.0.0:{port}")
    print(f"📚 Documentation: http://0.0.0.0:{port}/docs\n")

    uvicorn.run(app, host="0.0.0.0", port=port, log_level=settings.LOG_LEVEL.lower())
