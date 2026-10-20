import Link from 'next/link';

export const metadata = {
  title: 'About The Vedic Science & Panchanga | Muhurta Planner',
  description: 'Understanding the 5 classical limbs of Panchanga and deterministic astronomical calculation.',
};

const FIVE_PILLARS = [
  {
    num: '1',
    name: 'Tithi',
    subtitle: 'Lunar Day',
    icon: '🌓',
    desc: 'The exact 12° longitudinal separation between the Moon and Sun, creating 30 Tithis across Shukla (waxing) and Krishna (waning) Pakshas.',
  },
  {
    num: '2',
    name: 'Vara',
    subtitle: 'Solar Weekday',
    icon: '☀️',
    desc: 'The 7 planetary rulers of each solar day (Ravivara through Shanivara). Each planet governs specific activities and temporal energies.',
  },
  {
    num: '3',
    name: 'Nakshatra',
    subtitle: 'Lunar Mansion',
    icon: '✨',
    desc: 'The 27 asterisms classified by classical disposition: Dhruva (fixed for construction), Chara (movable for vehicles), Mridu (tender for celebrations), and Kshipra (swift for agreements).',
  },
  {
    num: '4',
    name: 'Yoga',
    subtitle: 'Luni-Solar Conjunction',
    icon: '☸️',
    desc: 'The 27 angular relationships obtained by adding the longitudes of the Sun and Moon. Auspicious Yogas like Siddhi and Amrita foster success, while Vishkambha is avoided.',
  },
  {
    num: '5',
    name: 'Karana',
    subtitle: 'Half-Lunar Day',
    icon: '⏳',
    desc: 'Half of a Tithi (6° separation). There are 11 Karanas in total. Inauspicious Karanas like Vishti (Bhadra) are strictly avoided for starting any major milestone.',
  },
];

export default function AboutPage() {
  return (
    <main className="max-w-5xl mx-auto px-4 sm:px-6 py-12 sm:py-16 space-y-12">
      {/* ── HEADER ──────────────────────────────────────────────────────── */}
      <div className="text-center space-y-3">
        <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs font-serif tracking-widest uppercase shadow-[0_0_15px_rgba(245,158,11,0.2)]">
          <span className="animate-diya text-sm">🪔</span>
          <span>Vedic Science & Computation</span>
        </div>
        <h1 className="text-3xl sm:text-5xl font-serif font-bold text-slate-100 tracking-tight">
          The Sacred Geometry of Timing
        </h1>
        <p className="text-sm sm:text-base text-amber-100/75 max-w-2xl mx-auto leading-relaxed">
          How Muhurta Planner merges ancient Drik astronomy with deterministic computation to eliminate AI hallucinations.
        </p>
      </div>

      {/* ── THE CORE PRINCIPLE ───────────────────────────────────────────── */}
      <div className="vedic-card-vibrant rounded-3xl p-6 sm:p-8 space-y-4">
        <div className="flex items-center gap-3 border-b border-amber-900/40 pb-3">
          <span className="text-2xl">⚖️</span>
          <h2 className="text-xl font-serif font-bold text-amber-200">
            The Non-Negotiable Principle: Physics vs. Probability
          </h2>
        </div>
        <p className="text-xs sm:text-sm text-amber-100/80 leading-relaxed">
          General AI chatbots cannot calculate astronomical coordinates. When asked for Rahu Kalam or Nakshatra timings, raw LLMs invent facts over 80% of the time because they predict word sequences rather than solving celestial geometry.
        </p>
        <p className="text-xs sm:text-sm text-amber-100/80 leading-relaxed">
          In <strong>Muhurta Planner</strong>, all planetary coordinates, sunrise/sunset times, and five Panchang factors are computed by a <strong>deterministic engine</strong> using the Swiss Ephemeris (Lahiri Ayanamsa). The LLM is strictly confined to parsing natural human language and formatting pre-computed facts.
        </p>
      </div>

      {/* ── 5 PILLARS (PANCHANGA) ────────────────────────────────────────── */}
      <div className="vedic-card-vibrant rounded-3xl p-6 sm:p-8 space-y-6">
        <div>
          <div className="inline-flex items-center gap-2 text-xs font-serif text-amber-400 uppercase tracking-widest font-bold">
            <span>Pancha (Five) + Anga (Limbs)</span>
          </div>
          <h2 className="text-xl sm:text-2xl font-serif font-bold text-slate-100 mt-1">
            The Five Classical Pillars of Panchanga
          </h2>
          <p className="text-xs sm:text-sm text-amber-200/70 mt-1">
            Every candidate 30-minute Muhurta slot is evaluated against all 5 classical limbs simultaneously:
          </p>
        </div>

        {/* 5 Distinct Cards in a Balanced Responsive Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {FIVE_PILLARS.map((p) => (
            <div
              key={p.num}
              className="p-5 bg-black/40 rounded-2xl border border-amber-500/20 hover:border-amber-500/40 transition space-y-2.5 flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between">
                  <span className="text-2xl">{p.icon}</span>
                  <span className="px-2 py-0.5 rounded-md text-[10px] font-mono font-bold bg-amber-500/10 text-amber-300 border border-amber-500/30">
                    Pillar #{p.num}
                  </span>
                </div>
                <h3 className="font-serif font-bold text-base text-amber-100 mt-2">
                  {p.num}. {p.name}
                </h3>
                <p className="text-[11px] font-semibold text-amber-400/90 uppercase tracking-wider">
                  {p.subtitle}
                </p>
                <p className="text-xs text-amber-100/70 leading-relaxed mt-2">
                  {p.desc}
                </p>
              </div>
            </div>
          ))}

          {/* 6th Card: Choghadiya Precision (Bonus classical system) */}
          <div className="p-5 bg-gradient-to-br from-amber-950/30 to-black/60 rounded-2xl border border-amber-500/30 space-y-2.5 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between">
                <span className="text-2xl">⏳</span>
                <span className="px-2 py-0.5 rounded-md text-[10px] font-mono font-bold bg-emerald-500/10 text-emerald-300 border border-emerald-500/30">
                  Micro-Timing
                </span>
              </div>
              <h3 className="font-serif font-bold text-base text-amber-100 mt-2">
                Choghadiya Periods
              </h3>
              <p className="text-[11px] font-semibold text-emerald-400/90 uppercase tracking-wider">
                Amrit • Shubh • Labh
              </p>
              <p className="text-xs text-amber-100/70 leading-relaxed mt-2">
                Each day and night is divided into eight 90-minute segments. The engine prioritizes nectar periods (Amrit, Shubh, Labh) and filters out Rog, Udveg, and Kaal.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* ── UNIVERSAL PROTECTIVE AVOIDANCES ─────────────────────────────── */}
      <div className="p-6 sm:p-8 rounded-3xl bg-gradient-to-r from-red-950/40 via-amber-950/50 to-orange-950/40 border border-amber-500/40 space-y-4 shadow-lg">
        <div className="flex items-center gap-3 border-b border-amber-900/40 pb-3">
          <span className="text-2xl">🛡️</span>
          <div>
            <h3 className="text-lg font-serif font-bold text-amber-300">
              Universal Protective Avoidances
            </h3>
            <p className="text-xs text-amber-200/70">Hard filters applied before any score is calculated</p>
          </div>
        </div>
        <p className="text-xs sm:text-sm leading-relaxed text-amber-100/80">
          Every candidate window is automatically cross-checked and discarded if it falls during:
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3 text-xs">
          <div className="p-3 bg-black/50 rounded-xl border border-rose-500/30 text-rose-200">
            <strong className="block text-rose-300 mb-0.5">Rahu Kalam</strong>
            <span>90-minute daily malefic solar slice governed by Rahu.</span>
          </div>
          <div className="p-3 bg-black/50 rounded-xl border border-rose-500/30 text-rose-200">
            <strong className="block text-rose-300 mb-0.5">Inauspicious Choghadiya</strong>
            <span>Segments of Udveg (anxiety), Kaal (loss), and Rog (illness).</span>
          </div>
          <div className="p-3 bg-black/50 rounded-xl border border-rose-500/30 text-rose-200">
            <strong className="block text-rose-300 mb-0.5">Amavasya (Tithi 30)</strong>
            <span>New moon phase traditionally avoided for worldly milestones.</span>
          </div>
          <div className="p-3 bg-black/50 rounded-xl border border-rose-500/30 text-rose-200">
            <strong className="block text-rose-300 mb-0.5">Vishti Karana (Bhadra)</strong>
            <span>Turbulent micro-half-tithi bringing obstacles.</span>
          </div>
        </div>
      </div>

      {/* ── CTA ─────────────────────────────────────────────────────────── */}
      <div className="text-center pt-4 pb-6 space-y-3">
        <Link
          href="/planner"
          className="inline-flex items-center gap-2.5 px-8 py-3.5 rounded-2xl bg-gradient-to-r from-amber-500 via-orange-500 to-red-600 hover:from-amber-400 hover:to-red-500 text-slate-950 font-serif font-bold text-xs uppercase tracking-wider transition shadow-[0_0_25px_rgba(245,158,11,0.4)]"
        >
          <span>Calculate Your Muhurta Now</span>
          <span>→</span>
        </Link>
        <p className="text-xs text-amber-300/60 font-sans">
          Fast, deterministic, and free to use.
        </p>
      </div>
    </main>
  );
}
