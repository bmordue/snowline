"""Pipeline orchestration for snowline extraction."""

from datetime import date, timedelta
from typing import Iterator

import geopandas as gpd

from src.config import Config
from src.data.loader import DataLoader
from src.processing.processor import SnowlineProcessor


class SnowlinePipeline:
    """Orchestrates the snowline extraction pipeline."""
    
    def __init__(
        self, 
        config: Config,
        loader: DataLoader,
        processor: SnowlineProcessor
    ):
        """
        Initialize the pipeline.
        
        Args:
            config: Application configuration.
            loader: Data loader for snow observations.
            processor: Snowline processor implementation.
        """
        self.config = config
        self.loader = loader
        self.processor = processor
    
    def _date_range(self) -> Iterator[date]:
        """Generate dates in the configured range."""
        current = self.config.time.start_date
        while current <= self.config.time.end_date:
            yield current
            current += timedelta(days=1)
    
    def run(self) -> dict[date, gpd.GeoDataFrame]:
        """
        Run the full pipeline, returning snowlines by date.
        
        Returns:
            Dictionary mapping dates to GeoDataFrames containing snowline
            geometries for that date.
        """
        # Load and filter data
        data = self.loader.load()
        
        # Filter by date range
        filtered_data = self.loader.filter_by_date_range(
            self.config.time.start_date,
            self.config.time.end_date
        )
        
        # Update the loader's cached data with filtered data
        self.loader._raw_data = filtered_data
        
        # Filter by bounding box
        filtered_data = self.loader.filter_by_bounding_box(
            self.config.region.bounding_box
        )
        
        # Update the loader's cached data with filtered data
        self.loader._raw_data = filtered_data
        
        # Convert to GeoDataFrame
        gdf = self.loader.to_geodataframe()
        
        # Process each date
        results = {}
        for target_date in self._date_range():
            snowline = self.processor.extract_snowline(gdf, target_date)
            results[target_date] = snowline
        
        return results
