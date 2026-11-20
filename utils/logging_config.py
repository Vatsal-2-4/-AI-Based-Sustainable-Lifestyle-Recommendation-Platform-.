"""Configure app logging without recording secrets or unnecessary profile data."""
import logging

def get_logger(name="sustainable_platform"):
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
    return logging.getLogger(name)
