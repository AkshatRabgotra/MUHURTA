'use client';

import { useState } from 'react';
import type { Slot } from '@/types';
import { api, downloadSlotIcs } from '@/lib/api';

interface SlotCardProps {
  slot: Slot;
  userTimezone?: string;
  planTitle?: string;
  locationName?: string;
  onAddedToCalendar?: (slotId: string) => void;
}

export default function SlotCard({
  slot,
  userTimezone = 'Asia/Kolkata',
  planTitle = 'Auspicious Muhurta',
  locationName = 'Bengaluru',
  onAddedToCalendar,
}: SlotCardProps) {
  const [calendarStatus, setCalendarStatus] = useState<'idle' | 'loading' | 'added' | 'error'>('idle');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [feedbackRating, setFeedbackRating] = useState<number | null>(null);

  const formatSlotTime = (isoString: string) => {
    try {
      return new Intl.DateTimeFormat('en-US', {
        timeZone: userTimezone,
        weekday: 'short',
        month: 'short',
        day: 'numeric',
        hour: 'numeric',
        minute: '2-digit',
        hour12: true,
      }).format(new Date(isoString));
    } catch {
      return new Date(isoString).toLocaleString();
    }
  };

  const handleAddToCalendar = async () => {
    setErrorMessage(null);
    try {
      // 1. Instantly open Google Calendar with prefilled event details
      const title = encodeURIComponent(`Auspicious Muhurta: ${planTitle}`);
      const details = encodeURIComponent(slot.explanation_text || 'Calculated via Vedic Muhurta Engine');
      const location = encodeURIComponent(locationName || '');
      const startIso = slot.start_utc.replace(/[-:]/g, '').split('.')[0] + 'Z';
      const endIso = slot.end_utc.replace(/[-:]/g, '').split('.')[0] + 'Z';
      const gcalUrl = `https://calendar.google.com/calendar/render?action=TEMPLATE&text=${title}&dates=${startIso}/${endIso}&details=${details}&location=${location}`;
      window.open(gcalUrl, '_blank');

      setCalendarStatus('added');
      if (onAddedToCalendar) onAddedToCalendar(slot.id);

      // 2. Silently attempt backend sync for Telegram reminders if user is logged in
      api.addToCalendar(slot.id).catch(() => {
        // Safe to ignore for guests
      });
    } catch {
      setCalendarStatus('error');
    }
  };

  const handleDownloadIcs = () => {
    downloadSlotIcs(slot, planTitle, locationName);
  };

  const handleFeedback = async (rating: 1 | -1) => {
    setFeedbackRating(rating);
    try {
      await api.submitFeedback(slot.id, rating);
    } catch (err) {
      console.error('Failed to submit feedback', err);
    }
  };

  return (
    <div className="vedic-card-vibrant rounded-2xl p-5 transition flex flex-col justify-between group">
      <div>
        {/* Top Header: Rank & Score */}
        <div className="flex items-center justify-between mb-3">
          <span className="inline-flex items-center gap-1.5 px-3 py-0.5 rounded-full text-xs font-serif font-bold bg-amber-500/20 text-amber-300 border border-amber-500/40">
            Slot #{slot.rank}
          </span>
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-lg text-xs font-bold bg-emerald-950/60 text-emerald-300 border border-emerald-500/40">
            ★ {slot.score.toFixed(1)} pts
          </span>
        </div>

        {/* Date and Time */}
        <div className="mb-3">
          <p className="text-base sm:text-lg font-serif font-bold text-amber-100 group-hover:text-amber-200 transition leading-snug">
            {formatSlotTime(slot.start_utc)}
          </p>
          <p className="text-xs text-amber-300/60 mt-0.5">
            to {formatSlotTime(slot.end_utc)} ({userTimezone})
          </p>
        </div>

        {/* Explanation */}
        <p className="text-xs text-amber-100/90 leading-relaxed mb-4 bg-black/40 p-3 rounded-xl border border-amber-900/40">
          {slot.explanation_text || 'Auspicious timing aligned with classical Vedic Muhurta principles.'}
        </p>

        {/* Factors Breakdown */}
        {slot.reasons && slot.reasons.length > 0 && (
          <div className="mb-4">
            <p className="text-[10px] font-serif font-bold uppercase tracking-widest text-amber-400 mb-1.5">
              Planetary Alignments
            </p>
            <div className="flex flex-wrap gap-1.5">
              {slot.reasons.map((r, i) => (
                <span
                  key={i}
                  className="inline-flex items-center gap-1 rounded-md bg-white/5 border border-amber-500/20 px-2 py-0.5 text-[11px] text-amber-200"
                >
                  <span className="text-amber-400/60">{r.factor}:</span> {r.value}
                  <span className="text-emerald-400 font-semibold">(+{r.points})</span>
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Footer Actions */}
      <div className="pt-3 border-t border-amber-900/40 space-y-2">
        <div className="flex items-center gap-1.5">
          {/* Google Calendar Button */}
          <button
            onClick={handleAddToCalendar}
            disabled={calendarStatus === 'loading' || calendarStatus === 'added'}
            className={`flex-1 flex items-center justify-center gap-1.5 rounded-xl py-2 px-3 text-xs font-bold transition shadow-sm ${
              calendarStatus === 'added'
                ? 'bg-emerald-950/70 text-emerald-300 border border-emerald-500/40'
                : 'bg-gradient-to-r from-amber-500 to-orange-600 hover:from-amber-400 hover:to-orange-500 text-slate-950'
            }`}
          >
            {calendarStatus === 'loading'
              ? 'Adding...'
              : calendarStatus === 'added'
              ? '✓ Added to Cal'
              : '+ Google Cal'}
          </button>

          {/* .ICS Download Button */}
          <button
            onClick={handleDownloadIcs}
            title="Download universal .ics for Apple / Outlook / Mobile"
            className="px-2.5 py-2 rounded-xl border border-amber-500/30 bg-white/5 hover:bg-white/10 text-amber-200 text-xs font-medium transition"
          >
            .ICS
          </button>

          {/* Telegram Reminder */}
          <a
            href="https://t.me/VedicMuhurtaBot"
            target="_blank"
            rel="noopener noreferrer"
            title="Open @VedicMuhurtaBot for reminders"
            className="p-2 rounded-xl border border-sky-500/40 bg-sky-950/40 hover:bg-sky-900/60 text-sky-300 text-xs transition"
          >
            ✈️
          </a>

          {/* Feedback */}
          <div className="flex items-center gap-0.5 border-l border-amber-900/40 pl-1.5">
            <button
              onClick={() => handleFeedback(1)}
              className={`p-1 rounded text-xs transition ${
                feedbackRating === 1 ? 'text-emerald-400 font-bold' : 'text-amber-200/40 hover:text-amber-200'
              }`}
            >
              👍
            </button>
            <button
              onClick={() => handleFeedback(-1)}
              className={`p-1 rounded text-xs transition ${
                feedbackRating === -1 ? 'text-rose-400 font-bold' : 'text-amber-200/40 hover:text-amber-200'
              }`}
            >
              👎
            </button>
          </div>
        </div>

        {errorMessage && (
          <p className="text-[11px] text-amber-300 text-center">
            {errorMessage}
          </p>
        )}
      </div>
    </div>
  );
}
