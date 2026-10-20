'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import type { TelegramLinkResponse, User } from '@/types';

const COMMON_TIMEZONES = [
  'Asia/Kolkata',
  'Asia/Dubai',
  'Asia/Singapore',
  'Asia/Tokyo',
  'Europe/London',
  'America/New_York',
  'America/Los_Angeles',
];

export default function SettingsPage() {
  const [user, setUser] = useState<User | null>(null);
  const [timezone, setTimezone] = useState('Asia/Kolkata');
  const [defaultCity, setDefaultCity] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  const [telegramLink, setTelegramLink] = useState<TelegramLinkResponse | null>(null);
  const [isGeneratingTelegram, setIsGeneratingTelegram] = useState(false);

  useEffect(() => {
    api.getMe()
      .then((data) => {
        setUser(data);
        if (data.timezone) setTimezone(data.timezone);
        if (data.default_city) setDefaultCity(data.default_city);
      })
      .catch((err) => console.error('Failed to load user', err));
  }, []);

  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    setSaveSuccess(false);
    try {
      const updated = await api.updateMe({
        timezone,
        default_city: defaultCity,
      });
      setUser(updated);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err) {
      console.error('Failed to update profile', err);
    } finally {
      setIsSaving(false);
    }
  };

  const handleGenerateTelegramCode = async () => {
    setIsGeneratingTelegram(true);
    try {
      const res = await api.linkTelegram();
      setTelegramLink(res);
    } catch (err) {
      console.error('Failed to generate Telegram code', err);
    } finally {
      setIsGeneratingTelegram(false);
    }
  };

  return (
    <main className="max-w-2xl mx-auto px-4 sm:px-6 py-10 space-y-6">
      <div className="pb-3 border-b border-stone-200">
        <h1 className="text-2xl font-serif font-bold text-stone-900 tracking-tight">
          Settings & Coordinates
        </h1>
        <p className="text-xs text-stone-500 mt-0.5">
          Configure default calculation city and automated calendar reminders.
        </p>
      </div>

      {/* Preferences Form */}
      <div className="bg-white rounded-2xl border border-stone-200 p-6 shadow-sm space-y-4">
        <h2 className="text-sm font-semibold text-stone-800">
          Default Location
        </h2>
        <form onSubmit={handleSaveProfile} className="space-y-4">
          <div>
            <label htmlFor="timezone-select" className="block text-xs font-medium text-stone-600 mb-1">
              Timezone
            </label>
            <select
              id="timezone-select"
              value={timezone}
              onChange={(e) => setTimezone(e.target.value)}
              className="w-full rounded-xl border border-stone-200 px-3 py-2 text-xs text-stone-900 focus:border-amber-600 outline-none transition"
            >
              {COMMON_TIMEZONES.map((tz) => (
                <option key={tz} value={tz}>
                  {tz}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label htmlFor="city-input" className="block text-xs font-medium text-stone-600 mb-1">
              Default City
            </label>
            <input
              id="city-input"
              type="text"
              value={defaultCity}
              onChange={(e) => setDefaultCity(e.target.value)}
              placeholder="e.g. Bengaluru, India"
              className="w-full rounded-xl border border-stone-200 px-3 py-2 text-xs text-stone-900 placeholder-stone-400 focus:border-amber-600 outline-none transition"
            />
          </div>

          <div className="flex items-center justify-between pt-1">
            <button
              type="submit"
              disabled={isSaving}
              className="px-5 py-2 rounded-xl bg-amber-700 hover:bg-amber-800 text-white font-semibold text-xs shadow-sm disabled:opacity-50 transition"
            >
              {isSaving ? 'Saving...' : 'Save Settings'}
            </button>
            {saveSuccess && (
              <span className="text-xs text-emerald-700 font-medium">
                ✓ Saved successfully
              </span>
            )}
          </div>
        </form>
      </div>

      {/* Telegram Link Card */}
      <div className="bg-white rounded-2xl border border-stone-200 p-6 shadow-sm space-y-3">
        <h2 className="text-sm font-semibold text-stone-800">
          Telegram Reminders
        </h2>
        <p className="text-xs text-stone-600 leading-relaxed">
          Connect our bot <strong className="text-stone-900">@VedicMuhurtaBot</strong> to receive an alert 24 hours before your chosen auspicious timing.
        </p>

        {user?.telegram_chat_id ? (
          <div className="rounded-xl bg-emerald-50 border border-emerald-200 p-3 text-xs text-emerald-800 flex items-center justify-between">
            <span>✓ Connected to Telegram (Chat ID: {user.telegram_chat_id})</span>
          </div>
        ) : (
          <div className="space-y-3 pt-1">
            <button
              onClick={handleGenerateTelegramCode}
              disabled={isGeneratingTelegram}
              className="px-4 py-2 rounded-xl border border-stone-300 bg-stone-50 hover:bg-stone-100 text-stone-800 font-medium text-xs transition"
            >
              {isGeneratingTelegram ? 'Connecting...' : 'Connect @VedicMuhurtaBot →'}
            </button>

            {telegramLink && (
              <div className="p-3.5 rounded-xl bg-amber-50 border border-amber-200 text-xs space-y-1.5">
                <p className="text-amber-900">
                  Open Telegram and send <code>/start {telegramLink.code}</code>:
                </p>
                <a
                  href={telegramLink.deep_link}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-block font-mono text-amber-800 underline font-semibold text-xs"
                >
                  {telegramLink.deep_link}
                </a>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Google Calendar */}
      <div className="bg-white rounded-2xl border border-stone-200 p-6 shadow-sm space-y-2">
        <h2 className="text-sm font-semibold text-stone-800">
          Google Calendar Integration
        </h2>
        <p className="text-xs text-stone-600">
          Authenticate with Google to add Muhurta slots to your primary calendar with one click.
        </p>
        <div className="pt-2">
          <a
            href={api.getGoogleLoginUrl()}
            className="inline-block px-4 py-2 rounded-xl border border-stone-300 bg-stone-50 hover:bg-stone-100 text-stone-800 font-medium text-xs transition"
          >
            Authorize Google Calendar ↗
          </a>
        </div>
      </div>
    </main>
  );
}
