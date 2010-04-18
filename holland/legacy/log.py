try:
    import logging
    import logging.handlers as handlers
except ImportError:
    import holland.backports.logging as logging
    import holland.backports.logging.handlers as handlers

def get_logging():
    logging.handlers = handlers
    return logging

def get_logger(namespace):
    """
    Get logging namespace.  
    
    Example:
    
        log = holland.helpers.log.get_logger(__name__)
    """
    return logging.getLogger(namespace)

