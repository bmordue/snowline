"""Cartopy-based map renderer for generating SVG maps."""

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
import geopandas as gpd
from pathlib import Path
from datetime import date

from src.config import Config
from src.mapping.renderer import MapRenderer


class CartopyRenderer(MapRenderer):
    """Render maps using Matplotlib and Cartopy."""
    
    # North arrow positioning constants (in axes fraction coordinates)
    NORTH_ARROW_X = 0.95
    NORTH_ARROW_Y = 0.95
    NORTH_ARROW_LENGTH = 0.08
    
    def __init__(self, config: Config):
        """Initialize the Cartopy renderer.
        
        Parameters
        ----------
        config : Config
            Application configuration containing region bounding box,
            output styling, and basemap settings.
        """
        self.config = config
        self.bbox = config.region.bounding_box
        self.style = config.output.style
        self.projection = ccrs.PlateCarree()
    
    def _create_figure(self) -> tuple:
        """Create figure with map projection."""
        fig = plt.figure(figsize=(12, 10), dpi=150)
        ax = fig.add_subplot(1, 1, 1, projection=self.projection)
        
        # Set map extent
        ax.set_extent([
            self.bbox.min_lon,
            self.bbox.max_lon,
            self.bbox.min_lat,
            self.bbox.max_lat
        ], crs=self.projection)
        
        return fig, ax
    
    def _add_base_map(self, ax) -> None:
        """Add base map features.
        
        Uses Natural Earth features at 110m resolution (lowest detail) to minimize
        data requirements. These may require downloading on first use if not cached.
        """
        # Set background color (ocean) as fallback
        ax.set_facecolor('#e6f3ff')
        
        try:
            # Use 110m (lowest resolution) features to minimize data requirements
            # Add land and ocean
            ax.add_feature(
                cfeature.LAND.with_scale('110m'), 
                facecolor='#f0f0f0',
                edgecolor='none'
            )
            ax.add_feature(
                cfeature.OCEAN.with_scale('110m'), 
                facecolor='#e6f3ff'
            )
            
            # Add coastlines and borders
            ax.add_feature(
                cfeature.COASTLINE.with_scale('110m'), 
                linewidth=0.5,
                edgecolor='#666666'
            )
            ax.add_feature(
                cfeature.BORDERS.with_scale('110m'), 
                linewidth=0.3,
                linestyle=':'
            )
            
            # Add rivers and lakes
            ax.add_feature(
                cfeature.RIVERS.with_scale('110m'), 
                linewidth=0.3,
                edgecolor='#99ccff'
            )
            ax.add_feature(
                cfeature.LAKES.with_scale('110m'), 
                facecolor='#e6f3ff',
                edgecolor='#99ccff'
            )
        except Exception:
            # If Natural Earth data cannot be loaded (offline, network error, etc.),
            # the ocean background color provides a minimal base map
            pass
    
    def _add_custom_basemap(self, ax) -> None:
        """Add custom basemap from shapefile if configured."""
        if self.config.input.basemap_data:
            basemap = gpd.read_file(self.config.input.basemap_data)
            basemap.plot(
                ax=ax,
                facecolor='none',
                edgecolor='#333333',
                linewidth=0.5,
                transform=self.projection
            )
    
    def _add_snowline(
        self, 
        ax, 
        snowline: gpd.GeoDataFrame
    ) -> None:
        """Add snowline to the map."""
        if snowline.empty:
            return
        
        # Check if all geometries are None
        if snowline.geometry.isna().all():
            return
        
        snowline.plot(
            ax=ax,
            color=self.style.snowline_color,
            linewidth=self.style.snowline_width,
            transform=self.projection,
            zorder=10  # Ensure snowline is on top
        )
    
    def _add_graticules(self, ax) -> None:
        """Add latitude/longitude grid lines."""
        gl = ax.gridlines(
            draw_labels=True,
            linewidth=0.5,
            color=self.style.gridline_color,
            linestyle=self.style.gridline_style,
            alpha=0.7
        )
        
        # Configure label positions
        gl.top_labels = False
        gl.right_labels = False
        gl.xformatter = LONGITUDE_FORMATTER
        gl.yformatter = LATITUDE_FORMATTER
        gl.xlabel_style = {'size': 8}
        gl.ylabel_style = {'size': 8}
    
    def _add_north_arrow(self, ax) -> None:
        """Add north arrow to the map."""
        # Create arrow using class constants for positioning
        ax.annotate(
            'N',
            xy=(self.NORTH_ARROW_X, self.NORTH_ARROW_Y - self.NORTH_ARROW_LENGTH),
            xytext=(self.NORTH_ARROW_X, self.NORTH_ARROW_Y),
            xycoords='axes fraction',
            textcoords='axes fraction',
            fontsize=12,
            fontweight='bold',
            ha='center',
            va='bottom',
            arrowprops=dict(
                arrowstyle='->',
                lw=2,
                color='black'
            )
        )
    
    def _add_title(self, ax, target_date: date) -> None:
        """Add title with date."""
        ax.set_title(
            f"Snowline - {target_date.strftime('%d %B %Y')}",
            fontsize=14,
            fontweight='bold',
            pad=10
        )
    
    def _add_legend(self, ax) -> None:
        """Add legend explaining map elements."""
        legend_elements = [
            Line2D(
                [0], [0],
                color=self.style.snowline_color,
                linewidth=self.style.snowline_width,
                label='Snowline'
            )
        ]
        
        ax.legend(
            handles=legend_elements,
            loc='lower left',
            framealpha=0.9
        )
    
    def render(
        self,
        snowline: gpd.GeoDataFrame,
        target_date: date,
        output_path: Path
    ) -> Path:
        """Render the map and save as SVG."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            # Try rendering with full Natural Earth features
            fig, ax = self._create_figure()
            
            # Add map elements
            self._add_base_map(ax)
            self._add_custom_basemap(ax)
            self._add_snowline(ax, snowline)
            self._add_graticules(ax)
            self._add_north_arrow(ax)
            self._add_title(ax, target_date)
            self._add_legend(ax)
            
            # Save to file
            fig.savefig(
                output_path,
                format='svg',
                bbox_inches='tight',
                pad_inches=0.1
            )
            plt.close(fig)
        except Exception as e:
            # If rendering fails (typically due to offline Natural Earth data),
            # fall back to rendering without basemap features
            if 'fig' in locals():
                plt.close(fig)
            
            fig, ax = self._create_figure()
            
            # Add only elements that don't require external data
            ax.set_facecolor('#e6f3ff')  # Simple ocean background
            self._add_custom_basemap(ax)
            self._add_snowline(ax, snowline)
            self._add_graticules(ax)
            self._add_north_arrow(ax)
            self._add_title(ax, target_date)
            self._add_legend(ax)
            
            # Save to file
            fig.savefig(
                output_path,
                format='svg',
                bbox_inches='tight',
                pad_inches=0.1
            )
            plt.close(fig)
        
        return output_path
