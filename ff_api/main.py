import uvicorn
import argparse
from fastapi import FastAPI
from contextlib import asynccontextmanager
from ff_api.api.routes import router
from ff_api.api.middleware import RequestIDMiddleware, RateLimitMiddleware, error_handler_middleware
from ff_api.config.settings import settings
from ff_api.core.transport import transport
import logging

logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info(f"Starting FF API {settings.OB_VERSION}...")
    yield
    # Shutdown
    logger.info("Shutting down FF API...")
    await transport.close()

app = FastAPI(
    title="Free Fire UID Verification API",
    version="3.0",
    lifespan=lifespan
)

app.add_middleware(RequestIDMiddleware)
app.add_middleware(RateLimitMiddleware, rpm_limit=settings.RATE_LIMIT_RPM)
app.middleware("http")(error_handler_middleware)

app.include_router(router)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FF API Server")
    parser.add_argument("--port", type=int, default=settings.SERVER_PORT)
    parser.add_argument("--serve", action="store_true", default=True)
    args = parser.parse_args()

    uvicorn.run(app, host="0.0.0.0", port=args.port)
