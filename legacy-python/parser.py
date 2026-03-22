# PASTE THIS FILE AS-IS
# engine/parser.py
from __future__ import annotations

import re
from typing import Dict

import pandas as pd

from .models import Category

# --- Optional keyword-based fallback rules (used if Category is blank/unknown) ---
DEFAULT_CATEGORY_RULES = [
    ("dining", re.compile(r"\b(restaurant|cafe|coffee|grubhub|doordash|uber eats|ubereats|seamless)\b", re.I)),
    ("groceries", re.compile(r"\b(whole foods|wholefoods|trader joe|trader joes|kroger|aldi|costco|wegmans)\b", re.I)),
    ("travel", re.compile(r"\b(airlines|delta|united|aa\b|american airlines|jetblue|marriott|hilton|hyatt|airbnb|expedia|booking\.com)\b", re.I)),
]

# Map issuer categories to our internal buckets
# You can extend this as you see more categories in your exports.
ISSUER_CATEGORY_MAP = [
    ("dining", re.compile(r"(dining|restaurants?|fast\s*food|food\s*&\s*drink|coffee)", re.I)),
    ("groceries", re.compile(r"(grocery|supermarket|warehouse\s*club)", re.I)),
    ("travel", re.compile(r"(travel|airline|hotel|lodging|car\s*rental|rideshare|uber|lyft|transport)", re.I)),
]

def _norm_cols(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [c.strip().lower() for c in df.columns]
    return df

def _to_float(x) -> float:
    if pd.isna(x):
        return 0.0
    if isinstance(x, (int, float)):
        return float(x)
    s = str(x).strip()
    if s == "":
        return 0.0
    # remove $ and commas
    s = s.replace("$", "").replace(",", "")
    try:
        return float(s)
    except ValueError:
        return 0.0

def infer_category_from_text(text: str) -> Category:
    t = text or ""
    for cat, rx in DEFAULT_CATEGORY_RULES:
        if rx.search(t):
            return cat  # type: ignore
    return "other"

def map_issuer_category(raw_cat: str, description: str) -> Category:
    rc = (raw_cat or "").strip()
    if rc:
        for cat, rx in ISSUER_CATEGORY_MAP:
            if rx.search(rc):
                return cat  # type: ignore
    # fallback to description
    return infer_category_from_text(description)

def parse_statement_csv(file) -> pd.DataFrame:
    """
    Supports headers like:
      Transaction Date, Posted Date, Card No., Description, Category, Debit, Credit
    Produces:
      transaction_date, posted_date, card_no, description, raw_category, amount, category
    where amount is positive spend only.
    """
    df = pd.read_csv(file, sep=None, engine="python")  # auto-detect delimiter
    df = _norm_cols(df)

    # Expected columns (case-insensitive after normalization)
    required_any = {
        "transaction date": "transaction_date",
        "posted date": "posted_date",
        "card no.": "card_no",
        "description": "description",
        "category": "raw_category",
        "debit": "debit",
        "credit": "credit",
    }

    # Some exports remove punctuation; accept variants
    def find_col(*candidates: str) -> str | None:
        cols = set(df.columns)
        for c in candidates:
            if c in cols:
                return c
        return None

    col_txn = find_col("transaction date", "transaction_date", "trans date", "date")
    col_posted = find_col("posted date", "posted_date")
    col_card = find_col("card no.", "card no", "card", "card number", "card_no")
    col_desc = find_col("description", "merchant", "details")
    col_cat = find_col("category", "mcc", "type")
    col_debit = find_col("debit")
    col_credit = find_col("credit")

    if not col_desc or not col_debit or not col_credit:
        raise ValueError("Missing required columns. Need at least: Description, Debit, Credit.")

    out = pd.DataFrame()
    out["transaction_date"] = df[col_txn] if col_txn else ""
    out["posted_date"] = df[col_posted] if col_posted else ""
    out["card_no"] = df[col_card] if col_card else ""
    out["description"] = df[col_desc].astype(str)
    out["raw_category"] = df[col_cat].astype(str) if col_cat else ""

    debit = df[col_debit].apply(_to_float)
    credit = df[col_credit].apply(_to_float)

    # Spend is Debit - Credit (keep positive only)
    out["amount"] = (debit - credit).astype(float)
    out = out[out["amount"] > 0].copy()

    # Normalize category bucket
    out["category"] = out.apply(
        lambda r: map_issuer_category(str(r["raw_category"]), str(r["description"])),
        axis=1,
    )

    return out

def spend_by_category(df_txn: pd.DataFrame) -> Dict[Category, float]:
    sums = df_txn.groupby("category")["amount"].sum().to_dict()
    return {
        "dining": float(sums.get("dining", 0.0)),
        "groceries": float(sums.get("groceries", 0.0)),
        "travel": float(sums.get("travel", 0.0)),
        "other": float(sums.get("other", 0.0)),
    }
