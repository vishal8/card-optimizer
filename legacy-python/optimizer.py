# PASTE THIS FILE AS-IS
import itertools
from typing import Dict, List

from .models import Allocation, Category, ScenarioResult, Valuations, ScenarioTotals
from .cards import Card
from .assumptions import BiltOptionAThresholds, BiltOptionBUnlock

CATEGORIES: List[Category] = ["dining", "groceries", "travel", "other"]


def evaluate_allocation(
    *,
    allocation: Allocation,
    cards: Dict[str, Card],
    spend: Dict[Category, float],
    rent: float,
    valuations: Valuations,
    rent_mode: str,
    bilt_a: BiltOptionAThresholds,
    bilt_b: BiltOptionBUnlock,
    vx_travel_avg_mult: float,
) -> ScenarioResult:
    # compute per-card spend buckets
    per_card_spend: Dict[str, Dict[Category, float]] = {
        name: {c: 0.0 for c in CATEGORIES} for name in cards.keys()
    }
    for cat, card_name in allocation.mapping.items():
        per_card_spend[card_name][cat] += float(spend.get(cat, 0.0))

    details = {}
    points_totals: Dict[str, float] = {}
    total_cashback = 0.0
    total_fees = 0.0
    total_value = 0.0

    for card_name, card in cards.items():
        rb = card.earn_points(
            per_card_spend[card_name],
            valuations,
            rent=rent,
            rent_mode=rent_mode,
            bilt_a=bilt_a,
            bilt_b=bilt_b,
            vx_travel_avg_mult=vx_travel_avg_mult,
        )
        details[card_name] = rb
        total_cashback += float(rb.cashback_usd)
        total_fees += float(rb.fees_usd)
        total_value += float(rb.value_usd)

        for prog, pts in rb.points_by_program.items():
            points_totals[prog] = points_totals.get(prog, 0.0) + float(pts)

    totals = ScenarioTotals(
        points_by_program=points_totals,
        cashback_usd=total_cashback,
        fees_usd=total_fees,
        value_usd=total_value,
    )

    return ScenarioResult(
        name="",
        allocation=allocation,
        totals=totals,
        details=details,
    )


def best_combo(
    *,
    card_universe: Dict[str, Card],
    spend: Dict[Category, float],
    rent: float,
    valuations: Valuations,
    rent_mode: str,
    bilt_a: BiltOptionAThresholds,
    bilt_b: BiltOptionBUnlock,
    vx_travel_avg_mult: float,
    max_cards: int = 3,
) -> List[ScenarioResult]:
    """
    Searches over:
      - choosing up to max_cards cards
      - allocating each category to one chosen card
    Returns top results (sorted by totals.value_usd).
    """
    results: List[ScenarioResult] = []

    all_card_names = list(card_universe.keys())
    for k in range(1, max_cards + 1):
        for chosen in itertools.combinations(all_card_names, k):
            chosen_cards = {name: card_universe[name] for name in chosen}

            # allocate each category to one of the chosen cards
            for assignment in itertools.product(chosen, repeat=len(CATEGORIES)):
                mapping = {cat: assignment[i] for i, cat in enumerate(CATEGORIES)}
                alloc = Allocation(mapping=mapping)

                r = evaluate_allocation(
                    allocation=alloc,
                    cards=chosen_cards,
                    spend=spend,
                    rent=rent,
                    valuations=valuations,
                    rent_mode=rent_mode,
                    bilt_a=bilt_a,
                    bilt_b=bilt_b,
                    vx_travel_avg_mult=vx_travel_avg_mult,
                )

                results.append(
                    ScenarioResult(
                        name=f"{k}-card: " + " + ".join(chosen),
                        allocation=r.allocation,
                        totals=r.totals,
                        details=r.details,
                    )
                )

    results.sort(key=lambda x: x.totals.value_usd, reverse=True)
    return results
