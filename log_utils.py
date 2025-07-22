import logging

class FlushFileHandler(logging.FileHandler):
    def emit(self, record):
        super().emit(record)
        self.flush()


def setup_logger(log_file="choochoowatch.log"):
    logger = logging.getLogger("choochoowatch")
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        file_handler = FlushFileHandler(log_file, mode="a", encoding="utf-8")
        formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    return logger


logger = setup_logger()


def log(msg: str) -> None:
    print(msg)
    logger.info(msg)
