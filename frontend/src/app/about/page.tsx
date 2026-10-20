import Link from 'next/link';

export default function AboutPage() {
  return (
    <main className="max-w-4xl mx-auto px-4 sm:px-6 py-12 sm:py-16 space-y-10">
      {/* Header */}
      <div className="text-center space-y-3">
        <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs font-serif tracking-widest uppercase shadow-[0_0_15px_rgba(245,158,11,0.2)]">
          <span className="animate-diya text-sm">🪔</span>
          <span>Vedic Science & Computation</span>
        </div>
        <h1 className="text-3xl sm:text-5xl font-serif font-bold text-slate-100">
          The Sacred Geometry of Timing
        </h1>
        <p className="text-sm sm:text-base text-amber-100/75 max-w-2xl mx-auto leading-relaxed">
          How Muhurta Planner merges ancient Drik astronomy with deterministic computation to eliminate AI hallucinations.
        </p>
      </div>

      {/* The Core Principle */}
      <div className="vedic-card-vibrant rounded-3xl p-6 sm:p-8 space-y-4">
        <h2 className="text-xl font-serif font-bold text-amber-200">
          The Non-Negotiable Principle: Physics vs. Probability
        </h2>
        <p className="text-xs sm:text-sm text-amber-100/80 leading-relaxed">
          General AI chatbots cannot calculate astronomical coordinates. When asked for Rahu Kalam or Nakshatra timings, raw LLMs invent facts 80% of the time because they predict word sequences rather than solving celestial geometry.
        </p>
        <p className="text-xs sm:text-sm text-amber-100/80 leading-relaxed">
          In <strong>Muhurta Planner</strong>, all planetary coordinates, sunrise/sunset times, and five Panchang factors are computed by a <strong>deterministic engine</strong> using the Swiss Ephemeris (Lahiri Ayanamsa). The LLM is strictly confined to parsing human language and formatting pre-computed facts.
        </p>
      </div>

      {/* 5 Pillars */}
      <div className="vedic-card-vibrant rounded-3xl p-6 sm:p-8 space-y-5">
        <h2 className="text-xl font-serif font-bold text-amber-200">
          The Five Classical Pillars (Panchanga)
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs text-amber-100/80">
          <div className="p-4 bg-black/40 rounded-2xl border border-amber-500/20 space-y-1">
            <strong className="block text-amber-300 font-serif text-sm">1. Tithi (Lunar Day)</strong>
            <span>Exact 12° longitudinal separation between Sun and Moon, split into Shukla and Krishna Paksha.</span>
          </div>
          <div className="p-4 bg-black/40 rounded-2xl border border-amber-500/20 space-y-1">
            <strong className="block text-amber-300 font-serif text-sm">2. Nakshatra (Lunar Mansion)</strong>
            <span>The 27 constellations classified by classical disposition: Dhruva (fixed), Kshipra (swift), Mridu (tender).</span>
          </div>
          <div className="p-4 bg-black/40 rounded-2xl border border-amber-500/20 space-y-1">
            <strong className="block text-amber-300 font-serif text-sm">3. Vara (Weekday)</strong>
            <span>The governing planetary lord of the solar day harmonized with your activity.</span>
          </div>
          <div className="p-4 bg-black/40 rounded-2xl border border-amber-500/20 space-y-1">
            <strong className="block text-amber-300 font-serif text-sm">4. Yoga & Karana</strong>
            <span>Solar-lunar conjunctions and micro-half-tithis filtering obstacles like Vishti.</span>
          </div>
        </div>
      </div>

      {/* Protective Rules */}
      <div className="p-6 rounded-3xl bg-gradient-to-r from-red-950/40 via-amber-950/50 to-orange-950/40 border border-amber-500/40 text-xs text-amber-200 space-y-2">
        <h3 className="text-base font-serif font-bold text-amber-300">
          Universal Protective Avoidances
        </h3>
        <p className="leading-relaxed text-amber-100/80">
          Every candidate window is automatically verified to avoid <strong>Rahu Kalam</strong> (the 90-minute daily inauspicious window), inauspicious Choghadiyas (<em>Udveg</em>, <em>Kaal</em>, <em>Rog</em>), Amavasya (tithi 30), and harsh <em>Tikshna</em> stars.
        </p>
      </div>

      {/* CTA */}
      <div className="text-center pt-2">
        <Link
          href="/planner"
          className="inline-flex items-center gap-2 px-8 py-3.5 rounded-2xl bg-gradient-to-r from-amber-500 via-orange-500 to-red-600 hover:from-amber-400 hover:to-red-500 text-slate-950 font-serif font-bold text-xs uppercase tracking-wider transition shadow-[0_0_20px_rgba(245,158,11,0.3)]"
        >
          <span>Consult the Muhurta Engine Now</span>
          <span>→</span>
        </Link>
      </div>
    </main>
  );
}
