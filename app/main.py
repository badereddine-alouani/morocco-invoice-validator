from fastapi import FastAPI
from app.core.logging import setup_logging
from app.routers import invoices
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.core.security import limiter



setup_logging()

app = FastAPI(title="Moroccan Invoice Validator")

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

origins = [
    "http://localhost:8501",
    "http://127.0.0.1:8501",
    "http://host.docker.internal:8501"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=["localhost", "127.0.0.1", "0.0.0.0", "*"]
)

app.include_router(invoices.router)



@app.get("/")
def health_check():
    return {"status": "ok", "version": "1.0.0"}