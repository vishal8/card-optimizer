# PASTE THIS FILE AS-IS
# engine/catalog/registry.py

from __future__ import annotations

from typing import List
from engine.cards import CatalogCard

# NOTE:
# - Multipliers below come from your table (points vs cashback split).
# - For cards with different multipliers for flights vs hotels, we store both in `meta`
#   and the app computes an **effective travel multiplier** from your spend mix.
# - No portals / lounge / partner perks are modeled in Phase 1.

def get_catalog() -> List[CatalogCard]:
    cards: List[CatalogCard] = []

    # -------------------------
    # Bilt (points)
    # -------------------------
    cards.append(
        CatalogCard(
            name="Bilt Blue",
            annual_fee=0.0,
            program="bilt",
            mult={"dining": 1.0, "groceries": 1.0, "travel": 1.0, "other": 1.0},
            meta={"flights_mult": 1.0, "hotels_mult": 1.0, "rent_mult": 1.0},
        )
    )
    cards.append(
        CatalogCard(
            name="Bilt Obsidian",
            annual_fee=95.0,
            program="bilt",
            mult={"dining": 3.0, "groceries": 1.0, "travel": 2.0, "other": 1.0},
            meta={"flights_mult": 2.0, "hotels_mult": 2.0, "rent_mult": 1.0},
        )
    )
    cards.append(
        CatalogCard(
            name="Bilt Palladium",
            annual_fee=495.0,
            program="bilt",
            mult={"dining": 2.0, "groceries": 2.0, "travel": 2.0, "other": 2.0},
            meta={"flights_mult": 2.0, "hotels_mult": 2.0, "rent_mult": 1.0},
        )
    )

    # -------------------------
    # Capital One (points)
    # -------------------------
    cards.append(
        CatalogCard(
            name="Venture X",
            annual_fee=395.0,
            program="capital_one",
            mult={"dining": 2.0, "groceries": 2.0, "travel": 2.0, "other": 2.0},
            meta={"flights_mult": 5.0, "hotels_mult": 10.0, "rent_mult": 0.0},
        )
    )

    # -------------------------
    # Amex (points)
    # -------------------------
    cards.append(
        CatalogCard(
            name="Amex Gold",
            annual_fee=325.0,
            program="amex_mr",
            mult={"dining": 4.0, "groceries": 4.0, "travel": 2.0, "other": 1.0},
            meta={"flights_mult": 2.0, "hotels_mult": 3.0, "rent_mult": 0.0},
        )
    )
    cards.append(
        CatalogCard(
            name="Amex Platinum",
            annual_fee=695.0,
            program="amex_mr",
            mult={"dining": 1.0, "groceries": 1.0, "travel": 5.0, "other": 1.0},
            meta={"flights_mult": 5.0, "hotels_mult": 5.0, "rent_mult": 0.0},
        )
    )

    # -------------------------
    # Chase (points)
    # -------------------------
    cards.append(
        CatalogCard(
            name="Chase Sapphire Reserve",
            annual_fee=795.0,
            program="chase_ur",
            mult={"dining": 3.0, "groceries": 1.0, "travel": 8.0, "other": 1.0},
            meta={"flights_mult": 8.0, "hotels_mult": 8.0, "rent_mult": 0.0},
        )
    )
    cards.append(
        CatalogCard(
            name="Chase Sapphire Preferred",
            annual_fee=95.0,
            program="chase_ur",
            mult={"dining": 3.0, "groceries": 1.0, "travel": 5.0, "other": 1.0},
            meta={"flights_mult": 5.0, "hotels_mult": 5.0, "rent_mult": 0.0},
        )
    )

    # -------------------------
    # Citi (points)
    # -------------------------
    cards.append(
        CatalogCard(
            name="Citi Strata Elite",
            annual_fee=595.0,
            program="citi_ty",
            mult={"dining": 3.0, "groceries": 1.0, "travel": 6.0, "other": 1.0},
            meta={"flights_mult": 6.0, "hotels_mult": 12.0, "rent_mult": 0.0},
        )
    )

    # -------------------------
    # Points-style travel rewards treated as points (valued via your 'cashback' valuation)
    # -------------------------
    cards.append(
        CatalogCard(
            name="Bank of America® Travel Rewards",
            annual_fee=0.0,
            program="cash_back",
            mult={"dining": 1.5, "groceries": 1.5, "travel": 1.5, "other": 1.5},
            meta={"flights_mult": 1.5, "hotels_mult": 1.5, "rent_mult": 0.0},
        )
    )

    # -------------------------
    # Cashback (encode % as points-per-$ where 1 pt = $0.01 because cash_back valuation defaults to 1.0¢)
    #   - 2% everywhere -> mult=2.0
    #   - 5% category -> mult=5.0
    # -------------------------
    cards.append(
        CatalogCard(
            name="Citi Double Cash",
            annual_fee=0.0,
            program="cash_back",
            mult={"dining": 2.0, "groceries": 2.0, "travel": 2.0, "other": 2.0},
            meta={"flights_mult": 2.0, "hotels_mult": 2.0, "rent_mult": 0.0},
        )
    )
    cards.append(
        CatalogCard(
            name="Amazon Prime Visa",
            annual_fee=0.0,
            program="cash_back",
            mult={"dining": 2.0, "groceries": 5.0, "travel": 5.0, "other": 1.0},
            meta={"flights_mult": 5.0, "hotels_mult": 5.0, "rent_mult": 0.0},
        )
    )

    return cards

