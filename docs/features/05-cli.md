# Feature Implementation Plan: Command-Line Interface

## Overview

Implement the command-line interface (CLI) that serves as the entry point for the Snowline Visualisation Tool, orchestrating configuration loading, data processing, and map generation.

## Current State

- `main.py` contains basic argument parsing and config loading
- No integration with processing or rendering components
- No progress reporting or error handling

## Requirements

- Accept configuration file path as command-line argument
- Load configuration and validate
- Orchestrate the full pipeline (load data, process, render)
- Provide progress feedback to user
- Handle errors gracefully with helpful messages
- Support dry-run mode for validation
- Return appropriate exit codes

## Implementation Steps

### Step 1: Enhance Argument Parser

Update `main.py`:

```python
import argparse
import sys
from pathlib import Path

def create_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        prog='snowline',
        description='Generate print-ready maps visualising historical snowlines.',
        epilog='For more information, see the documentation at docs/'
    )
    
    parser.add_argument(
        '--config', '-c',
        type=Path,
        required=True,
        help='Path to the YAML configuration file'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Validate configuration without processing'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='count',
        default=0,
        help='Increase output verbosity (can be repeated)'
    )
    
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Suppress all output except errors'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='%(prog)s 1.0.0'
    )
    
    return parser
```

### Step 2: Create Logging Configuration

Create `src/logging_config.py`:

```python
import logging
import sys

def configure_logging(verbosity: int, quiet: bool) -> logging.Logger:
    """Configure logging based on verbosity level."""
    logger = logging.getLogger('snowline')
    
    if quiet:
        level = logging.ERROR
    elif verbosity == 0:
        level = logging.WARNING
    elif verbosity == 1:
        level = logging.INFO
    else:
        level = logging.DEBUG
    
    logger.setLevel(level)
    
    # Console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    
    # Format
    if verbosity >= 2:
        fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    else:
        fmt = '%(levelname)s: %(message)s'
    
    handler.setFormatter(logging.Formatter(fmt))
    logger.addHandler(handler)
    
    return logger
```

### Step 3: Create Application Orchestrator

Create `src/app.py`:

```python
import logging
from pathlib import Path
from datetime import date
from typing import Optional

from src.config import load_config, Config, ConfigurationError
from src.data.loader import get_data_loader
from src.processing.pipeline import SnowlinePipeline
from src.processing.interpolation import InterpolationProcessor
from src.mapping.cartopy_renderer import CartopyRenderer
from src.mapping.generator import MapGenerator

logger = logging.getLogger('snowline')

class SnowlineApp:
    """Main application orchestrator."""
    
    def __init__(self, config_path: Path):
        self.config_path = config_path
        self.config: Optional[Config] = None
    
    def load_configuration(self) -> bool:
        """Load and validate configuration. Returns True on success."""
        try:
            self.config = load_config(self.config_path)
            logger.info(f"Configuration loaded from {self.config_path}")
            return True
        except ConfigurationError as e:
            logger.error(f"Configuration error: {e}")
            return False
        except FileNotFoundError:
            logger.error(f"Configuration file not found: {self.config_path}")
            return False
    
    def validate_inputs(self) -> bool:
        """Validate that input files exist. Returns True if valid."""
        if not self.config:
            return False
        
        snow_data = Path(self.config.input.snow_cover_data)
        if not snow_data.exists():
            logger.error(f"Snow cover data not found: {snow_data}")
            return False
        
        if self.config.input.basemap_data:
            basemap = Path(self.config.input.basemap_data)
            if not basemap.exists():
                logger.warning(f"Basemap not found: {basemap}")
                # Warning only, not fatal
        
        return True
    
    def run(self, dry_run: bool = False) -> int:
        """
        Run the full pipeline.
        
        Returns:
            Exit code (0 for success, non-zero for errors)
        """
        # Load configuration
        if not self.load_configuration():
            return 1
        
        # Validate inputs
        if not self.validate_inputs():
            return 1
        
        if dry_run:
            logger.info("Dry run complete. Configuration is valid.")
            self._print_summary()
            return 0
        
        try:
            return self._run_pipeline()
        except Exception as e:
            logger.exception(f"Pipeline failed: {e}")
            return 1
    
    def _run_pipeline(self) -> int:
        """Execute the processing and rendering pipeline."""
        # Initialize components
        loader = get_data_loader(self.config)
        processor = InterpolationProcessor(self.config.region.bounding_box)
        pipeline = SnowlinePipeline(self.config, loader, processor)
        
        renderer = CartopyRenderer(self.config)
        generator = MapGenerator(self.config, renderer)
        
        # Run processing
        logger.info("Starting snowline extraction...")
        snowlines = pipeline.run()
        logger.info(f"Extracted snowlines for {len(snowlines)} dates")
        
        # Generate maps
        logger.info("Generating maps...")
        output_paths = generator.generate_all(snowlines)
        
        # Report results
        logger.info(f"Generated {len(output_paths)} maps")
        for path in output_paths:
            logger.info(f"  {path}")
        
        return 0
    
    def _print_summary(self) -> None:
        """Print configuration summary."""
        print("\nConfiguration Summary:")
        print(f"  Input data: {self.config.input.snow_cover_data}")
        print(f"  Region: {self.config.region.bounding_box}")
        print(f"  Date range: {self.config.time.start_date} to "
              f"{self.config.time.end_date}")
        print(f"  Output directory: {self.config.output.directory}")
```

### Step 4: Update Main Entry Point

Update `main.py`:

```python
#!/usr/bin/env python3
"""
Snowline Visualisation Tool

Generate print-ready maps visualising historical snowlines in Scotland.
"""

import sys
from pathlib import Path

from src.logging_config import configure_logging
from src.app import SnowlineApp


def create_parser():
    # ... as defined above ...
    pass


def main() -> int:
    """Main entry point. Returns exit code."""
    parser = create_parser()
    args = parser.parse_args()
    
    # Configure logging
    logger = configure_logging(args.verbose, args.quiet)
    
    # Create and run application
    app = SnowlineApp(args.config)
    return app.run(dry_run=args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
```

### Step 5: Add Progress Reporting

For long-running operations, add progress feedback:

```python
from typing import Iterator, TypeVar
import sys

T = TypeVar('T')

def with_progress(
    items: Iterator[T],
    total: int,
    description: str = "Processing"
) -> Iterator[T]:
    """Wrap an iterator with progress reporting."""
    for i, item in enumerate(items, 1):
        # Simple progress indicator
        if sys.stdout.isatty():
            pct = (i / total) * 100
            print(f"\r{description}: {i}/{total} ({pct:.0f}%)", end='')
        yield item
    
    if sys.stdout.isatty():
        print()  # Newline after progress complete
```

For richer progress (optional), use `tqdm`:

```python
from tqdm import tqdm

for target_date in tqdm(date_range, desc="Generating maps"):
    # ... process date ...
```

### Step 6: Exit Codes

Define exit codes in `src/exit_codes.py`:

```python
from enum import IntEnum

class ExitCode(IntEnum):
    SUCCESS = 0
    CONFIGURATION_ERROR = 1
    INPUT_NOT_FOUND = 2
    PROCESSING_ERROR = 3
    OUTPUT_ERROR = 4
    UNKNOWN_ERROR = 99
```

## File Structure

```
main.py                 # Entry point
src/
  __init__.py
  app.py               # Application orchestrator
  logging_config.py    # Logging setup
  exit_codes.py        # Exit code definitions
```

## Testing Strategy

Create `tests/test_cli.py`:

1. **Valid config path**: Verify successful execution
2. **Missing config file**: Verify error message and exit code 1
3. **Invalid config content**: Verify validation error
4. **Dry run mode**: Verify no output files created
5. **Verbosity levels**: Verify logging output changes
6. **Version flag**: Verify version printed

### Integration Tests

Create `tests/test_integration.py`:

1. **End-to-end pipeline**: Run with test data, verify SVG output
2. **Empty date range**: Verify graceful handling
3. **Missing input data**: Verify helpful error message

### Test with subprocess

```python
import subprocess

def test_cli_help():
    result = subprocess.run(
        ['python', 'main.py', '--help'],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert 'configuration file' in result.stdout.lower()

def test_cli_missing_config():
    result = subprocess.run(
        ['python', 'main.py', '--config', 'nonexistent.yaml'],
        capture_output=True,
        text=True
    )
    assert result.returncode != 0
    assert 'not found' in result.stderr.lower()
```

## Dependencies

- Python standard library: `argparse`, `logging`, `sys`, `pathlib`
- Optional: `tqdm` for progress bars

## Usage Examples

```bash
# Basic usage
python main.py --config config.yaml

# Validate configuration only
python main.py --config config.yaml --dry-run

# Verbose output
python main.py --config config.yaml -v

# Very verbose (debug) output
python main.py --config config.yaml -vv

# Quiet mode (errors only)
python main.py --config config.yaml -q

# Show version
python main.py --version
```

## Error Messages

Provide clear, actionable error messages:

```
ERROR: Configuration file not found: /path/to/config.yaml
       Check that the file exists and the path is correct.

ERROR: Invalid bounding box: min_lon (-7.5) must be less than max_lon (-8.0)
       Check the 'region.bounding_box' section of your configuration.

ERROR: Snow cover data not found: ./data/ssgb_scotland.csv
       Download the SSGB dataset and update 'input.snow_cover_data' in config.yaml.
```

## Acceptance Criteria

- [ ] CLI accepts `--config` argument and loads configuration
- [ ] `--dry-run` validates without processing
- [ ] `--verbose` increases logging detail
- [ ] `--quiet` suppresses non-error output
- [ ] `--version` displays version number
- [ ] Helpful error messages for common issues
- [ ] Appropriate exit codes for different error conditions
- [ ] Progress feedback during processing
- [ ] Integration tests pass for end-to-end workflow
