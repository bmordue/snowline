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
        # Load data
        data = self.loader.load()
        
        # Filter by date range and bounding box
        filtered_data = data[
            (data['date'] >= self.config.time.start_date) &
            (data['date'] <= self.config.time.end_date) &
            (data['longitude'] >= self.config.region.bounding_box.min_lon) &
            (data['longitude'] <= self.config.region.bounding_box.max_lon) &
            (data['latitude'] >= self.config.region.bounding_box.min_lat) &
            (data['latitude'] <= self.config.region.bounding_box.max_lat)
        ]
        
        # Convert filtered data to GeoDataFrame
        from shapely.geometry import Point
        geometry = [Point(xy) for xy in zip(filtered_data['longitude'], filtered_data['latitude'])]
        gdf = gpd.GeoDataFrame(filtered_data, geometry=geometry, crs="EPSG:4326")
        
        # Process each date
        results = {}
        for target_date in self._date_range():
            snowline = self.processor.extract_snowline(gdf, target_date)
            results[target_date] = snowline
        
        return results
