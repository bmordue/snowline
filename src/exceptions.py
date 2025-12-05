"""Custom exceptions for the Snowline visualization tool."""


class ConfigurationError(Exception):
    """Raised when configuration validation fails."""
    pass


class DataValidationError(Exception):
    """Raised when data validation fails."""
    pass
