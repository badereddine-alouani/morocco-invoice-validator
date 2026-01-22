from fastapi import APIRouter, UploadFile, HTTPException
from pathlib import Path
from app.worker import process_invoice_task
from celery.result import AsyncResult
from app.celery_app import celery_app
import os
import shutil


router = APIRouter(prefix="/invoices", tags=["Invoices"])
UPLOAD_DIR = Path("temp")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

@router.post("/validate")
def validate_invoice_endpoint(file: UploadFile):

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed.")
    
    filename = Path(file.filename).name
    save_to = UPLOAD_DIR / f"temp_{filename}"
    
    try:
        with open(save_to, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        task = process_invoice_task.delay(str(save_to))

        return {
            "task_id": task.id,
            "status": "processing started",
            "message": f"Check results at GET /invoices/status/{task.id}"
        }
    except Exception as e:
        if save_to.exists():
            os.remove(save_to)
        raise HTTPException(status_code=500, detail=f"Could not save file: {e}")
    
    finally:
        file.file.close()



@router.get("/status/{task_id}")
def get_task_status(task_id: str):
    task_result = AsyncResult(task_id, app=celery_app)

    if task_result.state == 'SUCCESS':
        return {"status": "Completed", "data": task_result.result}
    elif task_result.state == 'FAILURE':
        return {"status": "Failed", "error": str(task_result.result)}
    
    else:
        return {"status": "Pending"}

