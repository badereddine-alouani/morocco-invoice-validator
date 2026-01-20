from fastapi import FastAPI
from app.core.logging import setup_logging
from app.routers import invoices


setup_logging()

app = FastAPI(title="Moroccan Invoice Validator")

app.include_router(invoices.router)

@app.get("/")
def health_check():
    return {"status": "System is running", "location": "Morocco"}