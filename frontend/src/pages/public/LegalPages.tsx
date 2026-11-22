import React from 'react';

export const PrivacyPage: React.FC = () => {
  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-16 space-y-8 font-sans text-xs text-[#5C5752] leading-relaxed">
      <div className="space-y-2 border-b border-[#E8E4DC] pb-4">
        <span className="font-mono text-xs uppercase tracking-widest text-[#7A5F2B]">
          STATUTORY LEGAL NOTICE
        </span>
        <h1 className="font-serif text-3xl font-medium text-[#1A1714]">
          Privacy Policy & DPDP Alignment
        </h1>
        <p className="font-mono text-[11px] text-[#7A746A]">
          Effective Date: 22 November 2026 · Pending Formal Legal Counsel Review
        </p>
      </div>

      <section className="space-y-3">
        <h2 className="font-serif text-lg text-[#1A1714]">1. Institutional Framework</h2>
        <p>
          AUDRYN operates as an on-premise and local decision-support tool for Chartered Accountants. This policy reflects alignment with India's Digital Personal Data Protection Act, 2023 and the DPDP Rules, 2025 (notified under G.S.R. 846(E) on 13 November 2025).
        </p>
      </section>

      <section className="space-y-3">
        <h2 className="font-serif text-lg text-[#1A1714]">2. Data Processing & Egress</h2>
        <p>
          In default configurations, financial documents and LLM inference run locally on the auditor's workstation via Ollama. No client financial figures are transmitted to commercial third-party LLM providers. Network-level packet capture verification is required before making absolute zero-egress guarantees.
        </p>
      </section>

      <section className="space-y-3">
        <h2 className="font-serif text-lg text-[#1A1714]">3. Data Fiduciary Contact</h2>
        <p className="font-mono text-[11px] bg-[#F6F3EB] p-3 border border-[#E8E4DC]">
          Compliance Officer: [Owner to supply appointed DPO]<br />
          Contact Email: [Owner to supply legal@firm.example]<br />
          Address: [Owner to supply registered office]
        </p>
      </section>
    </div>
  );
};

export const TermsPage: React.FC = () => {
  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-16 space-y-8 font-sans text-xs text-[#5C5752] leading-relaxed">
      <div className="space-y-2 border-b border-[#E8E4DC] pb-4">
        <span className="font-mono text-xs uppercase tracking-widest text-[#7A5F2B]">
          TERMS OF USE
        </span>
        <h1 className="font-serif text-3xl font-medium text-[#1A1714]">
          Terms of Service & Disclaimer
        </h1>
        <p className="font-mono text-[11px] text-[#7A746A]">
          Effective Date: 22 November 2026 · Pending Formal Legal Counsel Review
        </p>
      </div>

      <section className="space-y-3">
        <h2 className="font-serif text-lg text-[#1A1714]">1. No Statutory Audit Opinion</h2>
        <p>
          AUDRYN is not a chartered accounting firm and does not provide statutory audit opinions, tax certifications, or formal attestations. The system provides decision support only. Responsibility for all audit opinions rests entirely with the signing Chartered Accountant.
        </p>
      </section>
    </div>
  );
};

export const CookiePage: React.FC = () => {
  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-16 space-y-8 font-sans text-xs text-[#5C5752] leading-relaxed">
      <div className="space-y-2 border-b border-[#E8E4DC] pb-4">
        <span className="font-mono text-xs uppercase tracking-widest text-[#7A5F2B]">
          COOKIE & LOCAL STORAGE POLICY
        </span>
        <h1 className="font-serif text-3xl font-medium text-[#1A1714]">
          Cookie & Preference Disclosure
        </h1>
        <p className="font-mono text-[11px] text-[#7A746A]">
          Effective Date: 22 November 2026 · Pending Formal Legal Counsel Review
        </p>
      </div>

      <section className="space-y-3">
        <h2 className="font-serif text-lg text-[#1A1714]">1. Essential Storage Only</h2>
        <p>
          AUDRYN does not use third-party marketing or tracking cookies. Local storage is strictly reserved for essential accessibility preferences:
        </p>
        <ul className="list-disc list-inside space-y-1 font-mono text-[11px] bg-[#F6F3EB] p-3 border border-[#E8E4DC]">
          <li><code>audryn_reduced_effects</code>: Stores user preference for visual motion reduction.</li>
        </ul>
      </section>
    </div>
  );
};

export const DemoThankYouPage: React.FC<{ onNavigate: (path: string) => void }> = ({ onNavigate }) => {
  return (
    <div className="max-w-2xl mx-auto px-4 py-24 text-center space-y-6">
      <div className="w-12 h-12 mx-auto bg-[#1A7A40]/10 border border-[#1A7A40] flex items-center justify-center text-[#1A7A40] font-bold">
        ✓
      </div>
      <h1 className="font-serif text-3xl text-[#1A1714]">
        Demonstration Request Simulation Complete
      </h1>
      <p className="font-sans text-xs text-[#5C5752] leading-relaxed max-w-md mx-auto">
        This is a client-side prototype demonstration. No external server transmission occurred. In production, this form will connect directly to the firm's verified demonstration intake service.
      </p>
      <button
        onClick={() => onNavigate('/')}
        className="px-5 py-2.5 bg-[#1A1714] text-[#F6F3EB] text-xs font-mono font-semibold"
      >
        Return to Home
      </button>
    </div>
  );
};

export const NotFoundPage: React.FC<{ onNavigate: (path: string) => void }> = ({ onNavigate }) => {
  return (
    <div className="max-w-2xl mx-auto px-4 py-24 text-center space-y-6">
      <div className="font-mono text-4xl font-bold text-[#7A5F2B]">404</div>
      <h1 className="font-serif text-2xl text-[#1A1714]">Record Not Found</h1>
      <p className="font-sans text-xs text-[#5C5752] max-w-sm mx-auto">
        The requested URL or evidence record does not exist in AUDRYN’s working paper manifest.
      </p>
      <button
        onClick={() => onNavigate('/')}
        className="px-4 py-2 bg-[#1A1714] text-[#F6F3EB] text-xs font-mono font-semibold"
      >
        Return to Home
      </button>
    </div>
  );
};
