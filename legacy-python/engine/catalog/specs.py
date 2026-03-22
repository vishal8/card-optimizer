# PASTE THIS FILE AS-IS
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any


@dataclass(frozen=True)
class CardSpec:
    id: str
    name: str
    issuer: str
    program: str  # e.g. "capital_one", "chase_ur", "amex_mr", "citi_ty", "cash_back", "bilt"
    annual_fee: float

    # Multipliers by category: dining, groceries, travel, other, rent
    mult: Dict[str, float] = field(default_factory=dict)

    # Optional: hard caps or behavioral constraints (we’ll use later)
    meta: Dict[str, Any] = field(default_factory=dict)

    # Tags for UX filtering later
    tags: List[str] = field(default_factory=list)


def default_catalog() -> List[CardSpec]:
    """
    Phase-1 catalog = 4 existing + 10 new + Palladium.
    Modeling is intentionally simple: category multipliers + annual fee.
    Credits, caps, and promo rules can be added in Batch B.
    """
    C = []

    # --- Existing cards (already in your system) ---
    C += [
        CardSpec(
            id="venture_x",
            name="Venture X",
            issuer="Capital One",
            program="capital_one",
            annual_fee=395.0,
            mult={"dining": 2.0, "groceries": 2.0, "travel": 2.0, "other": 2.0, "rent": 0.0},
            tags=["baseline", "travel", "premium"],
        ),
        CardSpec(
            id="amazon_prime_visa",
            name="Amazon Prime Visa",
            issuer="Chase",
            program="cash_back",
            annual_fee=0.0,
            # We'll keep groceries rate driven by your existing AmazonPrimeAssumptions in factory
            mult={"dining": 0.0, "groceries": 0.0, "travel": 0.0, "other": 0.0, "rent": 0.0},
            meta={"uses_amazon_assumption": True},
            tags=["groceries", "cashback"],
        ),
        CardSpec(
            id="bilt_blue",
            name="Bilt Blue",
            issuer="Bilt",
            program="bilt",
            annual_fee=0.0,
            mult={"dining": 3.0, "groceries": 2.0, "travel": 2.0, "other": 1.0, "rent": 1.0},
            tags=["rent", "points"],
        ),
        CardSpec(
            id="bilt_obsidian",
            name="Bilt Obsidian",
            issuer="Bilt",
            program="bilt",
            annual_fee=95.0,
            mult={"dining": 3.0, "groceries": 2.0, "travel": 2.0, "other": 1.0, "rent": 1.0},
            meta={"bonus_category_ui": True},  # you already have obs_bonus UI
            tags=["rent", "points"],
        ),
    ]

    # --- Chase (3) ---
    C += [
        CardSpec(
            id="csp",
            name="Chase Sapphire Preferred (CSP)",
            issuer="Chase",
            program="chase_ur",
            annual_fee=95.0,
            mult={"dining": 3.0, "groceries": 1.0, "travel": 2.0, "other": 1.0, "rent": 0.0},
            tags=["travel", "points"],
        ),
        CardSpec(
            id="csr",
            name="Chase Sapphire Reserve (CSR)",
            issuer="Chase",
            program="chase_ur",
            annual_fee=550.0,
            mult={"dining": 3.0, "groceries": 1.0, "travel": 3.0, "other": 1.0, "rent": 0.0},
            tags=["travel", "premium", "points"],
        ),
        CardSpec(
            id="cfu",
            name="Chase Freedom Unlimited (CFU)",
            issuer="Chase",
            program="chase_ur",
            annual_fee=0.0,
            mult={"dining": 3.0, "groceries": 1.5, "travel": 1.5, "other": 1.5, "rent": 0.0},
            tags=["baseline", "points"],
        ),
    ]

    # --- Amex (3) ---
    C += [
        CardSpec(
            id="amex_gold",
            name="Amex Gold",
            issuer="Amex",
            program="amex_mr",
            annual_fee=250.0,
            mult={"dining": 4.0, "groceries": 4.0, "travel": 3.0, "other": 1.0, "rent": 0.0},
            tags=["groceries", "dining", "points"],
        ),
        CardSpec(
            id="amex_platinum",
            name="Amex Platinum",
            issuer="Amex",
            program="amex_mr",
            annual_fee=695.0,
            mult={"dining": 1.0, "groceries": 1.0, "travel": 5.0, "other": 1.0, "rent": 0.0},
            meta={"portal_like": True},
            tags=["travel", "premium", "points"],
        ),
        CardSpec(
            id="amex_bcp",
            name="Amex Blue Cash Preferred (BCP)",
            issuer="Amex",
            program="cash_back",
            annual_fee=95.0,
            mult={"dining": 1.0, "groceries": 6.0, "travel": 1.0, "other": 1.0, "rent": 0.0},
            tags=["groceries", "cashback"],
        ),
    ]

    # --- Citi (3) ---
    C += [
        CardSpec(
            id="citi_double_cash",
            name="Citi Double Cash",
            issuer="Citi",
            program="cash_back",
            annual_fee=0.0,
            mult={"dining": 2.0, "groceries": 2.0, "travel": 2.0, "other": 2.0, "rent": 0.0},
            tags=["baseline", "cashback"],
        ),
        CardSpec(
            id="citi_custom_cash",
            name="Citi Custom Cash",
            issuer="Citi",
            program="cash_back",
            annual_fee=0.0,
            # We’ll treat as 5x for chosen category later (Batch B); for now 3/3/3 simple
            mult={"dining": 3.0, "groceries": 3.0, "travel": 3.0, "other": 1.0, "rent": 0.0},
            meta={"top_category_logic_later": True},
            tags=["cashback"],
        ),
        CardSpec(
            id="citi_premier",
            name="Citi Premier",
            issuer="Citi",
            program="citi_ty",
            annual_fee=95.0,
            mult={"dining": 3.0, "groceries": 3.0, "travel": 3.0, "other": 1.0, "rent": 0.0},
            tags=["travel", "points"],
        ),
    ]

    # --- Bilt Premium ---
    C += [
        CardSpec(
            id="bilt_palladium",
            name="Bilt Palladium",
            issuer="Bilt",
            program="bilt",
            annual_fee=0.0,
            mult={"dining": 3.0, "groceries": 2.0, "travel": 2.0, "other": 1.0, "rent": 1.0},
            meta={"promo_aware": True, "restricted_use": True},
            tags=["rent", "promo", "points"],
        )
    ]

    return C
