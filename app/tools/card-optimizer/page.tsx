"use client";

import { useMemo, useState } from "react";

type Category = "dining" | "groceries" | "flights" | "hotels" | "other";

type Card = {
  name: string;
  annualFee: number;
  mult: Record<Category, number>;
  program: "cash_back" | "points";
};

const CATEGORIES: Category[] = ["dining", "groceries", "flights", "hotels", "other"];

// =====================
// CARD DATA
// =====================
const CARDS: Card[] = [
  {
    name: "Venture X",
    annualFee: 395,
    program: "points",
    mult: { dining: 2, groceries: 2, flights: 5, hotels: 10, other: 2 },
  },
  {
    name: "Amex Gold",
    annualFee: 325,
    program: "points",
    mult: { dining: 4, groceries: 4, flights: 2, hotels: 3, other: 1 },
  },
  {
    name: "Amazon Prime Visa",
    annualFee: 0,
    program: "cash_back",
    mult: { dining: 2, groceries: 5, flights: 5, hotels: 5, other: 1 },
  },
  {
    name: "Bilt",
    annualFee: 0,
    program: "points",
    mult: { dining: 3, groceries: 1, flights: 2, hotels: 2, other: 1 },
  },
];

// =====================
// VALUE FUNCTION
// =====================
function getValue(card: Card, category: Category, spend: number) {
  if (card.program === "cash_back") {
    return spend * (card.mult[category] / 100);
  }
  return spend * card.mult[category] * 0.01;
}

// =====================
// OPTIMIZER
// =====================
function bestCombo(cards: Card[], spend: Record<Category, number>) {
  let best: any = null;

  for (const d of cards) {
    for (const g of cards) {
      for (const f of cards) {
        for (const h of cards) {
          for (const o of cards) {
            const assignment = {
              dining: d,
              groceries: g,
              flights: f,
              hotels: h,
              other: o,
            };

            const used = new Set(Object.values(assignment).map((c) => c.name));
            if (used.size > 3) continue;

            let total = 0;

            for (const cat of CATEGORIES) {
              total += getValue(assignment[cat], cat, spend[cat]);
            }

            const fees = Array.from(used)
              .map((name) => cards.find((c) => c.name === name)!.annualFee)
              .reduce((a, b) => a + b, 0);

            const net = total - fees;

            if (!best || net > best.net) {
              best = { assignment, net, total, fees };
            }
          }
        }
      }
    }
  }

  return best;
}

// =====================
// UI
// =====================
export default function Page() {
  const [spend, setSpend] = useState({
    dining: 9000,
    groceries: 4000,
    flights: 3000,
    hotels: 5000,
    other: 7000,
  });

  const result = useMemo(() => bestCombo(CARDS, spend), [spend]);

  return (
    <div style={{ padding: 24 }}>
      <h1>Card Optimizer</h1>

      <h2>Spend</h2>
      {CATEGORIES.map((cat) => (
        <div key={cat}>
          {cat}:{" "}
          <input
            type="number"
            value={spend[cat]}
            onChange={(e) =>
              setSpend({ ...spend, [cat]: Number(e.target.value) })
            }
          />
        </div>
      ))}

      <h2>Best Result</h2>
      {result && (
        <>
          <div>Net: ${result.net.toFixed(0)}</div>
          <div>Fees: ${result.fees}</div>

          <pre>{JSON.stringify(result.assignment, null, 2)}</pre>
        </>
      )}
    </div>
  );
}