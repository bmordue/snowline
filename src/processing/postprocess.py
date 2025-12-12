"""Post-processing utilities for snowline geometries."""

from shapely.geometry import LineString, MultiLineString
from shapely.ops import linemerge
import geopandas as gpd


def simplify_snowline(
    gdf: gpd.GeoDataFrame, 
    tolerance: float = 0.001
) -> gpd.GeoDataFrame:
    """
    Simplify snowline geometry to reduce complexity.
    
    Args:
        gdf: GeoDataFrame containing snowline geometries.
        tolerance: Tolerance for Douglas-Peucker simplification algorithm.
        
    Returns:
        GeoDataFrame with simplified geometries.
    """
    gdf = gdf.copy()
    gdf['geometry'] = gdf['geometry'].simplify(tolerance)
    return gdf


def smooth_snowline(
    gdf: gpd.GeoDataFrame,
    buffer_distance: float = 0.005
) -> gpd.GeoDataFrame:
    """
    Smooth snowline using buffer-based smoothing.
    
    Args:
        gdf: GeoDataFrame containing snowline geometries.
        buffer_distance: Distance for buffer operations.
        
    Returns:
        GeoDataFrame with smoothed geometries.
    """
    gdf = gdf.copy()
    # Buffer out and back in to smooth, then extract boundary
    gdf['geometry'] = (
        gdf['geometry']
        .buffer(buffer_distance)
        .buffer(-buffer_distance)
        .boundary
    )
    return gdf


def merge_line_segments(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Merge connected line segments into continuous lines.
    
    Args:
        gdf: GeoDataFrame containing snowline geometries.
        
    Returns:
        GeoDataFrame with merged line segments.
    """
    gdf = gdf.copy()
    gdf['geometry'] = gdf['geometry'].apply(
        lambda g: linemerge(g) if isinstance(g, MultiLineString) else g
    )
    return gdf
