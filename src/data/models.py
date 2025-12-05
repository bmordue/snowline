"""Data models for snow observations."""

from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass
class SnowObservation:
    """Represents a single snow observation at a specific site and date."""
    date: date
    site_id: str
    latitude: float
    longitude: float
    snow_present: bool
    snow_depth: Optional[float] = None
    elevation: Optional[float] = None
