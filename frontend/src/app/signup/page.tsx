'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { api, ApiError } from '@/lib/api';

interface CityOption {
  city: string;
  tz: string;
  label: string;
}

interface CityGroup {
  group: string;
  options: CityOption[];
}

const CITY_GROUPS: CityGroup[] = [
  {
    group: '⭐ Metros & Major Tech Hubs',
    options: [
      { city: 'Bengaluru', tz: 'Asia/Kolkata', label: 'Bengaluru (Karnataka)' },
      { city: 'Mumbai', tz: 'Asia/Kolkata', label: 'Mumbai (Maharashtra)' },
      { city: 'New Delhi', tz: 'Asia/Kolkata', label: 'New Delhi / NCR' },
      { city: 'Hyderabad', tz: 'Asia/Kolkata', label: 'Hyderabad (Telangana)' },
      { city: 'Chennai', tz: 'Asia/Kolkata', label: 'Chennai (Tamil Nadu)' },
      { city: 'Kolkata', tz: 'Asia/Kolkata', label: 'Kolkata (West Bengal)' },
      { city: 'Pune', tz: 'Asia/Kolkata', label: 'Pune (Maharashtra)' },
      { city: 'Ahmedabad', tz: 'Asia/Kolkata', label: 'Ahmedabad (Gujarat)' },
    ],
  },
  {
    group: '🏛️ North India',
    options: [
      { city: 'Chandigarh', tz: 'Asia/Kolkata', label: 'Chandigarh (Punjab & Haryana)' },
      { city: 'Jaipur', tz: 'Asia/Kolkata', label: 'Jaipur (Rajasthan)' },
      { city: 'Jodhpur', tz: 'Asia/Kolkata', label: 'Jodhpur (Rajasthan)' },
      { city: 'Udaipur', tz: 'Asia/Kolkata', label: 'Udaipur (Rajasthan)' },
      { city: 'Lucknow', tz: 'Asia/Kolkata', label: 'Lucknow (Uttar Pradesh)' },
      { city: 'Kanpur', tz: 'Asia/Kolkata', label: 'Kanpur (Uttar Pradesh)' },
      { city: 'Noida', tz: 'Asia/Kolkata', label: 'Noida / Greater Noida (UP)' },
      { city: 'Gurugram', tz: 'Asia/Kolkata', label: 'Gurugram / Gurgaon (Haryana)' },
      { city: 'Agra', tz: 'Asia/Kolkata', label: 'Agra (Uttar Pradesh)' },
      { city: 'Amritsar', tz: 'Asia/Kolkata', label: 'Amritsar (Punjab)' },
      { city: 'Ludhiana', tz: 'Asia/Kolkata', label: 'Ludhiana (Punjab)' },
      { city: 'Dehradun', tz: 'Asia/Kolkata', label: 'Dehradun (Uttarakhand)' },
      { city: 'Shimla', tz: 'Asia/Kolkata', label: 'Shimla (Himachal Pradesh)' },
      { city: 'Jammu', tz: 'Asia/Kolkata', label: 'Jammu (J&K)' },
      { city: 'Srinagar', tz: 'Asia/Kolkata', label: 'Srinagar (J&K)' },
    ],
  },
  {
    group: '🪔 Sacred & Pilgrimage Centers',
    options: [
      { city: 'Varanasi', tz: 'Asia/Kolkata', label: 'Varanasi / Kashi (Uttar Pradesh)' },
      { city: 'Ayodhya', tz: 'Asia/Kolkata', label: 'Ayodhya (Uttar Pradesh)' },
      { city: 'Prayagraj', tz: 'Asia/Kolkata', label: 'Prayagraj / Allahabad (UP)' },
      { city: 'Mathura', tz: 'Asia/Kolkata', label: 'Mathura & Vrindavan (UP)' },
      { city: 'Haridwar', tz: 'Asia/Kolkata', label: 'Haridwar (Uttarakhand)' },
      { city: 'Rishikesh', tz: 'Asia/Kolkata', label: 'Rishikesh (Uttarakhand)' },
      { city: 'Ujjain', tz: 'Asia/Kolkata', label: 'Ujjain (Madhya Pradesh)' },
      { city: 'Tirupati', tz: 'Asia/Kolkata', label: 'Tirupati (Andhra Pradesh)' },
      { city: 'Puri', tz: 'Asia/Kolkata', label: 'Puri (Odisha)' },
      { city: 'Madurai', tz: 'Asia/Kolkata', label: 'Madurai (Tamil Nadu)' },
      { city: 'Gaya', tz: 'Asia/Kolkata', label: 'Gaya (Bihar)' },
    ],
  },
  {
    group: '🌴 South India',
    options: [
      { city: 'Kochi', tz: 'Asia/Kolkata', label: 'Kochi / Cochin (Kerala)' },
      { city: 'Thiruvananthapuram', tz: 'Asia/Kolkata', label: 'Thiruvananthapuram (Kerala)' },
      { city: 'Kozhikode', tz: 'Asia/Kolkata', label: 'Kozhikode / Calicut (Kerala)' },
      { city: 'Coimbatore', tz: 'Asia/Kolkata', label: 'Coimbatore (Tamil Nadu)' },
      { city: 'Tiruchirappalli', tz: 'Asia/Kolkata', label: 'Trichy (Tamil Nadu)' },
      { city: 'Salem', tz: 'Asia/Kolkata', label: 'Salem (Tamil Nadu)' },
      { city: 'Visakhapatnam', tz: 'Asia/Kolkata', label: 'Visakhapatnam / Vizag (AP)' },
      { city: 'Vijayawada', tz: 'Asia/Kolkata', label: 'Vijayawada (Andhra Pradesh)' },
      { city: 'Warangal', tz: 'Asia/Kolkata', label: 'Warangal (Telangana)' },
      { city: 'Mysuru', tz: 'Asia/Kolkata', label: 'Mysuru / Mysore (Karnataka)' },
      { city: 'Mangaluru', tz: 'Asia/Kolkata', label: 'Mangaluru / Mangalore (Karnataka)' },
      { city: 'Hubballi', tz: 'Asia/Kolkata', label: 'Hubballi-Dharwad (Karnataka)' },
      { city: 'Belagavi', tz: 'Asia/Kolkata', label: 'Belagavi / Belgaum (Karnataka)' },
    ],
  },
  {
    group: '🏰 West & Central India',
    options: [
      { city: 'Surat', tz: 'Asia/Kolkata', label: 'Surat (Gujarat)' },
      { city: 'Vadodara', tz: 'Asia/Kolkata', label: 'Vadodara / Baroda (Gujarat)' },
      { city: 'Rajkot', tz: 'Asia/Kolkata', label: 'Rajkot (Gujarat)' },
      { city: 'Gandhinagar', tz: 'Asia/Kolkata', label: 'Gandhinagar (Gujarat)' },
      { city: 'Nagpur', tz: 'Asia/Kolkata', label: 'Nagpur (Maharashtra)' },
      { city: 'Nashik', tz: 'Asia/Kolkata', label: 'Nashik (Maharashtra)' },
      { city: 'Thane', tz: 'Asia/Kolkata', label: 'Thane & Navi Mumbai (Maharashtra)' },
      { city: 'Chhatrapati Sambhajinagar', tz: 'Asia/Kolkata', label: 'Chhatrapati Sambhajinagar (MH)' },
      { city: 'Indore', tz: 'Asia/Kolkata', label: 'Indore (Madhya Pradesh)' },
      { city: 'Bhopal', tz: 'Asia/Kolkata', label: 'Bhopal (Madhya Pradesh)' },
      { city: 'Gwalior', tz: 'Asia/Kolkata', label: 'Gwalior (Madhya Pradesh)' },
      { city: 'Jabalpur', tz: 'Asia/Kolkata', label: 'Jabalpur (Madhya Pradesh)' },
      { city: 'Raipur', tz: 'Asia/Kolkata', label: 'Raipur (Chhattisgarh)' },
      { city: 'Goa', tz: 'Asia/Kolkata', label: 'Goa / Panaji' },
    ],
  },
  {
    group: '🌄 East & North-East India',
    options: [
      { city: 'Patna', tz: 'Asia/Kolkata', label: 'Patna (Bihar)' },
      { city: 'Ranchi', tz: 'Asia/Kolkata', label: 'Ranchi (Jharkhand)' },
      { city: 'Jamshedpur', tz: 'Asia/Kolkata', label: 'Jamshedpur (Jharkhand)' },
      { city: 'Bhubaneswar', tz: 'Asia/Kolkata', label: 'Bhubaneswar (Odisha)' },
      { city: 'Cuttack', tz: 'Asia/Kolkata', label: 'Cuttack (Odisha)' },
      { city: 'Guwahati', tz: 'Asia/Kolkata', label: 'Guwahati (Assam)' },
      { city: 'Siliguri', tz: 'Asia/Kolkata', label: 'Siliguri (West Bengal)' },
      { city: 'Shillong', tz: 'Asia/Kolkata', label: 'Shillong (Meghalaya)' },
      { city: 'Agartala', tz: 'Asia/Kolkata', label: 'Agartala (Tripura)' },
      { city: 'Imphal', tz: 'Asia/Kolkata', label: 'Imphal (Manipur)' },
    ],
  },
  {
    group: '🌐 International Diaspora',
    options: [
      { city: 'Dubai', tz: 'Asia/Dubai', label: 'Dubai (UAE - GST)' },
      { city: 'London', tz: 'Europe/London', label: 'London (UK - GMT/BST)' },
      { city: 'Singapore', tz: 'Asia/Singapore', label: 'Singapore (SGT)' },
      { city: 'New York', tz: 'America/New_York', label: 'New York (USA - EST/EDT)' },
      { city: 'San Francisco', tz: 'America/Los_Angeles', label: 'San Francisco / Silicon Valley (PST/PDT)' },
      { city: 'Toronto', tz: 'America/Toronto', label: 'Toronto (Canada - EST/EDT)' },
      { city: 'Sydney', tz: 'Australia/Sydney', label: 'Sydney (Australia - AEST)' },
    ],
  },
  {
    group: '✏️ Other Location',
    options: [
      { city: 'OTHER', tz: 'Asia/Kolkata', label: '✍️ Other City / Town (Enter below)' },
    ],
  },
];

const ALL_CITIES: CityOption[] = CITY_GROUPS.flatMap((g) => g.options);

export default function SignupPage() {
  const router = useRouter();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [selectedCity, setSelectedCity] = useState(ALL_CITIES[0]);
  const [isCustomCity, setIsCustomCity] = useState(false);
  const [customCityName, setCustomCityName] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) return;
    setIsLoading(true);
    setError(null);

    const finalCity = isCustomCity && customCityName.trim()
      ? customCityName.trim()
      : selectedCity.city;

    try {
      await api.register({
        name,
        email,
        password,
        default_city: finalCity,
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
              Primary City (for Local Sunrise & Rahu Kalam calculations)
            </label>
            <select
              value={selectedCity.city}
              onChange={(e) => {
                const found = ALL_CITIES.find((c) => c.city === e.target.value);
                if (found) {
                  setSelectedCity(found);
                  if (found.city === 'OTHER') {
                    setIsCustomCity(true);
                  } else {
                    setIsCustomCity(false);
                  }
                }
              }}
              className="w-full px-3.5 py-2 rounded-xl bg-[#090604] border border-amber-500/30 text-xs text-amber-100 focus:border-amber-400 focus:outline-none transition"
            >
              {CITY_GROUPS.map((group) => (
                <optgroup key={group.group} label={group.group} className="bg-[#1a0e08] text-amber-300 font-semibold">
                  {group.options.map((c) => (
                    <option key={c.city} value={c.city} className="bg-[#120B07] text-amber-100 font-normal">
                      {c.label}
                    </option>
                  ))}
                </optgroup>
              ))}
            </select>
          </div>

          {isCustomCity && (
            <div className="space-y-1">
              <label className="block text-xs font-semibold text-amber-200/80">
                Enter Your City or Town Name
              </label>
              <input
                type="text"
                required={isCustomCity}
                value={customCityName}
                onChange={(e) => setCustomCityName(e.target.value)}
                placeholder="e.g. Aligarh, Solapur, Thrissur, Bilaspur..."
                className="w-full px-3.5 py-2 rounded-xl bg-[#090604] border border-amber-500/40 text-xs text-amber-50 placeholder-amber-200/30 focus:border-amber-400 focus:outline-none transition shadow-[0_0_10px_rgba(245,158,11,0.15)]"
              />
              <p className="text-[10px] text-amber-400/60 leading-tight">
                Our astronomical engine will automatically look up the exact coordinates for precise local solar calculations.
              </p>
            </div>
          )}

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
