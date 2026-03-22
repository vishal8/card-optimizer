# PASTE THIS FILE AS-IS
from dataclasses import dataclass
from typing import Dict

# Simple string constants (Python 3.8 safe)
CATEGORY_DINING = "dining"
CATEGORY_GROCERIES = "groceries"
CATEGORY_TRAVEL = "travel"
CATEGORY_OTHER = "other"

Category = str
BiltRentMode = str


@dataclass
class SpendProfileAnnual:
    rent: float
    dining: float
    groceries: float
    flights: float
    hotels: float
    other: float

    @property
    def travel(self) -> float:
        return float(self.flights + self.hotels)

    def by_category(self) -> Dict[Category, float]:
        return {
            CATEGORY_DINING: float(self.dining),
            CATEGORY_GROCERIES: float(self.groceries),
            CATEGORY_TRAVEL: float(self.travel),
            CATEGORY_OTHER: float(self.other),
        }


@dataclass
class SpendProfileMonthly:
    rent: float
    dining: float
    groceries: float
    travel: float
    other: float

    def by_category(self) -> Dict[Category, float]:
        return {
            CATEGORY_DINING: float(self.dining),
            CATEGORY_GROCERIES: float(self.groceries),
            CATEGORY_TRAVEL: float(self.travel),
            CATEGORY_OTHER: float(self.other),
        }


@dataclass
class Valuations:
    """
    User-defined valuations in $ per point/mile, per program.
    Example:
      {"bilt": 0.0125, "capital_one": 0.0100}
    """
    by_program: Dict[str, float]

    def value_of(self, program: str, points: float) -> float:
        return float(points) * float(self.by_program.get(program, 0.0))


@dataclass
class ResultBreakdown:
    """
    Per-card breakdown. Cards can generate:
      - points in one or more programs
      - cashback in USD
      - fees in USD
    value_usd should already incorporate: points valuation + cashback - fees
    """
    points_by_program: Dict[str, float]
    cashback_usd: float
    fees_usd: float
    value_usd: float
    notes: str = ""


@dataclass
class Allocation:
    mapping: Dict[Category, str]


@dataclass
class ScenarioTotals:
    points_by_program: Dict[str, float]
    cashback_usd: float
    fees_usd: float
    value_usd: float


@dataclass
class ScenarioResult:
    name: str
    allocation: Allocation
    totals: ScenarioTotals
    details: Dict[str, ResultBreakdown]
