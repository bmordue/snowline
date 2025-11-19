# Tooling and Libraries

This document outlines the recommended Python libraries for the Snowline Visualization Tool. Given that this is an offline data processing and map generation tool, the focus is on a robust scientific and geospatial Python stack.

## Core Libraries

*   **GeoPandas:** The primary tool for working with vector data (e.g., the extracted snowline). It extends the pandas DataFrame to allow for spatial operations.
    *   **Use Cases:** Reading/writing geospatial file formats (Shapefile, GeoJSON), geometric operations, and spatial joins.
    *   **Link:** [https://geopandas.org/](https://geopandas.org/)

*   **Rasterio:** The essential library for reading and writing raster data, such as satellite imagery or digital elevation models which might be used for base maps or analysis.
    *   **Use Cases:** Opening raster files, reading metadata, and clipping/masking raster data to a specific region.
    *   **Link:** [https://rasterio.readthedocs.io/](https://rasterio.readthedocs.io/)

*   **Matplotlib:** The foundational plotting library in Python. It will serve as the engine for creating the static map outputs.
    *   **Use Cases:** Creating figures and axes, drawing plots, customizing plot elements (titles, labels), and saving figures to files (including SVG).
    *   **Link:** [https://matplotlib.org/](https://matplotlib.org/)

*   **Cartopy:** A library designed for geospatial data processing in order to produce maps and other geospatial data analyses. It integrates seamlessly with Matplotlib.
    *   **Use Cases:** Creating map projections, adding geographic features (coastlines, borders), and plotting data on projected axes, including gridlines and north arrows.
    *   **Link:** [https://scitools.org.uk/cartopy/](https://scitools.org.uk/cartopy/)

## Supporting Libraries

*   **PyYAML:** To parse the `config.yaml` file that drives the application.
    *   **Use Cases:** Safely loading the YAML configuration into a Python dictionary.
    *   **Link:** [https://pyyaml.org/](https://pyyaml.org/)

*   **Shapely:** For manipulation and analysis of planar geometric objects. It is a core dependency of GeoPandas.
    *   **Use Cases:** Performing geometric operations on points, lines, and polygons.
    *   **Link:** [https://shapely.readthedocs.io/](https://shapely.readthedocs.io/)

*   **NumPy:** The fundamental package for scientific computing with Python. It's a dependency for many of the above libraries.
    *   **Use Cases:** Numerical operations, especially on raster data arrays.
    *   **Link:** [https://numpy.org/](https://numpy.org/)
