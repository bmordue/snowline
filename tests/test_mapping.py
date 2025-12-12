"""Tests for the mapping module."""

import pytest
import shutil
from dataclasses import replace
from datetime import date
from pathlib import Path

import geopandas as gpd
from shapely.geometry import LineString

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
        input=InputConfig(snow_cover_data=tmp_path / "snow.csv"),
        region=RegionConfig(bounding_box=bbox),
        time=TimeConfig(
            start_date=date(2005, 1, 15),
            end_date=date(2005, 1, 16)
        ),
        output=OutputConfig(
            directory=tmp_path / "output",
            filename_prefix="snowline_",
            style=StyleConfig(
                snowline_color="#0000FF",
                snowline_width=1.5,
                gridline_color="#CCCCCC",
                gridline_style="--"
            )
        )
    )
    
    return config


@pytest.fixture
def sample_snowline():
    """Create a sample snowline GeoDataFrame."""
    line = LineString([(-5.0, 56.0), (-4.5, 56.5), (-4.0, 57.0)])
    gdf = gpd.GeoDataFrame(
        {'geometry': [line]},
        crs="EPSG:4326"
    )
    return gdf


@pytest.fixture
def empty_snowline():
    """Create an empty snowline GeoDataFrame."""
    gdf = gpd.GeoDataFrame(
        {'geometry': []},
        crs="EPSG:4326"
    )
    return gdf


class TestMapRenderer:
    """Tests for the MapRenderer abstract base class."""
    
    def test_is_abstract(self):
        """Test that MapRenderer is abstract and cannot be instantiated."""
        with pytest.raises(TypeError):
            MapRenderer()


class TestCartopyRenderer:
    """Tests for the CartopyRenderer class."""
    
    def test_initialization(self, test_config):
        """Test renderer initialization."""
        renderer = CartopyRenderer(test_config)
        
        assert renderer.config == test_config
        assert renderer.bbox == test_config.region.bounding_box
        assert renderer.style == test_config.output.style
    
    def test_render_creates_svg_file(self, test_config, sample_snowline, tmp_path):
        """Test that rendering creates an SVG file."""
        renderer = CartopyRenderer(test_config)
        output_path = tmp_path / "test_map.svg"
        target_date = date(2005, 1, 15)
        
        result_path = renderer.render(sample_snowline, target_date, output_path)
        
        assert result_path == output_path
        assert output_path.exists()
        assert output_path.suffix == ".svg"
    
    def test_render_with_empty_snowline(self, test_config, empty_snowline, tmp_path):
        """Test rendering with an empty snowline."""
        renderer = CartopyRenderer(test_config)
        output_path = tmp_path / "empty_map.svg"
        target_date = date(2005, 1, 15)
        
        result_path = renderer.render(empty_snowline, target_date, output_path)
        
        assert result_path == output_path
        assert output_path.exists()
    
    def test_render_creates_output_directory(self, test_config, sample_snowline, tmp_path):
        """Test that rendering creates output directory if it doesn't exist."""
        renderer = CartopyRenderer(test_config)
        output_path = tmp_path / "subdir" / "nested" / "map.svg"
        target_date = date(2005, 1, 15)
        
        # Directory shouldn't exist yet
        assert not output_path.parent.exists()
        
        renderer.render(sample_snowline, target_date, output_path)
        
        # Directory should be created
        assert output_path.parent.exists()
        assert output_path.exists()
    
    def test_render_applies_custom_style(self, test_config, sample_snowline, tmp_path):
        """Test that custom style is applied."""
        # Create a modified config to avoid mutating the shared fixture
        from dataclasses import replace
        custom_style = replace(
            test_config.output.style,
            snowline_color="#FF0000",
            snowline_width=2.5
        )
        custom_output = replace(test_config.output, style=custom_style)
        custom_config = replace(test_config, output=custom_output)
        
        renderer = CartopyRenderer(custom_config)
        output_path = tmp_path / "styled_map.svg"
        target_date = date(2005, 1, 15)
        
        renderer.render(sample_snowline, target_date, output_path)
        
        # Check that file was created (full style verification would require SVG parsing)
        assert output_path.exists()
        
        # Basic check: ensure SVG contains some expected content
        content = output_path.read_text()
        assert "svg" in content.lower()
    
    def test_svg_content_structure(self, test_config, sample_snowline, tmp_path):
        """Test that generated SVG has expected structure."""
        renderer = CartopyRenderer(test_config)
        output_path = tmp_path / "structure_test.svg"
        target_date = date(2005, 1, 15)
        
        renderer.render(sample_snowline, target_date, output_path)
        
        content = output_path.read_text()
        
        # Check for SVG elements
        assert '<?xml' in content
        assert '<svg' in content
        assert '</svg>' in content
    
    def test_render_with_date_formatting(self, test_config, sample_snowline, tmp_path):
        """Test that date is properly formatted in title."""
        renderer = CartopyRenderer(test_config)
        output_path = tmp_path / "date_test.svg"
        target_date = date(2005, 3, 25)
        
        renderer.render(sample_snowline, target_date, output_path)
        
        content = output_path.read_text()
        # Date should be formatted as "25 March 2005"
        assert "25 March 2005" in content


class TestMapGenerator:
    """Tests for the MapGenerator class."""
    
    def test_initialization(self, test_config):
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
        
        assert filename == "snowline_2005-01-15.svg"
    
    def test_generate_filename_with_different_prefix(self, test_config):
        """Test filename generation with custom prefix."""
        # Create a modified config to avoid mutating the shared fixture
        custom_output = replace(test_config.output, filename_prefix="map_")
        custom_config = replace(test_config, output=custom_output)
        
        renderer = CartopyRenderer(custom_config)
        generator = MapGenerator(custom_config, renderer)
        
        filename = generator._generate_filename(date(2005, 12, 31))
        
        assert filename == "map_2005-12-31.svg"
    
    def test_generate_single(self, test_config, sample_snowline, tmp_path):
        """Test generating a single map."""
        renderer = CartopyRenderer(test_config)
        generator = MapGenerator(test_config, renderer)
        target_date = date(2005, 1, 15)
        
        output_path = generator.generate_single(sample_snowline, target_date)
        
        expected_path = tmp_path / "output" / "snowline_2005-01-15.svg"
        assert output_path == expected_path
        assert output_path.exists()
    
    def test_generate_all(self, test_config, sample_snowline, tmp_path):
        """Test generating maps for multiple dates."""
        renderer = CartopyRenderer(test_config)
        generator = MapGenerator(test_config, renderer)
        
        # Create snowlines for multiple dates
        snowlines = {
            date(2005, 1, 15): sample_snowline,
            date(2005, 1, 16): sample_snowline,
            date(2005, 1, 17): sample_snowline,
        }
        
        output_paths = generator.generate_all(snowlines)
        
        assert len(output_paths) == 3
        
        # Check all files exist
        for path in output_paths:
            assert path.exists()
            assert path.suffix == ".svg"
        
        # Check filenames
        filenames = [p.name for p in output_paths]
        assert "snowline_2005-01-15.svg" in filenames
        assert "snowline_2005-01-16.svg" in filenames
        assert "snowline_2005-01-17.svg" in filenames
    
    def test_generate_all_creates_output_directory(self, test_config, sample_snowline, tmp_path):
        """Test that generate_all creates output directory."""
        # Remove output directory if it exists
        output_dir = tmp_path / "output"
        if output_dir.exists():
            shutil.rmtree(output_dir)
        
        renderer = CartopyRenderer(test_config)
        generator = MapGenerator(test_config, renderer)
        
        snowlines = {date(2005, 1, 15): sample_snowline}
        
        output_paths = generator.generate_all(snowlines)
        
        assert output_dir.exists()
        assert len(output_paths) == 1
        assert output_paths[0].exists()
    
    def test_generate_all_with_empty_dict(self, test_config):
        """Test generating maps with empty snowlines dict."""
        renderer = CartopyRenderer(test_config)
        generator = MapGenerator(test_config, renderer)
        
        output_paths = generator.generate_all({})
        
        assert output_paths == []


class TestIntegration:
    """Integration tests for the mapping module."""
    
    def test_full_workflow(self, test_config, tmp_path):
        """Test the complete workflow from config to map generation."""
        # Create sample data
        line = LineString([(-5.0, 56.0), (-4.5, 56.5), (-4.0, 57.0)])
        snowline = gpd.GeoDataFrame({'geometry': [line]}, crs="EPSG:4326")
        
        # Create renderer and generator
        renderer = CartopyRenderer(test_config)
        generator = MapGenerator(test_config, renderer)
        
        # Generate maps
        snowlines = {
            date(2005, 1, 15): snowline,
            date(2005, 1, 16): snowline,
        }
        
        output_paths = generator.generate_all(snowlines)
        
        # Verify results
        assert len(output_paths) == 2
        for path in output_paths:
            assert path.exists()
            content = path.read_text()
            assert '<?xml' in content
            assert '<svg' in content
