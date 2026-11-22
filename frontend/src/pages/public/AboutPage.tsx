import React from 'react';
import { Building2, Users2, ShieldCheck, Scale } from 'lucide-react';

export const AboutPage: React.FC = () => {
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16 space-y-12">
      <div className="max-w-3xl space-y-4">
        <span className="font-mono text-xs uppercase tracking-widest text-[#7A5F2B]">
          ORGANIZATION & ETHOS
        </span>
        <h1 className="font-serif text-3xl sm:text-4xl lg:text-5xl font-medium text-[#1A1714] tracking-tight">
          Built for the rigors of statutory audit.
        </h1>
        <p className="font-sans text-base text-[#5C5752] leading-relaxed">
          AUDRYN was conceived by audit practitioners and systems engineers to bring deterministic mathematical verification and multi-agent counter-evidence challenge to statutory audit teams.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 pt-6">
        <div className="bg-white border border-[#E8E4DC] p-6 space-y-3">
          <Scale className="w-5 h-5 text-[#7A5F2B]" aria-hidden="true" />
          <h2 className="font-serif text-xl text-[#1A1714]">The Core Ethos</h2>
          <p className="font-sans text-xs text-[#5C5752] leading-relaxed">
            In modern statutory audits, financial data is fragmented across ERPs, spreadsheets, and banking portals. Auditors are pressured to accept black-box AI conclusions. AUDRYN rejects black-box automation: we enforce an unbroken chain of physical vouchers, mathematical proof, and counter-evidence scrutiny before any conclusion is drawn.
          </p>
        </div>

        <div className="bg-white border border-[#E8E4DC] p-6 space-y-3">
          <Building2 className="w-5 h-5 text-[#7A5F2B]" aria-hidden="true" />
          <h2 className="font-serif text-xl text-[#1A1714]">Target Audience</h2>
          <p className="font-sans text-xs text-[#5C5752] leading-relaxed">
            Audit Associates, Senior Auditors, Audit Managers, and Partners at small and mid-sized Chartered Accountancy firms who require rigor, traceability, and defensibility under ICAI Peer Review and NFRA scrutiny.
          </p>
        </div>
      </div>

      {/* Owner-Supplied Corporate Information Placeholders */}
      <div className="bg-[#F6F3EB] border border-[#E8E4DC] p-6 space-y-3 font-mono text-xs">
        <span className="text-[#7A5F2B] font-bold block uppercase">
          CORPORATE DETAILS (OWNER-SUPPLIED INFORMATION)
        </span>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-[#5C5752]">
          <div>Registered Address: [Owner to supply corporate headquarters]</div>
          <div>Corporate Identity Number (CIN): [Owner to supply CIN / LLPIN]</div>
          <div>Statutory Auditor Contact: [Owner to supply compliance contact]</div>
          <div>Principal Place of Business: India</div>
        </div>
      </div>
    </div>
  );
};
