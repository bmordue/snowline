"""Tests for processing pipeline."""

import pytest
from datetime import date
from pathlib import Path
import tempfile
import os

import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

from src.config import Config, BoundingBox, InputConfig, RegionConfig, TimeConfig, OutputConfig
from src.data.loader import SSGBDataLoader
from src.processing.interpolation import InterpolationProcessor
from src.processing.pipeline import SnowlinePipeline


@pytest.fixture
def test_config_with_data(tmp_path):
    """Create a test configuration with temporary data file."""
    # Create test data file
    data_file = tmp_path / "test_snow.csv"
    test_data = []
    
    # Create synthetic data for two dates with 2D grid distribution
    for d in [date(2005, 1, 15), date(2005, 1, 16)]:
        site_num = 0
        for i in range(5):
            for j in range(5):
                lat = 56.0 + i * 0.5
                lon = -5.0 + j * 0.4
                test_data.append({
                    'date': d,
                    'site_id': f'SITE_{site_num}',
                    'latitude': lat,
                    'longitude': lon,
                    'snow_present': lat > 57.0
                })
                site_num += 1
    
    df = pd.DataFrame(test_data)
    df.to_csv(data_file, index=False)
    
    # Create config
    bbox = BoundingBox(min_lon=-6.0, max_lon=-3.0, min_lat=55.0, max_lat=59.0)
    
    config = Config(
        input=InputConfig(snow_cover_data=data_file),
        region=RegionConfig(bounding_box=bbox),
        time=TimeConfig(
            start_date=date(2005, 1, 15),
            end_date=date(2005, 1, 16)
        ),
        output=OutputConfig(
            directory=tmp_path / "output",
            filename_prefix="test_"
        )
    )
    
    return config


class TestSnowlinePipeline:
    """Tests for the SnowlinePipeline class."""
    
    def test_pipeline_initialization(self, test_config_with_data):
        """Test pipeline initialization."""
        loader = SSGBDataLoader(test_config_with_data.input.snow_cover_data)
        processor = InterpolationProcessor(
            bbox=test_config_with_data.region.bounding_box
        )
        
        pipeline = SnowlinePipeline(
            config=test_config_with_data,
            loader=loader,
            processor=processor
        )
        
        assert pipeline.config == test_config_with_data
        assert pipeline.loader == loader
        assert pipeline.processor == processor
    
    def test_date_range_generation(self, test_config_with_data):
        """Test date range generation."""
        loader = SSGBDataLoader(test_config_with_data.input.snow_cover_data)
        processor = InterpolationProcessor(
            bbox=test_config_with_data.region.bounding_box
        )
        
        pipeline = SnowlinePipeline(
            config=test_config_with_data,
            loader=loader,
            processor=processor
        )
        
        dates = list(pipeline._date_range())
        
        assert len(dates) == 2
        assert dates[0] == date(2005, 1, 15)
        assert dates[1] == date(2005, 1, 16)
    
    def test_pipeline_run(self, test_config_with_data):
        """Test full pipeline execution."""
        loader = SSGBDataLoader(test_config_with_data.input.snow_cover_data)
        processor = InterpolationProcessor(
            bbox=test_config_with_data.region.bounding_box,
            grid_resolution=0.1
        )
        
        pipeline = SnowlinePipeline(
            config=test_config_with_data,
            loader=loader,
            processor=processor
        )
        
        results = pipeline.run()
        
        # Check results structure
        assert isinstance(results, dict)
        assert len(results) == 2
        
        # Check that all dates are present
        assert date(2005, 1, 15) in results
        assert date(2005, 1, 16) in results
        
        # Check that each result is a GeoDataFrame
        for d, gdf in results.items():
            assert isinstance(gdf, gpd.GeoDataFrame)
            assert len(gdf) > 0
    
    def test_pipeline_with_empty_date_range(self, test_config_with_data):
        """Test pipeline with a date range that has no data."""
        # Modify config to use date range outside of data
        test_config_with_data.time.start_date = date(2005, 2, 1)
        test_config_with_data.time.end_date = date(2005, 2, 2)
        
        loader = SSGBDataLoader(test_config_with_data.input.snow_cover_data)
        processor = InterpolationProcessor(
            bbox=test_config_with_data.region.bounding_box
        )
        
        pipeline = SnowlinePipeline(
            config=test_config_with_data,
            loader=loader,
            processor=processor
        )
        
        results = pipeline.run()
        
        # Should still return results for the dates, but empty
        assert isinstance(results, dict)
        assert len(results) == 2
        
        # Each result should be empty GeoDataFrame
        for d, gdf in results.items():
            assert isinstance(gdf, gpd.GeoDataFrame)
