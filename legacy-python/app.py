from __future__ import annotations

import itertools
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional, Any

import pandas as pd
import streamlit as st


# ============================================================
# Data model
# ============================================================

CATEGORIES = ["dining", "groceries", "flights", "hotels", "other"]

PROGRAM_LABELS = {
    "cash_back": "Cashback ($)",
    "bilt": "Bilt",
    "capital_one": "Capital One",
    "amex_mr": "Amex MR",
    "chase_ur": "Chase UR",
    "citi_ty": "Citi TY",
}

@dataclass(frozen=True)
class Card:
    name: str
    annual_fee: float
    program: str  # "cash_back" or points program key
    mult: Dict[str, float]
    conditions: Optional[Dict[str, Any]] = None


# ============================================================
# Bilt rent modeling (Phase 1 — explicit and configurable)
# ============================================================

@dataclass(frozen=True)
class BiltOptionA:
    """Tiered boost on rent value based on how much *non-rent* spend you route to Bilt."""
    tier_25_mult: float = 0.50
    tier_50_mult: float = 0.75
    tier_75_mult: float = 1.00
    tier_100_mult: float = 1.25

@dataclass(frozen=True)
class BiltOptionB:
    """Unlock rent value up to a cap based on non-rent spend."""
    bilt_cash_rate: float = 0.04   # 4% of rent as max value
    unlock_rate: float = 0.03      # unlock value at 3% of non-rent spend on Bilt

def bilt_rent_value(
    *,
    rent: float,
    non_rent_spend_on_bilt: float,
    bilt_cpp: float,  # e.g., 0.01 means 1cpp
    mode: str,        # "option_a" or "option_b"
    opt_a: BiltOptionA,
    opt_b: BiltOptionB,
) -> Tuple[float, str]:
    """
    Returns (rent_value_usd, explanation).
    This is deliberately transparent and easy to change.

    Option A (tiered):
      - Assume rent earns 1x in points-equivalent.
      - Base rent value = rent * 1 * bilt_cpp
      - Apply tier multiplier based on non_rent_spend_on_bilt / rent:
          <25% -> 0
          25-50% -> tier_25_mult
          50-75% -> tier_50_mult
          75-100% -> tier_75_mult
          >=100% -> tier_100_mult

    Option B (unlock):
      - Max rent value cap = rent * bilt_cash_rate
      - Unlocked value = non_rent_spend_on_bilt * unlock_rate
      - Rent value = min(cap, unlocked)
    """
    rent = float(rent)
    non_rent_spend_on_bilt = float(non_rent_spend_on_bilt)
    bilt_cpp = float(bilt_cpp)

    if rent <= 0:
        return 0.0, "No rent."

    if mode == "option_a":
        ratio = non_rent_spend_on_bilt / rent if rent > 0 else 0.0
        if ratio < 0.25:
            tier_mult = 0.0
            tier_label = "<25% (0×)"
        elif ratio < 0.50:
            tier_mult = opt_a.tier_25_mult
            tier_label = f"25–50% ({tier_mult}×)"
        elif ratio < 0.75:
            tier_mult = opt_a.tier_50_mult
            tier_label = f"50–75% ({tier_mult}×)"
        elif ratio < 1.00:
            tier_mult = opt_a.tier_75_mult
            tier_label = f"75–100% ({tier_mult}×)"
        else:
            tier_mult = opt_a.tier_100_mult
            tier_label = f"≥100% ({tier_mult}×)"

        base = rent * 1.0 * bilt_cpp
        val = base * tier_mult
        exp = f"Option A: base=${base:,.0f} (rent×1×cpp) × tier {tier_label} => ${val:,.0f}"
        return float(val), exp

    if mode == "option_b":
        cap = rent * opt_b.bilt_cash_rate
        unlocked = non_rent_spend_on_bilt * opt_b.unlock_rate
        val = min(cap, unlocked)
        exp = f"Option B: min(cap=${cap:,.0f} (rent×{opt_b.bilt_cash_rate:.0%}), unlocked=${unlocked:,.0f} (nonrent×{opt_b.unlock_rate:.0%})) => ${val:,.0f}"
        return float(val), exp

    return 0.0, "Unknown rent mode."


# ============================================================
# Earning math (single source of truth)
# ============================================================

def value_for_spend(
    *,
    card: Card,
    category: str,
    spend: float,
    cpp_by_program: Dict[str, float],
    has_prime: bool,
    whole_foods_share: float,
    use_travel_portal: bool,
) -> Tuple[float, str, str]:
    spend = float(spend)
    mult = float(card.mult.get(category, 0.0))
    conds = card.conditions or {}

    if card.program == "cash_back":
        # Amazon-specific logic
        if card.name == "Amazon Prime Visa":
            if category == "groceries":
                prime_rate = 5.0 if has_prime else 3.0
                wf_spend = spend * float(whole_foods_share)
                other_grocery_spend = spend - wf_spend

                wf_cash = wf_spend * (prime_rate / 100.0)
                other_cash = other_grocery_spend * (1.0 / 100.0)
                total_cash = wf_cash + other_cash

                return total_cash, f"${total_cash:,.0f}", f"blended grocery"

            if category in ["flights", "hotels"]:
                if use_travel_portal:
                    travel_rate = 5.0 if has_prime else 3.0
                else:
                    travel_rate = 1.0
                cash = spend * (travel_rate / 100.0)
                return cash, f"${cash:,.0f}", f"{travel_rate:g}%"

        cash = spend * (mult / 100.0)
        return float(cash), f"${cash:,.0f}", f"{mult:g}%"

    cpp = float(cpp_by_program.get(card.program, 0.0))
    pts = spend * mult
    usd = pts * cpp
    return float(usd), f"{pts:,.0f} pts", f"{mult:g}×"

# ============================================================
# Catalog (starter set — replace with your full table later)
# IMPORTANT: For cashback cards, multipliers must be % rates (5 means 5%).
# ============================================================

CATALOG: List[Card] = [
    Card("Bilt Blue", 0.0, "bilt", {"dining": 1, "groceries": 1, "flights": 1, "hotels": 1, "other": 1}),
    Card("Bilt Obsidian", 95.0, "bilt", {"dining": 3, "groceries": 1, "flights": 2, "hotels": 2, "other": 1}),
    Card("Bilt Palladium", 495.0, "bilt", {"dining": 2, "groceries": 2, "flights": 2, "hotels": 2, "other": 2}),

    Card("Venture X", 395.0, "capital_one", {"dining": 2, "groceries": 2, "flights": 5, "hotels": 10, "other": 2}),
    Card("Amex Gold", 325.0, "amex_mr", {"dining": 4, "groceries": 4, "flights": 2, "hotels": 3, "other": 1}),
    Card("Amex Platinum", 695.0, "amex_mr", {"dining": 1, "groceries": 1, "flights": 5, "hotels": 5, "other": 1}),

    Card("Chase Sapphire Reserve", 795.0, "chase_ur", {"dining": 3, "groceries": 1, "flights": 8, "hotels": 8, "other": 1}),
    Card("Chase Sapphire Preferred", 95.0, "chase_ur", {"dining": 3, "groceries": 1, "flights": 5, "hotels": 5, "other": 1}),

    Card("Citi Strata Elite", 595.0, "citi_ty", {"dining": 3, "groceries": 1, "flights": 6, "hotels": 12, "other": 1}),

    # Cashback examples — % rates:
    Card("Citi Double Cash", 0.0, "cash_back", {"dining": 2, "groceries": 2, "flights": 2, "hotels": 2, "other": 2}),
    Card(
        "Amazon Prime Visa",
        0.0,
        "cash_back",
        {
            "dining": 2,
            "groceries": 5,   # but conditional
            "flights": 5,     # but portal only
            "hotels": 5,      # but portal only
            "other": 1,
        },
        conditions={
            "requires_prime": True,
            "portal_required_for_travel": True,
            "limited_grocery_scope": True,
        }
)
]

CATALOG_BY_NAME = {c.name: c for c in CATALOG}
BILT_NAMES = {"Bilt Blue", "Bilt Obsidian", "Bilt Palladium"}


# ============================================================
# Optimizer
# ============================================================

def evaluate_assignment(
    *,
    assignment: Dict[str, str],
    selected: Dict[str, Card],
    spend: Dict[str, float],
    cpp_by_program: Dict[str, float],
    rent: float,
    rent_mode: str,
    opt_a: BiltOptionA,
    opt_b: BiltOptionB,
    has_prime: bool,
    whole_foods_share: float,
    use_travel_portal: bool,
) -> Dict:
    used_cards = sorted(set(assignment.values()))
    core_value = 0.0
    rows = []

    # compute non-rent spend on bilt (needed for rent modeling)
    non_rent_on_bilt = 0.0

    for cat in CATEGORIES:
        card_name = assignment[cat]
        card = selected[card_name]
        v, earned_disp, mult_disp = value_for_spend(
        card=card,
        category=cat,
        spend=spend[cat],
        cpp_by_program=cpp_by_program,
        has_prime=has_prime,
        whole_foods_share=whole_foods_share,
        use_travel_portal=use_travel_portal,
    )
        core_value += v
        if card_name in BILT_NAMES:
            non_rent_on_bilt += float(spend[cat])

        rows.append({
            "Category": cat,
            "Spend": spend[cat],
            "Card": card_name,
            "Program": PROGRAM_LABELS.get(card.program, card.program),
            "Rate": mult_disp,
            "Earned": earned_disp,
            "Value ($)": v,
        })

    # fees
    fees = sum(float(selected[n].annual_fee) for n in used_cards)

    # rent value (only if any bilt card used)
    rent_value = 0.0
    rent_explain = "No Bilt used."
    chosen_rent_mode = "—"

    bilt_cpp = float(cpp_by_program.get("bilt", 0.0))
    if rent > 0 and any(n in BILT_NAMES for n in used_cards):
        if rent_mode == "auto":
            v_a, exp_a = bilt_rent_value(rent=rent, non_rent_spend_on_bilt=non_rent_on_bilt, bilt_cpp=bilt_cpp, mode="option_a", opt_a=opt_a, opt_b=opt_b)
            v_b, exp_b = bilt_rent_value(rent=rent, non_rent_spend_on_bilt=non_rent_on_bilt, bilt_cpp=bilt_cpp, mode="option_b", opt_a=opt_a, opt_b=opt_b)
            if v_a >= v_b:
                rent_value, rent_explain, chosen_rent_mode = v_a, exp_a, "Option A"
            else:
                rent_value, rent_explain, chosen_rent_mode = v_b, exp_b, "Option B"
        elif rent_mode == "option_a":
            rent_value, rent_explain = bilt_rent_value(rent=rent, non_rent_spend_on_bilt=non_rent_on_bilt, bilt_cpp=bilt_cpp, mode="option_a", opt_a=opt_a, opt_b=opt_b)
            chosen_rent_mode = "Option A"
        else:
            rent_value, rent_explain = bilt_rent_value(rent=rent, non_rent_spend_on_bilt=non_rent_on_bilt, bilt_cpp=bilt_cpp, mode="option_b", opt_a=opt_a, opt_b=opt_b)
            chosen_rent_mode = "Option B"

    total = core_value + rent_value - fees

    return {
        "assignment": dict(assignment),
        "used_cards": used_cards,
        "core_value": float(core_value),
        "rent_value": float(rent_value),
        "fees": float(fees),
        "total_value": float(total),
        "rent_mode_used": chosen_rent_mode,
        "rent_explain": rent_explain,
        "non_rent_on_bilt": float(non_rent_on_bilt),
        "rows": rows,
    }


def best_combos(
    *,
    selected_cards: Dict[str, Card],
    spend: Dict[str, float],
    cpp_by_program: Dict[str, float],
    rent: float,
    rent_mode: str,
    opt_a: BiltOptionA,
    opt_b: BiltOptionB,
    max_cards_allowed: int,
    has_prime: bool,
    whole_foods_share: float,
    use_travel_portal: bool,
    top_k: int = 10,
) -> List[Dict]:
    names = list(selected_cards.keys())
    raw_results = []

    for combo in itertools.product(names, repeat=len(CATEGORIES)):
        assignment = dict(zip(CATEGORIES, combo))
        used = set(combo)
        if len(used) > max_cards_allowed:
            continue

        res = evaluate_assignment(
            assignment=assignment,
            selected=selected_cards,
            spend=spend,
            cpp_by_program=cpp_by_program,
            rent=rent,
            rent_mode=rent_mode,
            opt_a=opt_a,
            opt_b=opt_b,
            has_prime=has_prime,
            whole_foods_share=whole_foods_share,
            use_travel_portal=use_travel_portal,
        )
        raw_results.append(res)

    raw_results.sort(
        key=lambda x: (x["total_value"], -len(x["used_cards"])),
        reverse=True,
    )

    deduped = []
    seen = set()

    for r in raw_results:
        key = (
            tuple(sorted(r["used_cards"])),
            tuple((cat, r["assignment"][cat]) for cat in CATEGORIES),
            round(r["total_value"], 6),
            r["rent_mode_used"],
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(r)

        if len(deduped) >= top_k:
            break

    return deduped


# ============================================================
# UI
# ============================================================

st.set_page_config(page_title="Card Optimizer (Fresh)", layout="wide")
st.title("Credit Card Optimizer — Fresh Build")

with st.sidebar:
    st.header("Card selection")
    all_names = [c.name for c in CATALOG]
    chosen_names = st.multiselect("Cards to include", all_names, default=["Bilt Obsidian", "Venture X", "Amex Gold", "Amazon Prime Visa"])
    has_prime = st.checkbox("I have Amazon Prime", value=True)
    whole_foods_share = st.slider("Share of grocery spend at Whole Foods / Amazon", 0.0, 1.0, 0.25)
    use_travel_portal = st.checkbox("I book travel through portal when required", value=False)

    st.header("Spend (annual)")
    rent = st.number_input("Rent ($/yr)", min_value=0.0, value=60000.0, step=1000.0)
    dining = st.number_input("Dining ($/yr)", min_value=0.0, value=9000.0, step=500.0)
    groceries = st.number_input("Groceries ($/yr)", min_value=0.0, value=4000.0, step=500.0)
    flights = st.number_input("Flights ($/yr)", min_value=0.0, value=3000.0, step=500.0)
    hotels = st.number_input("Hotels ($/yr)", min_value=0.0, value=5000.0, step=500.0)
    other = st.number_input("Other ($/yr)", min_value=0.0, value=7000.0, step=500.0)

    st.header("Point values (cpp)")
    # cpp inputs are dollars per point (e.g. 1.0 cpp -> 0.01)
    bilt_cpp = st.number_input("Bilt (cpp)", value=1.0, step=0.1) / 100.0
    cap1_cpp = st.number_input("Capital One (cpp)", value=1.0, step=0.1) / 100.0
    amex_cpp = st.number_input("Amex MR (cpp)", value=1.2, step=0.1) / 100.0
    chase_cpp = st.number_input("Chase UR (cpp)", value=1.25, step=0.05) / 100.0
    citi_cpp = st.number_input("Citi TY (cpp)", value=1.1, step=0.1) / 100.0

    cpp_by_program = {
        "cash_back": 1.0,  # not used for cash_back valuation; cash is cash
        "bilt": float(bilt_cpp),
        "capital_one": float(cap1_cpp),
        "amex_mr": float(amex_cpp),
        "chase_ur": float(chase_cpp),
        "citi_ty": float(citi_cpp),
    }

    st.header("Optimizer constraints")
    max_cards_allowed = st.slider("Max cards allowed", min_value=1, max_value=6, value=3)

    st.header("Rent mode (Bilt)")
    rent_mode = st.radio("Mode", ["auto", "option_a", "option_b"], index=0, horizontal=True)

    with st.expander("Bilt Option A tiers"):
        a25 = st.number_input("tier_25_mult", value=0.50, step=0.05)
        a50 = st.number_input("tier_50_mult", value=0.75, step=0.05)
        a75 = st.number_input("tier_75_mult", value=1.00, step=0.05)
        a100 = st.number_input("tier_100_mult", value=1.25, step=0.05)
        opt_a = BiltOptionA(a25, a50, a75, a100)

    with st.expander("Bilt Option B unlock"):
        bcr = st.number_input("bilt_cash_rate", value=0.04, step=0.01, format="%.2f")
        ur = st.number_input("unlock_rate", value=0.03, step=0.01, format="%.2f")
        opt_b = BiltOptionB(bcr, ur)

spend = {
    "dining": float(dining),
    "groceries": float(groceries),
    "flights": float(flights),
    "hotels": float(hotels),
    "other": float(other),
}

if not chosen_names:
    st.info("Select at least one card.")
    st.stop()

selected_cards = {n: CATALOG_BY_NAME[n] for n in chosen_names if n in CATALOG_BY_NAME}
if not selected_cards:
    st.error("No valid cards selected.")
    st.stop()

# -------------------------
# Optimizer
# -------------------------
st.subheader("Optimizer result")

with st.spinner("Searching best combinations..."):
    top = best_combos(
        selected_cards=selected_cards,
        spend=spend,
        cpp_by_program=cpp_by_program,
        rent=float(rent),
        rent_mode=str(rent_mode),
        opt_a=opt_a,
        opt_b=opt_b,
        max_cards_allowed=int(max_cards_allowed),
        has_prime=has_prime,
        whole_foods_share=whole_foods_share,
        use_travel_portal=use_travel_portal,
        top_k=10,
    )

best = top[0]
best_core = max(top, key=lambda x: x["core_value"])

st.info(
    f"Best core-spend combo (ignoring rent and fees): "
    f"{', '.join(best_core['used_cards'])} — ${best_core['core_value']:,.0f}/yr"
)
st.success(
    f"Best combo uses {len(best['used_cards'])} card(s): "
    f"**{', '.join(best['used_cards'])}** — "
    f"**${best['total_value']:,.0f}/yr net of rent + fees**"
)

c1, c2 = st.columns([2, 1])
with c1:
    df_best = pd.DataFrame(best["rows"]).copy()
    total_spend_categories = sum(spend.values())

    df_best["Spend"] = df_best["Spend"].map(lambda x: f"${x:,.0f}")
    df_best["Value ($)"] = df_best["Value ($)"].map(lambda x: f"${x:,.0f}")

    summary_rows = pd.DataFrame([
        {
            "Category": "TOTAL (spend categories)",
            "Spend": f"${total_spend_categories:,.0f}",
            "Card": "—",
            "Program": "—",
            "Rate": "—",
            "Earned": "—",
            "Value ($)": f"${best['core_value']:,.0f}",
        },
        {
            "Category": "Rent",
            "Spend": f"${rent:,.0f}",
            "Card": "Bilt" if best["rent_value"] > 0 else "—",
            "Program": "Bilt" if best["rent_value"] > 0 else "—",
            "Rate": best["rent_mode_used"] if best["rent_value"] > 0 else "—",
            "Earned": "—",
            "Value ($)": f"${best['rent_value']:,.0f}",
        },
        {
            "Category": "Fees",
            "Spend": "—",
            "Card": ", ".join(best["used_cards"]),
            "Program": "—",
            "Rate": "—",
            "Earned": "—",
            "Value ($)": f"-${best['fees']:,.0f}",
        },
        {
            "Category": "TOTAL NET",
            "Spend": "—",
            "Card": "—",
            "Program": "—",
            "Rate": "—",
            "Earned": "—",
            "Value ($)": f"${best['total_value']:,.0f}",
        },
    ])

    df_best = pd.concat([df_best, summary_rows], ignore_index=True)
    st.dataframe(df_best, use_container_width=True, hide_index=True)

with c2:
    st.markdown("**Allocation**")
    st.json(best["assignment"])
    st.markdown("**Totals**")
    st.write(f"Core value: ${best['core_value']:,.0f}")
    st.write(f"Rent value: ${best['rent_value']:,.0f} ({best['rent_mode_used']})")
    st.caption(best["rent_explain"])
    st.write(f"Fees: -${best['fees']:,.0f}")
    st.write(f"**Net: ${best['total_value']:,.0f}**")
    if best["non_rent_on_bilt"] > 0:
        st.caption(f"Non-rent spend routed to Bilt: ${best['non_rent_on_bilt']:,.0f}")

st.divider()
st.subheader("Top contenders")

seen = set()
contenders = []

for r in top:
    key = (
        round(r["total_value"], 2),
        tuple(sorted(r["used_cards"])),
        r["rent_mode_used"],
        r["assignment"]["dining"],
        r["assignment"]["groceries"],
        r["assignment"]["flights"],
        r["assignment"]["hotels"],
        r["assignment"]["other"],
    )
    if key in seen:
        continue
    seen.add(key)

    contenders.append({
        "Net value ($/yr)": round(r["total_value"], 2),
        "Cards used": ", ".join(r["used_cards"]),
        "Rent mode": r["rent_mode_used"],
        "Dining": r["assignment"]["dining"],
        "Groceries": r["assignment"]["groceries"],
        "Flights": r["assignment"]["flights"],
        "Hotels": r["assignment"]["hotels"],
        "Other": r["assignment"]["other"],
    })

contenders_df = pd.DataFrame(contenders).head(10)
st.dataframe(contenders_df, use_container_width=True, hide_index=True)

# -------------------------
# Comparator
# -------------------------
st.divider()
st.subheader("Comparator (single-card vs single-card)")

choices = list(selected_cards.keys())
colA, colB = st.columns(2)
with colA:
    a_name = st.selectbox("Card A", choices, index=0, key="cmp_a")
with colB:
    b_name = st.selectbox("Card B", choices, index=min(1, len(choices) - 1), key="cmp_b")

def single_card_breakdown(card: Card) -> Tuple[pd.DataFrame, float, str]:
    rows = []
    total_core = 0.0
    non_rent_on_bilt = 0.0

    for cat in CATEGORIES:
        v, earned_disp, mult_disp = value_for_spend(
            card=card,
            category=cat,
            spend=spend[cat],
            cpp_by_program=cpp_by_program,
            has_prime=has_prime,
            whole_foods_share=whole_foods_share,
            use_travel_portal=use_travel_portal,
)
        total_core += v
        if card.name in BILT_NAMES:
            non_rent_on_bilt += float(spend[cat])

        rows.append({
            "Category": cat,
            "Spend": f"${spend[cat]:,.0f}",
            "Rate": mult_disp,
            "Earned": earned_disp,
            "Value ($)": f"${v:,.0f}",
        })

    rent_v = 0.0
    rent_exp = "No Bilt used."
    rent_a = 0.0
    rent_b = 0.0

    if float(rent) > 0 and card.name in BILT_NAMES:
        rent_a, exp_a = bilt_rent_value(
            rent=rent,
            non_rent_spend_on_bilt=non_rent_on_bilt,
            bilt_cpp=cpp_by_program["bilt"],
            mode="option_a",
            opt_a=opt_a,
            opt_b=opt_b,
        )
        rent_b, exp_b = bilt_rent_value(
            rent=rent,
            non_rent_spend_on_bilt=non_rent_on_bilt,
            bilt_cpp=cpp_by_program["bilt"],
            mode="option_b",
            opt_a=opt_a,
            opt_b=opt_b,
        )

        if rent_mode == "auto":
            if rent_a >= rent_b:
                rent_v, rent_exp = rent_a, exp_a
            else:
                rent_v, rent_exp = rent_b, exp_b
        elif rent_mode == "option_a":
            rent_v, rent_exp = rent_a, exp_a
        else:
            rent_v, rent_exp = rent_b, exp_b

        rows.append({
            "Category": "Rent (Option A)",
            "Spend": f"${rent:,.0f}",
            "Rate": "engine-modeled",
            "Earned": "—",
            "Value ($)": f"${rent_a:,.0f}",
        })
        rows.append({
            "Category": "Rent (Option B)",
            "Spend": f"${rent:,.0f}",
            "Rate": "engine-modeled",
            "Earned": "—",
            "Value ($)": f"${rent_b:,.0f}",
        })
        rows.append({
            "Category": "Rent (Used)",
            "Spend": f"${rent:,.0f}",
            "Rate": rent_mode if rent_mode != "auto" else ("Option A" if rent_a >= rent_b else "Option B"),
            "Earned": "—",
            "Value ($)": f"${rent_v:,.0f}",
        })

    fee = float(card.annual_fee)
    net = float(total_core + rent_v - fee)

    rows.append({
        "Category": "Fee",
        "Spend": "—",
        "Rate": "—",
        "Earned": "—",
        "Value ($)": f"-${fee:,.0f}",
    })
    rows.append({
        "Category": "TOTAL NET",
        "Spend": "—",
        "Rate": "—",
        "Earned": "—",
        "Value ($)": f"${net:,.0f}",
    })

    meta = (
        f"Core=${total_core:,.0f} | Rent A=${rent_a:,.0f} | Rent B=${rent_b:,.0f} | "
        f"Used=${rent_v:,.0f} | Fee=${fee:,.0f} | Net=${net:,.0f}\n"
        f"{rent_exp}"
    )
    return pd.DataFrame(rows), net, meta

a_df, a_net, a_meta = single_card_breakdown(selected_cards[a_name])
b_df, b_net, b_meta = single_card_breakdown(selected_cards[b_name])

c1, c2 = st.columns(2)
with c1:
    st.markdown(f"### A — {a_name}")
    st.dataframe(a_df, use_container_width=True, hide_index=True)
    st.caption(a_meta)

with c2:
    st.markdown(f"### B — {b_name}")
    st.dataframe(b_df, use_container_width=True, hide_index=True)
    st.caption(b_meta)

delta = b_net - a_net
if abs(delta) < 1e-9:
    st.info("Tie: both cards have the same net annual value in the single-card scenario.")
else:
    winner = b_name if delta > 0 else a_name
    st.success(f"Winner: **{winner}** by **${abs(delta):,.0f}/yr** (single-card scenario)")
