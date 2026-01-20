from fastapi import APIRouter, UploadFile, HTTPException
from pathlib import Path
from app.schemas.invoices import ValidationResult
from app.services.invoice import process_invoice
import os
import shutil


router = APIRouter(prefix="/invoices", tags=["Invoices"])
UPLOAD_DIR = Path("temp")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

@router.post("/validate", response_model=ValidationResult)
def validate_invoice_endpoint(file: UploadFile):

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed.")
    
    filename = Path(file.filename).name
    save_to = UPLOAD_DIR / f"temp_{filename}"
    
    try:
        with open(save_to, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        result = process_invoice(str(save_to))

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not save file: {e}")
    
    finally:
        file.file.close()
        if save_to.exists():
            os.remove(save_to)
