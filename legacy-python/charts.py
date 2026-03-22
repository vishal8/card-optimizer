# PASTE THIS FILE AS-IS
from __future__ import annotations

import numpy as np
import pandas as pd

def build_increment_curve(
    *,
    max_spend: float,
    step: float = 100.0,
    fn_points,
):
    """
    Produces a DataFrame with columns:
      additional_spend, points
    where points is computed by fn_points(additional_spend).
    """
    xs = np.arange(0, max_spend + step, step, dtype=float)
    ys = [float(fn_points(x)) for x in xs]
    return pd.DataFrame({"additional_spend": xs, "points": ys})

def effective_multiplier_curve(df_points: pd.DataFrame) -> pd.DataFrame:
    """
    Multiplier = total_points / additional_spend
    (with safe handling for 0)
    """
    df = df_points.copy()
    df["multiplier"] = df.apply(
        lambda r: (r["points"] / r["additional_spend"]) if r["additional_spend"] > 0 else 0.0,
        axis=1,
    )
    return df
