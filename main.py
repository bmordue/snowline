import argparse
import sys
import traceback
from pathlib import Path

import yaml

from src.config import load_config, ConfigurationError
from src.data.loader import SSGBDataLoader
from src.processing.interpolation import InterpolationProcessor
from src.processing.pipeline import SnowlinePipeline
from src.mapping.cartopy_renderer import CartopyRenderer
from src.mapping.generator import MapGenerator


def main():
    parser = argparse.ArgumentParser(description="Snowline Visualization Tool")
    parser.add_argument("--config", type=str, required=True,
                        help="Path to the YAML configuration file")
    args = parser.parse_args()

    try:
        # Load configuration
        config = load_config(Path(args.config))
        print("Configuration loaded successfully:")
        print(f"  Input snow cover data: {config.input.snow_cover_data}")
        print(f"  Input basemap data: {config.input.basemap_data}")
        print(f"  Region bounding box: "
              f"({config.region.bounding_box.min_lon}, {config.region.bounding_box.min_lat}) to "
              f"({config.region.bounding_box.max_lon}, {config.region.bounding_box.max_lat})")
        print(f"  Time period: {config.time.start_date} to {config.time.end_date}")
        print(f"  Output directory: {config.output.directory}")
        print(f"  Output filename prefix: {config.output.filename_prefix}")
        print(f"  Style - snowline color: {config.output.style.snowline_color}")
        print(f"  Style - snowline width: {config.output.style.snowline_width}")
        print(f"  Style - gridline color: {config.output.style.gridline_color}")
        print(f"  Style - gridline style: {config.output.style.gridline_style}")
        print()
        
        # Initialize pipeline components
        print("Initializing pipeline...")
        loader = SSGBDataLoader(config.input.snow_cover_data)
        processor = InterpolationProcessor(bbox=config.region.bounding_box)
        pipeline = SnowlinePipeline(
            config=config,
            loader=loader,
            processor=processor
        )
        
        # Run snowline extraction
        print("Extracting snowlines...")
        snowlines = pipeline.run()
        print(f"Extracted snowlines for {len(snowlines)} dates")
        
        # Generate maps
        print("Generating maps...")
        renderer = CartopyRenderer(config)
        generator = MapGenerator(config, renderer)
        output_paths = generator.generate_all(snowlines)
        
        # Report results
        print(f"\nSuccessfully generated {len(output_paths)} maps:")
        for path in output_paths:
            print(f"  {path}")
        
    except ConfigurationError as e:
        print(f"Configuration error: {e}")
        sys.exit(1)
    except FileNotFoundError as e:
        print(f"Error: File not found - {e}")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"Error parsing YAML configuration: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error during processing: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
