import Link from 'next/link';

export const metadata = {
  title: 'Terms of Service | Vedic Muhurta Planner',
  description: 'Terms of Service for Vedic Muhurta Planner.',
};

export default function TermsPage() {
  return (
    <main className="max-w-3xl mx-auto px-4 sm:px-6 py-12 space-y-8 text-amber-100/90 font-sans">
      <div className="space-y-2 border-b border-amber-900/40 pb-6">
        <Link href="/" className="text-xs font-serif text-amber-400 hover:text-amber-300 transition">
          ← Back to Muhurta Planner
        </Link>
        <h1 className="text-3xl font-serif font-bold text-slate-100">Terms of Service</h1>
        <p className="text-xs text-amber-300/60">Last updated: October 2026</p>
      </div>

      <section className="space-y-4 text-sm leading-relaxed">
        <h2 className="text-lg font-serif font-bold text-amber-300">1. Acceptance of Terms</h2>
        <p>
          By accessing and using Vedic Muhurta Planner, you agree to comply with and be bound by these Terms of Service.
        </p>
      </section>

      <section className="space-y-4 text-sm leading-relaxed">
        <h2 className="text-lg font-serif font-bold text-amber-300">2. Service Description & Astrology Disclaimer</h2>
        <p>
          Vedic Muhurta Planner provides astronomical timing calculations based on classical Vedic astrological texts (Muhurta Chintamani, Brihat Samhita) and the Swiss Ephemeris.
        </p>
        <p className="p-4 rounded-xl bg-amber-950/40 border border-amber-500/30 text-amber-200 text-xs">
          <strong>Disclaimer:</strong> Astrological recommendations and Muhurta scores are provided for spiritual, cultural, and planning guidance only. They do not constitute legal, medical, financial, or architectural advice. Users exercise their own judgment for personal and business milestones.
        </p>
      </section>

      <section className="space-y-4 text-sm leading-relaxed">
        <h2 className="text-lg font-serif font-bold text-amber-300">3. Contact</h2>
        <p>
          For inquiries or support, contact:{' '}
          <a href="mailto:akshat0.r28@gmail.com" className="text-amber-400 underline font-semibold">
            akshat0.r28@gmail.com
          </a>
        </p>
      </section>
    </main>
  );
}
