#!/usr/bin/env python3
"""Snowline Visualisation Tool.

Command-line entry point. Generates print-ready SVG maps visualising
historical snowlines in Scotland.
"""

import argparse
import sys
from pathlib import Path

from src.app import SnowlineApp
from src.logging_config import configure_logging

__version__ = "1.0.0"


def create_parser() -> argparse.ArgumentParser:
    """Create and configure the CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog='snowline',
        description=(
            'Generate print-ready maps visualising historical snowlines.'
        ),
        epilog='For more information, see the documentation at docs/',
    )

    parser.add_argument(
        '--config', '-c',
        type=Path,
        required=True,
        help='Path to the YAML configuration file',
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Validate configuration without processing',
    )

    parser.add_argument(
        '--verbose', '-v',
        action='count',
        default=0,
        help='Increase output verbosity (can be repeated)',
    )

    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Suppress all output except errors',
    )

    parser.add_argument(
        '--version',
        action='version',
        version=f'%(prog)s {__version__}',
    )

    return parser


def main(argv=None) -> int:
    """Main entry point. Returns an exit code."""
    parser = create_parser()
    args = parser.parse_args(argv)

    configure_logging(args.verbose, args.quiet)

    app = SnowlineApp(args.config)
    return app.run(dry_run=args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
