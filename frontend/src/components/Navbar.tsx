'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import type { User } from '@/types';

export default function Navbar() {
  const pathname = usePathname();
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    api.getMe()
      .then(setUser)
      .catch(() => setUser(null));
  }, [pathname]);

  const handleLogout = async () => {
    try {
      await api.logout();
      setUser(null);
      router.push('/');
    } catch (err) {
      console.error('Logout failed', err);
    }
  };

  const navLinks = [
    { href: '/', label: 'Home' },
    { href: '/planner', label: 'Find Muhurta', highlight: true },
    { href: '/plans', label: 'History' },
    { href: '/about', label: 'About' },
  ];

  return (
    <header className="border-b border-amber-900/40 bg-[#0D0805]/90 backdrop-blur-md sticky top-0 z-50">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
        {/* Brand */}
        <div className="flex items-center gap-7">
          <Link href="/" className="flex items-center gap-2.5 group">
            {/* Animated Diya emblem */}
            <div className="w-9 h-9 rounded-full bg-gradient-to-tr from-red-600 via-amber-500 to-amber-300 p-0.5 shadow-[0_0_15px_rgba(245,158,11,0.5)] group-hover:scale-105 transition">
              <div className="w-full h-full rounded-full bg-[#120B07] flex items-center justify-center">
                <span className="text-amber-400 font-serif font-bold text-base animate-diya">
                  🪔
                </span>
              </div>
            </div>

            <div className="flex flex-col">
              <span className="text-lg font-serif font-bold tracking-wide text-flame-gradient">
                MUHURTA
              </span>
              <span className="text-[9px] uppercase tracking-widest text-amber-400/90 -mt-1 font-sans font-semibold">
                Vedic Engine
              </span>
            </div>
          </Link>

          {/* Navigation Links */}
          <nav className="hidden md:flex items-center gap-1.5">
            {navLinks.map((link) => {
              const active = pathname === link.href;
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
                    link.highlight
                      ? 'bg-gradient-to-r from-amber-500 to-orange-600 text-slate-950 font-bold shadow-[0_0_12px_rgba(245,158,11,0.3)] hover:brightness-110'
                      : active
                      ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                      : 'text-amber-100/70 hover:text-amber-200 hover:bg-white/5'
                  }`}
                >
                  {link.label}
                </Link>
              );
            })}
          </nav>
        </div>

        {/* Right side actions */}
        <div className="flex items-center gap-3">
          {/* Telegram Pill */}
          <a
            href="https://t.me/VedicMuhurtaBot"
            target="_blank"
            rel="noopener noreferrer"
            className="hidden sm:inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-sky-950/60 border border-sky-500/40 text-sky-300 hover:bg-sky-900/60 transition shadow-sm"
          >
            <span className="text-xs">✈️</span>
            <span>@VedicMuhurtaBot</span>
          </a>

          {user ? (
            <div className="flex items-center gap-3">
              <Link
                href="/settings"
                className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-amber-500/30 bg-amber-950/30 hover:bg-amber-900/40 transition text-xs text-amber-200"
              >
                <span className="w-5 h-5 rounded-full bg-amber-500 text-slate-950 flex items-center justify-center font-bold text-[10px]">
                  {user.name ? user.name[0].toUpperCase() : 'U'}
                </span>
                <span className="hidden sm:inline font-medium">
                  {user.name || user.email.split('@')[0]}
                </span>
              </Link>
              <button
                onClick={handleLogout}
                className="text-xs text-amber-200/50 hover:text-rose-400 transition"
              >
                Logout
              </button>
            </div>
          ) : (
            <div className="flex items-center gap-2">
              <Link
                href="/login"
                className="px-3 py-1.5 rounded-lg text-xs font-semibold text-amber-100 hover:text-amber-300 transition"
              >
                Sign In
              </Link>
              <Link
                href="/signup"
                className="px-3.5 py-1.5 rounded-lg text-xs font-bold bg-gradient-to-r from-amber-500 via-orange-500 to-red-600 text-white shadow-[0_0_15px_rgba(234,88,12,0.4)] hover:brightness-110 transition"
              >
                Sign Up
              </Link>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
