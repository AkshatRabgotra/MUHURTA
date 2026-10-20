'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import type { FunnelData } from '@/types';

export default function AdminFunnelPage() {
  const [funnelData, setFunnelData] = useState<FunnelData[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setIsLoading(true);
    api.getFunnel()
      .then((res) => {
        setFunnelData(res.variants);
      })
      .catch((err) => {
        setError(err.message || 'Failed to load funnel analytics.');
      })
      .finally(() => {
        setIsLoading(false);
      });
  }, []);

  const steps = [
    { key: 'request_created', label: 'Requests Created' },
    { key: 'slots_viewed', label: 'Slots Viewed' },
    { key: 'slot_added_to_calendar', label: 'Added to Calendar' },
    { key: 'reminder_sent', label: 'Reminders Sent' },
    { key: 'feedback_given', label: 'Feedback Given' },
  ] as const;

  return (
    <main className="max-w-5xl mx-auto px-4 sm:px-6 py-10 space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 tracking-tight">Experimentation & Funnel Analytics</h1>
        <p className="text-sm text-gray-500 mt-1">
          A/B Prompt Variant Performance Comparison (<code>explain_v1</code> vs <code>explain_v2</code>).
        </p>
      </div>

      {isLoading ? (
        <div className="h-64 bg-white rounded-2xl border border-gray-200 animate-pulse" />
      ) : error ? (
        <div className="rounded-2xl bg-rose-50 border border-rose-200 p-6 text-sm text-rose-800">
          <p className="font-semibold mb-1">Could not load analytics</p>
          <p>{error}</p>
        </div>
      ) : (
        <div className="space-y-8">
          {/* Funnel Metrics Table */}
          <div className="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden">
            <div className="p-6 border-b border-gray-100">
              <h2 className="text-lg font-bold text-gray-900">Funnel Progression Table</h2>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="bg-gray-50/80 text-xs uppercase font-semibold text-gray-500 border-b border-gray-200">
                  <tr>
                    <th className="px-6 py-3.5">Prompt Variant</th>
                    <th className="px-6 py-3.5">Requests</th>
                    <th className="px-6 py-3.5">Slots Viewed</th>
                    <th className="px-6 py-3.5">Calendar Adds</th>
                    <th className="px-6 py-3.5">Reminders</th>
                    <th className="px-6 py-3.5">Feedback</th>
                    <th className="px-6 py-3.5">Conversion</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {funnelData.map((v) => (
                    <tr key={v.prompt_variant} className="hover:bg-gray-50/50">
                      <td className="px-6 py-4 font-mono font-bold text-indigo-700">
                        {v.prompt_variant}
                      </td>
                      <td className="px-6 py-4 text-gray-700">{v.request_created}</td>
                      <td className="px-6 py-4 text-gray-700">{v.slots_viewed}</td>
                      <td className="px-6 py-4 font-semibold text-emerald-700">
                        {v.slot_added_to_calendar}
                      </td>
                      <td className="px-6 py-4 text-gray-700">{v.reminder_sent}</td>
                      <td className="px-6 py-4 text-gray-700">{v.feedback_given}</td>
                      <td className="px-6 py-4 font-bold text-indigo-900">
                        {v.conversion_rate_viewed_to_calendar}%
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Visual Bar Comparison */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {funnelData.map((variant) => {
              const maxVal = Math.max(
                variant.request_created,
                variant.slots_viewed,
                variant.slot_added_to_calendar,
                1
              );

              return (
                <div
                  key={variant.prompt_variant}
                  className="bg-white rounded-2xl border border-gray-200 p-6 shadow-sm space-y-4"
                >
                  <div className="flex items-center justify-between pb-3 border-b border-gray-100">
                    <h3 className="font-bold text-gray-900 font-mono">
                      {variant.prompt_variant}
                    </h3>
                    <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-indigo-50 text-indigo-700">
                      Conv: {variant.conversion_rate_viewed_to_calendar}%
                    </span>
                  </div>

                  <div className="space-y-3">
                    {steps.map((st) => {
                      const count = variant[st.key] || 0;
                      const percentage = Math.round((count / maxVal) * 100);

                      return (
                        <div key={st.key}>
                          <div className="flex justify-between text-xs text-gray-600 mb-1">
                            <span>{st.label}</span>
                            <span className="font-semibold">{count}</span>
                          </div>
                          <div className="w-full bg-gray-100 rounded-full h-2.5 overflow-hidden">
                            <div
                              className="bg-indigo-600 h-2.5 rounded-full transition-all duration-500"
                              style={{ width: `${Math.max(percentage, 3)}%` }}
                            />
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </main>
  );
}
