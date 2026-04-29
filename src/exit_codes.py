"""Exit code definitions for the Snowline CLI."""

from enum import IntEnum


class ExitCode(IntEnum):
    """Standard exit codes returned by the Snowline CLI."""

    SUCCESS = 0
    CONFIGURATION_ERROR = 1
    INPUT_NOT_FOUND = 2
    PROCESSING_ERROR = 3
    OUTPUT_ERROR = 4
    UNKNOWN_ERROR = 99
