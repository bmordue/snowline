"""Tests for mapping module."""

import pytest
from datetime import date
from pathlib import Path
import tempfile

import geopandas as gpd
from shapely.geometry import LineString, Point

from src.config import (
    Config, BoundingBox, InputConfig, RegionConfig, 
    TimeConfig, OutputConfig, StyleConfig
)
from src.mapping.renderer import MapRenderer
from src.mapping.cartopy_renderer import CartopyRenderer
from src.mapping.generator import MapGenerator


@pytest.fixture
def test_config(tmp_path):
    """Create a test configuration."""
    bbox = BoundingBox(min_lon=-6.0, max_lon=-3.0, min_lat=55.0, max_lat=59.0)
    
    config = Config(
        input=InputConfig(snow_cover_data=tmp_path / "test_data.csv"),
        region=RegionConfig(bounding_box=bbox),
        time=TimeConfig(
            start_date=date(2005, 1, 15),
            end_date=date(2005, 1, 16)
        ),
        output=OutputConfig(
            directory=tmp_path / "output",
            filename_prefix="test_snowline_",
            style=StyleConfig(
                snowline_color="#FF0000",
                snowline_width=2.0,
                gridline_color="#CCCCCC",
                gridline_style="--"
            )
        )
    )
    
    return config


@pytest.fixture
def sample_snowline():
    """Create a sample snowline GeoDataFrame."""
    geometry = LineString([(-5.0, 56.0), (-4.5, 56.5), (-4.0, 57.0)])
    
    gdf = gpd.GeoDataFrame(
        {
            'date': [date(2005, 1, 15)],
            'geometry': [geometry],
            'observation_count': [10]
        },
        crs="EPSG:4326"
    )
    
    return gdf


@pytest.fixture
def empty_snowline():
    """Create an empty snowline GeoDataFrame."""
    gdf = gpd.GeoDataFrame(
        {
            'date': [date(2005, 1, 15)],
            'geometry': [None],
            'observation_count': [0]
        },
        crs="EPSG:4326"
    )
    
    return gdf


class TestMapRenderer:
    """Tests for MapRenderer abstract base class."""
    
    def test_renderer_is_abstract(self):
        """Test that MapRenderer cannot be instantiated directly."""
        with pytest.raises(TypeError):
            MapRenderer()


class TestCartopyRenderer:
    """Tests for CartopyRenderer."""
    
    def test_renderer_initialization(self, test_config):
        """Test renderer initialization with config."""
        renderer = CartopyRenderer(test_config)
        
        assert renderer.config == test_config
        assert renderer.bbox == test_config.region.bounding_box
        assert renderer.style == test_config.output.style
    
    def test_render_creates_svg(self, test_config, sample_snowline, tmp_path):
        """Test that render creates an SVG file."""
        renderer = CartopyRenderer(test_config)
        output_path = tmp_path / "test_map.svg"
        
        result = renderer.render(
            snowline=sample_snowline,
            target_date=date(2005, 1, 15),
            output_path=output_path
        )
        
        assert result == output_path
        assert output_path.exists()
        assert output_path.suffix == ".svg"
    
    def test_render_with_empty_snowline(self, test_config, empty_snowline, tmp_path):
        """Test rendering with empty snowline."""
        renderer = CartopyRenderer(test_config)
        output_path = tmp_path / "test_map_empty.svg"
        
        result = renderer.render(
            snowline=empty_snowline,
            target_date=date(2005, 1, 15),
            output_path=output_path
        )
        
        assert result == output_path
        assert output_path.exists()
    
    def test_render_creates_output_directory(self, test_config, sample_snowline, tmp_path):
        """Test that render creates output directory if it doesn't exist."""
        renderer = CartopyRenderer(test_config)
        output_path = tmp_path / "nonexistent" / "subdir" / "test_map.svg"
        
        assert not output_path.parent.exists()
        
        renderer.render(
            snowline=sample_snowline,
            target_date=date(2005, 1, 15),
            output_path=output_path
        )
        
        assert output_path.exists()
        assert output_path.parent.exists()


class TestMapGenerator:
    """Tests for MapGenerator."""
    
    def test_generator_initialization(self, test_config):
        """Test generator initialization."""
        renderer = CartopyRenderer(test_config)
        generator = MapGenerator(test_config, renderer)
        
        assert generator.config == test_config
        assert generator.renderer == renderer
    
    def test_generate_filename(self, test_config):
        """Test filename generation."""
        renderer = CartopyRenderer(test_config)
        generator = MapGenerator(test_config, renderer)
        
        filename = generator._generate_filename(date(2005, 1, 15))
        
        assert filename == "test_snowline_2005-01-15.svg"
    
    def test_generate_single(self, test_config, sample_snowline, tmp_path):
        """Test generating a single map."""
        renderer = CartopyRenderer(test_config)
        generator = MapGenerator(test_config, renderer)
        
        output_path = generator.generate_single(
            snowline=sample_snowline,
            target_date=date(2005, 1, 15)
        )
        
        assert output_path.exists()
        assert output_path.name == "test_snowline_2005-01-15.svg"
    
    def test_generate_all(self, test_config, tmp_path):
        """Test generating maps for multiple dates."""
        renderer = CartopyRenderer(test_config)
        generator = MapGenerator(test_config, renderer)
        
        # Create snowlines for two dates
        snowlines = {
            date(2005, 1, 15): gpd.GeoDataFrame(
                {
                    'date': [date(2005, 1, 15)],
                    'geometry': [LineString([(-5.0, 56.0), (-4.0, 57.0)])],
                    'observation_count': [10]
                },
                crs="EPSG:4326"
            ),
            date(2005, 1, 16): gpd.GeoDataFrame(
                {
                    'date': [date(2005, 1, 16)],
                    'geometry': [LineString([(-5.0, 56.5), (-4.0, 57.5)])],
                    'observation_count': [12]
                },
                crs="EPSG:4326"
            )
        }
        
        output_paths = generator.generate_all(snowlines)
        
        assert len(output_paths) == 2
        assert all(path.exists() for path in output_paths)
        assert all(path.suffix == ".svg" for path in output_paths)
        
        # Check filenames
        filenames = [path.name for path in output_paths]
        assert "test_snowline_2005-01-15.svg" in filenames
        assert "test_snowline_2005-01-16.svg" in filenames
