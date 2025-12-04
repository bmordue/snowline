# Feature Implementation Plan: Configuration Loading

## Overview

Implement the configuration loading system that parses and validates the `config.yaml` file, providing a structured configuration object to the rest of the application.

## Current State

- `main.py` contains basic YAML loading with `yaml.safe_load()`
- No validation of configuration values
- No structured data model for configuration

## Requirements

- Parse YAML configuration file
- Validate all required fields are present
- Validate field types and values (e.g., dates are valid, bounding box coordinates are sensible)
- Provide sensible defaults for optional fields
- Return a structured configuration object

## Implementation Steps

### Step 1: Create Configuration Data Classes

Create `src/config.py` with dataclasses to represent the configuration structure:

```python
from dataclasses import dataclass, field
from datetime import date
from typing import Optional
from pathlib import Path

@dataclass
class BoundingBox:
    min_lon: float
    max_lon: float
    min_lat: float
    max_lat: float

@dataclass
class InputConfig:
    snow_cover_data: Path
    basemap_data: Optional[Path] = None

@dataclass
class RegionConfig:
    bounding_box: BoundingBox

@dataclass
class TimeConfig:
    start_date: date
    end_date: date

@dataclass
class StyleConfig:
    snowline_color: str = "#0000FF"
    snowline_width: float = 1.5
    gridline_color: str = "#CCCCCC"
    gridline_style: str = "--"

@dataclass
class OutputConfig:
    directory: Path
    filename_prefix: str
    style: StyleConfig = field(default_factory=StyleConfig)

@dataclass
class Config:
    input: InputConfig
    region: RegionConfig
    time: TimeConfig
    output: OutputConfig
```

### Step 2: Create Configuration Loader

Add a `load_config()` function that:

1. Reads the YAML file
2. Parses dates from strings to `date` objects
3. Converts paths to `Path` objects
4. Instantiates the dataclass hierarchy
5. Returns a `Config` object

```python
def load_config(config_path: Path) -> Config:
    with open(config_path, 'r') as f:
        raw = yaml.safe_load(f)
    
    # Parse and construct Config object
    ...
```

### Step 3: Implement Validation

Add validation logic to check:

- **Required fields**: Raise `ConfigurationError` if missing
- **Bounding box validity**:
  - `min_lon < max_lon`
  - `min_lat < max_lat`
  - Longitude in range [-180, 180]
  - Latitude in range [-90, 90]
- **Date validity**:
  - `start_date <= end_date`
  - Dates are parseable in YYYY-MM-DD format
- **Path existence**: Warn if input paths don't exist (don't fail, as they may be created later)
- **Colour validity**: Check hex codes or named colours are valid

```python
class ConfigurationError(Exception):
    """Raised when configuration validation fails."""
    pass

def validate_bounding_box(bbox: BoundingBox) -> None:
    if bbox.min_lon >= bbox.max_lon:
        raise ConfigurationError("min_lon must be less than max_lon")
    # ... additional checks
```

### Step 4: Update main.py

Refactor `main.py` to use the new configuration loader:

```python
from src.config import load_config, ConfigurationError

def main():
    # ... argument parsing ...
    try:
        config = load_config(Path(args.config))
    except ConfigurationError as e:
        print(f"Configuration error: {e}")
        sys.exit(1)
```

## File Structure

```
src/
  __init__.py
  config.py         # Configuration dataclasses and loader
  exceptions.py     # Custom exceptions (ConfigurationError)
```

## Testing Strategy

Create `tests/test_config.py`:

1. **Valid configuration**: Load a complete valid config, verify all fields
2. **Missing required fields**: Verify `ConfigurationError` raised for each required field
3. **Invalid bounding box**: Test various invalid coordinate combinations
4. **Invalid dates**: Test unparseable dates and start > end
5. **Default values**: Verify defaults applied for optional fields
6. **Path handling**: Verify relative paths resolved correctly

## Dependencies

- `pyyaml` (already specified in PRD)
- Python standard library: `dataclasses`, `datetime`, `pathlib`

## Acceptance Criteria

- [ ] Configuration file is parsed into a structured `Config` object
- [ ] All required fields are validated
- [ ] Helpful error messages for invalid configuration
- [ ] Default values applied for optional fields
- [ ] Unit tests pass with >90% coverage for config module
