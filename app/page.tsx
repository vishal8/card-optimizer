import Link from "next/link";

export default function HomePage() {
  return (
    <main className="min-h-screen bg-black text-white p-8">
      <h1 className="text-4xl font-semibold">Card Optimizer</h1>
      <p className="mt-3 text-zinc-400">
        Standalone project for optimizing credit card combinations and comparing single-card outcomes.
      </p>
      <div className="mt-6">
        <Link
          href="/tools/card-optimizer"
          className="inline-block rounded-2xl border border-zinc-700 px-5 py-3 hover:bg-zinc-900"
        >
          Open optimizer
        </Link>
      </div>
    </main>
  );
}