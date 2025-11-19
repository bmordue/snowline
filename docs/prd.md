# Product Requirements Document (PRD): Snowline Visualization Tool

## 1. Overview

This document defines the requirements for the Snowline Visualization Tool, an offline data processing pipeline that generates print-ready maps visualizing historical snowlines in Scotland, UK.

## 2. Objective

The primary objective is to create a command-line tool that processes historical snow cover data and produces high-quality, static maps (SVG format) showing the snowline for a user-defined region and time period. This tool is intended for researchers, cartographers, and anyone needing high-fidelity print outputs for analysis and publication.

## 3. Target Audience

*   Climate Researchers
*   Glaciologists
*   Geographers
*   Cartographers and GIS Analysts

## 4. Features & Requirements

### 4.1. Core Functionality

*   **Data Ingestion:** The tool will ingest snow cover data from specified sources, primarily the Snow Survey of Great Britain (SSGB) dataset.
*   **Data Processing:** It will execute a data processing pipeline to extract a vector snowline from the raw data for a given date.
*   **Map Generation:** It will generate a static map of the extracted snowline overlaid on a base map.
*   **Configuration Driven:** All aspects of the tool's execution will be controlled by a single YAML configuration file.

### 4.2. Configuration (`config.yaml`)

The tool will be entirely driven by a `config.yaml` file, which will specify:
*   **Input Data:** Path to the local snow cover data.
*   **Region of Interest:** A geographic bounding box (min/max latitude and longitude) defining the map extent.
*   **Date Range:** A start and end date for which to generate maps.
*   **Output Settings:**
    *   `output_path`: The directory where the generated SVG files will be saved.
    *   `filename_prefix`: A prefix for output files (e.g., `scotland_snowline_`).

### 4.3. Map Output

*   **Format:** The primary output format for maps will be **SVG (Scalable Vector Graphics)**.
*   **Map Elements:** Each map will contain:
    *   The extracted snowline for a specific date.
    *   A base map layer (e.g., terrain or political boundaries).
    *   **North Arrow**.
    *   **Graticules (Grid Lines)** for latitude and longitude.
*   **Styling:** The visual style of the map elements (e.g., line thickness, color) will be configurable.

### 4.4. Command-Line Interface (CLI)

*   The tool will be executed from the command line.
*   A single command will initiate the pipeline, which will read the `config.yaml` and generate the outputs.
*   Example usage: `python main.py --config /path/to/config.yaml`

## 5. Technical Requirements

*   **Language:** Python
*   **Core Libraries:**
    *   Geospatial data handling: GeoPandas, Rasterio, Shapely
    *   Map plotting: Matplotlib, Cartopy
    *   Configuration parsing: PyYAML

## 6. Out of Scope for Version 1.0

*   Interactive GUI or TUI for configuration.
*   Web application or any network-based functionality.
*   On-the-fly data fetching or processing. The pipeline is for local, offline use.
*   Support for output formats other than SVG.
*   Animated outputs (e.g., GIFs).
