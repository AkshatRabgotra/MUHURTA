import Link from 'next/link';

export const metadata = {
  title: 'Privacy Policy | Vedic Muhurta Planner',
  description: 'Privacy Policy for Vedic Muhurta Planner application.',
};

export default function PrivacyPage() {
  return (
    <main className="max-w-3xl mx-auto px-4 sm:px-6 py-12 space-y-8 text-amber-100/90 font-sans">
      <div className="space-y-2 border-b border-amber-900/40 pb-6">
        <Link href="/" className="text-xs font-serif text-amber-400 hover:text-amber-300 transition">
          ← Back to Muhurta Planner
        </Link>
        <h1 className="text-3xl font-serif font-bold text-slate-100">Privacy Policy</h1>
        <p className="text-xs text-amber-300/60">Last updated: October 2026</p>
      </div>

      <section className="space-y-4 text-sm leading-relaxed">
        <h2 className="text-lg font-serif font-bold text-amber-300">1. Information We Collect</h2>
        <p>
          When you use Vedic Muhurta Planner, we collect minimal information required to compute auspicious timings:
        </p>
        <ul className="list-disc pl-5 space-y-1.5 text-amber-200/80">
          <li><strong>Account Data:</strong> If you sign in via Google OAuth or email, we receive your email address, name, and profile identifier.</li>
          <li><strong>Consultation Queries:</strong> The activity text, requested location (city), and dates you provide to compute astrological windows.</li>
          <li><strong>Telegram ID:</strong> If you choose to connect your Telegram account for reminders, we store your Telegram chat identifier.</li>
        </ul>
      </section>

      <section className="space-y-4 text-sm leading-relaxed">
        <h2 className="text-lg font-serif font-bold text-amber-300">2. How We Use Your Information</h2>
        <p>
          Your information is used solely to:
        </p>
        <ul className="list-disc pl-5 space-y-1.5 text-amber-200/80">
          <li>Calculate astronomical Panchang and Muhurta factors using the Swiss Ephemeris engine.</li>
          <li>Save and synchronize your previous consultations across devices.</li>
          <li>Deliver scheduled Telegram notifications 1 hour prior to your auspicious timing window (if enabled).</li>
        </ul>
        <p>
          We do <strong>not</strong> sell, rent, or monetize your personal data with third-party advertisers.
        </p>
      </section>

      <section className="space-y-4 text-sm leading-relaxed">
        <h2 className="text-lg font-serif font-bold text-amber-300">3. Google User Data Policy</h2>
        <p>
          Vedic Muhurta Planner requests access only to basic Google profile information (email, name, profile picture) via OAuth 2.0. We do not access, store, or modify your Google Calendar or private emails directly. Calendar events are added directly through your local web browser interface.
        </p>
      </section>

      <section className="space-y-4 text-sm leading-relaxed">
        <h2 className="text-lg font-serif font-bold text-amber-300">4. Contact Us</h2>
        <p>
          If you have any questions regarding this Privacy Policy or your data, please contact us at:
          <br />
          <a href="mailto:akshat0.r28@gmail.com" className="text-amber-400 underline font-semibold">
            akshat0.r28@gmail.com
          </a>
        </p>
      </section>
    </main>
  );
}
