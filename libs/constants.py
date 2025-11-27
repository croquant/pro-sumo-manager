"""Shared constants for the application."""

from typing import Final

# Game calendar constants
N_MONTHS: Final[int] = 12
N_DAYS: Final[int] = 24

# Ability constants (overall power level)
MIN_POTENTIAL: Final[int] = 5
MEAN_POTENTIAL: Final[int] = 30  # Mean for Gaussian distribution
SIGMA_POTENTIAL: Final[int] = 20  # Standard deviation for Gaussian distribution
MAX_POTENTIAL: Final[int] = 100

# Individual stat constants
MIN_STAT_VALUE: Final[int] = 1
MAX_STAT_VALUE: Final[int] = 20
NUM_STATS: Final[int] = 5  # strength, technique, balance, endurance, mental
