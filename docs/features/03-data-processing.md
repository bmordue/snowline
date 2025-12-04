# Feature Implementation Plan: Data Processing (Snowline Extraction)

## Overview

Implement the data processing pipeline that extracts vector snowlines from raw snow observation data. This is the core algorithmic component of the tool.

## Current State

- No processing implementation exists
- Data processing workflow documented in `docs/data_processing.md`
- Input will be a GeoDataFrame of point observations

## Requirements

- Process point-based snow observations into a snowline boundary
- Handle sparse observation data (140 sites across Scotland)
- Produce vector output (LineString/MultiLineString geometry)
- Support processing for individual dates
- Handle edge cases (no snow, complete snow cover)

## Algorithm Design

### Challenge: Point Data to Line Boundary

The SSGB data consists of point observations, not raster imagery. This requires a different approach than the NDSI method described in the data processing docs.

### Proposed Approach: Interpolation + Contouring

1. **Spatial Interpolation**: Interpolate point observations to a regular grid
2. **Binary Classification**: Apply threshold to create snow/no-snow grid
3. **Contour Extraction**: Extract the 0.5 contour as the snowline

### Alternative: Convex Hull / Alpha Shape

For sparse data, use computational geometry:
1. Separate points into snow-present and snow-absent sets
2. Compute boundary using alpha shapes
3. Extract the interface between the two regions

## Implementation Steps

### Step 1: Create Processing Interface

Create `src/processing/processor.py`:

```python
from abc import ABC, abstractmethod
import geopandas as gpd
from shapely.geometry import LineString, MultiLineString
from datetime import date

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
        
        Returns GeoDataFrame with snowline geometry and metadata.
        """
        pass
```

### Step 2: Implement Interpolation-Based Processor

Create `src/processing/interpolation.py`:

```python
import numpy as np
from scipy.interpolate import griddata
from scipy.ndimage import gaussian_filter
from skimage import measure
import geopandas as gpd
from shapely.geometry import LineString, MultiLineString
from src.config import BoundingBox

class InterpolationProcessor(SnowlineProcessor):
    """Extract snowline using spatial interpolation and contouring."""
    
    def __init__(
        self, 
        bbox: BoundingBox,
        grid_resolution: float = 0.01,  # degrees
        interpolation_method: str = 'linear',
        smoothing_sigma: float = 1.0
    ):
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
    ) -> MultiLineString:
        """Convert contour arrays to Shapely geometry."""
        grid_x, grid_y = self._create_grid()
        
        lines = []
        for contour in contours:
            # Convert grid indices to coordinates
            coords = [
                (
                    grid_x[0, int(c[1])],
                    grid_y[int(c[0]), 0]
                )
                for c in contour
            ]
            if len(coords) >= 2:
                lines.append(LineString(coords))
        
        return MultiLineString(lines) if lines else None
    
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
                {'date': [], 'geometry': []},
                crs="EPSG:4326"
            )
        
        # Check for edge cases
        if date_obs['snow_present'].all():
            # Complete snow cover - no snowline
            return self._create_empty_result(target_date, "complete_snow")
        
        if not date_obs['snow_present'].any():
            # No snow - no snowline
            return self._create_empty_result(target_date, "no_snow")
        
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
```

### Step 3: Implement Post-Processing

Create `src/processing/postprocess.py`:

```python
from shapely.geometry import LineString, MultiLineString
from shapely.ops import linemerge
import geopandas as gpd

def simplify_snowline(
    gdf: gpd.GeoDataFrame, 
    tolerance: float = 0.001
) -> gpd.GeoDataFrame:
    """Simplify snowline geometry to reduce complexity."""
    gdf = gdf.copy()
    gdf['geometry'] = gdf['geometry'].simplify(tolerance)
    return gdf

def smooth_snowline(
    gdf: gpd.GeoDataFrame,
    buffer_distance: float = 0.005
) -> gpd.GeoDataFrame:
    """Smooth snowline using buffer-based smoothing."""
    gdf = gdf.copy()
    # Buffer out and back in to smooth
    gdf['geometry'] = (
        gdf['geometry']
        .buffer(buffer_distance)
        .buffer(-buffer_distance)
        .boundary
    )
    return gdf

def merge_line_segments(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Merge connected line segments into continuous lines."""
    gdf = gdf.copy()
    gdf['geometry'] = gdf['geometry'].apply(
        lambda g: linemerge(g) if isinstance(g, MultiLineString) else g
    )
    return gdf
```

### Step 4: Create Processing Pipeline

Create `src/processing/pipeline.py`:

```python
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
        """Run the full pipeline, returning snowlines by date."""
        # Load and filter data
        data = self.loader.load()
        data = self.loader.filter_by_date_range(
            self.config.time.start_date,
            self.config.time.end_date
        )
        data = self.loader.filter_by_bounding_box(
            self.config.region.bounding_box
        )
        
        # Convert to GeoDataFrame
        gdf = self.loader.to_geodataframe()
        
        # Process each date
        results = {}
        for target_date in self._date_range():
            snowline = self.processor.extract_snowline(gdf, target_date)
            results[target_date] = snowline
        
        return results
```

## File Structure

```
src/
  processing/
    __init__.py
    processor.py      # Abstract interface
    interpolation.py  # Interpolation-based implementation
    postprocess.py    # Line simplification and smoothing
    pipeline.py       # Pipeline orchestration
```

## Testing Strategy

Create `tests/test_processing.py`:

1. **Simple case**: Known point distribution, verify snowline location
2. **No data for date**: Verify empty result returned
3. **Complete snow cover**: Verify edge case handled
4. **No snow**: Verify edge case handled
5. **Contour extraction**: Test with synthetic grid data
6. **Post-processing**: Test simplification and smoothing

### Test Fixtures

Create synthetic observation data for testing:

```python
def create_test_observations():
    """Create test data with known snowline at lat=57.0"""
    observations = []
    for lon in np.arange(-5.0, -3.0, 0.2):
        for lat in np.arange(56.0, 58.0, 0.2):
            observations.append({
                'date': date(2005, 1, 15),
                'site_id': f'TEST_{lon}_{lat}',
                'latitude': lat,
                'longitude': lon,
                'snow_present': lat > 57.0  # Snow above lat 57
            })
    return gpd.GeoDataFrame(observations)
```

## Dependencies

- `scipy`: Spatial interpolation (`griddata`), Gaussian filter
- `scikit-image`: Contour extraction (`measure.find_contours`)
- `shapely`: Geometry operations
- `geopandas`: Spatial data handling
- `numpy`: Numerical operations

## Configuration Extensions

Consider adding processing-specific configuration:

```yaml
processing:
  grid_resolution: 0.01  # degrees
  interpolation_method: linear  # or 'cubic', 'nearest'
  smoothing_sigma: 1.0
  simplification_tolerance: 0.001
```

## Edge Cases and Error Handling

1. **Insufficient data points**: Need minimum 3 points for interpolation
2. **All points same value**: No snowline exists
3. **Disconnected regions**: May produce multiple line segments
4. **Data gaps**: Large areas without observations may produce artefacts

## Acceptance Criteria

- [ ] Snowline extracted from point observations
- [ ] Edge cases (no snow, full snow) handled gracefully
- [ ] Output is valid GeoDataFrame with LineString/MultiLineString geometry
- [ ] Post-processing produces clean, simplified lines
- [ ] Pipeline processes full date range from configuration
- [ ] Unit tests pass with >85% coverage for processing module
