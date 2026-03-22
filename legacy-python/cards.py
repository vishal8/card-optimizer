# PASTE THIS FILE AS-IS
from dataclasses import dataclass, field
from typing import Dict, Optional, Any

from .models import Category, Valuations, ResultBreakdown
from .assumptions import BiltOptionAThresholds, BiltOptionBUnlock

CardName = str


@dataclass(frozen=True)
class Card:
    name: CardName
    annual_fee: float

    def earn_points(
        self,
        spend: Dict[Category, float],
        valuations: Valuations,
        *,
        rent: float = 0.0,
        rent_mode: Optional[str] = None,  # "option_a_tiered" | "option_b_cash_unlock"
        bilt_a: Optional[BiltOptionAThresholds] = None,
        bilt_b: Optional[BiltOptionBUnlock] = None,
        vx_travel_avg_mult: float = 7.5,
    ) -> ResultBreakdown:
        raise NotImplementedError


# -------------------------
# Concrete cards
# -------------------------

@dataclass(frozen=True)
class VentureX(Card):
    other_mult: float = 2.0

    def earn_points(self, spend: Dict[Category, float], valuations: Valuations, **kwargs) -> ResultBreakdown:
        travel_mult = float(kwargs.get("vx_travel_avg_mult", 7.5))

        points = (
            spend.get("dining", 0.0) * self.other_mult
            + spend.get("groceries", 0.0) * self.other_mult
            + spend.get("other", 0.0) * self.other_mult
            + spend.get("travel", 0.0) * travel_mult
        )

        fees = float(self.annual_fee)
        cashback = 0.0
        value = valuations.value_of("capital_one", points) + cashback - fees

        return ResultBreakdown(
            points_by_program={"capital_one": float(points)},
            cashback_usd=float(cashback),
            fees_usd=float(fees),
            value_usd=float(value),
            notes="VX miles valued using your per-program setting; travel uses avg multiplier.",
        )


@dataclass(frozen=True)
class AmazonPrimeVisa(Card):
    grocery_cashback_rate: float = 0.05

    def earn_points(self, spend: Dict[Category, float], valuations: Valuations, **kwargs) -> ResultBreakdown:
        cashback = float(spend.get("groceries", 0.0)) * float(self.grocery_cashback_rate)
        fees = float(self.annual_fee)
        value = cashback - fees

        return ResultBreakdown(
            points_by_program={},
            cashback_usd=float(cashback),
            fees_usd=float(fees),
            value_usd=float(value),
            notes=f"{self.grocery_cashback_rate:.0%} cashback on groceries assumed.",
        )


# -------------------------
# Bilt cards (ALL support rent modeling)
# -------------------------

def _rent_points_option_a(*, rent: float, eligible_spend: float, bilt_a: BiltOptionAThresholds) -> float:
    if rent <= 0:
        return 0.0
    ratio = eligible_spend / rent if rent > 0 else 0.0
    if ratio >= 1.0:
        mult = bilt_a.tier_100_mult
    elif ratio >= 0.75:
        mult = bilt_a.tier_75_mult
    elif ratio >= 0.50:
        mult = bilt_a.tier_50_mult
    elif ratio >= 0.25:
        mult = bilt_a.tier_25_mult
    else:
        mult = 0.0
    return float(rent) * float(mult)


def _rent_points_option_b(*, rent: float, eligible_spend: float, bilt_b: BiltOptionBUnlock) -> float:
    if rent <= 0:
        return 0.0
    bilt_cash = float(eligible_spend) * float(bilt_b.bilt_cash_rate)
    unlockable_rent = min(float(rent), float(bilt_cash) / float(bilt_b.unlock_rate))
    # 1 rent point per $ unlocked rent
    return float(unlockable_rent)


def _bilt_rent_points(*, rent: float, eligible_spend: float, rent_mode: Optional[str], bilt_a, bilt_b) -> (float, str):
    if rent_mode == "option_a_tiered":
        if not bilt_a:
            raise ValueError("bilt_a thresholds required")
        return _rent_points_option_a(rent=rent, eligible_spend=eligible_spend, bilt_a=bilt_a), "Rent via Option A tiers."
    if rent_mode == "option_b_cash_unlock":
        if not bilt_b:
            raise ValueError("bilt_b unlock required")
        return _rent_points_option_b(rent=rent, eligible_spend=eligible_spend, bilt_b=bilt_b), "Rent via Option B cash unlock."
    return 0.0, "Rent not enabled."


@dataclass(frozen=True)
class BiltBlue(Card):
    def earn_points(
        self,
        spend: Dict[Category, float],
        valuations: Valuations,
        *,
        rent: float = 0.0,
        rent_mode: Optional[str] = None,
        bilt_a: Optional[BiltOptionAThresholds] = None,
        bilt_b: Optional[BiltOptionBUnlock] = None,
        **kwargs
    ) -> ResultBreakdown:
        eligible_spend = float(sum(spend.values()))
        base_points = eligible_spend * 1.0  # 1x everywhere

        rent_points, rent_note = _bilt_rent_points(
            rent=float(rent), eligible_spend=eligible_spend, rent_mode=rent_mode, bilt_a=bilt_a, bilt_b=bilt_b
        )

        total_points = float(base_points + rent_points)
        fees = float(self.annual_fee)
        value = valuations.value_of("bilt", total_points) - fees

        return ResultBreakdown(
            points_by_program={"bilt": float(total_points)},
            cashback_usd=0.0,
            fees_usd=float(fees),
            value_usd=float(value),
            notes="Blue: 1x everywhere. " + rent_note,
        )


@dataclass(frozen=True)
class BiltPalladium(Card):
    def earn_points(
        self,
        spend: Dict[Category, float],
        valuations: Valuations,
        *,
        rent: float = 0.0,
        rent_mode: Optional[str] = None,
        bilt_a: Optional[BiltOptionAThresholds] = None,
        bilt_b: Optional[BiltOptionBUnlock] = None,
        **kwargs
    ) -> ResultBreakdown:
        dining = float(spend.get("dining", 0.0))
        groceries = float(spend.get("groceries", 0.0))
        travel = float(spend.get("travel", 0.0))
        other = float(spend.get("other", 0.0))

        eligible_spend = dining + groceries + travel + other
        base_points = eligible_spend * 2.0  # 2x everywhere

        rent_points, rent_note = _bilt_rent_points(
            rent=float(rent), eligible_spend=eligible_spend, rent_mode=rent_mode, bilt_a=bilt_a, bilt_b=bilt_b
        )

        total_points = float(base_points + rent_points)
        fees = float(self.annual_fee)
        value = valuations.value_of("bilt", total_points) - fees

        return ResultBreakdown(
            points_by_program={"bilt": float(total_points)},
            cashback_usd=0.0,
            fees_usd=float(fees),
            value_usd=float(value),
            notes="Palladium: 2x everywhere. " + rent_note,
        )


@dataclass(frozen=True)
class BiltObsidian(Card):
    def earn_points(
        self,
        spend: Dict[Category, float],
        valuations: Valuations,
        *,
        rent: float = 0.0,
        rent_mode: Optional[str] = None,
        bilt_a: Optional[BiltOptionAThresholds] = None,
        bilt_b: Optional[BiltOptionBUnlock] = None,
        **kwargs
    ) -> ResultBreakdown:
        dining = float(spend.get("dining", 0.0))
        groceries = float(spend.get("groceries", 0.0))
        travel = float(spend.get("travel", 0.0))
        other = float(spend.get("other", 0.0))

        eligible_spend = dining + groceries + travel + other

        # Fixed: 3x dining, 2x travel, 1x everything else
        base_points = dining * 3.0 + travel * 2.0 + groceries * 1.0 + other * 1.0

        rent_points, rent_note = _bilt_rent_points(
            rent=float(rent), eligible_spend=eligible_spend, rent_mode=rent_mode, bilt_a=bilt_a, bilt_b=bilt_b
        )

        total_points = float(base_points + rent_points)
        fees = float(self.annual_fee)
        value = valuations.value_of("bilt", total_points) - fees

        return ResultBreakdown(
            points_by_program={"bilt": float(total_points)},
            cashback_usd=0.0,
            fees_usd=float(fees),
            value_usd=float(value),
            notes="Obsidian: 3x dining, 2x travel, 1x other. " + rent_note,
        )


# -------------------------
# CatalogCard (catalog-driven)
# -------------------------

@dataclass(frozen=True)
class CatalogCard(Card):
    """
    Engine-compatible, catalog-driven card.

    - Points programs: multiplier = points per $
    - Cashback: multiplier = 0.02 (2%) OR 2.0 (2%) - normalized
    """
    program: str = "cash_back"
    mult: Dict[str, float] = field(default_factory=dict)
    meta: Dict[str, Any] = field(default_factory=dict)

    def _m(self, key: str) -> float:
        return float(self.mult.get(key, 0.0))

    def _cash_rate(self, key: str) -> float:
        v = float(self.mult.get(key, 0.0))
        return (v / 100.0) if v > 1.0 else v

    def earn_points(self, spend: Dict[Category, float], valuations: Valuations, **kwargs) -> ResultBreakdown:
        dining = float(spend.get("dining", 0.0))
        groceries = float(spend.get("groceries", 0.0))
        travel = float(spend.get("travel", 0.0))
        other = float(spend.get("other", 0.0))

        fees = float(self.annual_fee)

        if self.program == "cash_back":
            cashback = (
                dining * self._cash_rate("dining")
                + groceries * self._cash_rate("groceries")
                + travel * self._cash_rate("travel")
                + other * self._cash_rate("other")
            )
            value = float(cashback) - fees
            return ResultBreakdown(
                points_by_program={},
                cashback_usd=float(cashback),
                fees_usd=float(fees),
                value_usd=float(value),
                notes="Catalog cashback card (simplified).",
            )

        pts = dining * self._m("dining") + groceries * self._m("groceries") + travel * self._m("travel") + other * self._m("other")
        value = valuations.value_of(self.program, float(pts)) - fees

        return ResultBreakdown(
            points_by_program={self.program: float(pts)},
            cashback_usd=0.0,
            fees_usd=float(fees),
            value_usd=float(value),
            notes="Catalog points card (simplified).",
        )
