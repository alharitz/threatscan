import logging
import os

class NoExceptionFilter(logging.Filter):
    def filter(self, record):
        record.exc_info = None
        record.exc_text = None
        return True

def setup_logger():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    log_dir = os.path.join(base_dir, "../storage/logs")
    log_dir = os.path.normpath(log_dir)
    os.makedirs(log_dir, exist_ok=True)

    root_logger = logging.getLogger("threatscan")
    root_logger.setLevel(logging.DEBUG)

    if root_logger.hasHandlers():
        root_logger.handlers.clear()


    # LOG INFO
    info_handler = logging.FileHandler(os.path.join(log_dir, "info.log"), mode="w", encoding="utf-8")
    info_handler.setLevel(logging.INFO)
    info_handler.setFormatter(logging.Formatter(
        "[%(asctime)s][%(levelname)s][%(name)s] %(message)s"
    ))

    # LOG WARNING
    warning_handler = logging.FileHandler(os.path.join(log_dir, "warning.log"), mode="w")
    warning_handler.setLevel(logging.WARNING)
    warning_handler.setFormatter(logging.Formatter(
        "[%(asctime)s][%(levelname)s][%(name)s] %(message)s"
    ))

    # LOG ERROR
    error_handler = logging.FileHandler(os.path.join(log_dir, "error.log"), mode="w")
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(logging.Formatter(
        "[%(asctime)s][%(levelname)s][%(name)s] %(message)s"
    ))


    # CONSOLE LOGGING, you can turn on these for development

    # CONSOLE LOG INFO
    console_log_handler = logging.StreamHandler()
    console_log_handler.setFormatter(...)
    console_log_handler.setLevel(logging.INFO)
    console_log_handler.addFilter(NoExceptionFilter())
    console_log_handler.setFormatter(logging.Formatter(
        "[%(asctime)s][%(levelname)s][%(name)s]: %(message)s"
    ))

    # CONSOLE LOG WARNING
    console_warning_handler = logging.StreamHandler()
    console_warning_handler.setLevel(logging.WARNING)
    console_warning_handler.addFilter(NoExceptionFilter())
    console_warning_handler.setFormatter(logging.Formatter(
        "[%(asctime)s][%(levelname)s][%(name)s]: %(message)s"
    ))

    # CONSOLE LOG ERROR
    console_error_handler = logging.StreamHandler()
    console_error_handler.setLevel(logging.ERROR)
    console_error_handler.addFilter(NoExceptionFilter())
    console_error_handler.setFormatter(logging.Formatter(
        "[%(asctime)s][%(levelname)s][%(name)s] Something went wrong, check /storage/logs/error.log for details"
    ))

    # ROOT LOGGER
    root_logger.addHandler(error_handler)
    root_logger.addHandler(info_handler)

    root_logger.addHandler(console_log_handler)
    root_logger.addHandler(console_error_handler)

    return root_logger