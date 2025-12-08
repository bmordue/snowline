"""Abstract base class for snowline extraction algorithms."""

from abc import ABC, abstractmethod
from datetime import date

import geopandas as gpd


class SnowlineProcessor(ABC):
    """Abstract base class for snowline extraction algorithms."""
    
    @abstractmethod
    def extract_snowline(
        self, 
        observations: gpd.GeoDataFrame,
        target_date: date
    ) -> gpd.GeoDataFrame:
        """
        Extract snowline from observations for a specific date.
        
        Args:
            observations: GeoDataFrame containing snow observations with
                         'date', 'snow_present', and geometry columns.
            target_date: The date for which to extract the snowline.
        
        Returns:
            GeoDataFrame with snowline geometry (LineString/MultiLineString)
            and metadata. Returns empty GeoDataFrame if no snowline exists.
        """
        pass
