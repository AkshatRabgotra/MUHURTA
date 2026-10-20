'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import type { UnmappedRequestGroup } from '@/types';
import Link from 'next/link';

export default function AdminUnmappedPage() {
  const [groups, setGroups] = useState<UnmappedRequestGroup[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setIsLoading(true);
    api.getUnmappedAnalytics()
      .then((res) => {
        setGroups(res);
      })
      .catch((err) => {
        setError(err.message || 'Failed to load unmapped requests.');
      })
      .finally(() => {
        setIsLoading(false);
      });
  }, []);

  return (
    <main className="max-w-5xl mx-auto px-4 sm:px-6 py-10 space-y-8">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 tracking-tight">Unmapped & Fallback Requests</h1>
          <p className="text-sm text-gray-500 mt-1">
            Requests routed to <code>general_fallback</code> or with confidence &lt; 0.75. Use this to determine which category rules to author next.
          </p>
        </div>
        <Link
          href="/admin/funnel"
          className="text-sm font-semibold text-indigo-600 hover:text-indigo-800 transition"
        >
          View Funnel Analytics →
        </Link>
      </div>

      {isLoading ? (
        <div className="h-64 bg-white rounded-2xl border border-gray-200 animate-pulse" />
      ) : error ? (
        <div className="rounded-2xl bg-rose-50 border border-rose-200 p-6 text-sm text-rose-800">
          <p className="font-semibold mb-1">Could not load unmapped requests</p>
          <p>{error}</p>
        </div>
      ) : groups.length === 0 ? (
        <div className="bg-white rounded-2xl border border-gray-200 p-12 text-center text-gray-500">
          <p className="font-semibold text-gray-900 text-base mb-1">No unmapped requests found</p>
          <p className="text-sm">All incoming requests have matched defined category or override profiles with high confidence.</p>
        </div>
      ) : (
        <div className="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden">
          <div className="p-6 border-b border-gray-100 flex items-center justify-between">
            <h2 className="text-lg font-bold text-gray-900">High-Priority Clusters to Author ({groups.length})</h2>
            <span className="text-xs text-gray-400">Sorted by frequency</span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-gray-50/80 text-xs uppercase font-semibold text-gray-500 border-b border-gray-200">
                <tr>
                  <th className="py-3.5 px-6">Intent Cluster</th>
                  <th className="py-3.5 px-6">Count</th>
                  <th className="py-3.5 px-6">Latest Request</th>
                  <th className="py-3.5 px-6">Sample Requests</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {groups.map((group, idx) => (
                  <tr key={idx} className="hover:bg-gray-50/50 transition">
                    <td className="py-4 px-6 font-semibold text-gray-900 capitalize">
                      {group.keyword}
                    </td>
                    <td className="py-4 px-6">
                      <span className="inline-flex items-center rounded-full bg-amber-50 border border-amber-200 px-2.5 py-0.5 text-xs font-bold text-amber-800">
                        {group.count}
                      </span>
                    </td>
                    <td className="py-4 px-6 text-gray-600 text-xs max-w-xs truncate" title={group.newest_request}>
                      {group.newest_request}
                    </td>
                    <td className="py-4 px-6 text-xs text-gray-500">
                      <ul className="list-disc list-inside space-y-1">
                        {group.sample_requests.slice(0, 3).map((sample, sIdx) => (
                          <li key={sIdx} className="truncate max-w-sm" title={sample}>
                            {sample}
                          </li>
                        ))}
                      </ul>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </main>
  );
}
