import logging

def setup_logger():
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)  # Set to INFO to reduce the verbosity of the logs
    formatter = logging.Formatter('%(asctime)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    handler.setFormatter(formatter)
    logger = logging.getLogger(__name__)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)  # Set to INFO to reduce the verbosity of the logs
    logger.propagate = False
    return logger
