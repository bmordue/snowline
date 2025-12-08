"""Interpolation-based snowline extraction."""

from datetime import date
from typing import Optional

import numpy as np
from scipy.interpolate import griddata
from scipy.ndimage import gaussian_filter
from skimage import measure
import geopandas as gpd
from shapely.geometry import LineString, MultiLineString

from src.config import BoundingBox
from src.processing.processor import SnowlineProcessor


class InterpolationProcessor(SnowlineProcessor):
    """Extract snowline using spatial interpolation and contouring."""
    
    def __init__(
        self, 
        bbox: BoundingBox,
        grid_resolution: float = 0.01,  # degrees
        interpolation_method: str = 'linear',
        smoothing_sigma: float = 1.0
    ):
        """
        Initialize the interpolation processor.
        
        Args:
            bbox: Geographic bounding box for the interpolation grid.
            grid_resolution: Grid cell size in degrees.
            interpolation_method: Scipy interpolation method ('linear', 'cubic', 'nearest').
            smoothing_sigma: Gaussian smoothing sigma for noise reduction.
        """
        self.bbox = bbox
        self.grid_resolution = grid_resolution
        self.interpolation_method = interpolation_method
        self.smoothing_sigma = smoothing_sigma
    
    def _create_grid(self) -> tuple[np.ndarray, np.ndarray]:
        """Create regular grid for interpolation."""
        x = np.arange(
            self.bbox.min_lon, 
            self.bbox.max_lon, 
            self.grid_resolution
        )
        y = np.arange(
            self.bbox.min_lat, 
            self.bbox.max_lat, 
            self.grid_resolution
        )
        return np.meshgrid(x, y)
    
    def _interpolate_to_grid(
        self, 
        observations: gpd.GeoDataFrame
    ) -> np.ndarray:
        """Interpolate point observations to regular grid."""
        points = np.column_stack([
            observations.geometry.x,
            observations.geometry.y
        ])
        values = observations['snow_present'].astype(float).values
        
        grid_x, grid_y = self._create_grid()
        grid_z = griddata(
            points, 
            values, 
            (grid_x, grid_y),
            method=self.interpolation_method,
            fill_value=0.0
        )
        return grid_z
    
    def _extract_contour(
        self, 
        grid: np.ndarray, 
        level: float = 0.5
    ) -> list[np.ndarray]:
        """Extract contour lines at specified level."""
        # Apply smoothing to reduce noise
        smoothed = gaussian_filter(grid, sigma=self.smoothing_sigma)
        
        # Find contours using marching squares
        contours = measure.find_contours(smoothed, level)
        return contours
    
    def _contours_to_geometry(
        self, 
        contours: list[np.ndarray]
    ) -> Optional[MultiLineString]:
        """Convert contour arrays to Shapely geometry."""
        if not contours:
            return None
            
        grid_x, grid_y = self._create_grid()
        
        lines = []
        for contour in contours:
            # Convert grid indices to coordinates
            coords = []
            for c in contour:
                row_idx = np.round(c[0]).astype(int)
                col_idx = np.round(c[1]).astype(int)
                # Ensure indices are within bounds
                if 0 <= row_idx < grid_y.shape[0] and 0 <= col_idx < grid_x.shape[1]:
                    coords.append((
                        grid_x[0, col_idx],
                        grid_y[row_idx, 0]
                    ))
            if len(coords) >= 2:
                lines.append(LineString(coords))
        
        return MultiLineString(lines) if lines else None
    
    def _create_empty_result(
        self, 
        target_date: date, 
        reason: str
    ) -> gpd.GeoDataFrame:
        """Create an empty result GeoDataFrame."""
        return gpd.GeoDataFrame(
            {
                'date': [target_date],
                'geometry': [None],
                'observation_count': [0],
                'reason': [reason]
            },
            crs="EPSG:4326"
        )
    
    def extract_snowline(
        self, 
        observations: gpd.GeoDataFrame,
        target_date: date
    ) -> gpd.GeoDataFrame:
        """Extract snowline for a specific date."""
        # Filter to target date
        date_obs = observations[
            observations['date'] == target_date
        ]
        
        if len(date_obs) == 0:
            return gpd.GeoDataFrame(
                {'date': [], 'geometry': [], 'observation_count': []},
                crs="EPSG:4326"
            )
        
        # Check for edge cases
        if date_obs['snow_present'].all():
            # Complete snow cover - no snowline
            return self._create_empty_result(target_date, "complete_snow")
        
        if not date_obs['snow_present'].any():
            # No snow - no snowline
            return self._create_empty_result(target_date, "no_snow")
        
        # Need at least 3 points for interpolation
        if len(date_obs) < 3:
            return self._create_empty_result(target_date, "insufficient_data")
        
        # Perform interpolation and contouring
        grid = self._interpolate_to_grid(date_obs)
        contours = self._extract_contour(grid)
        geometry = self._contours_to_geometry(contours)
        
        return gpd.GeoDataFrame(
            {
                'date': [target_date],
                'geometry': [geometry],
                'observation_count': [len(date_obs)]
            },
            crs="EPSG:4326"
        )
