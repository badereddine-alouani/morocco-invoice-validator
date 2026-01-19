import logging
import sys

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

def setup_logging():
  
    # 1. Create a StreamHandler (prints to Console/Terminal)
    # This is crucial for Docker/Cloud logs
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT))

    # 2. Configure the Root Logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO) # Capture INFO, WARNING, ERROR
    root_logger.addHandler(handler)

    # 3. Silence noisy libraries (Optional)
    # Prevent internal libraries (like HTTP clients) from flooding your logs
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("pdfminer").setLevel(logging.WARNING)