# Feature Implementation Plan: Map Generation

## Overview

Implement the map generation system that produces print-ready SVG maps with snowlines overlaid on base maps, complete with cartographic elements (north arrow, graticules, title).

## Current State

- No map generation implementation exists
- PRD specifies SVG output with Matplotlib and Cartopy
- Configuration includes styling options for snowline and gridlines

## Requirements

- Generate high-quality SVG maps suitable for print
- Include base map layer (terrain or political boundaries)
- Overlay extracted snowline
- Add cartographic elements:
  - North arrow
  - Graticules (grid lines) with labels
  - Title with date
  - Scale bar (optional)
- Support configurable styling
- Generate one map per date in the specified range

## Implementation Steps

### Step 1: Create Map Renderer Interface

Create `src/mapping/renderer.py`:

```python
from abc import ABC, abstractmethod
from pathlib import Path
from datetime import date
import geopandas as gpd

from src.config import Config

class MapRenderer(ABC):
    """Abstract base class for map rendering."""
    
    @abstractmethod
    def render(
        self,
        snowline: gpd.GeoDataFrame,
        target_date: date,
        output_path: Path
    ) -> Path:
        """Render a map and save to file. Returns output path."""
        pass
```

### Step 2: Implement Cartopy-Based Renderer

Create `src/mapping/cartopy_renderer.py`:

```python
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
import geopandas as gpd
from pathlib import Path
from datetime import date

from src.config import Config, StyleConfig, BoundingBox
from src.mapping.renderer import MapRenderer

class CartopyRenderer(MapRenderer):
    """Render maps using Matplotlib and Cartopy."""
    
    def __init__(self, config: Config):
        self.config = config
        self.bbox = config.region.bounding_box
        self.style = config.output.style
        self.projection = ccrs.PlateCarree()
    
    def _create_figure(self) -> tuple[plt.Figure, plt.Axes]:
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
    
    def _add_base_map(self, ax: plt.Axes) -> None:
        """Add base map features."""
        # Add land and ocean
        ax.add_feature(
            cfeature.LAND, 
            facecolor='#f0f0f0',
            edgecolor='none'
        )
        ax.add_feature(
            cfeature.OCEAN, 
            facecolor='#e6f3ff'
        )
        
        # Add coastlines and borders
        ax.add_feature(
            cfeature.COASTLINE, 
            linewidth=0.5,
            edgecolor='#666666'
        )
        ax.add_feature(
            cfeature.BORDERS, 
            linewidth=0.3,
            linestyle=':'
        )
        
        # Add rivers and lakes
        ax.add_feature(
            cfeature.RIVERS, 
            linewidth=0.3,
            edgecolor='#99ccff'
        )
        ax.add_feature(
            cfeature.LAKES, 
            facecolor='#e6f3ff',
            edgecolor='#99ccff'
        )
    
    def _add_custom_basemap(self, ax: plt.Axes) -> None:
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
        ax: plt.Axes, 
        snowline: gpd.GeoDataFrame
    ) -> None:
        """Add snowline to the map."""
        if snowline.empty or snowline.geometry.iloc[0] is None:
            return
        
        snowline.plot(
            ax=ax,
            color=self.style.snowline_color,
            linewidth=self.style.snowline_width,
            transform=self.projection,
            zorder=10  # Ensure snowline is on top
        )
    
    def _add_graticules(self, ax: plt.Axes) -> None:
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
    
    def _add_north_arrow(self, ax: plt.Axes) -> None:
        """Add north arrow to the map."""
        # Position in axes coordinates (top-right corner)
        arrow_x = 0.95
        arrow_y = 0.95
        arrow_length = 0.08
        
        # Create arrow
        ax.annotate(
            'N',
            xy=(arrow_x, arrow_y - arrow_length),
            xytext=(arrow_x, arrow_y),
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
    
    def _add_title(self, ax: plt.Axes, target_date: date) -> None:
        """Add title with date."""
        ax.set_title(
            f"Snowline - {target_date.strftime('%d %B %Y')}",
            fontsize=14,
            fontweight='bold',
            pad=10
        )
    
    def _add_legend(self, ax: plt.Axes) -> None:
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
        fig, ax = self._create_figure()
        
        # Add map elements
        self._add_base_map(ax)
        if self.config.input.basemap_data:
            self._add_custom_basemap(ax)
        self._add_snowline(ax, snowline)
        self._add_graticules(ax)
        self._add_north_arrow(ax)
        self._add_title(ax, target_date)
        self._add_legend(ax)
        
        # Save to file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(
            output_path,
            format='svg',
            bbox_inches='tight',
            pad_inches=0.1
        )
        plt.close(fig)
        
        return output_path
```

### Step 3: Create Map Generator Orchestrator

Create `src/mapping/generator.py`:

```python
from pathlib import Path
from datetime import date
import geopandas as gpd
from typing import Dict, List

from src.config import Config
from src.mapping.renderer import MapRenderer

class MapGenerator:
    """Generates maps for all dates in the pipeline results."""
    
    def __init__(self, config: Config, renderer: MapRenderer):
        self.config = config
        self.renderer = renderer
    
    def _generate_filename(self, target_date: date) -> str:
        """Generate output filename for a date."""
        return (
            f"{self.config.output.filename_prefix}"
            f"{target_date.strftime('%Y-%m-%d')}.svg"
        )
    
    def generate_all(
        self, 
        snowlines: Dict[date, gpd.GeoDataFrame]
    ) -> List[Path]:
        """Generate maps for all dates. Returns list of output paths."""
        output_dir = Path(self.config.output.directory)
        output_paths = []
        
        for target_date, snowline in snowlines.items():
            filename = self._generate_filename(target_date)
            output_path = output_dir / filename
            
            self.renderer.render(snowline, target_date, output_path)
            output_paths.append(output_path)
        
        return output_paths
    
    def generate_single(
        self,
        snowline: gpd.GeoDataFrame,
        target_date: date
    ) -> Path:
        """Generate a single map. Returns output path."""
        output_dir = Path(self.config.output.directory)
        filename = self._generate_filename(target_date)
        output_path = output_dir / filename
        
        return self.renderer.render(snowline, target_date, output_path)
```

### Step 4: Add Scale Bar (Optional Enhancement)

```python
from cartopy.mpl.geoaxes import GeoAxes

def add_scale_bar(
    ax: GeoAxes,
    length_km: float = 50,
    location: tuple = (0.1, 0.05)
) -> None:
    """Add a scale bar to the map."""
    # Calculate scale bar length in degrees (approximate)
    # At 57°N latitude, 1 degree longitude ≈ 60 km
    lat_center = (ax.get_extent()[2] + ax.get_extent()[3]) / 2
    km_per_degree = 111.32 * np.cos(np.radians(lat_center))
    length_deg = length_km / km_per_degree
    
    # Draw scale bar
    x0, y0 = location
    ax.plot(
        [x0, x0 + length_deg],
        [y0, y0],
        transform=ccrs.PlateCarree(),
        color='black',
        linewidth=3
    )
    
    # Add label
    ax.text(
        x0 + length_deg / 2,
        y0 - 0.01,
        f'{int(length_km)} km',
        transform=ccrs.PlateCarree(),
        ha='center',
        fontsize=8
    )
```

## File Structure

```
src/
  mapping/
    __init__.py
    renderer.py         # Abstract interface
    cartopy_renderer.py # Cartopy implementation
    generator.py        # Orchestration
    elements.py         # Reusable map elements (scale bar, etc.)
```

## Testing Strategy

Create `tests/test_mapping.py`:

1. **Basic rendering**: Render with empty snowline, verify SVG created
2. **Snowline rendering**: Render with valid snowline geometry
3. **Filename generation**: Verify correct date formatting
4. **Output directory creation**: Verify directory created if missing
5. **Style application**: Verify configured colours applied
6. **Base map loading**: Test custom basemap from shapefile

### Visual Testing

For map output, manual visual inspection is important:

1. Create a set of reference outputs for comparison
2. Generate maps with known test data
3. Compare visually or use image diffing tools

## Dependencies

- `matplotlib`: Core plotting library
- `cartopy`: Geospatial plotting and projections
- `geopandas`: For reading and plotting snowline geometries

## Configuration Extensions

Consider additional styling options:

```yaml
output:
  style:
    # Existing options...
    
    # Map dimensions
    figure_width: 12
    figure_height: 10
    dpi: 150
    
    # Base map styling
    land_color: "#f0f0f0"
    ocean_color: "#e6f3ff"
    coastline_color: "#666666"
    
    # Title styling
    title_fontsize: 14
    title_fontweight: bold
    
    # Scale bar
    show_scale_bar: true
    scale_bar_length_km: 50
```

## SVG Optimisation

For print-ready output, consider:

1. **Font embedding**: Ensure fonts are embedded or converted to paths
2. **Layer organisation**: Group elements logically for editing in vector software
3. **Metadata**: Include date and configuration in SVG metadata

```python
def _add_metadata(self, fig: plt.Figure, target_date: date) -> None:
    """Add metadata to the SVG."""
    fig.set_metadata({
        'Title': f'Snowline Map - {target_date}',
        'Creator': 'Snowline Visualization Tool',
        'Date': target_date.isoformat()
    })
```

## Acceptance Criteria

- [ ] SVG maps generated with correct geographic extent
- [ ] Base map features (coastlines, borders) rendered correctly
- [ ] Snowline overlaid with configured styling
- [ ] Graticules displayed with coordinate labels
- [ ] North arrow positioned correctly
- [ ] Title includes formatted date
- [ ] Output files saved with correct naming convention
- [ ] Output directory created if it doesn't exist
- [ ] Unit tests pass with >80% coverage for mapping module
