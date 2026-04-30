"""Logging configuration for the Snowline CLI."""

import logging
import sys


def configure_logging(verbosity: int = 0, quiet: bool = False) -> logging.Logger:
    """Configure the ``snowline`` logger based on verbosity.

    Parameters
    ----------
    verbosity : int
        Verbosity level. ``0`` enables WARNING (default), ``1`` enables INFO,
        and ``2`` or greater enables DEBUG.
    quiet : bool
        If ``True``, suppress all output except errors. Overrides ``verbosity``.

    Returns
    -------
    logging.Logger
        The configured ``snowline`` logger.
    """
    logger = logging.getLogger('snowline')

    if quiet:
        level = logging.ERROR
    elif verbosity == 0:
        level = logging.WARNING
    elif verbosity == 1:
        level = logging.INFO
    else:
        level = logging.DEBUG

    logger.setLevel(level)

    # Remove any pre-existing handlers so that repeated calls (e.g. in tests)
    # do not duplicate log output.
    for existing in list(logger.handlers):
        logger.removeHandler(existing)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)

    if verbosity >= 2:
        fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    else:
        fmt = '%(levelname)s: %(message)s'

    handler.setFormatter(logging.Formatter(fmt))
    logger.addHandler(handler)
    logger.propagate = False

    return logger
