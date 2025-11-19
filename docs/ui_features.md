# User Interface Features

This document describes the key features of the user interface for the snowline visualization tool.

## 1. Map View

The central and largest component of the UI will be an interactive map.

*   **Base Map:** A high-quality base map (e.g., satellite, terrain) from a provider like Mapbox.
*   **Snowline Overlay:** The extracted snowline will be overlaid on the map.
*   **Controls:**
    *   Standard pan and zoom controls.
    *   A-B comparison slider to compare snowline between two different dates.
    *   Layer switcher to toggle between different base map styles.
    *   A scale bar and attribution information.

## 2. Time and Date Controls

These controls will allow users to select the time period for the visualization.

*   **Time Slider:** A slider that allows the user to scrub through time and see the snowline change.
*   **Animation Controls:**
    *   Play/pause button to animate the snowline changes.
    *   Animation speed control (e.g., 1x, 2x, 4x).
*   **Date Range Picker:** Two calendar inputs to select a start and end date for the available data.

## 3. Region Selection

Users should be able to select the geographic region they are interested in.

*   **Search Box:** A geocoding search box to find a specific place by name.
*   **Predefined Regions:** A dropdown menu of interesting regions (e.g., "The Alps," "The Himalayas," "Sierra Nevada").
*   **Custom Region:** A drawing tool that allows users to draw a polygon on the map to define their own region of interest.

## 4. Information Panel

A sidebar or panel that displays information about the data and visualization.

*   **Data Source Information:** Display the source of the snow cover data being shown.
*   **Current Date:** Show the date of the currently displayed snowline.
*   **Statistics:**
    *   Calculate and display the area of snow cover in the current view.
    *   Show the elevation of the snowline.
*   **Trend Chart:** A simple line chart showing the total snow cover area over the selected time period.

## 5. Export and Sharing

*   **Download Data:** A button to download the snowline data for the current view in GeoJSON format.
*   **Download Image:** A button to export the current map view as a PNG or JPG image.
*   **Share URL:** A button to generate a shareable URL that preserves the current map view, date, and region.
