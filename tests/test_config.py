"""Tests for configuration loading and validation."""

import pytest
from datetime import date
from pathlib import Path
import tempfile
import os

from src.config import (
    load_config,
    Config,
    BoundingBox,
    InputConfig,
    RegionConfig,
    TimeConfig,
    StyleConfig,
    OutputConfig,
    _validate_bounding_box,
    _validate_dates,
    _validate_color,
    _validate_style,
)
from src.exceptions import ConfigurationError


@pytest.fixture
def valid_config_yaml():
    """Return a valid configuration YAML string."""
    return """
input:
  snow_cover_data: ./data/snow.csv
  basemap_data: ./data/basemap.shp

region:
  bounding_box:
    min_lon: -7.5
    max_lon: -1.0
    min_lat: 54.5
    max_lat: 59.0

time:
  start_date: "2005-01-15"
  end_date: "2005-01-20"

output:
  directory: ./output/maps
  filename_prefix: scotland_snowline_
  style:
    snowline_color: "#0000FF"
    snowline_width: 1.5
    gridline_color: "#CCCCCC"
    gridline_style: '--'
"""


@pytest.fixture
def minimal_config_yaml():
    """Return a minimal valid configuration YAML with only required fields."""
    return """
input:
  snow_cover_data: ./data/snow.csv

region:
  bounding_box:
    min_lon: -7.5
    max_lon: -1.0
    min_lat: 54.5
    max_lat: 59.0

time:
  start_date: "2005-01-15"
  end_date: "2005-01-20"

output:
  directory: ./output/maps
  filename_prefix: test_
"""


@pytest.fixture
def temp_config_file(valid_config_yaml):
    """Create a temporary config file and return its path."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(valid_config_yaml)
        temp_path = f.name
    yield Path(temp_path)
    os.unlink(temp_path)


class TestLoadConfig:
    """Tests for the load_config function."""

    def test_load_valid_config(self, temp_config_file):
        """Test loading a complete valid configuration."""
        config = load_config(temp_config_file)
        
        assert isinstance(config, Config)
        assert isinstance(config.input, InputConfig)
        assert isinstance(config.region, RegionConfig)
        assert isinstance(config.time, TimeConfig)
        assert isinstance(config.output, OutputConfig)

    def test_load_config_fields(self, temp_config_file):
        """Test that all fields are correctly parsed."""
        config = load_config(temp_config_file)
        
        # Input fields
        assert config.input.snow_cover_data == Path("./data/snow.csv")
        assert config.input.basemap_data == Path("./data/basemap.shp")
        
        # Bounding box
        assert config.region.bounding_box.min_lon == -7.5
        assert config.region.bounding_box.max_lon == -1.0
        assert config.region.bounding_box.min_lat == 54.5
        assert config.region.bounding_box.max_lat == 59.0
        
        # Time period
        assert config.time.start_date == date(2005, 1, 15)
        assert config.time.end_date == date(2005, 1, 20)
        
        # Output
        assert config.output.directory == Path("./output/maps")
        assert config.output.filename_prefix == "scotland_snowline_"
        
        # Style
        assert config.output.style.snowline_color == "#0000FF"
        assert config.output.style.snowline_width == 1.5
        assert config.output.style.gridline_color == "#CCCCCC"
        assert config.output.style.gridline_style == "--"

    def test_load_minimal_config_with_defaults(self, minimal_config_yaml):
        """Test that defaults are applied for optional fields."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(minimal_config_yaml)
            temp_path = Path(f.name)
        
        try:
            config = load_config(temp_path)
            
            # basemap_data should be None
            assert config.input.basemap_data is None
            
            # Style should use defaults
            assert config.output.style.snowline_color == "#0000FF"
            assert config.output.style.snowline_width == 1.5
            assert config.output.style.gridline_color == "#CCCCCC"
            assert config.output.style.gridline_style == "--"
        finally:
            os.unlink(temp_path)

    def test_load_config_file_not_found(self):
        """Test that FileNotFoundError is raised for missing file."""
        with pytest.raises(FileNotFoundError):
            load_config(Path("/nonexistent/config.yaml"))

    def test_load_empty_config(self):
        """Test that ConfigurationError is raised for empty file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("")
            temp_path = Path(f.name)
        
        try:
            with pytest.raises(ConfigurationError, match="Configuration file is empty"):
                load_config(temp_path)
        finally:
            os.unlink(temp_path)


class TestMissingRequiredFields:
    """Tests for missing required configuration fields."""

    def test_missing_input_section(self):
        """Test error when input section is missing."""
        yaml_content = """
region:
  bounding_box:
    min_lon: -7.5
    max_lon: -1.0
    min_lat: 54.5
    max_lat: 59.0
time:
  start_date: "2005-01-15"
  end_date: "2005-01-20"
output:
  directory: ./output
  filename_prefix: test_
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_path = Path(f.name)
        
        try:
            with pytest.raises(ConfigurationError, match="Missing required configuration field: input"):
                load_config(temp_path)
        finally:
            os.unlink(temp_path)

    def test_missing_snow_cover_data(self):
        """Test error when snow_cover_data is missing."""
        yaml_content = """
input:
  basemap_data: ./data/basemap.shp
region:
  bounding_box:
    min_lon: -7.5
    max_lon: -1.0
    min_lat: 54.5
    max_lat: 59.0
time:
  start_date: "2005-01-15"
  end_date: "2005-01-20"
output:
  directory: ./output
  filename_prefix: test_
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_path = Path(f.name)
        
        try:
            with pytest.raises(ConfigurationError, match="Missing required configuration field: input.snow_cover_data"):
                load_config(temp_path)
        finally:
            os.unlink(temp_path)

    def test_missing_bounding_box(self):
        """Test error when bounding_box is missing."""
        yaml_content = """
input:
  snow_cover_data: ./data/snow.csv
region: {}
time:
  start_date: "2005-01-15"
  end_date: "2005-01-20"
output:
  directory: ./output
  filename_prefix: test_
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_path = Path(f.name)
        
        try:
            with pytest.raises(ConfigurationError, match="Missing required configuration field: region.bounding_box"):
                load_config(temp_path)
        finally:
            os.unlink(temp_path)

    def test_missing_start_date(self):
        """Test error when start_date is missing."""
        yaml_content = """
input:
  snow_cover_data: ./data/snow.csv
region:
  bounding_box:
    min_lon: -7.5
    max_lon: -1.0
    min_lat: 54.5
    max_lat: 59.0
time:
  end_date: "2005-01-20"
output:
  directory: ./output
  filename_prefix: test_
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_path = Path(f.name)
        
        try:
            with pytest.raises(ConfigurationError, match="Missing required configuration field: time.start_date"):
                load_config(temp_path)
        finally:
            os.unlink(temp_path)


class TestBoundingBoxValidation:
    """Tests for bounding box validation."""

    def test_valid_bounding_box(self):
        """Test that a valid bounding box passes validation."""
        bbox = BoundingBox(min_lon=-7.5, max_lon=-1.0, min_lat=54.5, max_lat=59.0)
        _validate_bounding_box(bbox)  # Should not raise

    def test_min_lon_greater_than_max_lon(self):
        """Test error when min_lon >= max_lon."""
        bbox = BoundingBox(min_lon=0.0, max_lon=-1.0, min_lat=54.5, max_lat=59.0)
        with pytest.raises(ConfigurationError, match="min_lon.*must be less than max_lon"):
            _validate_bounding_box(bbox)

    def test_min_lat_greater_than_max_lat(self):
        """Test error when min_lat >= max_lat."""
        bbox = BoundingBox(min_lon=-7.5, max_lon=-1.0, min_lat=60.0, max_lat=59.0)
        with pytest.raises(ConfigurationError, match="min_lat.*must be less than max_lat"):
            _validate_bounding_box(bbox)

    def test_min_longitude_out_of_range(self):
        """Test error when min_lon is out of valid range."""
        bbox = BoundingBox(min_lon=-200.0, max_lon=-1.0, min_lat=54.5, max_lat=59.0)
        with pytest.raises(ConfigurationError, match="min_lon.*must be in range"):
            _validate_bounding_box(bbox)

    def test_max_longitude_out_of_range(self):
        """Test error when max_lon is out of valid range."""
        bbox = BoundingBox(min_lon=-7.5, max_lon=200.0, min_lat=54.5, max_lat=59.0)
        with pytest.raises(ConfigurationError, match="max_lon.*must be in range"):
            _validate_bounding_box(bbox)

    def test_min_latitude_out_of_range(self):
        """Test error when min_lat is out of valid range."""
        bbox = BoundingBox(min_lon=-7.5, max_lon=-1.0, min_lat=-100.0, max_lat=59.0)
        with pytest.raises(ConfigurationError, match="min_lat.*must be in range"):
            _validate_bounding_box(bbox)

    def test_max_latitude_out_of_range(self):
        """Test error when max_lat is out of valid range."""
        bbox = BoundingBox(min_lon=-7.5, max_lon=-1.0, min_lat=54.5, max_lat=100.0)
        with pytest.raises(ConfigurationError, match="max_lat.*must be in range"):
            _validate_bounding_box(bbox)


class TestDateValidation:
    """Tests for date validation."""

    def test_valid_dates(self):
        """Test that valid dates pass validation."""
        time_config = TimeConfig(start_date=date(2005, 1, 15), end_date=date(2005, 1, 20))
        _validate_dates(time_config)  # Should not raise

    def test_same_start_and_end_date(self):
        """Test that same start and end date is valid."""
        time_config = TimeConfig(start_date=date(2005, 1, 15), end_date=date(2005, 1, 15))
        _validate_dates(time_config)  # Should not raise

    def test_start_date_after_end_date(self):
        """Test error when start_date > end_date."""
        time_config = TimeConfig(start_date=date(2005, 1, 20), end_date=date(2005, 1, 15))
        with pytest.raises(ConfigurationError, match="start_date.*must be on or before"):
            _validate_dates(time_config)

    def test_invalid_date_format(self):
        """Test error for invalid date format in YAML."""
        yaml_content = """
input:
  snow_cover_data: ./data/snow.csv
region:
  bounding_box:
    min_lon: -7.5
    max_lon: -1.0
    min_lat: 54.5
    max_lat: 59.0
time:
  start_date: "15-01-2005"
  end_date: "2005-01-20"
output:
  directory: ./output
  filename_prefix: test_
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_path = Path(f.name)
        
        try:
            with pytest.raises(ConfigurationError, match="Invalid date format"):
                load_config(temp_path)
        finally:
            os.unlink(temp_path)


class TestColorValidation:
    """Tests for color validation."""

    def test_valid_hex_color_6_digits(self):
        """Test that 6-digit hex colors are valid."""
        _validate_color("#0000FF", "test_field")  # Should not raise
        _validate_color("#aabbcc", "test_field")  # Should not raise

    def test_valid_hex_color_3_digits(self):
        """Test that 3-digit hex colors are valid."""
        _validate_color("#00F", "test_field")  # Should not raise
        _validate_color("#abc", "test_field")  # Should not raise

    def test_valid_named_color(self):
        """Test that named colors are valid."""
        _validate_color("blue", "test_field")  # Should not raise
        _validate_color("RED", "test_field")  # Should not raise (case insensitive)

    def test_invalid_hex_color(self):
        """Test error for invalid hex color."""
        with pytest.raises(ConfigurationError, match="Invalid hex color code"):
            _validate_color("#00GGFF", "test_field")

    def test_invalid_named_color(self):
        """Test error for invalid named color."""
        with pytest.raises(ConfigurationError, match="Invalid color"):
            _validate_color("notacolor", "test_field")


class TestStyleValidation:
    """Tests for style validation."""

    def test_valid_style(self):
        """Test that a valid style passes validation."""
        style = StyleConfig(
            snowline_color="#0000FF",
            snowline_width=2.0,
            gridline_color="gray",
            gridline_style="--"
        )
        _validate_style(style)  # Should not raise

    def test_negative_snowline_width(self):
        """Test error for negative snowline width."""
        style = StyleConfig(snowline_width=-1.0)
        with pytest.raises(ConfigurationError, match="snowline_width.*must be positive"):
            _validate_style(style)

    def test_zero_snowline_width(self):
        """Test error for zero snowline width."""
        style = StyleConfig(snowline_width=0.0)
        with pytest.raises(ConfigurationError, match="snowline_width.*must be positive"):
            _validate_style(style)

    def test_invalid_snowline_color(self):
        """Test error for invalid snowline color."""
        style = StyleConfig(snowline_color="invalid")
        with pytest.raises(ConfigurationError, match="Invalid color for snowline_color"):
            _validate_style(style)


class TestPathHandling:
    """Tests for path handling."""

    def test_relative_paths_preserved(self, temp_config_file):
        """Test that relative paths are preserved as Path objects."""
        config = load_config(temp_config_file)
        
        assert isinstance(config.input.snow_cover_data, Path)
        assert isinstance(config.output.directory, Path)
        assert str(config.input.snow_cover_data) == "data/snow.csv"

    def test_absolute_paths_preserved(self):
        """Test that absolute paths are preserved."""
        yaml_content = """
input:
  snow_cover_data: /absolute/path/to/snow.csv
region:
  bounding_box:
    min_lon: -7.5
    max_lon: -1.0
    min_lat: 54.5
    max_lat: 59.0
time:
  start_date: "2005-01-15"
  end_date: "2005-01-20"
output:
  directory: /absolute/output
  filename_prefix: test_
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_path = Path(f.name)
        
        try:
            config = load_config(temp_path)
            assert str(config.input.snow_cover_data) == "/absolute/path/to/snow.csv"
        finally:
            os.unlink(temp_path)
