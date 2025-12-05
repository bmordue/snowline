"""Data loader implementations for snow cover data."""

from abc import ABC, abstractmethod
from datetime import date
from pathlib import Path
from typing import Optional

import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

from src.config import Config, BoundingBox
from src.data.validation import validate_snow_data


class DataLoader(ABC):
    """Abstract base class for data loaders."""
    
    @abstractmethod
    def load(self) -> pd.DataFrame:
        """Load the raw data."""
        pass
    
    @abstractmethod
    def filter_by_date_range(self, start: date, end: date) -> pd.DataFrame:
        """Filter data to specified date range (inclusive)."""
        pass
    
    @abstractmethod
    def filter_by_bounding_box(self, bbox: BoundingBox) -> pd.DataFrame:
        """Filter data to specified geographic region."""
        pass


class SSGBDataLoader(DataLoader):
    """Loader for Snow Survey of Great Britain data."""
    
    def __init__(self, data_path: Path):
        """Initialize the loader with a path to the CSV file.
        
        Args:
            data_path: Path to the SSGB CSV data file.
        """
        self.data_path = data_path
        self._raw_data: Optional[pd.DataFrame] = None
    
    def load(self) -> pd.DataFrame:
        """Load the raw CSV data, caching it in memory.
        
        Returns:
            DataFrame containing the loaded data.
            
        Raises:
            FileNotFoundError: If the data file does not exist.
            DataValidationError: If the data fails validation.
        """
        if self._raw_data is None:
            try:
                self._raw_data = pd.read_csv(
                    self.data_path,
                    parse_dates=['date'],
                    dtype={'site_id': str}
                )
                # Convert parsed datetime64 to date objects for consistency
                self._raw_data['date'] = pd.to_datetime(self._raw_data['date']).dt.date
            except ValueError as e:
                if "parse_dates" in str(e):
                    # Missing date column - load without parsing and let validation catch it
                    self._raw_data = pd.read_csv(
                        self.data_path,
                        dtype={'site_id': str}
                    )
                else:
                    raise
            validate_snow_data(self._raw_data)
        return self._raw_data.copy()
    
    def filter_by_date_range(
        self, 
        start_date: date, 
        end_date: date
    ) -> pd.DataFrame:
        """Filter data to specified date range (inclusive).
        
        Args:
            start_date: Start of date range (inclusive).
            end_date: End of date range (inclusive).
            
        Returns:
            DataFrame filtered to the specified date range.
        """
        df = self.load()
        mask = (df['date'] >= start_date) & (df['date'] <= end_date)
        return df[mask].copy()
    
    def filter_by_bounding_box(
        self, 
        bbox: BoundingBox
    ) -> pd.DataFrame:
        """Filter data to specified geographic region.
        
        Args:
            bbox: BoundingBox defining the geographic region.
            
        Returns:
            DataFrame filtered to the specified region.
        """
        df = self.load()
        mask = (
            (df['longitude'] >= bbox.min_lon) & 
            (df['longitude'] <= bbox.max_lon) &
            (df['latitude'] >= bbox.min_lat) & 
            (df['latitude'] <= bbox.max_lat)
        )
        return df[mask].copy()
    
    def to_geodataframe(self) -> gpd.GeoDataFrame:
        """Convert the loaded data to a GeoDataFrame for spatial operations.
        
        Returns:
            GeoDataFrame with geometry column derived from lat/lon coordinates.
        """
        df = self.load()
        geometry = [Point(xy) for xy in zip(df['longitude'], df['latitude'])]
        return gpd.GeoDataFrame(df, geometry=geometry, crs="EPSG:4326")


def get_data_loader(config: Config) -> DataLoader:
    """Factory function to return appropriate loader based on config.
    
    Args:
        config: Application configuration containing input file paths.
        
    Returns:
        A DataLoader instance appropriate for the configured data source.
    """
    # For now, only SSGB CSV is supported
    return SSGBDataLoader(config.input.snow_cover_data)
