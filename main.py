import uvicorn
from fastapi import FastAPI
from api.routes import router
from api.middleware import RequestIDMiddleware, RateLimitMiddleware, error_handler
from api.errors import FFError
from core.transport import transport
from config.settings import settings

app = FastAPI(title="Free Fire UID Verification API", version="3.0.0")

# Register middleware
app.add_middleware(RequestIDMiddleware)
app.add_middleware(RateLimitMiddleware)

# Register error handler
app.add_exception_handler(FFError, error_handler)
app.add_exception_handler(Exception, error_handler)

# Register routes
app.include_router(router)

@app.on_event("startup")
async def startup_event():
    print(f"Starting Free Fire API {settings.OB_VERSION}...")
    await transport.get_session()

@app.on_event("shutdown")
async def shutdown_event():
    await transport.close()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=settings.SERVER_PORT)
