'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { api, ApiError } from '@/lib/api';

const CITIES = [
  { city: 'Bengaluru', tz: 'Asia/Kolkata', label: 'Bengaluru (IST)' },
  { city: 'Mumbai', tz: 'Asia/Kolkata', label: 'Mumbai (IST)' },
  { city: 'Delhi', tz: 'Asia/Kolkata', label: 'Delhi (IST)' },
  { city: 'Hyderabad', tz: 'Asia/Kolkata', label: 'Hyderabad (IST)' },
  { city: 'Chennai', tz: 'Asia/Kolkata', label: 'Chennai (IST)' },
  { city: 'London', tz: 'Europe/London', label: 'London (GMT/BST)' },
  { city: 'New York', tz: 'America/New_York', label: 'New York (EST/EDT)' },
];

export default function SignupPage() {
  const router = useRouter();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [selectedCity, setSelectedCity] = useState(CITIES[0]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) return;
    setIsLoading(true);
    setError(null);

    try {
      await api.register({
        name,
        email,
        password,
        default_city: selectedCity.city,
        timezone: selectedCity.tz,
      });
      router.push('/planner');
    } catch (err: any) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError('Sign up failed. Please check your information.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <main className="min-h-[80vh] flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-sm vedic-card-vibrant rounded-3xl p-7 sm:p-8 space-y-5 animate-gold-pulse">
        {/* Header */}
        <div className="text-center space-y-2">
          <div className="w-11 h-11 mx-auto rounded-full bg-gradient-to-tr from-red-600 via-amber-500 to-amber-300 p-0.5 shadow-[0_0_15px_rgba(245,158,11,0.5)]">
            <div className="w-full h-full rounded-full bg-[#120B07] flex items-center justify-center">
              <span className="text-amber-400 font-serif font-bold text-lg animate-diya">
                🪔
              </span>
            </div>
          </div>
          <h1 className="text-xl font-serif font-bold text-slate-100">
            Create Your Account
          </h1>
          <p className="text-xs text-amber-200/60">
            Set your primary city for local astronomical calculations
          </p>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="p-3.5 rounded-xl bg-rose-950/40 border border-rose-500/40 text-rose-300 text-xs">
            {error}
          </div>
        )}

        {/* Google Sign In */}
        <a
          href={api.getGoogleLoginUrl()}
          className="w-full py-2.5 px-4 rounded-xl bg-white hover:bg-amber-50 text-slate-900 font-semibold text-xs transition flex items-center justify-center gap-2.5 shadow-sm"
        >
          <svg className="w-4 h-4" viewBox="0 0 24 24">
            <path
              fill="#4285F4"
              d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
            />
            <path
              fill="#34A853"
              d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
            />
            <path
              fill="#FBBC05"
              d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"
            />
            <path
              fill="#EA4335"
              d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"
            />
          </svg>
          <span>Sign up with Google</span>
        </a>

        <div className="relative flex items-center justify-center">
          <div className="border-t border-amber-900/40 w-full" />
          <span className="bg-[#120B07] px-2 text-[10px] text-amber-400/60 uppercase tracking-widest font-mono">
            or with email
          </span>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-3">
          <div>
            <label className="block text-xs font-semibold text-amber-200/80 mb-1">
              Full Name
            </label>
            <input
              type="text"
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Arjun"
              className="w-full px-3.5 py-2 rounded-xl bg-[#090604] border border-amber-500/30 text-xs text-amber-50 placeholder-amber-200/30 focus:border-amber-400 focus:outline-none transition"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-amber-200/80 mb-1">
              Email
            </label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              className="w-full px-3.5 py-2 rounded-xl bg-[#090604] border border-amber-500/30 text-xs text-amber-50 placeholder-amber-200/30 focus:border-amber-400 focus:outline-none transition"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-amber-200/80 mb-1">
              Password
            </label>
            <input
              type="password"
              required
              minLength={6}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              className="w-full px-3.5 py-2 rounded-xl bg-[#090604] border border-amber-500/30 text-xs text-amber-50 placeholder-amber-200/30 focus:border-amber-400 focus:outline-none transition"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-amber-200/80 mb-1">
              Primary City
            </label>
            <select
              value={selectedCity.city}
              onChange={(e) => {
                const found = CITIES.find((c) => c.city === e.target.value);
                if (found) setSelectedCity(found);
              }}
              className="w-full px-3.5 py-2 rounded-xl bg-[#090604] border border-amber-500/30 text-xs text-amber-100 focus:border-amber-400 focus:outline-none transition"
            >
              {CITIES.map((c) => (
                <option key={c.city} value={c.city} className="bg-[#120B07] text-amber-100">
                  {c.label}
                </option>
              ))}
            </select>
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full py-2.5 rounded-xl bg-gradient-to-r from-amber-500 via-orange-500 to-red-600 hover:from-amber-400 hover:to-red-500 text-slate-950 font-bold text-xs uppercase tracking-wider shadow-[0_0_15px_rgba(245,158,11,0.3)] disabled:opacity-40 transition mt-2"
          >
            {isLoading ? 'Creating Account...' : 'Complete Sign Up'}
          </button>
        </form>

        {/* Footer */}
        <p className="text-center text-xs text-amber-200/60">
          Already registered?{' '}
          <Link href="/login" className="text-amber-400 font-semibold hover:underline">
            Sign In
          </Link>
        </p>
      </div>
    </main>
  );
}
