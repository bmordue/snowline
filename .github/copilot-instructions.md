# Snowline Visualization Tool - Copilot Instructions

## Project Overview

This is an offline data processing tool for visualizing the historical snowline across Scotland, UK. It generates high-quality, print-ready SVG maps based on snow cover data from the Snow Survey of Great Britain (SSGB) dataset.

**Technology Stack:**
- Python 3.12
- Core libraries: GeoPandas, Pandas, Matplotlib, Cartopy, Rasterio
- Configuration: PyYAML
- Testing: pytest
- Build system: Nix (optional, via flake.nix and shell.nix)

**Architecture:**
- Command-line tool driven by a YAML configuration file (`config.yaml`)
- Modular structure with separate modules for config loading, data processing, and map generation
- Entry point: `main.py`
- Source code: `src/` directory
- Tests: `tests/` directory

## Build & Test Commands

### Installing Dependencies
```bash
python -m pip install --upgrade pip
pip install pytest pandas geopandas pyyaml shapely
```

Note: For a complete development environment, additional geospatial libraries may be needed (rasterio, cartopy, matplotlib).

### Running the Tool
```bash
python main.py --config config.yaml
```

### Running Tests
```bash
export PYTHONPATH=$(pwd)
python -m pytest tests/ -v
```

### Running Specific Tests
```bash
export PYTHONPATH=$(pwd)
python -m pytest tests/test_config.py -v
```

## Coding Standards

### Python Style
- Follow PEP 8 style guidelines
- Use type hints where appropriate for function signatures
- Prefer explicit variable names over abbreviations
- Use docstrings for modules, classes, and public functions

### Code Organization
- Keep business logic in the `src/` directory
- Place all tests in the `tests/` directory
- Use fixtures in `tests/fixtures/` for test data
- Configuration-related code goes in `src/config.py`
- Data processing code goes in `src/data/` module

### Imports
- Group imports in standard order: standard library, third-party, local imports
- Use absolute imports from the project root (e.g., `from src.config import load_config`)

### Error Handling
- Use custom exceptions defined in `src/exceptions.py`
- Raise `ConfigurationError` for configuration validation issues
- Provide clear, user-friendly error messages

### Testing
- Write unit tests for all new functionality
- Use pytest fixtures for reusable test components
- Place test fixtures in `tests/fixtures/` directory
- Test configuration validation thoroughly
- Ensure PYTHONPATH is set correctly when running tests

## Configuration

The tool is driven by a YAML configuration file with the following sections:
- `input`: Paths to data files (snow_cover_data, basemap_data)
- `region`: Bounding box coordinates (min_lon, max_lon, min_lat, max_lat)
- `time`: Date range (start_date, end_date)
- `output`: Output settings (directory, filename_prefix, style)

See `docs/configuration.md` for complete specification.

## Documentation

- Keep documentation in the `docs/` directory
- Main documentation files:
  - `docs/prd.md`: Product requirements
  - `docs/configuration.md`: Configuration file specification
  - `docs/tooling.md`: Libraries and tools used
  - `docs/data_processing.md`: Data processing workflow
  - `docs/data_sources.md`: Information about data sources
- Update documentation when adding new features or changing existing behavior

## Pull Request Quality

### Before Opening a PR
- Ensure all tests pass: `python -m pytest tests/ -v`
- Verify the code follows PEP 8 style guidelines
- Add tests for new functionality
- Update relevant documentation in `docs/` if adding features
- Ensure no sensitive data or credentials are committed

### PR Requirements
- Include clear description of changes
- Reference related issues
- Add tests that validate the changes
- Keep changes focused and minimal
- Update the configuration documentation if config schema changes

## Notes for Copilot Coding Agent

### What to Do
- Make minimal, focused changes to address specific issues
- Add comprehensive tests for new functionality
- Update documentation when adding or modifying features
- Use existing patterns and conventions from the codebase
- Validate configuration inputs thoroughly using the existing validation functions
- Use the exception classes defined in `src/exceptions.py`

### What to Avoid
- Don't modify or remove existing tests unless they're broken or need updating for your changes
- Don't upgrade library versions unless specifically required for the task
- Don't add new dependencies without justification
- Don't modify the CI workflow unless necessary
- Don't remove or modify working code without a clear reason
- Avoid making broad refactors; prefer surgical changes

### Specific Guidance
- When working with configuration: Use the existing validation pattern with separate validation functions
- When adding new config fields: Update the dataclasses in `src/config.py` and add appropriate validation
- When working with geospatial data: Follow the patterns established in existing code using GeoPandas
- Path handling: Use `pathlib.Path` for file paths
- Date handling: Use `datetime.date` from the standard library

### Testing Notes
- Always set `PYTHONPATH` when running tests
- Use temporary directories for test files (see existing test patterns)
- Clean up test files after tests complete
- Test both valid and invalid inputs for validation functions
