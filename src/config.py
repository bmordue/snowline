"""Configuration loading and validation for the Snowline visualization tool."""

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, Dict, Optional
import re
import warnings

import yaml

from .exceptions import ConfigurationError


@dataclass
class BoundingBox:
    """Geographic bounding box with longitude and latitude coordinates."""
    min_lon: float
    max_lon: float
    min_lat: float
    max_lat: float


@dataclass
class InputConfig:
    """Configuration for input data sources."""
    snow_cover_data: Path
    basemap_data: Optional[Path] = None


@dataclass
class RegionConfig:
    """Configuration for the geographic region."""
    bounding_box: BoundingBox


@dataclass
class TimeConfig:
    """Configuration for the time period."""
    start_date: date
    end_date: date


@dataclass
class StyleConfig:
    """Configuration for visualization styling."""
    snowline_color: str = "#0000FF"
    snowline_width: float = 1.5
    gridline_color: str = "#CCCCCC"
    gridline_style: str = "--"


@dataclass
class OutputConfig:
    """Configuration for output files."""
    directory: Path
    filename_prefix: str
    style: StyleConfig = field(default_factory=StyleConfig)


@dataclass
class Config:
    """Main configuration object containing all settings."""
    input: InputConfig
    region: RegionConfig
    time: TimeConfig
    output: OutputConfig


# Valid CSS color names (subset of common colors)
VALID_COLOR_NAMES = {
    "black", "white", "red", "green", "blue", "yellow", "cyan", "magenta",
    "gray", "grey", "orange", "purple", "pink", "brown", "navy", "teal",
    "olive", "maroon", "aqua", "fuchsia", "lime", "silver"
}


def _validate_color(color: str, field_name: str) -> None:
    """Validate that a color is either a valid hex code or named color."""
    # Check for valid hex color code
    if color.startswith("#"):
        hex_pattern = re.compile(r'^#([0-9A-Fa-f]{3}|[0-9A-Fa-f]{6})$')
        if not hex_pattern.match(color):
            raise ConfigurationError(
                f"Invalid hex color code for {field_name}: '{color}'. "
                "Expected format: #RGB or #RRGGBB"
            )
    elif color.lower() not in VALID_COLOR_NAMES:
        raise ConfigurationError(
            f"Invalid color for {field_name}: '{color}'. "
            f"Expected a hex code (#RRGGBB) or named color."
        )


def _validate_bounding_box(bbox: BoundingBox) -> None:
    """Validate bounding box coordinates."""
    if bbox.min_lon >= bbox.max_lon:
        raise ConfigurationError(
            f"min_lon ({bbox.min_lon}) must be less than max_lon ({bbox.max_lon})"
        )
    if bbox.min_lat >= bbox.max_lat:
        raise ConfigurationError(
            f"min_lat ({bbox.min_lat}) must be less than max_lat ({bbox.max_lat})"
        )
    if not (-180 <= bbox.min_lon <= 180):
        raise ConfigurationError(
            f"min_lon ({bbox.min_lon}) must be in range [-180, 180]"
        )
    if not (-180 <= bbox.max_lon <= 180):
        raise ConfigurationError(
            f"max_lon ({bbox.max_lon}) must be in range [-180, 180]"
        )
    if not (-90 <= bbox.min_lat <= 90):
        raise ConfigurationError(
            f"min_lat ({bbox.min_lat}) must be in range [-90, 90]"
        )
    if not (-90 <= bbox.max_lat <= 90):
        raise ConfigurationError(
            f"max_lat ({bbox.max_lat}) must be in range [-90, 90]"
        )


def _validate_dates(time_config: TimeConfig) -> None:
    """Validate date configuration."""
    if time_config.start_date > time_config.end_date:
        raise ConfigurationError(
            f"start_date ({time_config.start_date}) must be on or before "
            f"end_date ({time_config.end_date})"
        )


def _validate_style(style: StyleConfig) -> None:
    """Validate style configuration."""
    _validate_color(style.snowline_color, "snowline_color")
    _validate_color(style.gridline_color, "gridline_color")
    
    if style.snowline_width <= 0:
        raise ConfigurationError(
            f"snowline_width ({style.snowline_width}) must be positive"
        )


def _warn_missing_paths(config: Config) -> None:
    """Warn if input paths don't exist."""
    if not config.input.snow_cover_data.exists():
        warnings.warn(
            f"Snow cover data path does not exist: {config.input.snow_cover_data}"
        )
    if config.input.basemap_data and not config.input.basemap_data.exists():
        warnings.warn(
            f"Basemap data path does not exist: {config.input.basemap_data}"
        )


def _get_required(data: Dict[str, Any], key: str, parent: str = "") -> Any:
    """Get a required field from a dictionary, raising ConfigurationError if missing."""
    if key not in data:
        path = f"{parent}.{key}" if parent else key
        raise ConfigurationError(f"Missing required configuration field: {path}")
    return data[key]


def _parse_date(date_str: str, field_name: str) -> date:
    """Parse a date string in YYYY-MM-DD format."""
    try:
        return date.fromisoformat(date_str)
    except (ValueError, TypeError) as e:
        raise ConfigurationError(
            f"Invalid date format for {field_name}: '{date_str}'. "
            f"Expected YYYY-MM-DD format."
        ) from e


def _parse_bounding_box(data: Dict[str, Any]) -> BoundingBox:
    """Parse bounding box from raw configuration data."""
    return BoundingBox(
        min_lon=float(_get_required(data, "min_lon", "region.bounding_box")),
        max_lon=float(_get_required(data, "max_lon", "region.bounding_box")),
        min_lat=float(_get_required(data, "min_lat", "region.bounding_box")),
        max_lat=float(_get_required(data, "max_lat", "region.bounding_box")),
    )


def _parse_input_config(data: Dict[str, Any]) -> InputConfig:
    """Parse input configuration from raw data."""
    snow_cover_data = Path(_get_required(data, "snow_cover_data", "input"))
    basemap_data = data.get("basemap_data")
    return InputConfig(
        snow_cover_data=snow_cover_data,
        basemap_data=Path(basemap_data) if basemap_data else None,
    )


def _parse_region_config(data: Dict[str, Any]) -> RegionConfig:
    """Parse region configuration from raw data."""
    bbox_data = _get_required(data, "bounding_box", "region")
    return RegionConfig(bounding_box=_parse_bounding_box(bbox_data))


def _parse_time_config(data: Dict[str, Any]) -> TimeConfig:
    """Parse time configuration from raw data."""
    start_date_str = _get_required(data, "start_date", "time")
    end_date_str = _get_required(data, "end_date", "time")
    return TimeConfig(
        start_date=_parse_date(start_date_str, "time.start_date"),
        end_date=_parse_date(end_date_str, "time.end_date"),
    )


def _parse_style_config(data: Optional[Dict[str, Any]]) -> StyleConfig:
    """Parse style configuration from raw data, using defaults for missing fields."""
    if data is None:
        return StyleConfig()
    return StyleConfig(
        snowline_color=data.get("snowline_color", "#0000FF"),
        snowline_width=float(data.get("snowline_width", 1.5)),
        gridline_color=data.get("gridline_color", "#CCCCCC"),
        gridline_style=data.get("gridline_style", "--"),
    )


def _parse_output_config(data: Dict[str, Any]) -> OutputConfig:
    """Parse output configuration from raw data."""
    return OutputConfig(
        directory=Path(_get_required(data, "directory", "output")),
        filename_prefix=_get_required(data, "filename_prefix", "output"),
        style=_parse_style_config(data.get("style")),
    )


def load_config(config_path: Path) -> Config:
    """Load and validate configuration from a YAML file.
    
    Args:
        config_path: Path to the YAML configuration file.
        
    Returns:
        A validated Config object.
        
    Raises:
        ConfigurationError: If the configuration is invalid or missing required fields.
        FileNotFoundError: If the configuration file does not exist.
        yaml.YAMLError: If the YAML file is malformed.
    """
    with open(config_path, 'r') as f:
        raw = yaml.safe_load(f)
    
    if raw is None:
        raise ConfigurationError("Configuration file is empty")
    
    # Parse required top-level sections
    input_data = _get_required(raw, "input")
    region_data = _get_required(raw, "region")
    time_data = _get_required(raw, "time")
    output_data = _get_required(raw, "output")
    
    # Parse each section
    input_config = _parse_input_config(input_data)
    region_config = _parse_region_config(region_data)
    time_config = _parse_time_config(time_data)
    output_config = _parse_output_config(output_data)
    
    # Validate
    _validate_bounding_box(region_config.bounding_box)
    _validate_dates(time_config)
    _validate_style(output_config.style)
    
    config = Config(
        input=input_config,
        region=region_config,
        time=time_config,
        output=output_config,
    )
    
    # Warn about missing paths (don't fail)
    _warn_missing_paths(config)
    
    return config
