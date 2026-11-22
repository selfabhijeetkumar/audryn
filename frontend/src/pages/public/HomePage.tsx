import React, { useState } from 'react';
import { ArrowRight, Lock } from 'lucide-react';
import { LedgerFolioScene, calculateStageAndInterpolation } from '../../components/scene/LedgerFolioScene';

interface HomePageProps {
  onNavigate: (path: string) => void;
}

// Exact chapter midpoints for direct stepping (Task 1 hold ranges)
const STAGE_MIDPOINTS = [0.05, 0.20, 0.35, 0.50, 0.65, 0.80, 0.95];

export const HomePage: React.FC<HomePageProps> = ({ onNavigate }) => {
  const [scrollProgress, setScrollProgress] = useState<number>(0.05);

  const { activeStage } = calculateStageAndInterpolation(scrollProgress);

  const chapters = [
    {
      stage: 0,
      slug: 'S0: THE PROBLEM (0%–10% HOLD)',
      title: 'Scattered financial evidence',
      body: 'Financial records arrive in scattered fragments across trial balances, bank statements, tax returns and supplier invoices. Conclusions are difficult to trace back to source vouchers.',
      evidence: '40 disordered source vouchers and spreadsheets awaiting extraction.',
    },
    {
      stage: 1,
      slug: 'S1: EXTRACTION (15%–25% HOLD)',
      title: 'Deterministic record extraction',
      body: 'OCR and layout parsers extract tabular figures with cryptographic SHA-256 provenance hashes. Every extracted cell remembers its source document and page coordinates.',
      evidence: 'SHA-256: e3b0c44298fc1c14... Page 14, Bounding Box [88, 120, 240, 48].',
    },
    {
      stage: 2,
      slug: 'S2: VERIFICATION (30%–40% HOLD)',
      title: 'Zero floating-point arithmetic',
      body: 'Financial reconciliations execute in Python Decimal arithmetic. Variance calculations eliminate IEEE-754 rounding errors. Calculation ticks certify mathematical correctness only.',
      evidence: 'Calculated Variance: ₹ 45,00,000.00 exact Decimal difference.',
    },
    {
      stage: 3,
      slug: 'S3: RELATIONSHIPS (45%–55% HOLD)',
      title: 'Statutory tax rulebooks',
      body: 'Multi-agent intelligence maps cross-year journal entries against statutory sections of the Income-tax Act, 1961 (Sections 115BAA, 32, 50, and 44AB).',
      evidence: 'Mapped block depreciation rules and 180-day addition thresholds.',
    },
    {
      stage: 4,
      slug: 'S4: CHALLENGE (60%–70% HOLD)',
      title: 'Independent counter-evidence',
      body: 'An independent reviewer agent searches for contradictory evidence and alternative explanations before any anomaly is proposed. Findings are never assumed to be fraud.',
      evidence: 'Verdict: PARTIALLY_SUPPORTED. Delivery note indicates subsequent dispatch.',
    },
    {
      stage: 5,
      slug: 'S5: HUMAN JUDGMENT (75%–85% HOLD)',
      title: 'Licensed auditor sign-off',
      body: 'AUDRYN proposes; licensed Chartered Accountants decide. The interface reserves brass accents exclusively for human statutory approval. No autonomous opinions.',
      evidence: 'CA Sign-Off Stamp: ICAI Membership No. 084920 · Timestamp recorded.',
    },
    {
      stage: 6,
      slug: 'S6: ACCOUNTABILITY (90%–100% HOLD)',
      title: 'Reproducible working papers',
      body: 'The audit working paper binds into an indexed report manifest. Unresolved items and incomplete checks are prominently disclosed on the report face.',
      evidence: 'Manifest Hash: 9f86d081... Status: DRAFT · 1 Unresolved Item Disclosed.',
    },
  ];

  return (
    <main id="main-content" className="w-full">
      {/* Hero Section — Meets Section 11 First-Screen Contract */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-16 pb-12 border-b border-[#E8E4DC]">
        <div className="max-w-3xl space-y-6">
          <div className="inline-flex items-center gap-2 px-3 py-1 bg-[#E8E4DC] border border-[#7A746A] text-xs font-mono text-[#1A1714]">
            <Lock className="w-3.5 h-3.5 text-[#7A5F2B]" aria-hidden="true" />
            <span>AUDIT DECISION-SUPPORT SYSTEM FOR CA & ACCOUNTING FIRMS</span>
          </div>

          <h1 className="font-serif text-4xl sm:text-5xl lg:text-6xl font-medium tracking-tight text-[#1A1714] leading-[1.12]">
            Evidence before conclusions.
          </h1>

          <p className="font-sans text-base sm:text-lg text-[#3A3632] leading-relaxed">
            AUDRYN is an evidence-first audit intelligence system for CA and accounting firms. It traces proposed findings to their sources, challenges them with counter-evidence, and leaves decisions to human reviewers.
          </p>

          <div className="pt-2 flex flex-wrap items-center gap-4">
            <button
              onClick={() => onNavigate('/request-demo')}
              className="px-6 py-3 bg-[#1A1714] text-[#F6F3EB] text-xs font-mono font-semibold tracking-wider hover:bg-[#2A2826] transition-colors focus:ring-2 focus:ring-[#7A5F2B] flex items-center gap-2"
            >
              Request a Demonstration
              <ArrowRight className="w-4 h-4" aria-hidden="true" />
            </button>

            <button
              onClick={() => onNavigate('/platform')}
              className="px-6 py-3 border border-[#1A1714] text-[#1A1714] text-xs font-mono font-semibold tracking-wider hover:bg-[#E8E4DC] transition-colors focus:ring-2 focus:ring-[#7A5F2B]"
            >
              See How It Works
            </button>
          </div>
        </div>
      </section>

      {/* 3D Continuous Scroll Section — The Indexed Ledger Folio */}
      <section className="bg-[#121110] text-[#F6F3EB] py-16 border-b border-[#2A2724]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="mb-6 flex flex-col md:flex-row md:items-end justify-between gap-4">
            <div>
              <span className="font-mono text-xs uppercase tracking-widest text-[#B08D4F]">
                PHYSICAL AUDIT GRAMMAR · EXACT 7 HOLDS & 6 TRANSITIONS
              </span>
              <h2 className="font-serif text-2xl sm:text-3xl text-[#F6F3EB] mt-1">
                The Indexed Ledger Folio
              </h2>
            </div>

            {/* Stage Stepper Navigation (Jumps to exact hold midpoint) */}
            <div className="flex flex-wrap items-center gap-1.5 font-mono text-xs" role="tablist" aria-label="3D Ledger Stages">
              {chapters.map((ch, idx) => (
                <button
                  key={ch.stage}
                  role="tab"
                  aria-selected={activeStage === ch.stage}
                  onClick={() => setScrollProgress(STAGE_MIDPOINTS[idx])}
                  className={`px-2.5 py-1 text-[11px] border transition-colors focus:outline-none focus:ring-1 focus:ring-[#B08D4F] ${
                    activeStage === ch.stage
                      ? 'bg-[#B08D4F] text-[#121110] font-bold border-[#B08D4F]'
                      : 'bg-[#1E1C1A] text-[#9C968F] border-[#3A3632] hover:border-[#B08D4F]'
                  }`}
                >
                  S{ch.stage}
                </button>
              ))}
            </div>
          </div>

          {/* Continuous Scroll Scrubber Bar */}
          <div className="mb-6 bg-[#1A1816] border border-[#2A2724] p-3 flex items-center gap-4 font-mono text-xs">
            <span className="text-[#B08D4F] shrink-0 text-[11px]">SCROLL SCRUBBER:</span>
            <input
              type="range"
              min="0"
              max="1"
              step="0.005"
              value={scrollProgress}
              onChange={(e) => setScrollProgress(parseFloat(e.target.value))}
              className="w-full accent-[#B08D4F] cursor-pointer"
              aria-label="Continuous 3D Ledger Scroll Progress"
            />
            <span className="text-[#9C968F] shrink-0 text-[11px] min-w-[50px] text-right">
              {Math.round(scrollProgress * 100)}%
            </span>
          </div>

          {/* Interactive Split View: 3D Scene + Active Chapter Narrative */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
            {/* 3D Canvas Container (Single Shared WebGL Context) */}
            <div className="lg:col-span-7 h-[480px] sm:h-[540px] bg-[#1A1816] border border-[#2A2724]">
              <LedgerFolioScene scrollProgress={scrollProgress} />
            </div>

            {/* Synchronized Chapter Narrative Card */}
            <div className="lg:col-span-5 space-y-6">
              <div className="bg-[#1A1816] border border-[#2A2724] p-6 space-y-4">
                <div className="flex items-center justify-between text-xs font-mono text-[#B08D4F]">
                  <span>{chapters[activeStage].slug}</span>
                  <span className="text-[#9C968F]">CHAPTER {activeStage + 1} OF 7</span>
                </div>

                <h3 className="font-serif text-xl sm:text-2xl text-[#F6F3EB]">
                  {chapters[activeStage].title}
                </h3>

                <p className="font-sans text-xs sm:text-sm text-[#E8E4DC] leading-relaxed">
                  {chapters[activeStage].body}
                </p>

                <div className="pt-4 border-t border-[#2A2724] font-mono text-xs space-y-1">
                  <span className="text-[10px] text-[#9C968F] uppercase tracking-wider block">
                    INSPECTABLE EVIDENCE RECORD:
                  </span>
                  <p className="text-[#F6F3EB] text-[11px] bg-[#121110] p-2 border border-[#2A2724]">
                    {chapters[activeStage].evidence}
                  </p>
                </div>
              </div>

              <div className="flex items-center justify-between font-mono text-xs">
                <button
                  disabled={activeStage === 0}
                  onClick={() => setScrollProgress(STAGE_MIDPOINTS[Math.max(0, activeStage - 1)])}
                  className="px-3 py-1.5 border border-[#3A3632] text-[#9C968F] hover:text-[#F6F3EB] disabled:opacity-30 disabled:pointer-events-none"
                >
                  ← Previous Hold
                </button>

                <span className="text-[#9C968F]">SYNTHETIC DATA</span>

                <button
                  disabled={activeStage === chapters.length - 1}
                  onClick={() => setScrollProgress(STAGE_MIDPOINTS[Math.min(chapters.length - 1, activeStage + 1)])}
                  className="px-3 py-1.5 border border-[#3A3632] text-[#9C968F] hover:text-[#F6F3EB] disabled:opacity-30 disabled:pointer-events-none"
                >
                  Next Hold →
                </button>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Accessible Table Parity (WCAG parity for 3D canvas content) */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="space-y-4">
          <h3 className="font-serif text-xl text-[#1A1714]">
            Auditable Evidence Ledger (Screen Reader Parity)
          </h3>
          <p className="font-sans text-xs text-[#3A3632]">
            The following table contains the exact semantic information conveyed in the 3D folio scene.
          </p>

          <div className="overflow-x-auto border border-[#E8E4DC] bg-white">
            <table className="w-full text-left font-mono text-xs border-collapse">
              <thead className="bg-[#F6F3EB] text-[#1A1714] border-b border-[#E8E4DC]">
                <tr>
                  <th scope="col" className="p-3">Stage & Range</th>
                  <th scope="col" className="p-3">Audit Area</th>
                  <th scope="col" className="p-3">Key Requirement</th>
                  <th scope="col" className="p-3">Integrity Anchor</th>
                  <th scope="col" className="p-3">Sign-Off Authority</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#E8E4DC] text-[#3A3632]">
                {chapters.map((ch) => (
                  <tr key={ch.stage} className="hover:bg-[#FDFBF7]">
                    <td className="p-3 font-bold text-[#1A1714]">{ch.slug.split(' ')[0]}</td>
                    <td className="p-3 font-sans font-medium text-[#1A1714]">{ch.title}</td>
                    <td className="p-3">{ch.body}</td>
                    <td className="p-3 text-[11px] text-[#7A5F2B]">{ch.evidence}</td>
                    <td className="p-3 font-semibold text-[#1A1714]">
                      {ch.stage === 5 ? 'Licensed CA Partner' : 'System Engine'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>
    </main>
  );
};
