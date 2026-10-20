import type { Metadata } from 'next';
import { Cinzel, Plus_Jakarta_Sans } from 'next/font/google';
import { Analytics } from '@vercel/analytics/next';
import './globals.css';
import Navbar from '@/components/Navbar';

const cinzel = Cinzel({
  subsets: ['latin'],
  variable: '--font-cinzel',
  display: 'swap',
});

const plusJakarta = Plus_Jakarta_Sans({
  subsets: ['latin'],
  variable: '--font-sans',
  display: 'swap',
});

export const metadata: Metadata = {
  title: 'Muhurta — Vedic Auspicious Timing',
  description: 'Deterministic Vedic Panchang calculation for life milestones with zero hallucinations.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`${cinzel.variable} ${plusJakarta.variable}`}>
      <body className="min-h-screen bg-[#0A0604] text-amber-50 font-sans antialiased selection:bg-amber-600 selection:text-white flex flex-col relative overflow-x-hidden">
        {/* Subtle glowing ambient lighting */}
        <div className="fixed inset-0 pointer-events-none z-0 bg-[radial-gradient(ellipse_80%_60%_at_50%_-10%,rgba(234,88,12,0.22),transparent_70%)]" />
        <div className="fixed inset-0 pointer-events-none z-0 bg-[radial-gradient(ellipse_60%_50%_at_50%_100%,rgba(220,38,38,0.15),transparent_70%)]" />
        <div className="fixed inset-0 pointer-events-none z-0 opacity-15 bg-[radial-gradient(#f59e0b_1px,transparent_1px)] [background-size:28px_28px]" />

        <div className="relative z-10 flex flex-col min-h-screen">
          <Navbar />
          <div className="flex-1">
            {children}
          </div>
          <footer className="border-t border-amber-900/40 bg-[#070402]/90 backdrop-blur-md py-6 px-4 text-center text-xs text-amber-200/60">
            <div className="max-w-6xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-3">
              <div className="flex items-center gap-2">
                <span className="text-amber-500 font-serif font-bold text-base animate-pulse">ॐ</span>
                <span className="font-serif font-bold text-amber-100">Muhurta Planner</span>
                <span>• Traditional Drik Panchang (Lahiri Ayanamsa)</span>
              </div>
              <div className="flex items-center gap-4 text-amber-300/70">
                <a href="/about" className="hover:text-amber-200 transition">About</a>
                <span>•</span>
                <a href="/privacy" className="hover:text-amber-200 transition">Privacy Policy</a>
                <span>•</span>
                <a href="/terms" className="hover:text-amber-200 transition">Terms</a>
              </div>
            </div>
          </footer>
        </div>
        <Analytics />
      </body>
    </html>
  );
}
