"""Abstract base class for map rendering."""

from abc import ABC, abstractmethod
from pathlib import Path
from datetime import date
import geopandas as gpd

from src.config import Config


class MapRenderer(ABC):
    """Abstract base class for map rendering."""
    
    @abstractmethod
    def render(
        self,
        snowline: gpd.GeoDataFrame,
        target_date: date,
        output_path: Path
    ) -> Path:
        """Render a map and save to file. Returns output path."""
        pass
