"use client";

import { ReactNode, useEffect, useMemo, useState } from "react";

type Category = "dining" | "groceries" | "flights" | "hotels" | "other";
type Program = "cash_back" | "bilt" | "capital_one" | "amex_mr" | "chase_ur" | "citi_ty";
type RentMode = "auto" | "option_a" | "option_b";

type Card = {
  name: string;
  annualFee: number;
  program: Program;
  mult: Record<Category, number>;
};

type SpendState = Record<Category, number>;

type ScenarioRow = {
  category: Category;
  spend: number;
  card: string;
  program: string;
  rate: string;
  earned: string;
  value: number;
};

type Scenario = {
  assignment: Record<Category, string>;
  usedCards: string[];
  coreValue: number;
  rentValue: number;
  fees: number;
  totalValue: number;
  rentModeUsed: string;
  rentExplain: string;
  nonRentSpendOnBilt: number;
  rows: ScenarioRow[];
};

type SingleCardScenario = {
  rows: Array<{
    category: string;
    spend: string;
    rate: string;
    earned: string;
    value: string;
  }>;
  coreValue: number;
  rentA: number;
  rentB: number;
  usedRent: number;
  usedLabel: string;
  fee: number;
  net: number;
  explain: string;
};

const CATEGORIES: Category[] = ["dining", "groceries", "flights", "hotels", "other"];
const BILT_NAMES = new Set(["Bilt Blue", "Bilt Obsidian", "Bilt Palladium"]);

const PROGRAM_LABELS: Record<Program, string> = {
  cash_back: "Cashback",
  bilt: "Bilt",
  capital_one: "Capital One",
  amex_mr: "Amex MR",
  chase_ur: "Chase UR",
  citi_ty: "Citi TY",
};

const CARDS: Card[] = [
  { name: "Bilt Blue", annualFee: 0, program: "bilt", mult: { dining: 1, groceries: 1, flights: 1, hotels: 1, other: 1 } },
  { name: "Bilt Obsidian", annualFee: 95, program: "bilt", mult: { dining: 3, groceries: 1, flights: 2, hotels: 2, other: 1 } },
  { name: "Bilt Palladium", annualFee: 495, program: "bilt", mult: { dining: 2, groceries: 2, flights: 2, hotels: 2, other: 2 } },
  { name: "Venture X", annualFee: 395, program: "capital_one", mult: { dining: 2, groceries: 2, flights: 5, hotels: 10, other: 2 } },
  { name: "Amex Gold", annualFee: 325, program: "amex_mr", mult: { dining: 4, groceries: 4, flights: 2, hotels: 3, other: 1 } },
  { name: "Amex Platinum", annualFee: 695, program: "amex_mr", mult: { dining: 1, groceries: 1, flights: 5, hotels: 5, other: 1 } },
  { name: "Chase Sapphire Reserve", annualFee: 795, program: "chase_ur", mult: { dining: 3, groceries: 1, flights: 8, hotels: 8, other: 1 } },
  { name: "Chase Sapphire Preferred", annualFee: 95, program: "chase_ur", mult: { dining: 3, groceries: 1, flights: 5, hotels: 5, other: 1 } },
  { name: "Citi Strata Elite", annualFee: 595, program: "citi_ty", mult: { dining: 3, groceries: 1, flights: 6, hotels: 12, other: 1 } },
  { name: "Citi Double Cash", annualFee: 0, program: "cash_back", mult: { dining: 2, groceries: 2, flights: 2, hotels: 2, other: 2 } },
  { name: "Amazon Prime Visa", annualFee: 0, program: "cash_back", mult: { dining: 2, groceries: 5, flights: 5, hotels: 5, other: 1 } },
];

const EMPTY_SPEND: SpendState = {
  dining: 0,
  groceries: 0,
  flights: 0,
  hotels: 0,
  other: 0,
};

function fmtMoney(n: number): string {
  return `$${n.toLocaleString(undefined, { maximumFractionDigits: 0 })}`;
}

function safePct(n: number): string {
  return `${n.toFixed(2)}%`;
}

function cloneSpend(spend: SpendState): SpendState {
  return {
    dining: spend.dining,
    groceries: spend.groceries,
    flights: spend.flights,
    hotels: spend.hotels,
    other: spend.other,
  };
}

function kCombinations<T>(arr: T[], k: number): T[][] {
  const out: T[][] = [];

  function helper(start: number, path: T[]) {
    if (path.length === k) {
      out.push([...path]);
      return;
    }
    for (let i = start; i < arr.length; i++) {
      path.push(arr[i]);
      helper(i + 1, path);
      path.pop();
    }
  }

  helper(0, []);
  return out;
}

function biltRentValue(args: {
  rent: number;
  nonRentSpendOnBilt: number;
  biltCpp: number;
  mode: Exclude<RentMode, "auto">;
  tier25: number;
  tier50: number;
  tier75: number;
  tier100: number;
  biltCashRate: number;
  unlockRate: number;
}): { value: number; explain: string } {
  const {
    rent,
    nonRentSpendOnBilt,
    biltCpp,
    mode,
    tier25,
    tier50,
    tier75,
    tier100,
    biltCashRate,
    unlockRate,
  } = args;

  if (rent <= 0) return { value: 0, explain: "No rent." };

  if (mode === "option_a") {
    const ratio = nonRentSpendOnBilt / rent;
    let tierMult = 0;
    let tierLabel = "<25%";

    if (ratio >= 1.0) {
      tierMult = tier100;
      tierLabel = "≥100%";
    } else if (ratio >= 0.75) {
      tierMult = tier75;
      tierLabel = "75–100%";
    } else if (ratio >= 0.5) {
      tierMult = tier50;
      tierLabel = "50–75%";
    } else if (ratio >= 0.25) {
      tierMult = tier25;
      tierLabel = "25–50%";
    }

    const base = rent * biltCpp;
    const value = base * tierMult;
    return {
      value,
      explain: `Option A: base ${fmtMoney(base)} × tier ${tierLabel} (${tierMult}×) = ${fmtMoney(value)}`,
    };
  }

  const cap = rent * biltCashRate;
  const unlocked = nonRentSpendOnBilt * unlockRate;
  const value = Math.min(cap, unlocked);
  return {
    value,
    explain: `Option B: min(cap ${fmtMoney(cap)}, unlocked ${fmtMoney(unlocked)}) = ${fmtMoney(value)}`,
  };
}

function valueForSpend(args: {
  card: Card;
  category: Category;
  spend: number;
  cppByProgram: Record<Program, number>;
  hasPrime: boolean;
  wholeFoodsShare: number;
  useTravelPortal: boolean;
}): { value: number; earned: string; rate: string } {
  const { card, category, spend, cppByProgram, hasPrime, wholeFoodsShare, useTravelPortal } = args;
  const mult = card.mult[category] ?? 0;

  if (card.program === "cash_back") {
    if (card.name === "Amazon Prime Visa") {
      if (category === "groceries") {
        const wfSpend = spend * wholeFoodsShare;
        const otherSpend = spend - wfSpend;
        const wfRate = hasPrime ? 5 : 3;
        const otherRate = 1;
        const value = wfSpend * (wfRate / 100) + otherSpend * (otherRate / 100);
        const blended = spend > 0 ? (value / spend) * 100 : 0;
        return { value, earned: fmtMoney(value), rate: `blended ${safePct(blended)}` };
      }

      if (category === "flights" || category === "hotels") {
        const rate = useTravelPortal ? (hasPrime ? 5 : 3) : 1;
        const value = spend * (rate / 100);
        return { value, earned: fmtMoney(value), rate: `${rate}%` };
      }
    }

    const value = spend * (mult / 100);
    return { value, earned: fmtMoney(value), rate: `${mult}%` };
  }

  const points = spend * mult;
  const value = points * (cppByProgram[card.program] ?? 0);
  return {
    value,
    earned: `${points.toLocaleString(undefined, { maximumFractionDigits: 0 })} pts`,
    rate: `${mult}x`,
  };
}

function evaluateAssignment(args: {
  assignment: Record<Category, string>;
  selected: Record<string, Card>;
  spend: SpendState;
  cppByProgram: Record<Program, number>;
  rent: number;
  rentMode: RentMode;
  tier25: number;
  tier50: number;
  tier75: number;
  tier100: number;
  biltCashRate: number;
  unlockRate: number;
  hasPrime: boolean;
  wholeFoodsShare: number;
  useTravelPortal: boolean;
}): Scenario {
  const {
    assignment,
    selected,
    spend,
    cppByProgram,
    rent,
    rentMode,
    tier25,
    tier50,
    tier75,
    tier100,
    biltCashRate,
    unlockRate,
    hasPrime,
    wholeFoodsShare,
    useTravelPortal,
  } = args;

  const usedCards = Array.from(new Set(Object.values(assignment))).sort();
  let coreValue = 0;
  let nonRentSpendOnBilt = 0;

  const rows: ScenarioRow[] = CATEGORIES.map((category) => {
    const cardName = assignment[category];
    const card = selected[cardName];
    const result = valueForSpend({
      card,
      category,
      spend: spend[category],
      cppByProgram,
      hasPrime,
      wholeFoodsShare,
      useTravelPortal,
    });

    coreValue += result.value;
    if (BILT_NAMES.has(cardName)) nonRentSpendOnBilt += spend[category];

    return {
      category,
      spend: spend[category],
      card: cardName,
      program: PROGRAM_LABELS[card.program],
      rate: result.rate,
      earned: result.earned,
      value: result.value,
    };
  });

  const fees = usedCards.reduce((sum, name) => sum + (selected[name]?.annualFee ?? 0), 0);

  let rentValue = 0;
  let rentExplain = "No Bilt used.";
  let rentModeUsed = "—";

  if (rent > 0 && usedCards.some((n) => BILT_NAMES.has(n))) {
    const a = biltRentValue({
      rent,
      nonRentSpendOnBilt,
      biltCpp: cppByProgram.bilt,
      mode: "option_a",
      tier25,
      tier50,
      tier75,
      tier100,
      biltCashRate,
      unlockRate,
    });

    const b = biltRentValue({
      rent,
      nonRentSpendOnBilt,
      biltCpp: cppByProgram.bilt,
      mode: "option_b",
      tier25,
      tier50,
      tier75,
      tier100,
      biltCashRate,
      unlockRate,
    });

    if (rentMode === "auto") {
      if (a.value >= b.value) {
        rentValue = a.value;
        rentExplain = a.explain;
        rentModeUsed = "Option A";
      } else {
        rentValue = b.value;
        rentExplain = b.explain;
        rentModeUsed = "Option B";
      }
    } else if (rentMode === "option_a") {
      rentValue = a.value;
      rentExplain = a.explain;
      rentModeUsed = "Option A";
    } else {
      rentValue = b.value;
      rentExplain = b.explain;
      rentModeUsed = "Option B";
    }
  }

  return {
    assignment,
    usedCards,
    coreValue,
    rentValue,
    fees,
    totalValue: coreValue + rentValue - fees,
    rentModeUsed,
    rentExplain,
    nonRentSpendOnBilt,
    rows,
  };
}

function bestCombos(args: {
  selectedCards: Record<string, Card>;
  spend: SpendState;
  cppByProgram: Record<Program, number>;
  rent: number;
  rentMode: RentMode;
  tier25: number;
  tier50: number;
  tier75: number;
  tier100: number;
  biltCashRate: number;
  unlockRate: number;
  hasPrime: boolean;
  wholeFoodsShare: number;
  useTravelPortal: boolean;
  maxCardsAllowed: number;
  topK: number;
}): Scenario[] {
  const names = Object.keys(args.selectedCards);
  const raw: Scenario[] = [];

  for (let k = 1; k <= Math.min(args.maxCardsAllowed, names.length); k++) {
    const subsets = kCombinations(names, k);

    for (const chosen of subsets) {
      for (const d of chosen) {
        for (const g of chosen) {
          for (const f of chosen) {
            for (const h of chosen) {
              for (const o of chosen) {
                const assignment: Record<Category, string> = {
                  dining: d,
                  groceries: g,
                  flights: f,
                  hotels: h,
                  other: o,
                };

                raw.push(
                  evaluateAssignment({
                    assignment,
                    selected: args.selectedCards,
                    spend: args.spend,
                    cppByProgram: args.cppByProgram,
                    rent: args.rent,
                    rentMode: args.rentMode,
                    tier25: args.tier25,
                    tier50: args.tier50,
                    tier75: args.tier75,
                    tier100: args.tier100,
                    biltCashRate: args.biltCashRate,
                    unlockRate: args.unlockRate,
                    hasPrime: args.hasPrime,
                    wholeFoodsShare: args.wholeFoodsShare,
                    useTravelPortal: args.useTravelPortal,
                  })
                );
              }
            }
          }
        }
      }
    }
  }

  raw.sort((a, b) => {
    if (b.totalValue !== a.totalValue) return b.totalValue - a.totalValue;
    return a.usedCards.length - b.usedCards.length;
  });

  const bestByCardSet = new Map<string, Scenario>();

  for (const r of raw) {
    const cardSetKey = r.usedCards.join(" | ");
    const existing = bestByCardSet.get(cardSetKey);

    if (!existing || r.totalValue > existing.totalValue) {
      bestByCardSet.set(cardSetKey, r);
    }
  }

  const deduped = Array.from(bestByCardSet.values());

  deduped.sort((a, b) => {
    if (b.totalValue !== a.totalValue) return b.totalValue - a.totalValue;
    return a.usedCards.length - b.usedCards.length;
  });

  return deduped.slice(0, args.topK);
}

function buildSingleCardScenario(args: {
  card: Card;
  spend: SpendState;
  rent: number;
  rentMode: RentMode;
  cppByProgram: Record<Program, number>;
  tier25: number;
  tier50: number;
  tier75: number;
  tier100: number;
  biltCashRate: number;
  unlockRate: number;
  hasPrime: boolean;
  wholeFoodsShare: number;
  useTravelPortal: boolean;
}): SingleCardScenario {
  const {
    card,
    spend,
    rent,
    rentMode,
    cppByProgram,
    tier25,
    tier50,
    tier75,
    tier100,
    biltCashRate,
    unlockRate,
    hasPrime,
    wholeFoodsShare,
    useTravelPortal,
  } = args;

  let coreValue = 0;
  let nonRentSpendOnBilt = 0;

  const rows = CATEGORIES.map((category) => {
    const result = valueForSpend({
      card,
      category,
      spend: spend[category],
      cppByProgram,
      hasPrime,
      wholeFoodsShare,
      useTravelPortal,
    });

    coreValue += result.value;
    if (BILT_NAMES.has(card.name)) nonRentSpendOnBilt += spend[category];

    return {
      category,
      spend: fmtMoney(spend[category]),
      rate: result.rate,
      earned: result.earned,
      value: fmtMoney(result.value),
    };
  });

  let rentA = 0;
  let rentB = 0;
  let usedRent = 0;
  let usedLabel = "—";
  let explain = "No Bilt used.";

  if (rent > 0 && BILT_NAMES.has(card.name)) {
    const a = biltRentValue({
      rent,
      nonRentSpendOnBilt,
      biltCpp: cppByProgram.bilt,
      mode: "option_a",
      tier25,
      tier50,
      tier75,
      tier100,
      biltCashRate,
      unlockRate,
    });
    const b = biltRentValue({
      rent,
      nonRentSpendOnBilt,
      biltCpp: cppByProgram.bilt,
      mode: "option_b",
      tier25,
      tier50,
      tier75,
      tier100,
      biltCashRate,
      unlockRate,
    });

    rentA = a.value;
    rentB = b.value;

    if (rentMode === "auto") {
      if (a.value >= b.value) {
        usedRent = a.value;
        usedLabel = "Option A";
        explain = a.explain;
      } else {
        usedRent = b.value;
        usedLabel = "Option B";
        explain = b.explain;
      }
    } else if (rentMode === "option_a") {
      usedRent = a.value;
      usedLabel = "Option A";
      explain = a.explain;
    } else {
      usedRent = b.value;
      usedLabel = "Option B";
      explain = b.explain;
    }
  }

  const fee = card.annualFee;
  const net = coreValue + usedRent - fee;

  return {
    rows,
    coreValue,
    rentA,
    rentB,
    usedRent,
    usedLabel,
    fee,
    net,
    explain,
  };
}

function Table(props: { columns: string[]; rows: Array<Record<string, ReactNode>> }) {
  return (
    <div className="overflow-x-auto rounded-2xl border border-zinc-800 bg-zinc-950">
      <table className="min-w-full text-sm">
        <thead className="bg-zinc-900">
          <tr>
            {props.columns.map((col) => (
              <th key={col} className="border-b border-zinc-800 px-4 py-3 text-left font-medium text-zinc-300">
                {col}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {props.rows.map((row, idx) => (
            <tr key={idx} className="border-b border-zinc-900">
              {props.columns.map((col) => (
                <td key={col} className="px-4 py-3 align-top text-zinc-100">
                  {row[col]}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function CardOptimizerPage() {
  // draft state
  const [draftSelectedNames, setDraftSelectedNames] = useState<string[]>([]);
  const [draftSpend, setDraftSpend] = useState<SpendState>(EMPTY_SPEND);
  const [draftRent, setDraftRent] = useState(0);
  const [draftMaxCardsAllowed, setDraftMaxCardsAllowed] = useState(3);
  const [draftRentMode, setDraftRentMode] = useState<RentMode>("auto");
  const [draftHasPrime, setDraftHasPrime] = useState(true);
  const [draftWholeFoodsShare, setDraftWholeFoodsShare] = useState(0.25);
  const [draftUseTravelPortal, setDraftUseTravelPortal] = useState(false);
  const [draftBiltCpp, setDraftBiltCpp] = useState(1.0);
  const [draftCap1Cpp, setDraftCap1Cpp] = useState(1.0);
  const [draftAmexCpp, setDraftAmexCpp] = useState(1.2);
  const [draftChaseCpp, setDraftChaseCpp] = useState(1.25);
  const [draftCitiCpp, setDraftCitiCpp] = useState(1.1);

  // committed state
  const [selectedNames, setSelectedNames] = useState<string[]>([]);
  const [spend, setSpend] = useState<SpendState>(EMPTY_SPEND);
  const [rent, setRent] = useState(0);
  const [maxCardsAllowed, setMaxCardsAllowed] = useState(3);
  const [rentMode, setRentMode] = useState<RentMode>("auto");
  const [hasPrime, setHasPrime] = useState(true);
  const [wholeFoodsShare, setWholeFoodsShare] = useState(0.25);
  const [useTravelPortal, setUseTravelPortal] = useState(false);
  const [biltCpp, setBiltCpp] = useState(1.0);
  const [cap1Cpp, setCap1Cpp] = useState(1.0);
  const [amexCpp, setAmexCpp] = useState(1.2);
  const [chaseCpp, setChaseCpp] = useState(1.25);
  const [citiCpp, setCitiCpp] = useState(1.1);

  // fixed assumptions
  const tier25 = 0.5;
  const tier50 = 0.75;
  const tier75 = 1.0;
  const tier100 = 1.25;
  const biltCashRate = 0.04;
  const unlockRate = 0.03;

  const [cardA, setCardA] = useState("");
  const [cardB, setCardB] = useState("");

  function applyChanges() {
    setSelectedNames([...draftSelectedNames]);
    setSpend(cloneSpend(draftSpend));
    setRent(draftRent);
    setMaxCardsAllowed(draftMaxCardsAllowed);
    setRentMode(draftRentMode);
    setHasPrime(draftHasPrime);
    setWholeFoodsShare(draftWholeFoodsShare);
    setUseTravelPortal(draftUseTravelPortal);
    setBiltCpp(draftBiltCpp);
    setCap1Cpp(draftCap1Cpp);
    setAmexCpp(draftAmexCpp);
    setChaseCpp(draftChaseCpp);
    setCitiCpp(draftCitiCpp);
  }

  function clearAll() {
    setDraftSelectedNames([]);
    setDraftSpend(cloneSpend(EMPTY_SPEND));
    setDraftRent(0);
    setDraftMaxCardsAllowed(3);
    setDraftRentMode("auto");
    setDraftHasPrime(true);
    setDraftWholeFoodsShare(0.25);
    setDraftUseTravelPortal(false);
    setDraftBiltCpp(1.0);
    setDraftCap1Cpp(1.0);
    setDraftAmexCpp(1.2);
    setDraftChaseCpp(1.25);
    setDraftCitiCpp(1.1);

    setSelectedNames([]);
    setSpend(cloneSpend(EMPTY_SPEND));
    setRent(0);
    setMaxCardsAllowed(3);
    setRentMode("auto");
    setHasPrime(true);
    setWholeFoodsShare(0.25);
    setUseTravelPortal(false);
    setBiltCpp(1.0);
    setCap1Cpp(1.0);
    setAmexCpp(1.2);
    setChaseCpp(1.25);
    setCitiCpp(1.1);

    setCardA("");
    setCardB("");
  }

  const selectedCards = useMemo(() => {
    return Object.fromEntries(
      CARDS.filter((c) => selectedNames.includes(c.name)).map((c) => [c.name, c])
    ) as Record<string, Card>;
  }, [selectedNames]);

  const cppByProgram = useMemo<Record<Program, number>>(
    () => ({
      cash_back: 1,
      bilt: biltCpp / 100,
      capital_one: cap1Cpp / 100,
      amex_mr: amexCpp / 100,
      chase_ur: chaseCpp / 100,
      citi_ty: citiCpp / 100,
    }),
    [biltCpp, cap1Cpp, amexCpp, chaseCpp, citiCpp]
  );

  const scenarios = useMemo(() => {
    if (!Object.keys(selectedCards).length) return [];
    return bestCombos({
      selectedCards,
      spend,
      cppByProgram,
      rent,
      rentMode,
      tier25,
      tier50,
      tier75,
      tier100,
      biltCashRate,
      unlockRate,
      hasPrime,
      wholeFoodsShare,
      useTravelPortal,
      maxCardsAllowed,
      topK: 10,
    });
  }, [
    selectedCards,
    spend,
    cppByProgram,
    rent,
    rentMode,
    hasPrime,
    wholeFoodsShare,
    useTravelPortal,
    maxCardsAllowed,
  ]);

  const best = scenarios[0] ?? null;

  const bestCore = useMemo(() => {
    if (!scenarios.length) return null;
    return [...scenarios].sort((a, b) => b.coreValue - a.coreValue)[0];
  }, [scenarios]);

  const comparatorChoices = Object.keys(selectedCards);

  useEffect(() => {
    if (!comparatorChoices.length) {
      setCardA("");
      setCardB("");
      return;
    }

    if (!comparatorChoices.includes(cardA)) {
      setCardA(comparatorChoices[0]);
    }

    if (!comparatorChoices.includes(cardB)) {
      setCardB(comparatorChoices[Math.min(1, comparatorChoices.length - 1)]);
    }
  }, [comparatorChoices, cardA, cardB]);

  const scenarioA = useMemo(() => {
    const card = selectedCards[cardA];
    if (!card) return null;
    return buildSingleCardScenario({
      card,
      spend,
      rent,
      rentMode,
      cppByProgram,
      tier25,
      tier50,
      tier75,
      tier100,
      biltCashRate,
      unlockRate,
      hasPrime,
      wholeFoodsShare,
      useTravelPortal,
    });
  }, [
    cardA,
    selectedCards,
    spend,
    rent,
    rentMode,
    cppByProgram,
    hasPrime,
    wholeFoodsShare,
    useTravelPortal,
  ]);

  const scenarioB = useMemo(() => {
    const card = selectedCards[cardB];
    if (!card) return null;
    return buildSingleCardScenario({
      card,
      spend,
      rent,
      rentMode,
      cppByProgram,
      tier25,
      tier50,
      tier75,
      tier100,
      biltCashRate,
      unlockRate,
      hasPrime,
      wholeFoodsShare,
      useTravelPortal,
    });
  }, [
    cardB,
    selectedCards,
    spend,
    rent,
    rentMode,
    cppByProgram,
    hasPrime,
    wholeFoodsShare,
    useTravelPortal,
  ]);

  return (
    <main className="min-h-screen bg-black text-white">
      <div className="mx-auto max-w-7xl px-6 py-10">
        <div className="mb-8">
          <h1 className="text-5xl font-semibold tracking-tight">Card Optimizer</h1>
          <p className="mt-3 max-w-4xl text-lg text-zinc-400">
            Optimize across cards, compare single-card outcomes, and model Bilt rent value with Option A vs Option B.
          </p>
        </div>

        <div className="grid gap-6 lg:grid-cols-[360px_minmax(0,1fr)]">
          <section className="rounded-3xl border border-zinc-800 bg-zinc-950 p-5">
            <h2 className="text-xl font-semibold">Inputs</h2>

            <div className="mt-5 space-y-5">
              <div>
                <label className="mb-2 block text-sm font-medium text-zinc-300">Cards to include</label>
                <div className="grid gap-2">
                  {CARDS.map((card) => {
                    const checked = draftSelectedNames.includes(card.name);
                    return (
                      <label
                        key={card.name}
                        className="flex items-center justify-between rounded-2xl border border-zinc-800 px-3 py-2 hover:bg-zinc-900"
                      >
                        <span className="text-sm">{card.name}</span>
                        <input
                          type="checkbox"
                          checked={checked}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setDraftSelectedNames((prev) => [...prev, card.name]);
                            } else {
                              setDraftSelectedNames((prev) => prev.filter((x) => x !== card.name));
                            }
                          }}
                        />
                      </label>
                    );
                  })}
                </div>
              </div>

              <div className="rounded-2xl border border-zinc-800 p-4">
                <h3 className="mb-3 font-medium">Annual spend</h3>
                <div className="grid gap-3">
                  {CATEGORIES.map((cat) => (
                    <label key={cat} className="grid gap-1">
                      <span className="text-sm capitalize text-zinc-400">{cat}</span>
                      <input
                        className="rounded-xl border border-zinc-700 bg-zinc-900 px-3 py-2 outline-none"
                        type="number"
                        value={draftSpend[cat]}
                        onChange={(e) =>
                          setDraftSpend((prev) => ({ ...prev, [cat]: Number(e.target.value) || 0 }))
                        }
                      />
                    </label>
                  ))}
                  <label className="grid gap-1">
                    <span className="text-sm text-zinc-400">Rent</span>
                    <input
                      className="rounded-xl border border-zinc-700 bg-zinc-900 px-3 py-2 outline-none"
                      type="number"
                      value={draftRent}
                      onChange={(e) => setDraftRent(Number(e.target.value) || 0)}
                    />
                  </label>
                </div>
              </div>

              <div className="rounded-2xl border border-zinc-800 p-4">
                <h3 className="mb-3 font-medium">Amazon assumptions</h3>
                <div className="grid gap-4">
                  <label className="flex items-center justify-between gap-4">
                    <span className="text-sm text-zinc-300">I have Amazon Prime</span>
                    <input
                      type="checkbox"
                      checked={draftHasPrime}
                      onChange={(e) => setDraftHasPrime(e.target.checked)}
                    />
                  </label>

                  <label className="grid gap-1">
                    <span className="text-sm text-zinc-400">Share of grocery spend at Whole Foods / Amazon</span>
                    <input
                      type="range"
                      min={0}
                      max={1}
                      step={0.05}
                      value={draftWholeFoodsShare}
                      onChange={(e) => setDraftWholeFoodsShare(Number(e.target.value))}
                    />
                    <span className="text-sm text-zinc-500">{Math.round(draftWholeFoodsShare * 100)}%</span>
                  </label>

                  <label className="flex items-center justify-between gap-4">
                    <span className="text-sm text-zinc-300">Book travel through portal when required</span>
                    <input
                      type="checkbox"
                      checked={draftUseTravelPortal}
                      onChange={(e) => setDraftUseTravelPortal(e.target.checked)}
                    />
                  </label>
                </div>
              </div>

            <div className="rounded-2xl border border-zinc-800 p-4">
            <h3 className="mb-3 font-medium">Valuations (cpp)</h3>
            <div className="grid gap-3">
                {[
                ["Bilt", draftBiltCpp, setDraftBiltCpp],
                ["Capital One", draftCap1Cpp, setDraftCap1Cpp],
                ["Amex MR", draftAmexCpp, setDraftAmexCpp],
                ["Chase UR", draftChaseCpp, setDraftChaseCpp],
                ["Citi TY", draftCitiCpp, setDraftCitiCpp],
                ].map(([label, value, setter]) => (
                <label key={label as string} className="grid gap-1 min-w-0">
                    <span className="text-sm text-zinc-400">{label as string}</span>
                    <input
                    className="w-full min-w-0 rounded-xl border border-zinc-700 bg-zinc-900 px-3 py-2 outline-none"
                    type="number"
                    step="0.05"
                    value={value as number}
                    onChange={(e) => (setter as (n: number) => void)(Number(e.target.value) || 0)}
                    />
                </label>
                ))}
            </div>
            </div>

              <div className="rounded-2xl border border-zinc-800 p-4">
                <h3 className="mb-3 font-medium">Optimizer</h3>
                <div className="grid gap-3">
                  <label className="grid gap-1">
                    <span className="text-sm text-zinc-400">Max cards allowed</span>
                    <input
                      className="rounded-xl border border-zinc-700 bg-zinc-900 px-3 py-2 outline-none"
                      type="number"
                      min={1}
                      max={6}
                      value={draftMaxCardsAllowed}
                      onChange={(e) =>
                        setDraftMaxCardsAllowed(Math.max(1, Math.min(6, Number(e.target.value) || 1)))
                      }
                    />
                  </label>

                  <label className="grid gap-1">
                    <span className="text-sm text-zinc-400">Bilt rent mode</span>
                    <select
                      className="rounded-xl border border-zinc-700 bg-zinc-900 px-3 py-2 outline-none"
                      value={draftRentMode}
                      onChange={(e) => setDraftRentMode(e.target.value as RentMode)}
                    >
                      <option value="auto">Auto</option>
                      <option value="option_a">Option A</option>
                      <option value="option_b">Option B</option>
                    </select>
                  </label>
                </div>
              </div>

              <div className="rounded-2xl border border-zinc-800 p-4">
                <h3 className="mb-3 font-medium">Bilt assumptions</h3>
                <div className="space-y-2 text-sm text-zinc-400">
                  <div>Option A tiers: 25% → 0.50×, 50% → 0.75×, 75% → 1.00×, 100% → 1.25×</div>
                  <div>Option B: 4% rent cap, 3% unlock rate</div>
                  <div className="text-zinc-500">Shown for transparency only.</div>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3 pt-2">
                <button
                  type="button"
                  onClick={applyChanges}
                  className="rounded-xl bg-white px-4 py-3 font-medium text-black transition hover:bg-zinc-200"
                >
                  Apply
                </button>
                <button
                  type="button"
                  onClick={clearAll}
                  className="rounded-xl border border-zinc-700 px-4 py-3 font-medium text-white transition hover:bg-zinc-900"
                >
                  Clear
                </button>
              </div>
            </div>
          </section>

<section className="space-y-6">
  {!best ? (
    <div className="rounded-3xl border border-zinc-800 bg-zinc-950 p-8 text-zinc-400">
      Select cards, enter inputs, then click Apply.
    </div>
  ) : (
    <>
      {bestCore && (
        <div className="rounded-3xl border border-blue-900 bg-blue-950/30 p-5">
          <div className="text-sm uppercase tracking-wide text-blue-300">Core spend only</div>
          <div className="mt-2 text-lg font-medium">
            Best core-spend combo: {bestCore.usedCards.join(", ")} — {fmtMoney(bestCore.coreValue)}/yr
          </div>
        </div>
      )}

      <div className="rounded-3xl border border-emerald-900 bg-emerald-950/30 p-5">
        <div className="text-sm uppercase tracking-wide text-emerald-300">Optimizer result</div>
        <div className="mt-2 text-2xl font-semibold">
          Best combo: {best.usedCards.join(", ")} — {fmtMoney(best.totalValue)}/yr
        </div>
        <div className="mt-3 rounded-2xl border border-zinc-800 bg-zinc-950 p-4 text-sm text-zinc-400">
          Net annual value = value from category spend + modeled Bilt rent value − annual fees.
          Point cards are converted to dollars using your cpp assumptions. Cashback cards are treated as direct dollar value.
        </div>
      </div>

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_320px]">
        <div className="space-y-6">
          <Table
            columns={["Category", "Spend", "Card", "Program", "Rate", "Earned", "Value ($)"]}
            rows={[
              ...best.rows.map((r) => ({
                Category: r.category,
                Spend: fmtMoney(r.spend),
                Card: r.card,
                Program: r.program,
                Rate: r.rate,
                Earned: r.earned,
                "Value ($)": fmtMoney(r.value),
              })),
              {
                Category: "TOTAL (spend categories)",
                Spend: fmtMoney(CATEGORIES.reduce((sum, c) => sum + spend[c], 0)),
                Card: "—",
                Program: "—",
                Rate: "—",
                Earned: "—",
                "Value ($)": fmtMoney(best.coreValue),
              },
              {
                Category: "Rent",
                Spend: fmtMoney(rent),
                Card: best.rentValue > 0 ? "Bilt" : "—",
                Program: best.rentValue > 0 ? "Bilt" : "—",
                Rate: best.rentValue > 0 ? best.rentModeUsed : "—",
                Earned: "—",
                "Value ($)": fmtMoney(best.rentValue),
              },
              {
                Category: "Fees",
                Spend: "—",
                Card: best.usedCards.join(", "),
                Program: "—",
                Rate: "—",
                Earned: "—",
                "Value ($)": best.fees > 0 ? `-${fmtMoney(best.fees)}` : fmtMoney(0),
              },
              {
                Category: "TOTAL NET",
                Spend: "—",
                Card: "—",
                Program: "—",
                Rate: "—",
                Earned: "—",
                "Value ($)": fmtMoney(best.totalValue),
              },
            ]}
          />
        </div>

        <div className="rounded-3xl border border-zinc-800 bg-zinc-950 p-5">
          <h3 className="text-lg font-semibold">Best allocation</h3>
          <p className="mt-2 text-sm text-zinc-400">
            This shows which selected card is assigned to each spend category in the current best net-value setup.
          </p>

          <pre className="mt-4 overflow-x-auto rounded-2xl bg-black p-4 text-sm text-zinc-300">
            {JSON.stringify(best.assignment, null, 2)}
          </pre>

          <div className="mt-6 space-y-3">
            <div className="flex items-center justify-between gap-4">
              <span className="text-zinc-400">Spend value (non-rent)</span>
              <span>{fmtMoney(best.coreValue)}</span>
            </div>
            <div className="flex items-center justify-between gap-4">
              <span className="text-zinc-400">Modeled rent value</span>
              <span>
                {fmtMoney(best.rentValue)} {best.rentModeUsed !== "—" ? `(${best.rentModeUsed})` : ""}
              </span>
            </div>
            <div className="flex items-center justify-between gap-4">
              <span className="text-zinc-400">Annual fees</span>
              <span>{best.fees > 0 ? `-${fmtMoney(best.fees)}` : fmtMoney(0)}</span>
            </div>
            <div className="flex items-center justify-between gap-4 border-t border-zinc-800 pt-3 text-lg font-semibold">
              <span>Net annual value</span>
              <span>{fmtMoney(best.totalValue)}</span>
            </div>
          </div>

          <div className="mt-4 rounded-2xl border border-zinc-800 bg-black/50 p-4 text-sm text-zinc-400">
            {best.rentExplain}
          </div>

          {best.nonRentSpendOnBilt > 0 && (
            <div className="mt-3 text-sm text-zinc-500">
              Non-rent spend routed to Bilt: {fmtMoney(best.nonRentSpendOnBilt)}
            </div>
          )}
        </div>
      </div>

      <div className="rounded-3xl border border-zinc-800 bg-zinc-950 p-5">
        <div className="mb-4">
          <h2 className="text-2xl font-semibold">Top contenders</h2>
          <p className="mt-2 text-sm text-zinc-400">
            These are the best distinct card combinations ranked by net annual value.
            Each row shows the best assignment found for that specific set of cards.
          </p>
        </div>

        <Table
          columns={[
            "Net value ($/yr)",
            "Cards used",
            "Rent mode",
            "Dining",
            "Groceries",
            "Flights",
            "Hotels",
            "Other",
          ]}
          rows={scenarios.map((r) => ({
            "Net value ($/yr)": fmtMoney(r.totalValue),
            "Cards used": r.usedCards.join(", "),
            "Rent mode": r.rentModeUsed,
            Dining: r.assignment.dining,
            Groceries: r.assignment.groceries,
            Flights: r.assignment.flights,
            Hotels: r.assignment.hotels,
            Other: r.assignment.other,
          }))}
        />
      </div>

      <div className="rounded-3xl border border-zinc-800 bg-zinc-950 p-5">
        <h2 className="mb-4 text-2xl font-semibold">Comparator</h2>

        <div className="grid gap-4 md:grid-cols-2">
          <label className="grid gap-2">
            <span className="text-sm text-zinc-400">Card A</span>
            <select
              className="rounded-xl border border-zinc-700 bg-zinc-900 px-3 py-2 outline-none"
              value={cardA}
              onChange={(e) => setCardA(e.target.value)}
            >
              {comparatorChoices.map((name) => (
                <option key={name} value={name}>
                  {name}
                </option>
              ))}
            </select>
          </label>

          <label className="grid gap-2">
            <span className="text-sm text-zinc-400">Card B</span>
            <select
              className="rounded-xl border border-zinc-700 bg-zinc-900 px-3 py-2 outline-none"
              value={cardB}
              onChange={(e) => setCardB(e.target.value)}
            >
              {comparatorChoices.map((name) => (
                <option key={name} value={name}>
                  {name}
                </option>
              ))}
            </select>
          </label>
        </div>

        {scenarioA && scenarioB && (
          <>
            <div className="mt-6 grid gap-6 xl:grid-cols-2">
              <div className="space-y-3">
                <h3 className="text-lg font-medium">A — {cardA}</h3>
                <Table
                  columns={["Category", "Spend", "Rate", "Earned", "Value ($)"]}
                  rows={[
                    ...scenarioA.rows.map((r) => ({
                      Category: r.category,
                      Spend: r.spend,
                      Rate: r.rate,
                      Earned: r.earned,
                      "Value ($)": r.value,
                    })),
                    {
                      Category: "Rent (Option A)",
                      Spend: fmtMoney(rent),
                      Rate: "engine-modeled",
                      Earned: "—",
                      "Value ($)": fmtMoney(scenarioA.rentA),
                    },
                    {
                      Category: "Rent (Option B)",
                      Spend: fmtMoney(rent),
                      Rate: "engine-modeled",
                      Earned: "—",
                      "Value ($)": fmtMoney(scenarioA.rentB),
                    },
                    {
                      Category: "Rent (Used)",
                      Spend: fmtMoney(rent),
                      Rate: scenarioA.usedLabel,
                      Earned: "—",
                      "Value ($)": fmtMoney(scenarioA.usedRent),
                    },
                    {
                      Category: "Fee",
                      Spend: "—",
                      Rate: "—",
                      Earned: "—",
                      "Value ($)": scenarioA.fee > 0 ? `-${fmtMoney(scenarioA.fee)}` : fmtMoney(0),
                    },
                    {
                      Category: "TOTAL NET",
                      Spend: "—",
                      Rate: "—",
                      Earned: "—",
                      "Value ($)": fmtMoney(scenarioA.net),
                    },
                  ]}
                />
                <div className="rounded-2xl border border-zinc-800 bg-black/50 p-4 text-sm text-zinc-400">
                  {scenarioA.explain}
                </div>
              </div>

              <div className="space-y-3">
                <h3 className="text-lg font-medium">B — {cardB}</h3>
                <Table
                  columns={["Category", "Spend", "Rate", "Earned", "Value ($)"]}
                  rows={[
                    ...scenarioB.rows.map((r) => ({
                      Category: r.category,
                      Spend: r.spend,
                      Rate: r.rate,
                      Earned: r.earned,
                      "Value ($)": r.value,
                    })),
                    {
                      Category: "Rent (Option A)",
                      Spend: fmtMoney(rent),
                      Rate: "engine-modeled",
                      Earned: "—",
                      "Value ($)": fmtMoney(scenarioB.rentA),
                    },
                    {
                      Category: "Rent (Option B)",
                      Spend: fmtMoney(rent),
                      Rate: "engine-modeled",
                      Earned: "—",
                      "Value ($)": fmtMoney(scenarioB.rentB),
                    },
                    {
                      Category: "Rent (Used)",
                      Spend: fmtMoney(rent),
                      Rate: scenarioB.usedLabel,
                      Earned: "—",
                      "Value ($)": fmtMoney(scenarioB.usedRent),
                    },
                    {
                      Category: "Fee",
                      Spend: "—",
                      Rate: "—",
                      Earned: "—",
                      "Value ($)": scenarioB.fee > 0 ? `-${fmtMoney(scenarioB.fee)}` : fmtMoney(0),
                    },
                    {
                      Category: "TOTAL NET",
                      Spend: "—",
                      Rate: "—",
                      Earned: "—",
                      "Value ($)": fmtMoney(scenarioB.net),
                    },
                  ]}
                />
                <div className="rounded-2xl border border-zinc-800 bg-black/50 p-4 text-sm text-zinc-400">
                  {scenarioB.explain}
                </div>
              </div>
            </div>

            <div className="mt-6 rounded-2xl border border-zinc-800 bg-black/50 p-4 text-lg font-medium">
              {Math.abs(scenarioB.net - scenarioA.net) < 1e-9
                ? "Tie: both cards have the same net annual value."
                : `Winner: ${scenarioB.net > scenarioA.net ? cardB : cardA} by ${fmtMoney(
                    Math.abs(scenarioB.net - scenarioA.net)
                  )}/yr`}
            </div>
          </>
        )}
      </div>
    </>
  )}
</section>
        </div>
      </div>
    </main>
  );
}