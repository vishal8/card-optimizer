# PASTE THIS FILE AS-IS
from typing import Dict, Any
from .specs import CardSpec

from engine.cards import VentureX, AmazonPrimeVisa, BiltBlue, BiltObsidian, GenericCard
# NOTE:
# For now we implement new catalog cards using a tiny “Generic” adapter pattern:
# - We reuse your existing engine.cards where available.
# - For new cards we treat them as “points cards” where evaluate_allocation can still work
#   IF your engine cards support (name, annual_fee, other_mult) style.
#
# If your engine currently requires specific classes per card, we’ll add those classes in Batch B.
#
# Minimal-touch choice: keep factory returning only known classes for now, and
# treat new cards as “VentureX-like earn card” using other_mult as baseline and rely on allocation mapping.
#
# If you want accurate per-category multipliers for new cards in Phase-1, we’ll add
# a GenericCard class in engine/cards.py in Batch B (one small file change).

def make_engine_card(
    spec: CardSpec,
    *,
    user_inputs: Dict[str, Any],
) :
    """
    Returns an engine Card object.

    user_inputs includes:
      - vx (assumptions object)
      - amazon (assumptions object)
      - obs_bonus, obs_af, blue_af
      - etc
    """
    name = spec.name

    # Existing cards: use your real classes
    if name == "Venture X":
        vx = user_inputs["vx"]
        return VentureX(name="Venture X", annual_fee=float(vx.annual_fee), other_mult=float(vx.other_mult))

    if name == "Amazon Prime Visa":
        amazon = user_inputs["amazon"]
        return AmazonPrimeVisa(
            name="Amazon Prime Visa",
            annual_fee=0.0,
            grocery_cashback_rate=float(amazon.grocery_cashback_rate),
        )

    if name == "Bilt Blue":
        blue_af = float(user_inputs["blue_af"])
        return BiltBlue(name="Bilt Blue", annual_fee=blue_af)

    if name == "Bilt Obsidian":
        obs_af = float(user_inputs["obs_af"])
        obs_bonus = user_inputs["obs_bonus"]
        return BiltObsidian(name="Bilt Obsidian", annual_fee=obs_af, bonus_category=obs_bonus)

    # Phase-1 minimal touch:
    # Until we add GenericCard support, we can’t fully model new cards in engine.
    # So we intentionally throw a clear error if a new card is selected,
    # which forces Batch B to add GenericCard.
    # New catalog cards: handled by GenericCard
    return GenericCard(
        name=spec.name,
        program=spec.program,
        annual_fee=float(spec.annual_fee),
        mult=dict(spec.mult),
        meta=dict(spec.meta or {}),
    )
