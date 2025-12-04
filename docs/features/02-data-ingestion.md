# Feature Implementation Plan: Data Ingestion

## Overview

Implement the data ingestion layer that loads snow cover data from the Snow Survey of Great Britain (SSGB) dataset and prepares it for processing.

## Current State

- No data loading implementation exists
- Sample configuration references `./data/ssgb_scotland_1945-2007.csv`
- The actual SSGB data format needs to be determined from the source

## Requirements

- Load snow cover data from CSV format (primary)
- Support filtering by date range (from configuration)
- Support filtering by geographic region (from bounding box)
- Provide data in a format suitable for snowline extraction
- Handle missing or malformed data gracefully

## Data Source Analysis

### SSGB Dataset Structure (Expected)

Based on the data sources documentation, the SSGB dataset contains:
- Daily snow observations from 140 sites across Scotland
- Date range: 1945-2007
- Available from Environmental Information Data Centre (EIDC)

Expected columns (to be confirmed from actual data):
- `date`: Observation date
- `site_id`: Unique identifier for observation site
- `latitude`: Site latitude
- `longitude`: Site longitude
- `snow_depth`: Snow depth in cm (or binary presence/absence)
- `elevation`: Site elevation in metres

## Implementation Steps

### Step 1: Create Data Models

Create `src/data/models.py`:

```python
from dataclasses import dataclass
from datetime import date
from typing import Optional

@dataclass
class SnowObservation:
    date: date
    site_id: str
    latitude: float
    longitude: float
    snow_present: bool
    snow_depth: Optional[float] = None
    elevation: Optional[float] = None
```

### Step 2: Implement Data Loader

Create `src/data/loader.py`:

```python
import pandas as pd
import geopandas as gpd
from pathlib import Path
from datetime import date
from typing import List

from src.config import Config, BoundingBox

class SSGBDataLoader:
    """Loader for Snow Survey of Great Britain data."""
    
    def __init__(self, data_path: Path):
        self.data_path = data_path
        self._raw_data: Optional[pd.DataFrame] = None
    
    def load(self) -> pd.DataFrame:
        """Load the raw CSV data, caching it in memory."""
        if self._raw_data is None:
            self._raw_data = pd.read_csv(
                self.data_path,
                parse_dates=['date'],
                dtype={'site_id': str}
            )
        return self._raw_data
    
    def filter_by_date_range(
        self, 
        start_date: date, 
        end_date: date
    ) -> pd.DataFrame:
        """Filter data to specified date range (inclusive)."""
        ...
    
    def filter_by_bounding_box(
        self, 
        bbox: BoundingBox
    ) -> pd.DataFrame:
        """Filter data to specified geographic region."""
        ...
    
    def to_geodataframe(self) -> gpd.GeoDataFrame:
        """Convert to GeoDataFrame for spatial operations."""
        ...
```

### Step 3: Create Data Loader Factory

To support future data sources (e.g., satellite data), create an abstract interface:

```python
from abc import ABC, abstractmethod

class DataLoader(ABC):
    @abstractmethod
    def load(self) -> pd.DataFrame:
        pass
    
    @abstractmethod
    def filter_by_date_range(self, start: date, end: date) -> pd.DataFrame:
        pass
    
    @abstractmethod
    def filter_by_bounding_box(self, bbox: BoundingBox) -> pd.DataFrame:
        pass

def get_data_loader(config: Config) -> DataLoader:
    """Factory function to return appropriate loader based on config."""
    # For now, only SSGB CSV is supported
    return SSGBDataLoader(config.input.snow_cover_data)
```

### Step 4: Implement Data Validation

Add validation for loaded data:

```python
class DataValidationError(Exception):
    pass

def validate_snow_data(df: pd.DataFrame) -> None:
    """Validate that loaded data has required columns and valid values."""
    required_columns = ['date', 'site_id', 'latitude', 'longitude']
    
    missing = set(required_columns) - set(df.columns)
    if missing:
        raise DataValidationError(f"Missing required columns: {missing}")
    
    # Check for valid coordinate ranges
    if (df['latitude'].abs() > 90).any():
        raise DataValidationError("Invalid latitude values detected")
    
    if (df['longitude'].abs() > 180).any():
        raise DataValidationError("Invalid longitude values detected")
```

### Step 5: Implement Caching (Optional Enhancement)

For performance with large datasets:

```python
import pickle
from hashlib import md5

class CachedDataLoader:
    """Wrapper that caches loaded and filtered data."""
    
    def __init__(self, loader: DataLoader, cache_dir: Path):
        self.loader = loader
        self.cache_dir = cache_dir
    
    def _cache_key(self, params: dict) -> str:
        return md5(str(params).encode()).hexdigest()
    
    def load_cached(self, **filter_params) -> pd.DataFrame:
        cache_path = self.cache_dir / f"{self._cache_key(filter_params)}.pkl"
        if cache_path.exists():
            return pd.read_pickle(cache_path)
        # Load, filter, cache, return
        ...
```

## File Structure

```
src/
  data/
    __init__.py
    models.py       # Data classes for observations
    loader.py       # DataLoader implementations
    validation.py   # Data validation functions
```

## Testing Strategy

Create `tests/test_data_loader.py`:

1. **Load valid CSV**: Create fixture CSV, verify loading works
2. **Missing columns**: Verify appropriate error for malformed CSV
3. **Date filtering**: Test inclusive date range filtering
4. **Bounding box filtering**: Test geographic filtering
5. **Empty results**: Handle case where filters return no data
6. **GeoDataFrame conversion**: Verify geometry column created correctly

### Test Fixtures

Create `tests/fixtures/sample_ssgb.csv` with representative test data:

```csv
date,site_id,latitude,longitude,snow_present,snow_depth,elevation
2005-01-15,SITE001,57.1,-4.2,true,15.0,450
2005-01-15,SITE002,56.8,-3.9,false,,320
2005-01-16,SITE001,57.1,-4.2,true,12.0,450
```

## Dependencies

- `pandas`: Data loading and manipulation
- `geopandas`: Spatial data handling
- Python standard library: `pathlib`, `datetime`

## Future Considerations

- Support for satellite data formats (GeoTIFF via Rasterio)
- Support for Shapefile input
- Streaming large datasets
- Data interpolation for missing observations

## Acceptance Criteria

- [ ] CSV data loads successfully into DataFrame
- [ ] Date range filtering works correctly (inclusive bounds)
- [ ] Bounding box filtering works correctly
- [ ] Data validation catches common errors with helpful messages
- [ ] Conversion to GeoDataFrame produces valid geometry
- [ ] Unit tests pass with >90% coverage for data module
