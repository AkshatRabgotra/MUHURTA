'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api';
import type { PlanRequest } from '@/types';

export default function PlansHistoryPage() {
  const [plans, setPlans] = useState<PlanRequest[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setIsLoading(true);
    api.getPlans(1, 20)
      .then((res) => {
        setPlans(res.items || []);
      })
      .catch((err) => {
        setError(err.message || 'Failed to load consultation history.');
      })
      .finally(() => {
        setIsLoading(false);
      });
  }, []);

  return (
    <main className="max-w-4xl mx-auto px-4 sm:px-6 py-10 sm:py-14 space-y-6">
      <div className="flex items-center justify-between pb-4 border-b border-amber-900/40">
        <div>
          <h1 className="text-2xl sm:text-3xl font-serif font-bold text-slate-100 tracking-tight">
            Consultation History
          </h1>
          <p className="text-xs text-amber-200/60 mt-0.5">
            Past Vedic calculations and computed auspicious windows.
          </p>
        </div>
        <Link
          href="/planner"
          className="rounded-xl bg-gradient-to-r from-amber-500 to-orange-600 hover:from-amber-400 hover:to-orange-500 px-4 py-2 text-xs font-bold text-slate-950 transition shadow-[0_0_15px_rgba(245,158,11,0.3)]"
        >
          + New Muhurta
        </Link>
      </div>

      {isLoading ? (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-20 vedic-card-vibrant rounded-2xl p-5 animate-pulse" />
          ))}
        </div>
      ) : error ? (
        <div className="p-4 rounded-xl bg-rose-950/40 border border-rose-500/40 text-xs text-rose-300">
          {error}
        </div>
      ) : plans.length === 0 ? (
        <div className="vedic-card-vibrant rounded-2xl p-10 text-center space-y-3">
          <p className="text-sm font-serif font-semibold text-amber-200">No previous calculations</p>
          <p className="text-xs text-amber-200/60 max-w-sm mx-auto">
            Describe your event in the planner to calculate auspicious timings.
          </p>
          <Link
            href="/planner"
            className="inline-block rounded-xl bg-gradient-to-r from-amber-500 to-orange-600 text-slate-950 px-4 py-2 text-xs font-bold hover:brightness-110 transition"
          >
            Go to Planner
          </Link>
        </div>
      ) : (
        <div className="space-y-3">
          {plans.map((p) => (
            <Link
              key={p.id}
              href={`/planner?q=${encodeURIComponent(p.raw_text)}`}
              className="block rounded-2xl border border-amber-500/20 bg-[#120B07] p-5 hover:border-amber-400 transition group"
            >
              <div className="flex items-start justify-between gap-4 mb-1.5">
                <span className="px-2.5 py-0.5 rounded text-[11px] font-semibold bg-amber-500/15 text-amber-300 border border-amber-500/30 capitalize">
                  {p.category ? p.category.replace('_', ' ') : 'General'}
                </span>
                <span className="text-xs text-amber-300/50">
                  {new Date(p.created_at).toLocaleDateString(undefined, {
                    month: 'short',
                    day: 'numeric',
                    year: 'numeric',
                  })}
                </span>
              </div>
              <p className="text-xs sm:text-sm font-medium text-amber-100 group-hover:text-amber-300 transition line-clamp-2">
                &ldquo;{p.raw_text}&rdquo;
              </p>
              <div className="flex items-center justify-between text-[11px] text-amber-400/60 pt-2.5 mt-2.5 border-t border-amber-900/40">
                <span>{p.slots ? `${p.slots.length} auspicious slots computed` : 'Processed'}</span>
                <span className="text-amber-400 font-semibold group-hover:translate-x-1 transition">Revisit in Planner →</span>
              </div>
            </Link>
          ))}
        </div>
      )}
    </main>
  );
}
