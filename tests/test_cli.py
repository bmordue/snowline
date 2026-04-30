"""Tests for the Snowline command-line interface."""

import logging
import subprocess
import sys
from pathlib import Path

import pytest

from main import create_parser, main
from src.app import SnowlineApp
from src.exit_codes import ExitCode
from src.logging_config import configure_logging


REPO_ROOT = Path(__file__).resolve().parent.parent


VALID_CONFIG_TEMPLATE = """
input:
  snow_cover_data: {snow_data}
  basemap_data: null

region:
  bounding_box:
    min_lon: -7.5
    max_lon: -1.0
    min_lat: 54.5
    max_lat: 59.0

time:
  start_date: "2005-01-15"
  end_date: "2005-01-16"

output:
  directory: {output_dir}
  filename_prefix: scotland_snowline_
  style:
    snowline_color: "#0000FF"
    snowline_width: 1.5
    gridline_color: "#CCCCCC"
    gridline_style: "--"
"""


@pytest.fixture
def fixture_csv():
    """Path to the bundled SSGB CSV fixture."""
    return REPO_ROOT / "tests" / "fixtures" / "sample_ssgb.csv"


@pytest.fixture
def valid_config_file(tmp_path, fixture_csv):
    """Write a valid config YAML pointing at the fixture data and return its path."""
    output_dir = tmp_path / "out"
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        VALID_CONFIG_TEMPLATE.format(
            snow_data=fixture_csv,
            output_dir=output_dir,
        )
    )
    return config_path


class TestArgumentParser:
    """Tests for the argparse-based CLI argument parser."""

    def test_config_required(self):
        parser = create_parser()
        with pytest.raises(SystemExit):
            parser.parse_args([])

    def test_basic_arguments(self):
        parser = create_parser()
        args = parser.parse_args(['--config', 'foo.yaml'])
        assert args.config == Path('foo.yaml')
        assert args.dry_run is False
        assert args.verbose == 0
        assert args.quiet is False

    def test_short_flags(self):
        parser = create_parser()
        args = parser.parse_args(['-c', 'foo.yaml', '-vv', '-q'])
        assert args.config == Path('foo.yaml')
        assert args.verbose == 2
        assert args.quiet is True

    def test_dry_run_flag(self):
        parser = create_parser()
        args = parser.parse_args(['--config', 'foo.yaml', '--dry-run'])
        assert args.dry_run is True


class TestConfigureLogging:
    """Tests for logging configuration."""

    def teardown_method(self):
        # Reset the snowline logger between tests so handlers don't accumulate.
        logger = logging.getLogger('snowline')
        for handler in list(logger.handlers):
            logger.removeHandler(handler)

    def test_default_is_warning(self):
        logger = configure_logging(0, quiet=False)
        assert logger.level == logging.WARNING

    def test_verbose_one_is_info(self):
        logger = configure_logging(1, quiet=False)
        assert logger.level == logging.INFO

    def test_verbose_two_is_debug(self):
        logger = configure_logging(2, quiet=False)
        assert logger.level == logging.DEBUG

    def test_quiet_overrides_verbose(self):
        logger = configure_logging(2, quiet=True)
        assert logger.level == logging.ERROR

    def test_repeated_calls_do_not_duplicate_handlers(self):
        configure_logging(1, quiet=False)
        configure_logging(1, quiet=False)
        logger = logging.getLogger('snowline')
        assert len(logger.handlers) == 1


class TestSnowlineApp:
    """Tests for the SnowlineApp orchestrator."""

    def test_missing_config_returns_configuration_error(self, tmp_path):
        app = SnowlineApp(tmp_path / "does_not_exist.yaml")
        assert app.run(dry_run=True) == int(ExitCode.CONFIGURATION_ERROR)

    def test_invalid_config_returns_configuration_error(self, tmp_path):
        bad = tmp_path / "bad.yaml"
        bad.write_text("not: [valid")  # malformed YAML
        app = SnowlineApp(bad)
        assert app.run(dry_run=True) == int(ExitCode.CONFIGURATION_ERROR)

    def test_dry_run_with_valid_config_succeeds(self, valid_config_file, capsys):
        app = SnowlineApp(valid_config_file)
        assert app.run(dry_run=True) == int(ExitCode.SUCCESS)
        captured = capsys.readouterr()
        assert "Configuration Summary" in captured.out

    def test_dry_run_does_not_create_output(self, valid_config_file, tmp_path):
        app = SnowlineApp(valid_config_file)
        app.run(dry_run=True)
        # Output directory should not have been populated.
        output_dir = tmp_path / "out"
        assert not output_dir.exists() or not any(output_dir.iterdir())

    def test_missing_input_data_returns_input_not_found(self, tmp_path):
        config_path = tmp_path / "config.yaml"
        config_path.write_text(
            VALID_CONFIG_TEMPLATE.format(
                snow_data=tmp_path / "no_such_file.csv",
                output_dir=tmp_path / "out",
            )
        )
        app = SnowlineApp(config_path)
        assert app.run(dry_run=True) == int(ExitCode.INPUT_NOT_FOUND)


class TestMainEntryPoint:
    """Tests that exercise ``main()`` directly."""

    def teardown_method(self):
        logger = logging.getLogger('snowline')
        for handler in list(logger.handlers):
            logger.removeHandler(handler)

    def test_main_dry_run_success(self, valid_config_file):
        exit_code = main(['--config', str(valid_config_file), '--dry-run'])
        assert exit_code == int(ExitCode.SUCCESS)

    def test_main_missing_config(self, tmp_path):
        exit_code = main([
            '--config', str(tmp_path / 'missing.yaml'),
            '--dry-run',
        ])
        assert exit_code == int(ExitCode.CONFIGURATION_ERROR)


class TestCliSubprocess:
    """Tests that invoke the CLI as a subprocess."""

    def test_cli_help(self):
        result = subprocess.run(
            [sys.executable, str(REPO_ROOT / "main.py"), "--help"],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
            env={**__import__('os').environ, 'PYTHONPATH': str(REPO_ROOT)},
        )
        assert result.returncode == 0
        assert 'configuration file' in result.stdout.lower()

    def test_cli_version(self):
        result = subprocess.run(
            [sys.executable, str(REPO_ROOT / "main.py"), "--version"],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
            env={**__import__('os').environ, 'PYTHONPATH': str(REPO_ROOT)},
        )
        assert result.returncode == 0
        assert 'snowline' in result.stdout.lower()
