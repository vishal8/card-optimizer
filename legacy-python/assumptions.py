
# PASTE THIS FILE AS-IS
from __future__ import annotations

from dataclasses import dataclass

@dataclass(frozen=True)
class BiltOptionAThresholds:
    """
    Spend thresholds as a fraction of rent (monthly logic applied to the month).
    Multiplier applies to FULL rent once threshold reached.
    """
    tier_25_mult: float = 0.50
    tier_50_mult: float = 0.75
    tier_75_mult: float = 1.00
    tier_100_mult: float = 1.25

@dataclass(frozen=True)
class BiltOptionBUnlock:
    """
    Option B: Bilt Cash unlock conversion.
    If $30 Bilt Cash -> 1,000 points, then:
      unlock_rate = 0.03 $cash per 1 point
    """
    bilt_cash_rate: float = 0.04
    unlock_rate: float = 0.03

@dataclass(frozen=True)
class VentureXAssumptions:
    """
    VX multipliers can vary depending on portal use.
    Keep them editable in UI.
    """
    other_mult: float = 2.0
    flights_mult: float = 5.0
    hotels_mult: float = 10.0
    annual_fee: float = 395.0

@dataclass(frozen=True)
class AmazonPrimeAssumptions:
    """
    Amazon Prime Visa (Whole Foods) often 5% for Prime members.
    """
    grocery_cashback_rate: float = 0.05
