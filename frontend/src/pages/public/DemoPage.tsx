import React, { useState } from 'react';
import { ArrowRight, AlertCircle } from 'lucide-react';

interface DemoPageProps {
  onNavigate: (path: string) => void;
}

export const DemoPage: React.FC<DemoPageProps> = ({ onNavigate }) => {
  const [formData, setFormData] = useState({
    name: '',
    workEmail: '',
    firm: '',
    message: '',
    consent: false,
  });
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.name.trim() || !formData.workEmail.trim() || !formData.firm.trim()) {
      setError('Please complete all required fields (Name, Professional Email, Firm Name).');
      return;
    }
    if (!formData.consent) {
      setError('Consent to process your contact details is required under DPDP guidelines.');
      return;
    }
    setError(null);
    onNavigate('/demo-thank-you');
  };

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-16 space-y-8">
      <div className="space-y-3">
        <span className="font-mono text-xs uppercase tracking-widest text-[#7A5F2B]">
          TECHNICAL DEMONSTRATION
        </span>
        <h1 className="font-serif text-3xl sm:text-4xl font-medium text-[#1A1714] tracking-tight">
          Schedule an audit walk-through.
        </h1>
        <p className="font-sans text-xs sm:text-sm text-[#3A3632] leading-relaxed">
          See AUDRYN’s multi-agent counter-evidence challenge, deterministic Decimal calculations, and report manifest generator in action.
        </p>
      </div>

      {/* Prototype Notice */}
      <div className="p-3 bg-[#E8E4DC] border border-[#7A746A] flex items-center gap-2 text-xs font-mono text-[#1A1714]">
        <AlertCircle className="w-4 h-4 text-[#7A5F2B] shrink-0" aria-hidden="true" />
        <span>PROTOTYPE NOTICE: Demonstration intake is currently running in client simulation mode.</span>
      </div>

      <form onSubmit={handleSubmit} noValidate className="bg-white border border-[#E8E4DC] p-8 space-y-6">
        {error && (
          <div role="alert" className="p-3 bg-[#C0392B]/10 border border-[#C0392B] text-xs font-mono text-[#C0392B]">
            {error}
          </div>
        )}

        <div className="space-y-1">
          <label htmlFor="name" className="block font-mono text-xs font-semibold text-[#1A1714]">
            Auditor / Partner Name *
          </label>
          <input
            id="name"
            type="text"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            className="w-full px-3 py-2 border border-[#7A746A] text-xs font-sans focus:outline-none focus:ring-2 focus:ring-[#7A5F2B]"
            placeholder="e.g. CA Rajesh K. Sharma"
          />
        </div>

        <div className="space-y-1">
          <label htmlFor="workEmail" className="block font-mono text-xs font-semibold text-[#1A1714]">
            Professional / Firm Email *
          </label>
          <input
            id="workEmail"
            type="email"
            value={formData.workEmail}
            onChange={(e) => setFormData({ ...formData, workEmail: e.target.value })}
            className="w-full px-3 py-2 border border-[#7A746A] text-xs font-sans focus:outline-none focus:ring-2 focus:ring-[#7A5F2B]"
            placeholder="e.g. rajesh@firm.example"
          />
        </div>

        <div className="space-y-1">
          <label htmlFor="firm" className="block font-mono text-xs font-semibold text-[#1A1714]">
            Firm Name & City *
          </label>
          <input
            id="firm"
            type="text"
            value={formData.firm}
            onChange={(e) => setFormData({ ...formData, firm: e.target.value })}
            className="w-full px-3 py-2 border border-[#7A746A] text-xs font-sans focus:outline-none focus:ring-2 focus:ring-[#7A5F2B]"
            placeholder="e.g. Sharma Batliboi & Associates, Mumbai"
          />
        </div>

        <div className="space-y-1">
          <label htmlFor="message" className="block font-mono text-xs font-semibold text-[#1A1714]">
            Key Audit Areas of Interest (Optional)
          </label>
          <textarea
            id="message"
            rows={3}
            value={formData.message}
            onChange={(e) => setFormData({ ...formData, message: e.target.value })}
            className="w-full px-3 py-2 border border-[#7A746A] text-xs font-sans focus:outline-none focus:ring-2 focus:ring-[#7A5F2B]"
            placeholder="e.g. Section 115BAA corporate tax reconciliation, 180-day depreciation tests..."
          />
        </div>

        {/* DPDP Consent Notice */}
        <div className="pt-2 flex items-start gap-3">
          <input
            id="consent"
            type="checkbox"
            checked={formData.consent}
            onChange={(e) => setFormData({ ...formData, consent: e.target.checked })}
            className="mt-0.5 w-4 h-4 border border-[#7A746A] accent-[#7A5F2B] focus:ring-2 focus:ring-[#7A5F2B]"
          />
          <label htmlFor="consent" className="font-sans text-[11px] text-[#3A3632] leading-snug">
            I agree that AUDRYN may contact me regarding this product demonstration in accordance with our{' '}
            <button
              type="button"
              onClick={() => onNavigate('/legal/privacy')}
              className="text-[#1A1714] underline font-medium"
            >
              Privacy Policy
            </button>. Data will not be shared with external third parties.
          </label>
        </div>

        <button
          type="submit"
          className="w-full py-3 bg-[#1A1714] text-[#F6F3EB] text-xs font-mono font-semibold tracking-wider hover:bg-[#2A2826] transition-colors focus:ring-2 focus:ring-[#7A5F2B] flex items-center justify-center gap-2"
        >
          Submit Demonstration Request (Simulation)
          <ArrowRight className="w-4 h-4" aria-hidden="true" />
        </button>
      </form>
    </div>
  );
};
