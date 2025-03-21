import logging

# def setup_logger(name):
#     """Sets up a logger with console output."""
#     logger = logging.getLogger(name)
#     logger.setLevel(logging.INFO)

#     if not logger.handlers:
#         ch = logging.StreamHandler()
#         ch.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
#         logger.addHandler(ch)

#     return logger



def setup_logger(name):
    logging.basicConfig(level=logging.INFO)
    return logging.getLogger(name)