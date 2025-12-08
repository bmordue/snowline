"""Tests for data loader and validation."""

import pytest
from datetime import date
from pathlib import Path
import tempfile
import os

import pandas as pd
import geopandas as gpd

from src.config import BoundingBox
from src.data.loader import SSGBDataLoader, get_data_loader, DataLoader
from src.data.validation import validate_snow_data
from src.data.models import SnowObservation
from src.exceptions import DataValidationError


# Path to the test fixture
FIXTURE_PATH = Path(__file__).parent / "fixtures" / "sample_ssgb.csv"


class TestSnowObservation:
    """Tests for the SnowObservation data model."""

    def test_create_observation_with_all_fields(self):
        """Test creating an observation with all fields."""
        obs = SnowObservation(
            date=date(2005, 1, 15),
            site_id="SITE001",
            latitude=57.1,
            longitude=-4.2,
            snow_present=True,
            snow_depth=15.0,
            elevation=450.0
        )
        assert obs.date == date(2005, 1, 15)
        assert obs.site_id == "SITE001"
        assert obs.latitude == 57.1
        assert obs.longitude == -4.2
        assert obs.snow_present is True
        assert obs.snow_depth == 15.0
        assert obs.elevation == 450.0

    def test_create_observation_with_optional_none(self):
        """Test creating an observation with optional fields as None."""
        obs = SnowObservation(
            date=date(2005, 1, 15),
            site_id="SITE001",
            latitude=57.1,
            longitude=-4.2,
            snow_present=False,
            snow_depth=None,
            elevation=None
        )
        assert obs.snow_depth is None
        assert obs.elevation is None


class TestDataValidation:
    """Tests for data validation functions."""

    def test_validate_valid_data(self):
        """Test that valid data passes validation."""
        df = pd.DataFrame({
            'date': [date(2005, 1, 15)],
            'site_id': ['SITE001'],
            'latitude': [57.1],
            'longitude': [-4.2],
            'snow_present': [True]
        })
        validate_snow_data(df)  # Should not raise

    def test_validate_missing_date_column(self):
        """Test that missing date column raises error."""
        df = pd.DataFrame({
            'site_id': ['SITE001'],
            'latitude': [57.1],
            'longitude': [-4.2]
        })
        with pytest.raises(DataValidationError, match="Missing required columns"):
            validate_snow_data(df)

    def test_validate_missing_multiple_columns(self):
        """Test that multiple missing columns are reported."""
        df = pd.DataFrame({
            'site_id': ['SITE001']
        })
        with pytest.raises(DataValidationError, match="Missing required columns"):
            validate_snow_data(df)

    def test_validate_invalid_latitude(self):
        """Test that invalid latitude raises error."""
        df = pd.DataFrame({
            'date': [date(2005, 1, 15)],
            'site_id': ['SITE001'],
            'latitude': [100.0],  # Invalid: outside [-90, 90]
            'longitude': [-4.2]
        })
        with pytest.raises(DataValidationError, match="Invalid latitude"):
            validate_snow_data(df)

    def test_validate_invalid_longitude(self):
        """Test that invalid longitude raises error."""
        df = pd.DataFrame({
            'date': [date(2005, 1, 15)],
            'site_id': ['SITE001'],
            'latitude': [57.1],
            'longitude': [200.0]  # Invalid: outside [-180, 180]
        })
        with pytest.raises(DataValidationError, match="Invalid longitude"):
            validate_snow_data(df)


class TestSSGBDataLoader:
    """Tests for the SSGBDataLoader class."""

    def test_load_valid_csv(self):
        """Test loading a valid CSV file."""
        loader = SSGBDataLoader(FIXTURE_PATH)
        df = loader.load()
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 8
        assert 'date' in df.columns
        assert 'site_id' in df.columns
        assert 'latitude' in df.columns
        assert 'longitude' in df.columns

    def test_load_caches_data(self):
        """Test that loading caches the data."""
        loader = SSGBDataLoader(FIXTURE_PATH)
        df1 = loader.load()
        df2 = loader.load()
        
        # Both should be equal, and _raw_data should be cached
        assert loader._raw_data is not None
        pd.testing.assert_frame_equal(df1, df2)

    def test_load_returns_copy(self):
        """Test that load returns a copy (not modifying cached data)."""
        loader = SSGBDataLoader(FIXTURE_PATH)
        df1 = loader.load()
        df1['modified'] = True  # Modify the returned dataframe
        df2 = loader.load()
        
        # Original should not be modified
        assert 'modified' not in df2.columns

    def test_load_file_not_found(self):
        """Test that FileNotFoundError is raised for missing file."""
        loader = SSGBDataLoader(Path("/nonexistent/path.csv"))
        with pytest.raises(FileNotFoundError):
            loader.load()

    def test_load_parses_dates(self):
        """Test that dates are parsed correctly."""
        loader = SSGBDataLoader(FIXTURE_PATH)
        df = loader.load()
        
        # Check that dates are date objects
        assert all(isinstance(d, date) for d in df['date'])
        assert df['date'].iloc[0] == date(2005, 1, 15)

    def test_filter_by_date_range_inclusive(self):
        """Test date filtering is inclusive on both bounds."""
        loader = SSGBDataLoader(FIXTURE_PATH)
        
        filtered = loader.filter_by_date_range(
            start_date=date(2005, 1, 15),
            end_date=date(2005, 1, 16)
        )
        
        # Should include Jan 15 and Jan 16 observations
        assert len(filtered) == 4
        assert all(d >= date(2005, 1, 15) for d in filtered['date'])
        assert all(d <= date(2005, 1, 16) for d in filtered['date'])

    def test_filter_by_date_range_single_day(self):
        """Test filtering to a single day."""
        loader = SSGBDataLoader(FIXTURE_PATH)
        
        filtered = loader.filter_by_date_range(
            start_date=date(2005, 1, 17),
            end_date=date(2005, 1, 17)
        )
        
        assert len(filtered) == 2
        assert all(d == date(2005, 1, 17) for d in filtered['date'])

    def test_filter_by_date_range_no_results(self):
        """Test filtering returns empty when no data matches."""
        loader = SSGBDataLoader(FIXTURE_PATH)
        
        filtered = loader.filter_by_date_range(
            start_date=date(2000, 1, 1),
            end_date=date(2000, 12, 31)
        )
        
        assert len(filtered) == 0

    def test_filter_by_bounding_box(self):
        """Test filtering by geographic bounding box."""
        loader = SSGBDataLoader(FIXTURE_PATH)
        
        # Bounding box that includes SITE001 and SITE002 but not SITE003
        bbox = BoundingBox(
            min_lon=-5.0,
            max_lon=-3.0,
            min_lat=56.0,
            max_lat=58.0
        )
        
        filtered = loader.filter_by_bounding_box(bbox)
        
        # Should only include SITE001 and SITE002
        assert all(site in ['SITE001', 'SITE002'] for site in filtered['site_id'])
        assert 'SITE003' not in filtered['site_id'].values

    def test_filter_by_bounding_box_includes_edges(self):
        """Test that bounding box filtering is inclusive on edges."""
        loader = SSGBDataLoader(FIXTURE_PATH)
        
        # Exact bounding box for SITE001
        bbox = BoundingBox(
            min_lon=-4.2,
            max_lon=-4.2,
            min_lat=57.1,
            max_lat=57.1
        )
        
        filtered = loader.filter_by_bounding_box(bbox)
        
        assert len(filtered) > 0
        assert all(site == 'SITE001' for site in filtered['site_id'])

    def test_filter_by_bounding_box_no_results(self):
        """Test filtering returns empty when no data in region."""
        loader = SSGBDataLoader(FIXTURE_PATH)
        
        # Bounding box with no data
        bbox = BoundingBox(
            min_lon=0.0,
            max_lon=10.0,
            min_lat=0.0,
            max_lat=10.0
        )
        
        filtered = loader.filter_by_bounding_box(bbox)
        
        assert len(filtered) == 0

    def test_to_geodataframe(self):
        """Test conversion to GeoDataFrame."""
        loader = SSGBDataLoader(FIXTURE_PATH)
        gdf = loader.to_geodataframe()
        
        assert isinstance(gdf, gpd.GeoDataFrame)
        assert 'geometry' in gdf.columns
        assert gdf.crs.to_string() == "EPSG:4326"

    def test_to_geodataframe_geometry_correct(self):
        """Test that geometry points are created correctly."""
        loader = SSGBDataLoader(FIXTURE_PATH)
        gdf = loader.to_geodataframe()
        
        # Get first row
        first_row = gdf.iloc[0]
        
        # Geometry should be a Point with correct coordinates
        assert first_row.geometry.x == first_row['longitude']
        assert first_row.geometry.y == first_row['latitude']


class TestDataLoaderWithMalformedData:
    """Tests for handling malformed data."""

    def test_missing_required_column(self):
        """Test error when CSV is missing required column."""
        csv_content = """site_id,latitude,longitude,snow_present
SITE001,57.1,-4.2,true
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            temp_path = Path(f.name)
        
        try:
            loader = SSGBDataLoader(temp_path)
            with pytest.raises(DataValidationError, match="Missing required columns"):
                loader.load()
        finally:
            os.unlink(temp_path)


class TestGetDataLoader:
    """Tests for the get_data_loader factory function."""

    def test_returns_ssgb_loader(self):
        """Test that factory returns SSGBDataLoader for CSV input."""
        # Create a minimal mock config
        from src.config import Config, InputConfig, RegionConfig, TimeConfig, OutputConfig, StyleConfig
        
        config = Config(
            input=InputConfig(snow_cover_data=FIXTURE_PATH),
            region=RegionConfig(bounding_box=BoundingBox(
                min_lon=-7.5, max_lon=-1.0, min_lat=54.5, max_lat=59.0
            )),
            time=TimeConfig(start_date=date(2005, 1, 15), end_date=date(2005, 1, 20)),
            output=OutputConfig(
                directory=Path("./output"),
                filename_prefix="test_",
                style=StyleConfig()
            )
        )
        
        loader = get_data_loader(config)
        
        assert isinstance(loader, SSGBDataLoader)
        assert isinstance(loader, DataLoader)
        assert loader.data_path == FIXTURE_PATH
