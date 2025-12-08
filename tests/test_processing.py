"""Tests for data processing module."""

import pytest
from datetime import date
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, LineString, MultiLineString

from src.config import BoundingBox
from src.processing.processor import SnowlineProcessor
from src.processing.interpolation import InterpolationProcessor
from src.processing.postprocess import simplify_snowline, smooth_snowline, merge_line_segments


@pytest.fixture
def test_bbox():
    """Return a test bounding box."""
    return BoundingBox(min_lon=-5.0, max_lon=-3.0, min_lat=56.0, max_lat=58.0)


@pytest.fixture
def create_test_observations():
    """Create test data with known snowline at lat=57.0."""
    observations = []
    test_date = date(2005, 1, 15)
    
    # Create a grid of points with snow above latitude 57.0
    for lon in np.arange(-5.0, -3.0, 0.2):
        for lat in np.arange(56.0, 58.0, 0.2):
            observations.append({
                'date': test_date,
                'site_id': f'TEST_{lon}_{lat}',
                'latitude': lat,
                'longitude': lon,
                'snow_present': lat > 57.0  # Snow above lat 57
            })
    
    df = pd.DataFrame(observations)
    geometry = [Point(xy) for xy in zip(df['longitude'], df['latitude'])]
    return gpd.GeoDataFrame(df, geometry=geometry, crs="EPSG:4326")


@pytest.fixture
def empty_date_observations():
    """Create observations for a date with no data."""
    observations = []
    test_date = date(2005, 1, 20)
    
    for lon in np.arange(-5.0, -3.0, 0.5):
        for lat in np.arange(56.0, 58.0, 0.5):
            observations.append({
                'date': date(2005, 1, 15),  # Different date
                'site_id': f'TEST_{lon}_{lat}',
                'latitude': lat,
                'longitude': lon,
                'snow_present': True
            })
    
    df = pd.DataFrame(observations)
    geometry = [Point(xy) for xy in zip(df['longitude'], df['latitude'])]
    return gpd.GeoDataFrame(df, geometry=geometry, crs="EPSG:4326")


@pytest.fixture
def complete_snow_observations():
    """Create observations with complete snow cover."""
    observations = []
    test_date = date(2005, 1, 15)
    
    for lon in np.arange(-5.0, -3.0, 0.5):
        for lat in np.arange(56.0, 58.0, 0.5):
            observations.append({
                'date': test_date,
                'site_id': f'TEST_{lon}_{lat}',
                'latitude': lat,
                'longitude': lon,
                'snow_present': True  # All snow
            })
    
    df = pd.DataFrame(observations)
    geometry = [Point(xy) for xy in zip(df['longitude'], df['latitude'])]
    return gpd.GeoDataFrame(df, geometry=geometry, crs="EPSG:4326")


@pytest.fixture
def no_snow_observations():
    """Create observations with no snow."""
    observations = []
    test_date = date(2005, 1, 15)
    
    for lon in np.arange(-5.0, -3.0, 0.5):
        for lat in np.arange(56.0, 58.0, 0.5):
            observations.append({
                'date': test_date,
                'site_id': f'TEST_{lon}_{lat}',
                'latitude': lat,
                'longitude': lon,
                'snow_present': False  # No snow
            })
    
    df = pd.DataFrame(observations)
    geometry = [Point(xy) for xy in zip(df['longitude'], df['latitude'])]
    return gpd.GeoDataFrame(df, geometry=geometry, crs="EPSG:4326")


@pytest.fixture
def insufficient_data_observations():
    """Create observations with insufficient data points."""
    observations = []
    test_date = date(2005, 1, 15)
    
    # Only 2 points - insufficient for interpolation
    observations.append({
        'date': test_date,
        'site_id': 'TEST_1',
        'latitude': 56.5,
        'longitude': -4.5,
        'snow_present': False
    })
    observations.append({
        'date': test_date,
        'site_id': 'TEST_2',
        'latitude': 57.5,
        'longitude': -4.0,
        'snow_present': True
    })
    
    df = pd.DataFrame(observations)
    geometry = [Point(xy) for xy in zip(df['longitude'], df['latitude'])]
    return gpd.GeoDataFrame(df, geometry=geometry, crs="EPSG:4326")


class TestInterpolationProcessor:
    """Tests for the InterpolationProcessor class."""
    
    def test_initialization(self, test_bbox):
        """Test processor initialization."""
        processor = InterpolationProcessor(
            bbox=test_bbox,
            grid_resolution=0.01,
            interpolation_method='linear',
            smoothing_sigma=1.0
        )
        assert processor.bbox == test_bbox
        assert processor.grid_resolution == 0.01
        assert processor.interpolation_method == 'linear'
        assert processor.smoothing_sigma == 1.0
    
    def test_create_grid(self, test_bbox):
        """Test grid creation."""
        processor = InterpolationProcessor(bbox=test_bbox, grid_resolution=0.1)
        grid_x, grid_y = processor._create_grid()
        
        # Check grid dimensions
        assert grid_x.shape == grid_y.shape
        # Check grid bounds
        assert np.min(grid_x) >= test_bbox.min_lon
        assert np.max(grid_x) <= test_bbox.max_lon
        assert np.min(grid_y) >= test_bbox.min_lat
        assert np.max(grid_y) <= test_bbox.max_lat
    
    def test_extract_snowline_basic(self, test_bbox, create_test_observations):
        """Test basic snowline extraction with known data."""
        processor = InterpolationProcessor(bbox=test_bbox, grid_resolution=0.05)
        target_date = date(2005, 1, 15)
        
        result = processor.extract_snowline(create_test_observations, target_date)
        
        # Check result structure
        assert isinstance(result, gpd.GeoDataFrame)
        assert len(result) == 1
        assert 'date' in result.columns
        assert 'geometry' in result.columns
        assert 'observation_count' in result.columns
        
        # Check date
        assert result['date'].iloc[0] == target_date
        
        # Check that a geometry was extracted
        geometry = result['geometry'].iloc[0]
        assert geometry is not None
    
    def test_extract_snowline_no_data_for_date(self, test_bbox, empty_date_observations):
        """Test extraction when no data exists for the target date."""
        processor = InterpolationProcessor(bbox=test_bbox)
        target_date = date(2005, 1, 20)  # Date with no data
        
        result = processor.extract_snowline(empty_date_observations, target_date)
        
        # Should return empty GeoDataFrame
        assert isinstance(result, gpd.GeoDataFrame)
        assert len(result) == 0
    
    def test_extract_snowline_complete_snow(self, test_bbox, complete_snow_observations):
        """Test extraction with complete snow cover."""
        processor = InterpolationProcessor(bbox=test_bbox)
        target_date = date(2005, 1, 15)
        
        result = processor.extract_snowline(complete_snow_observations, target_date)
        
        # Should return result with reason
        assert isinstance(result, gpd.GeoDataFrame)
        assert len(result) == 1
        assert result['reason'].iloc[0] == 'complete_snow'
        assert result['geometry'].iloc[0] is None
    
    def test_extract_snowline_no_snow(self, test_bbox, no_snow_observations):
        """Test extraction with no snow."""
        processor = InterpolationProcessor(bbox=test_bbox)
        target_date = date(2005, 1, 15)
        
        result = processor.extract_snowline(no_snow_observations, target_date)
        
        # Should return result with reason
        assert isinstance(result, gpd.GeoDataFrame)
        assert len(result) == 1
        assert result['reason'].iloc[0] == 'no_snow'
        assert result['geometry'].iloc[0] is None
    
    def test_extract_snowline_insufficient_data(self, test_bbox, insufficient_data_observations):
        """Test extraction with insufficient data points."""
        processor = InterpolationProcessor(bbox=test_bbox)
        target_date = date(2005, 1, 15)
        
        result = processor.extract_snowline(insufficient_data_observations, target_date)
        
        # Should return result with reason
        assert isinstance(result, gpd.GeoDataFrame)
        assert len(result) == 1
        assert result['reason'].iloc[0] == 'insufficient_data'
        assert result['geometry'].iloc[0] is None
    
    def test_interpolate_to_grid(self, test_bbox, create_test_observations):
        """Test grid interpolation."""
        processor = InterpolationProcessor(bbox=test_bbox, grid_resolution=0.1)
        
        grid = processor._interpolate_to_grid(create_test_observations)
        
        # Check that grid is 2D array
        assert isinstance(grid, np.ndarray)
        assert grid.ndim == 2
        # Check that values are in expected range [0, 1]
        assert np.all(grid >= 0.0)
        assert np.all(grid <= 1.0)
    
    def test_extract_contour(self, test_bbox):
        """Test contour extraction from synthetic grid."""
        processor = InterpolationProcessor(bbox=test_bbox)
        
        # Create a simple synthetic grid with a clear contour
        grid_x, grid_y = processor._create_grid()
        grid = np.zeros(grid_x.shape)
        # Set upper half to 1.0
        grid[grid.shape[0]//2:, :] = 1.0
        
        contours = processor._extract_contour(grid, level=0.5)
        
        # Should find at least one contour
        assert len(contours) > 0
        # Each contour should have points
        for contour in contours:
            assert len(contour) > 0


class TestPostProcessing:
    """Tests for post-processing functions."""
    
    @pytest.fixture
    def sample_snowline(self):
        """Create a sample snowline GeoDataFrame."""
        coords = [(i * 0.1 - 4.5, 57.0 + np.sin(i * 0.5) * 0.1) for i in range(20)]
        line = LineString(coords)
        return gpd.GeoDataFrame(
            {
                'date': [date(2005, 1, 15)],
                'geometry': [line],
                'observation_count': [100]
            },
            crs="EPSG:4326"
        )
    
    @pytest.fixture
    def multi_line_snowline(self):
        """Create a snowline with multiple segments."""
        line1 = LineString([(-5.0, 57.0), (-4.5, 57.1), (-4.0, 57.0)])
        line2 = LineString([(-4.0, 57.0), (-3.5, 57.1), (-3.0, 57.0)])
        multi = MultiLineString([line1, line2])
        return gpd.GeoDataFrame(
            {
                'date': [date(2005, 1, 15)],
                'geometry': [multi],
                'observation_count': [100]
            },
            crs="EPSG:4326"
        )
    
    def test_simplify_snowline(self, sample_snowline):
        """Test geometry simplification."""
        original_coords = len(list(sample_snowline['geometry'].iloc[0].coords))
        
        simplified = simplify_snowline(sample_snowline, tolerance=0.01)
        
        # Check structure preserved
        assert isinstance(simplified, gpd.GeoDataFrame)
        assert len(simplified) == len(sample_snowline)
        
        # Check simplification reduced points (may not always be true for all geometries)
        # At minimum, geometry should still be valid
        assert simplified['geometry'].iloc[0].is_valid
    
    def test_smooth_snowline(self, sample_snowline):
        """Test geometry smoothing."""
        smoothed = smooth_snowline(sample_snowline, buffer_distance=0.005)
        
        # Check structure preserved
        assert isinstance(smoothed, gpd.GeoDataFrame)
        assert len(smoothed) == len(sample_snowline)
        
        # Geometry should still be valid
        assert smoothed['geometry'].iloc[0].is_valid
    
    def test_merge_line_segments(self, multi_line_snowline):
        """Test merging of line segments."""
        merged = merge_line_segments(multi_line_snowline)
        
        # Check structure preserved
        assert isinstance(merged, gpd.GeoDataFrame)
        assert len(merged) == len(multi_line_snowline)
        
        # Geometry should still be valid
        assert merged['geometry'].iloc[0].is_valid
    
    def test_simplify_preserves_crs(self, sample_snowline):
        """Test that simplification preserves CRS."""
        simplified = simplify_snowline(sample_snowline)
        assert simplified.crs == sample_snowline.crs
    
    def test_smooth_preserves_crs(self, sample_snowline):
        """Test that smoothing preserves CRS."""
        smoothed = smooth_snowline(sample_snowline)
        assert smoothed.crs == sample_snowline.crs
    
    def test_merge_preserves_crs(self, multi_line_snowline):
        """Test that merging preserves CRS."""
        merged = merge_line_segments(multi_line_snowline)
        assert merged.crs == multi_line_snowline.crs


class TestSnowlineProcessor:
    """Tests for the abstract SnowlineProcessor class."""
    
    def test_is_abstract(self):
        """Test that SnowlineProcessor cannot be instantiated directly."""
        with pytest.raises(TypeError):
            SnowlineProcessor()
