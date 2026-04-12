import uvicorn
from fastapi import FastAPI
from api.routes import router
from api.middleware import RequestIDMiddleware, RateLimitMiddleware, ff_error_handler
from api.errors import FFError
from config.settings import settings
from core.transport import transport
from contextlib import asynccontextmanager
import logging

# Configure logging
logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger("ff_api")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    logger.info(f"Starting Free Fire API v3.0 | OB Version: {settings.OB_VERSION}")
    yield
    # Shutdown logic
    logger.info("Shutting down...")
    await transport.close()

app = FastAPI(
    title="Free Fire UID Verification API",
    description="APEX v3.0 Unlimited - Production Grade API",
    version="3.0.0",
    lifespan=lifespan
)

# Add Middlewares
app.add_middleware(RequestIDMiddleware)
app.add_middleware(RateLimitMiddleware)

# Add Error Handlers
app.add_exception_handler(FFError, ff_error_handler)

# Include Routes
app.include_router(router)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.SERVER_PORT,
        reload=False,
        access_log=True
    )
