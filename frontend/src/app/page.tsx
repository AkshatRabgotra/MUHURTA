import Link from 'next/link';

const POPULAR_ACTIVITIES = [
  {
    title: 'Rental Agreement',
    desc: 'Sign lease in Bengaluru morning',
    icon: '📜',
    query: 'Sign rental agreement next week morning in Bengaluru',
  },
  {
    title: 'New Job / Joining',
    desc: 'First day at new workplace in Mumbai',
    icon: '💼',
    query: 'Starting my new job next month in Mumbai',
  },
  {
    title: 'Vehicle Delivery',
    desc: 'Taking new car or bike delivery in Delhi',
    icon: '🚗',
    query: 'Taking new car delivery this Friday afternoon in Delhi',
  },
  {
    title: 'Griha Pravesh',
    desc: 'House-warming ceremony in Hyderabad',
    icon: '🪔',
    query: 'Griha Pravesh house warming next month in Hyderabad',
  },
  {
    title: 'Buying Gold & Valuables',
    desc: 'Purchasing jewelry in Chennai',
    icon: '🪙',
    query: 'Purchasing gold jewelry this weekend in Chennai',
  },
  {
    title: 'Celebration & Gathering',
    desc: 'Family anniversary gathering in Pune',
    icon: '🎉',
    query: 'Wedding anniversary family party next Saturday in Pune',
  },
];

const PILLARS = [
  { name: 'Tithi', subtitle: 'Lunar Day (12° Phase)', desc: 'Moon-Sun separation defining Shukla and Krishna Pakshas.', icon: '🌓' },
  { name: 'Vara', subtitle: 'Solar Weekday', desc: 'Planetary ruler of the solar day harmonized with the activity.', icon: '☀️' },
  { name: 'Nakshatra', subtitle: 'Lunar Mansion (27)', desc: 'Disposition of stars: Dhruva, Chara, Mridu, and Kshipra.', icon: '✨' },
  { name: 'Yoga', subtitle: 'Luni-Solar Angle', desc: '27 combined longitudes fostering success (Amrita, Siddhi).', icon: '☸️' },
  { name: 'Karana', subtitle: 'Half-Tithi (6°)', desc: 'Micro-timing units filtering obstacles like Vishti Bhadra.', icon: '⏳' },
];

export default function HomePage() {
  return (
    <main className="min-h-screen">
      {/* ── HERO SECTION ──────────────────────────────────────────────────── */}
      <section className="relative pt-16 pb-20 px-4 sm:px-6 max-w-5xl mx-auto text-center overflow-hidden">
        {/* Animated rotating mandala wheel in background */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[520px] h-[520px] pointer-events-none opacity-10 animate-spin-slow">
          <svg viewBox="0 0 200 200" className="w-full h-full text-amber-500 fill-current">
            <circle cx="100" cy="100" r="90" fill="none" stroke="currentColor" strokeWidth="1" strokeDasharray="4 4" />
            <circle cx="100" cy="100" r="70" fill="none" stroke="currentColor" strokeWidth="1" />
            <polygon points="100,20 120,70 170,70 130,105 145,155 100,125 55,155 70,105 30,70 80,70" fill="none" stroke="currentColor" strokeWidth="1" />
            <polygon points="100,180 120,130 170,130 130,95 145,45 100,75 55,45 70,95 30,130 80,130" fill="none" stroke="currentColor" strokeWidth="0.8" opacity="0.7" />
          </svg>
        </div>

        {/* Sacred Sanskrit Invocation with flickering flame */}
        <div className="inline-flex items-center gap-2.5 px-4 py-1.5 rounded-full bg-gradient-to-r from-red-950/60 via-amber-950/70 to-orange-950/60 border border-amber-500/40 text-amber-200 text-xs font-serif tracking-widest uppercase mb-6 shadow-[0_0_20px_rgba(245,158,11,0.25)]">
          <span className="animate-diya text-sm">🪔</span>
          <span>ॐ शुभस्य शीघ्रम • Vedic Auspicious Timing</span>
          <span className="animate-diya text-sm">🪔</span>
        </div>

        <h1 className="text-4xl sm:text-6xl font-serif font-bold tracking-tight text-slate-100 max-w-3xl mx-auto leading-tight mb-6">
          Synchronize Your Milestone with the{' '}
          <span className="text-flame-gradient block mt-1">Cosmic Rhythm</span>
        </h1>

        <p className="text-sm sm:text-base text-amber-100/80 max-w-2xl mx-auto leading-relaxed mb-10 font-sans">
          Whether signing a lease, taking vehicle delivery, starting a job, or entering a home, our deterministic Swiss Ephemeris engine computes the top 3 Muhurta windows with zero hallucinations.
        </p>

        {/* Big Exciting CTA Button */}
        <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
          <Link
            href="/planner"
            className="w-full sm:w-auto px-8 py-4 rounded-2xl bg-gradient-to-r from-amber-500 via-orange-500 to-red-600 hover:from-amber-400 hover:via-orange-400 hover:to-red-500 text-slate-950 font-serif font-bold text-sm tracking-wide shadow-[0_0_30px_rgba(234,88,12,0.5)] hover:scale-105 transition flex items-center justify-center gap-3 animate-gold-pulse"
          >
            <span className="text-lg">🪔</span>
            <span>Begin Muhurta Consultation</span>
            <span>→</span>
          </Link>

          <Link
            href="/about"
            className="w-full sm:w-auto px-6 py-4 rounded-2xl bg-[#170E09] hover:bg-[#20140D] border border-amber-500/30 text-amber-200 font-semibold text-xs transition"
          >
            How the Science Works
          </Link>
        </div>
      </section>

      {/* ── INTERACTIVE ACTIVITY CARDS ────────────────────────────────────── */}
      <section className="max-w-5xl mx-auto px-4 sm:px-6 py-10 border-t border-amber-900/40">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-xs uppercase font-serif tracking-widest text-amber-400 font-bold">
              Popular Muhurta Categories
            </h2>
            <p className="text-xs text-amber-200/60 mt-0.5">Click any activity to calculate immediately</p>
          </div>
          <Link href="/planner" className="text-xs font-semibold text-amber-400 hover:text-amber-300 transition">
            View All in Planner →
          </Link>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {POPULAR_ACTIVITIES.map((act, idx) => (
            <Link
              key={idx}
              href={`/planner?q=${encodeURIComponent(act.query)}`}
              className="p-5 rounded-2xl vedic-card-vibrant transition group flex items-start gap-3.5 relative overflow-hidden"
            >
              <div className="text-3xl p-2.5 rounded-xl bg-amber-500/10 border border-amber-500/30 group-hover:scale-110 transition shrink-0">
                {act.icon}
              </div>
              <div>
                <h3 className="font-serif font-bold text-amber-100 group-hover:text-amber-300 text-sm">
                  {act.title}
                </h3>
                <p className="text-xs text-amber-200/70 mt-1 line-clamp-2">
                  {act.desc}
                </p>
                <span className="text-[10px] text-amber-400 font-semibold uppercase tracking-wider mt-3 block group-hover:translate-x-1 transition">
                  Calculate Auspicious Times →
                </span>
              </div>
            </Link>
          ))}
        </div>
      </section>

      {/* ── 5 PILLARS OF PANCHANG ────────────────────────────────────────── */}
      <section className="max-w-5xl mx-auto px-4 sm:px-6 py-14">
        <div className="text-center mb-10">
          <span className="text-xs font-serif tracking-widest text-amber-400 uppercase font-bold">
            Ancient Science • Pure Mathematics
          </span>
          <h2 className="text-2xl sm:text-3xl font-serif font-bold text-slate-100 mt-1">
            The Five Deterministic Pillars
          </h2>
          <p className="text-xs sm:text-sm text-amber-200/70 max-w-lg mx-auto mt-2">
            Every 30-minute slot is mathematically computed using the Swiss Ephemeris. Zero AI guesses.
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3.5">
          {PILLARS.map((p, idx) => (
            <div
              key={idx}
              className="p-5 rounded-2xl vedic-card-vibrant space-y-2 flex flex-col justify-between"
            >
              <div>
                <div className="text-2xl mb-2">{p.icon}</div>
                <h3 className="font-serif font-bold text-sm text-amber-200">
                  {p.name}
                </h3>
                <p className="text-[10px] uppercase tracking-wider text-amber-400/80 font-semibold">
                  {p.subtitle}
                </p>
                <p className="text-xs text-amber-100/70 leading-relaxed mt-2">
                  {p.desc}
                </p>
              </div>
              <div className="pt-3 border-t border-amber-900/40 text-[10px] font-mono text-amber-400/50">
                Panchanga #{idx + 1}
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* ── ZERO HALLUCINATION CALLOUT ────────────────────────────────────── */}
      <section className="max-w-5xl mx-auto px-4 sm:px-6 py-10">
        <div className="rounded-3xl bg-gradient-to-br from-red-950/40 via-[#170E09] to-[#0D0805] border border-amber-500/40 p-8 sm:p-10 shadow-[0_0_35px_rgba(245,158,11,0.2)]">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 items-center">
            <div className="space-y-4">
              <span className="px-3 py-1 rounded-full text-[10px] font-serif uppercase tracking-widest bg-amber-500/20 text-amber-300 border border-amber-500/30">
                Why Generic Chatbots Fail
              </span>
              <h3 className="text-2xl sm:text-3xl font-serif font-bold text-slate-100 leading-tight">
                AI Hallucinates. Celestial Physics Does Not.
              </h3>
              <p className="text-xs sm:text-sm text-amber-100/80 leading-relaxed">
                Raw LLMs calculate word probabilities, not planetary coordinates. In this system, the Swiss Ephemeris calculates all planetary degrees with sub-arcsecond accuracy, automatically filtering <em>Rahu Kalam</em> and inauspicious stars.
              </p>
              <div className="pt-2">
                <Link
                  href="/planner"
                  className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs uppercase tracking-wider transition"
                >
                  <span>Try It Yourself</span>
                  <span>→</span>
                </Link>
              </div>
            </div>

            {/* Visual Box */}
            <div className="bg-[#0A0604] rounded-2xl p-5 border border-amber-500/30 font-mono text-xs space-y-2 text-amber-200/90 shadow-inner">
              <p className="text-amber-400 text-[10px] uppercase font-bold tracking-widest pb-1 border-b border-amber-900/40">
                Algorithmic Execution
              </p>
              <p className="text-emerald-400">✓ Natural Intent Parsed</p>
              <p className="text-amber-300">✓ Swiss Ephemeris Coordinates Loaded</p>
              <p className="text-red-400">✕ Rahu Kalam Eliminated</p>
              <p className="text-emerald-400">✓ Top 3 Windows Graded (★ 15.5 pts)</p>
              <p className="text-sky-300">✓ 1-Click Calendar & Telegram Alert</p>
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}
