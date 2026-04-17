import uvicorn
from fastapi import FastAPI
from contextlib import asynccontextmanager
from api.routes import router
from api.middleware import RequestIDMiddleware, RateLimitMiddleware, error_handler_middleware
from core.transport import transport
from config.settings import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await transport.ensure_session()
    yield
    # Shutdown
    await transport.close()

app = FastAPI(
    title="Free Fire UID Verification API",
    version="3.0.0",
    description="Multi-region player data fetching API for Free Fire OB53",
    lifespan=lifespan
)

# Add middlewares in correct order
# error_handler_middleware should be outermost to catch everything
app.middleware("http")(error_handler_middleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(RequestIDMiddleware)

app.include_router(router)

if __name__ == "__main__":
    print(f"Starting FF API Server on port {settings.SERVER_PORT}...")
    print(f"Targeting version: {settings.OB_VERSION}")
    uvicorn.run(app, host="0.0.0.0", port=settings.SERVER_PORT)
