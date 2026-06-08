import logging


def get_logger(name: str | None = None) -> logging.Logger:
    if not name:
        return logging.getLogger("pymax")

    if name.startswith("pymax"):
        return logging.getLogger(name)

    return logging.getLogger(f"pymax.{name}")


logging.getLogger("pymax").addHandler(logging.NullHandler())
