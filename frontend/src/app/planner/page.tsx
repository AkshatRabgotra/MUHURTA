'use client';

import { Suspense, useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { api, ApiError } from '@/lib/api';
import type { PlanRequest } from '@/types';
import SlotCard from '@/components/SlotCard';

const EXAMPLES = [
  { label: 'Rental Agreement', query: 'Sign rental agreement next week morning in Bengaluru' },
  { label: 'New Job', query: 'Starting my new job next month in Mumbai' },
  { label: 'Buying a Vehicle', query: 'Taking car delivery this Friday afternoon in Delhi' },
  { label: 'House Warming', query: 'Griha Pravesh ceremony next month in Hyderabad' },
  { label: 'Buying Gold', query: 'Purchasing gold jewelry this weekend in Chennai' },
  { label: 'Anniversary Party', query: 'Wedding anniversary family gathering next Saturday in Pune' },
];

const CITIES = ['Bengaluru', 'Mumbai', 'Delhi', 'Hyderabad', 'Chennai', 'Pune', 'Kolkata', 'London', 'New York'];
const TIMES = ['Morning (9am - 12pm)', 'Afternoon (12pm - 4pm)', 'Evening (4pm - 8pm)', 'Anytime of day'];

function PlannerContent() {
  const searchParams = useSearchParams();
  const initialQuery = searchParams.get('q') || '';

  const [query, setQuery] = useState(initialQuery);
  const [isLoading, setIsLoading] = useState(false);
  const [loadingStep, setLoadingStep] = useState(0);
  const [plan, setPlan] = useState<PlanRequest | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Missing info prompt state (e.g. asking for city or time of day)
  const [promptQuestion, setPromptQuestion] = useState<{
    question: string;
    type: 'city' | 'time' | 'clarification';
    chips: string[];
  } | null>(null);

  // History state
  const [history, setHistory] = useState<PlanRequest[]>([]);
  const [showHistory, setShowHistory] = useState(false);
  const [isGuest, setIsGuest] = useState(true);

  const loadHistory = useCallback(async () => {
    try {
      const me = await api.getMe();
      if (me && me.email) {
        setIsGuest(false);
        const res = await api.getPlans(1, 15);
        setHistory(res.items || []);
        return;
      }
    } catch {
      setIsGuest(true);
    }

    // Local storage fallback for guest consultations
    if (typeof window !== 'undefined') {
      try {
        const stored = localStorage.getItem('muhurta_guest_history');
        if (stored) {
          setHistory(JSON.parse(stored));
        }
      } catch {
        // ignore
      }
    }
  }, []);

  const handleCompute = useCallback(async (textToRun: string, categoryOverride?: string) => {
    const trimmed = textToRun.trim();
    if (!trimmed) return;

    setError(null);
    setPromptQuestion(null);

    // Smart Missing Information Check
    const lower = trimmed.toLowerCase();
    const hasCity = CITIES.some((c) => lower.includes(c.toLowerCase())) ||
      lower.includes('city') || lower.includes('pune') || lower.includes('ahmedabad') || lower.includes('jaipur') || lower.includes('in ');

    if (trimmed.split(' ').length < 4 && !hasCity) {
      setPromptQuestion({
        question: 'Which city will this event take place in? (Our engine requires your coordinates to calculate local sunrise and Rahu Kalam timings)',
        type: 'city',
        chips: CITIES,
      });
      return;
    }

    setIsLoading(true);
    setLoadingStep(1);

    const timer = setInterval(() => {
      setLoadingStep((s) => (s < 3 ? s + 1 : s));
    }, 700);

    try {
      const result = await api.createPlan(trimmed, categoryOverride);
      clearInterval(timer);
      setPlan(result);

      // Persist to guest local storage
      if (typeof window !== 'undefined') {
        try {
          const stored = localStorage.getItem('muhurta_guest_history');
          const currentList: PlanRequest[] = stored ? JSON.parse(stored) : [];
          const updated = [result, ...currentList.filter((p) => p.id !== result.id)].slice(0, 10);
          localStorage.setItem('muhurta_guest_history', JSON.stringify(updated));
        } catch {
          // ignore
        }
      }

      loadHistory();
    } catch (err: any) {
      clearInterval(timer);
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError('Could not calculate auspicious timings. Please try again.');
      }
    } finally {
      setIsLoading(false);
    }
  }, [loadHistory]);

  useEffect(() => {
    loadHistory();
    if (initialQuery) {
      handleCompute(initialQuery);
    }
  }, [initialQuery, loadHistory, handleCompute]);

  const handleChipAnswer = (chip: string) => {
    if (promptQuestion?.type === 'city') {
      const updated = `${query} in ${chip}`;
      setQuery(updated);
      handleCompute(updated);
    } else if (promptQuestion?.type === 'time') {
      const updated = `${query}, ${chip}`;
      setQuery(updated);
      handleCompute(updated);
    }
  };

  const handleSelectHistory = (pastPlan: PlanRequest) => {
    setPlan(pastPlan);
    setQuery(pastPlan.raw_text);
    setShowHistory(false);
  };

  return (
    <main className="max-w-4xl mx-auto px-4 sm:px-6 py-10 sm:py-14 space-y-8">
      {/* ── HEADER ──────────────────────────────────────────────────────── */}
      <div className="text-center space-y-2">
        <div className="inline-flex items-center gap-2 px-4 py-1 rounded-full bg-gradient-to-r from-red-950/50 via-amber-950/60 to-orange-950/50 border border-amber-500/40 text-amber-200 text-xs font-serif tracking-widest uppercase shadow-[0_0_15px_rgba(245,158,11,0.2)]">
          <span className="animate-diya text-sm">🪔</span>
          <span>Vedic Muhurta Consultation</span>
        </div>
        <h1 className="text-3xl sm:text-4xl font-serif font-bold text-slate-100 tracking-tight">
          Consult the Auspicious Engine
        </h1>
        <p className="text-xs sm:text-sm text-amber-100/70 max-w-xl mx-auto">
          State your upcoming milestone in plain words. The engine calculates the top 3 Muhurta windows with zero hallucinations.
        </p>
      </div>

      {/* ── INPUT CARD ──────────────────────────────────────────────────── */}
      <div className="vedic-card-vibrant rounded-3xl p-6 sm:p-8 space-y-5 animate-gold-pulse">
        <div className="flex items-center justify-between pb-1">
          <label htmlFor="event-query" className="text-xs font-serif font-bold text-amber-200 uppercase tracking-widest flex items-center gap-1.5">
            <span>🪔</span>
            <span>What are you planning?</span>
          </label>
          {history.length > 0 && (
            <button
              onClick={() => setShowHistory(!showHistory)}
              className="text-xs font-semibold text-amber-400 hover:text-amber-300 transition flex items-center gap-1"
            >
              <span>📜</span>
              <span>{showHistory ? 'Hide Previous Chats' : `Previous Chats (${history.length})`}</span>
            </button>
          )}
        </div>

        {/* Previous consultations list */}
        {showHistory && (
          <div className="p-3 bg-[#0A0604] rounded-2xl border border-amber-500/30 space-y-2 max-h-52 overflow-y-auto">
            <p className="text-[10px] uppercase font-bold text-amber-400 tracking-widest">
              Revisit a previous consultation:
            </p>
            {history.map((h) => (
              <button
                key={h.id}
                onClick={() => handleSelectHistory(h)}
                className="w-full text-left p-2.5 rounded-xl bg-white/5 border border-white/5 hover:border-amber-500/40 text-xs text-amber-100 transition flex items-center justify-between group"
              >
                <span className="truncate max-w-md font-medium group-hover:text-amber-300 transition">{h.raw_text}</span>
                <span className="text-[10px] text-amber-400/60 whitespace-nowrap ml-2">
                  {new Date(h.created_at).toLocaleDateString()}
                </span>
              </button>
            ))}
          </div>
        )}

        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleCompute(query);
          }}
          className="space-y-4"
        >
          <textarea
            id="event-query"
            rows={3}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="e.g. I want to sign my rental agreement next week morning in Bengaluru..."
            className="w-full rounded-2xl bg-[#090604] border border-amber-500/30 p-4 text-xs sm:text-sm text-amber-50 placeholder-amber-200/40 focus:border-amber-400 focus:outline-none transition resize-none shadow-inner"
            disabled={isLoading}
          />

          {/* Interactive Clarification Question Prompt */}
          {promptQuestion && (
            <div className="p-4 rounded-2xl bg-amber-950/40 border border-amber-500/40 text-xs text-amber-200 space-y-3">
              <div className="flex items-center gap-2">
                <span className="w-5 h-5 rounded-full bg-amber-500 text-slate-950 flex items-center justify-center font-bold text-xs">
                  ?
                </span>
                <p className="font-semibold">{promptQuestion.question}</p>
              </div>
              <div className="flex flex-wrap gap-2">
                {promptQuestion.chips.map((chip, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => handleChipAnswer(chip)}
                    className="px-3 py-1.5 rounded-xl bg-white/10 border border-amber-500/30 hover:bg-amber-500/20 text-xs text-amber-200 font-medium transition"
                  >
                    + {chip}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Example suggestions */}
          <div>
            <span className="text-[10px] font-serif font-bold text-amber-400/80 uppercase tracking-widest block mb-2">
              Try an example:
            </span>
            <div className="flex flex-wrap gap-2">
              {EXAMPLES.map((ex, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => {
                    setQuery(ex.query);
                    handleCompute(ex.query);
                  }}
                  disabled={isLoading}
                  className="px-3 py-1.5 rounded-xl bg-white/5 border border-amber-500/20 text-amber-200/80 text-xs hover:border-amber-400 hover:text-amber-200 transition"
                >
                  {ex.label}
                </button>
              ))}
            </div>
          </div>

          {/* Submit Button */}
          <div className="flex items-center justify-between pt-2">
            <span className="text-[11px] text-amber-400/60 font-mono">
              Swiss Ephemeris • Lahiri Ayanamsa
            </span>
            <button
              type="submit"
              disabled={isLoading || !query.trim()}
              className="px-7 py-3 rounded-xl bg-gradient-to-r from-amber-500 via-orange-500 to-red-600 hover:from-amber-400 hover:to-red-500 text-slate-950 font-bold text-xs uppercase tracking-wider shadow-[0_0_20px_rgba(245,158,11,0.4)] disabled:opacity-40 transition flex items-center gap-2"
            >
              {isLoading ? (
                <>
                  <span className="w-3.5 h-3.5 border-2 border-slate-950 border-t-transparent rounded-full animate-spin" />
                  <span>Computing Muhurta...</span>
                </>
              ) : (
                <>
                  <span>Calculate Auspicious Times</span>
                  <span>→</span>
                </>
              )}
            </button>
          </div>
        </form>

        {/* Loading Step Indicator */}
        {isLoading && (
          <div className="pt-3 border-t border-amber-900/40 text-xs text-amber-200/80 flex items-center gap-2.5">
            <span className="w-3.5 h-3.5 border-2 border-amber-500 border-t-transparent rounded-full animate-spin" />
            <span>
              {loadingStep === 1 && 'Extracting constraints & location...'}
              {loadingStep === 2 && 'Computing planetary orbits & eliminating Rahu Kalam...'}
              {loadingStep === 3 && 'Evaluating Nakshatra classes & ranking top 3 windows...'}
            </span>
          </div>
        )}

        {/* Error Alert */}
        {error && (
          <div className="p-4 rounded-xl bg-rose-950/40 border border-rose-500/40 text-xs text-rose-300">
            {error}
          </div>
        )}
      </div>

      {/* ── RESULTS SECTION ─────────────────────────────────────────────── */}
      {plan && (
        <section aria-labelledby="results-title" className="space-y-6">
          {/* Ambiguous Clarification Card */}
          {plan.status === 'needs_clarification' && plan.clarification && (
            <div className="p-6 rounded-2xl bg-amber-950/40 border border-amber-500/40 space-y-3">
              <p className="font-serif font-bold text-amber-200 text-sm">
                {plan.clarification.question}
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {plan.clarification.options.map((opt, i) => (
                  <button
                    key={i}
                    onClick={() => handleCompute(query, opt.category)}
                    className="p-3.5 rounded-xl border border-amber-500/30 bg-[#0C0704] hover:bg-amber-900/30 transition text-left text-xs"
                  >
                    <p className="font-bold text-amber-200">{opt.label}</p>
                    {opt.description && (
                      <p className="text-[11px] text-amber-200/60 mt-1">{opt.description}</p>
                    )}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Results Header */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-amber-900/40">
            <div>
              <div className="flex items-center gap-2.5 flex-wrap">
                <h2 id="results-title" className="text-xl sm:text-2xl font-serif font-bold text-slate-100">
                  Top Auspicious Slots
                </h2>
                {plan.category && (
                  <span className="px-3 py-0.5 rounded-full text-xs font-semibold bg-amber-500/20 text-amber-300 border border-amber-500/40 capitalize">
                    {plan.category.replace('_', ' ')}
                  </span>
                )}
                {plan.override && (
                  <span className="px-3 py-0.5 rounded-full text-xs font-semibold bg-red-500/20 text-red-300 border border-red-500/40 capitalize">
                    {plan.override.replace('_', ' ')}
                  </span>
                )}
              </div>
              <p className="text-xs text-amber-200/60 mt-1">
                {plan.location_name && <span>Location: <strong className="text-amber-200">{plan.location_name}</strong> • </span>}
                <span>Timezone: {plan.timezone || 'Asia/Kolkata'}</span>
              </p>
            </div>
            <span className="text-xs text-amber-400 font-mono">
              30-minute windows • Rahu Kalam Free
            </span>
          </div>

          {/* Tradition Advisory (e.g. Wedding or Griha Pravesh) */}
          {plan.advisory_note && (
            <div className="p-4 rounded-2xl bg-amber-950/40 border border-amber-500/40 text-xs text-amber-200 flex items-start gap-3">
              <span className="text-lg">🪔</span>
              <div>
                <strong className="block text-amber-300 mb-0.5">Vedic Tradition Note:</strong>
                <span className="leading-relaxed">{plan.advisory_note}</span>
              </div>
            </div>
          )}

          {/* General Fallback Notice */}
          {plan.basis === 'general_fallback' && (
            <div className="p-3.5 rounded-xl bg-white/5 border border-amber-500/20 text-xs text-amber-200/80">
              ℹ️ Scored using universal avoidance rules (Rahu Kalam and inauspicious stars).
            </div>
          )}

          {/* Slots Cards */}
          {plan.slots.length === 0 ? (
            <div className="vedic-card-vibrant rounded-2xl p-8 text-center text-amber-200/70 text-xs">
              No auspicious slots found in this window. Try widening your time-of-day or date range.
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {plan.slots.map((slot) => (
                <SlotCard
                  key={slot.id}
                  slot={slot}
                  userTimezone={plan.timezone || 'Asia/Kolkata'}
                  planTitle={plan.raw_text}
                  locationName={plan.location_name || 'Bengaluru'}
                />
              ))}
            </div>
          )}

          {/* Guest Mode Callout */}
          {isGuest && (
            <div className="p-4 rounded-2xl bg-gradient-to-r from-amber-950/40 via-red-950/30 to-amber-950/40 border border-amber-500/30 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-xs text-amber-200/90 shadow-md">
              <div className="flex items-center gap-2.5">
                <span className="text-xl">🪔</span>
                <div>
                  <strong className="block text-amber-300">You are browsing in Guest Mode</strong>
                  <span>Your consultations are kept in this browser. Create an account to sync history across devices and receive Telegram alerts.</span>
                </div>
              </div>
              <div className="flex items-center gap-2 w-full sm:w-auto">
                <Link
                  href="/signup"
                  className="px-3.5 py-1.5 rounded-lg bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs transition text-center whitespace-nowrap"
                >
                  Sign Up Free
                </Link>
                <Link
                  href="/login"
                  className="px-3.5 py-1.5 rounded-lg border border-amber-500/40 hover:bg-white/5 text-amber-200 font-medium text-xs transition text-center whitespace-nowrap"
                >
                  Sign In
                </Link>
              </div>
            </div>
          )}
        </section>
      )}
    </main>
  );
}

export default function PlannerPage() {
  return (
    <Suspense fallback={<div className="p-12 text-center text-amber-400 font-serif">Loading Vedic Muhurta Planner...</div>}>
      <PlannerContent />
    </Suspense>
  );
}
