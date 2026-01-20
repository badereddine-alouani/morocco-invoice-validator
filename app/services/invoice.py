import logging
from pathlib import Path
from app.services.ocr_engine import extract_invoice_data
from app.services.validator import validate_invoice
from app.schemas.invoices import ValidationResult


logger = logging.getLogger(__name__)

def process_invoice(file_path: str) -> ValidationResult:
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"The file {file_path} does not exist.")
    
    if not path.is_file():
        raise IsADirectoryError(f"{file_path} is a directory, not a file.")
    
    if path.suffix.lower() != '.pdf':
        raise ValueError(f"Expected a .pdf file, but got {path.suffix}")
    
    filename = path.name
    logger.info(f"Processing file: {filename}")

    try:
        extracted_data = extract_invoice_data(file_path)

        logger.info(f"OCR Complete. Invoice #{extracted_data.meta.invoice_number}")

        issues = validate_invoice(extracted_data)

        is_valid = len(issues) == 0

        if is_valid:
            logger.info(f"Validation successful for {filename}")
        else:
            logger.warning(f"Validation failed for {filename} with {len(issues)} issues")

        return ValidationResult(is_valid=is_valid, filename=filename, issues=issues, extracted_data=extracted_data)
    
    except Exception as e:
        logger.error(f"Pipeline crashed processing {filename}: {e}", exc_info=True)
        raise e

