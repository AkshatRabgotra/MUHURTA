'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { api } from '@/lib/api';
import type { PlanRequest } from '@/types';
import SlotCard from '@/components/SlotCard';

export default function PlanDetailPage() {
  const params = useParams();
  const planId = params?.id as string;

  const [plan, setPlan] = useState<PlanRequest | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!planId) return;
    setIsLoading(true);
    api.getPlan(planId)
      .then(setPlan)
      .catch((err) => {
        setError(err.message || 'Failed to load plan details.');
      })
      .finally(() => {
        setIsLoading(false);
      });
  }, [planId]);

  return (
    <main className="max-w-4xl mx-auto px-4 sm:px-6 py-10">
      <div className="mb-6">
        <Link
          href="/plans"
          className="text-sm font-medium text-indigo-600 hover:text-indigo-800 transition"
        >
          ← Back to Plans History
        </Link>
      </div>

      {isLoading ? (
        <div className="space-y-6">
          <div className="h-32 bg-white rounded-2xl border border-gray-200 animate-pulse" />
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-64 bg-white rounded-2xl border border-gray-200 animate-pulse" />
            ))}
          </div>
        </div>
      ) : error || !plan ? (
        <div className="rounded-2xl bg-rose-50 border border-rose-200 p-6 text-sm text-rose-800">
          <p className="font-semibold mb-1">Plan not found</p>
          <p>{error || 'The requested plan could not be retrieved.'}</p>
        </div>
      ) : (
        <div className="space-y-8">
          {/* Metadata Card */}
          <div className="bg-white rounded-2xl border border-gray-200 p-6 sm:p-8 shadow-sm">
            <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
              <span className="inline-flex items-center rounded-md bg-indigo-50 border border-indigo-200 px-3 py-1 text-xs font-semibold text-indigo-700 capitalize">
                {plan.event_type || 'Event'}
              </span>
              <span className="text-xs text-gray-500">
                Created: {new Date(plan.created_at).toLocaleString()}
              </span>
            </div>

            <h1 className="text-xl sm:text-2xl font-bold text-gray-900 mb-4">
              &ldquo;{plan.raw_text}&rdquo;
            </h1>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 pt-4 border-t border-gray-100 text-xs text-gray-600">
              <div>
                <span className="block text-gray-400 font-medium uppercase">Location</span>
                <span className="font-semibold text-gray-800">{plan.location_name || 'Bengaluru'}</span>
              </div>
              <div>
                <span className="block text-gray-400 font-medium uppercase">Timezone</span>
                <span className="font-semibold text-gray-800">{plan.timezone || 'Asia/Kolkata'}</span>
              </div>
              <div>
                <span className="block text-gray-400 font-medium uppercase">Prompt Variant</span>
                <span className="font-semibold text-gray-800">{plan.prompt_variant || 'N/A'}</span>
              </div>
              <div>
                <span className="block text-gray-400 font-medium uppercase">Status</span>
                <span className="font-semibold text-emerald-700">{plan.status}</span>
              </div>
            </div>
          </div>

          {/* Slots Section */}
          <section>
            <h2 className="text-xl font-bold text-gray-900 mb-4">
              Computed Auspicious Slots ({plan.slots.length})
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {plan.slots.map((slot) => (
                <SlotCard
                  key={slot.id}
                  slot={slot}
                  userTimezone={plan.timezone || 'Asia/Kolkata'}
                />
              ))}
            </div>
          </section>
        </div>
      )}
    </main>
  );
}
