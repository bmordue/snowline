# User Interface Features

This document describes the key features of the user interface for the snowline visualization tool.

## TUI

This is a text-based interface using configuration files to drive an offline script pipeline.

There is no graphical user interface.

Initially all configuration can be taking from a config file; the TUI does not need to offer configuration options.

## Configurable options

## 1. Mapping

*   **Base Map:** A high-quality base map (e.g., satellite, terrain).
*   **Snowline Overlay:** The extracted snowline will be overlaid on the map.
*   **Other Overlays:**
*   * static file output, destined for print, so there are no controls on the map
    *   A scale bar and attribution information.

## 2. Start and End Date Selection

Start and End Date configuration options will allow users to select the time period for the visualization.

## 3. Region Selection

Users should be able to select the geographic region they are interested in by defining a geographic bounding box.

## 4. Information Panel

A sidebar or panel that displays information about the data and visualization.

*   **Data Source Information:** Display the source of the snow cover data being shown.
*   **Current Date:** Show the date of the currently displayed snowline.
*   **Statistics:**
    *   Calculate and display the area of snow cover in the current view.
    *   Show the elevation of the snowline.
*   **Trend Chart:** A simple line chart showing the total snow cover area over the selected time period.

