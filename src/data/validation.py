"""Data validation functions for snow observation data."""

import pandas as pd

from src.exceptions import DataValidationError


def validate_snow_data(df: pd.DataFrame) -> None:
    """Validate that loaded data has required columns and valid values.
    
    Args:
        df: DataFrame containing snow observation data.
        
    Raises:
        DataValidationError: If validation fails.
    """
    required_columns = ['date', 'site_id', 'latitude', 'longitude']
    
    missing = set(required_columns) - set(df.columns)
    if missing:
        raise DataValidationError(f"Missing required columns: {missing}")
    
    # Check for valid latitude range
    if not df['latitude'].empty and (df['latitude'].abs() > 90).any():
        raise DataValidationError("Invalid latitude values detected (must be in range [-90, 90])")
    
    # Check for valid longitude range
    if not df['longitude'].empty and (df['longitude'].abs() > 180).any():
        raise DataValidationError("Invalid longitude values detected (must be in range [-180, 180])")
