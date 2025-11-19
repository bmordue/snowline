# Configuration

The Snowline Visualization Tool is driven by a single YAML configuration file, typically named `config.yaml`. This document details the structure and available options for this file.

## File Structure

The configuration is organized into sections for clarity: `input`, `region`, `time`, and `output`.

```yaml
# -----------------------------------------------------------------
# Configuration for the Snowline Visualization Tool
# -----------------------------------------------------------------

# Section for defining input data sources
input:
  # Path to the primary snow cover dataset (e.g., the digitized SSGB data)
  # This should be a local file path.
  snow_cover_data: /path/to/your/snow_cover_data.csv

  # (Optional) Path to a basemap file, e.g., a shapefile for country borders.
  # If not provided, a default basemap from Cartopy may be used.
  basemap_data: /path/to/your/scotland_borders.shp

# Section for defining the geographic area of interest
region:
  # Bounding box for the map output, specified in WGS 84 coordinates.
  # min_lon: Minimum longitude (left edge)
  # max_lon: Maximum longitude (right edge)
  # min_lat: Minimum latitude (bottom edge)
  # max_lat: Maximum latitude (top edge)
  bounding_box:
    min_lon: -7.5
    max_lon: -1.0
    min_lat: 54.5
    max_lat: 59.0

# Section for defining the time period for the analysis
time:
  # The start date for generating maps. Format: YYYY-MM-DD
  start_date: "2005-01-15"
  # The end date for generating maps. Format: YYYY-MM-DD
  end_date: "2005-02-15"

# Section for defining the output settings
output:
  # The directory where the generated SVG maps will be saved.
  directory: ./output/maps

  # A prefix for the output filenames. The date will be appended.
  # e.g., "scotland_snowline_" will result in "scotland_snowline_2005-01-15.svg"
  filename_prefix: scotland_snowline_

  # Map styling options
  style:
    # Color of the snowline, can be a name or hex code.
    snowline_color: "#0000FF"
    # Line width of the snowline.
    snowline_width: 1.5
    # Color of the graticule lines.
    gridline_color: "#CCCCCC"
    # Line style of the graticules (e.g., '--', ':', '-.').
    gridline_style: '--'
```

## Parameter Details

### `input`
*   `snow_cover_data`: **Required.** The path to the main dataset from which snowlines will be derived.
*   `basemap_data`: **Optional.** A path to a vector file (e.g., Shapefile) to use as the base map layer. This provides more control than the default Cartopy maps.

### `region`
*   `bounding_box`: **Required.** Defines the geographic extent of the final map. The values should be floating-point numbers representing degrees of latitude and longitude.

### `time`
*   `start_date` / `end_date`: **Required.** Define the inclusive period for which maps should be generated. The tool will process data for each day within this range.

### `output`
*   `directory`: **Required.** The location where the output SVG files will be stored. The tool should create this directory if it doesn't exist.
*   `filename_prefix`: **Required.** A string that will be prepended to the output filenames, followed by the date.
*   `style`: **Optional.** A section to control the visual appearance of map elements. If omitted, default styles will be applied.
