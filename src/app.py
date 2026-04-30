"""Application orchestrator for the Snowline CLI."""

import logging
from pathlib import Path
from typing import Optional

import yaml

from src.config import Config, load_config
from src.exceptions import ConfigurationError
from src.exit_codes import ExitCode

logger = logging.getLogger('snowline')


class SnowlineApp:
    """Coordinates configuration loading, validation, and pipeline execution."""

    def __init__(self, config_path: Path):
        """Initialize the application.

        Parameters
        ----------
        config_path : Path
            Path to the YAML configuration file.
        """
        self.config_path = Path(config_path)
        self.config: Optional[Config] = None

    def load_configuration(self) -> bool:
        """Load and validate configuration. Returns ``True`` on success."""
        try:
            self.config = load_config(self.config_path)
        except FileNotFoundError:
            logger.error(
                f"Configuration file not found: {self.config_path}"
            )
            return False
        except ConfigurationError as exc:
            logger.error(f"Configuration error: {exc}")
            return False
        except yaml.YAMLError as exc:
            logger.error(f"Error parsing YAML configuration: {exc}")
            return False

        logger.info(f"Configuration loaded from {self.config_path}")
        return True

    def validate_inputs(self) -> bool:
        """Validate that input files exist. Returns ``True`` if valid."""
        if not self.config:
            return False

        snow_data = Path(self.config.input.snow_cover_data)
        if not snow_data.exists():
            logger.error(f"Snow cover data not found: {snow_data}")
            return False

        if self.config.input.basemap_data:
            basemap = Path(self.config.input.basemap_data)
            if not basemap.exists():
                # Warning only, not fatal. Clear the optional basemap path
                # so downstream rendering does not attempt to open it.
                logger.warning(f"Basemap not found: {basemap}")
                self.config.input.basemap_data = None

        return True

    def run(self, dry_run: bool = False) -> int:
        """Run the full pipeline.

        Parameters
        ----------
        dry_run : bool
            If ``True``, validate the configuration and inputs without
            executing the processing pipeline or writing any output.

        Returns
        -------
        int
            Exit code (``0`` for success, non-zero for errors).
        """
        if not self.load_configuration():
            return int(ExitCode.CONFIGURATION_ERROR)

        if not self.validate_inputs():
            return int(ExitCode.INPUT_NOT_FOUND)

        if dry_run:
            logger.info("Dry run complete. Configuration is valid.")
            self._print_summary()
            return int(ExitCode.SUCCESS)

        try:
            return self._run_pipeline()
        except Exception as exc:  # noqa: BLE001 - surface unexpected errors
            logger.exception(f"Pipeline failed: {exc}")
            return int(ExitCode.PROCESSING_ERROR)

    def _run_pipeline(self) -> int:
        """Execute the processing and rendering pipeline."""
        # Imports are performed lazily so that ``--dry-run`` does not
        # require the heavier geospatial dependencies.
        from src.data.loader import get_data_loader
        from src.mapping.cartopy_renderer import CartopyRenderer
        from src.mapping.generator import MapGenerator
        from src.processing.interpolation import InterpolationProcessor
        from src.processing.pipeline import SnowlinePipeline

        assert self.config is not None  # for type checkers

        loader = get_data_loader(self.config)
        processor = InterpolationProcessor(self.config.region.bounding_box)
        pipeline = SnowlinePipeline(self.config, loader, processor)

        renderer = CartopyRenderer(self.config)
        generator = MapGenerator(self.config, renderer)

        logger.info("Starting snowline extraction...")
        snowlines = pipeline.run()
        logger.info(f"Extracted snowlines for {len(snowlines)} dates")

        logger.info("Generating maps...")
        output_paths = generator.generate_all(snowlines)

        logger.info(f"Generated {len(output_paths)} maps")
        for path in output_paths:
            logger.info(f"  {path}")

        return int(ExitCode.SUCCESS)

    def _print_summary(self) -> None:
        """Print a configuration summary to stdout."""
        assert self.config is not None
        bbox = self.config.region.bounding_box
        print("\nConfiguration Summary:")
        print(f"  Input data: {self.config.input.snow_cover_data}")
        print(
            f"  Region: ({bbox.min_lon}, {bbox.min_lat}) to "
            f"({bbox.max_lon}, {bbox.max_lat})"
        )
        print(
            f"  Date range: {self.config.time.start_date} to "
            f"{self.config.time.end_date}"
        )
        print(f"  Output directory: {self.config.output.directory}")
