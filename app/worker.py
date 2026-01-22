import os
from app.celery_app import celery_app
from app.services.invoice import process_invoice
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)

@celery_app.task(bind=True)
def process_invoice_task(self, file_path: str):
    logger.info(f"Started processing invoice: {file_path}")
    try:
        logger.debug("Sending file to pipeline...")
        result = process_invoice(file_path)
        logger.debug("Pipeline complete.")

        if os.path.exists(file_path):
            os.remove(file_path)
            logger.debug(f"Deleted temp file: {file_path}")

        return result.model_dump()
    
    except Exception as e:
        logger.error(f"Processing failed for {file_path}: {e}", exc_info=True)
        return {"error": str(e), "status": "failed"}
    
    finally:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                logger.info(f"Deleted temp file: {file_path}")
            except Exception as cleanup_error:
                logger.warning(f"Failed to delete file: {cleanup_error}")