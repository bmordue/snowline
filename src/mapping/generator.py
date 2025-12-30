"""Map generator orchestrator for creating maps from snowline data."""

from pathlib import Path
from datetime import date
import geopandas as gpd
from typing import Dict, List

from src.config import Config
from src.mapping.renderer import MapRenderer


class MapGenerator:
    """Generates maps for all dates in the pipeline results."""
    
    def __init__(self, config: Config, renderer: MapRenderer):
        """Initialize the map generator.

        Parameters
        ----------
        config : Config
            Application configuration, including output directory and filename
            settings used when generating map files.
        renderer : MapRenderer
            Renderer responsible for drawing snowline maps and writing them to
            the output path.
        """
        self.config = config
        self.renderer = renderer
    
    def _generate_filename(self, target_date: date) -> str:
        """Generate output filename for a date."""
        return (
            f"{self.config.output.filename_prefix}"
            f"{target_date.strftime('%Y-%m-%d')}.svg"
        )
    
    def generate_all(
        self, 
        snowlines: Dict[date, gpd.GeoDataFrame]
    ) -> List[Path]:
        """Generate maps for all dates. Returns list of output paths."""
        output_dir = Path(self.config.output.directory)
        output_paths = []
        
        for target_date, snowline in snowlines.items():
            filename = self._generate_filename(target_date)
            output_path = output_dir / filename
            
            self.renderer.render(snowline, target_date, output_path)
            output_paths.append(output_path)
        
        return output_paths
    
    def generate_single(
        self,
        snowline: gpd.GeoDataFrame,
        target_date: date
    ) -> Path:
        """Generate a single map. Returns output path."""
        output_dir = Path(self.config.output.directory)
        filename = self._generate_filename(target_date)
        output_path = output_dir / filename
        
        return self.renderer.render(snowline, target_date, output_path)
