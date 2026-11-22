import React from 'react';
import { ProvenanceGraph } from '../../components/provenance/ProvenanceGraph';
import { ShieldCheck, Cpu, Scale, CheckSquare, Layers, FileCheck2, AlertCircle } from 'lucide-react';

interface PlatformPageProps {
  onNavigate: (path: string) => void;
}

export const PlatformPage: React.FC<PlatformPageProps> = ({ onNavigate }) => {
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16 space-y-16">
      {/* Page Header */}
      <div className="max-w-3xl space-y-4">
        <span className="font-mono text-xs uppercase tracking-widest text-[#7A5F2B]">
          PLATFORM ARCHITECTURE & CAPABILITIES
        </span>
        <h1 className="font-serif text-3xl sm:text-4xl lg:text-5xl font-medium text-[#1A1714] tracking-tight">
          Evidence-first audit intelligence.
        </h1>
        <p className="font-sans text-base text-[#5C5752] leading-relaxed">
          AUDRYN replaces scattered spreadsheet cross-checking with a traceable evidence graph, deterministic financial calculations, independent counter-evidence investigation, and human sign-off.
        </p>
      </div>

      {/* Interactive Provenance Graph Showcase */}
      <section className="space-y-4">
        <div className="flex items-center gap-2">
          <Layers className="w-5 h-5 text-[#7A5F2B]" aria-hidden="true" />
          <h2 className="font-serif text-2xl text-[#1A1714]">
            1. Evidence Graph & Provenance Trace
          </h2>
        </div>
        <p className="font-sans text-xs text-[#5C5752]">
          Every proposed audit observation links directly across a deterministic 2D evidence graph to underlying extracted fact rows and original SHA-256 verified documents.
        </p>
        <ProvenanceGraph />
      </section>

      {/* 6 Core Architectural Pillars */}
      <section className="space-y-6 pt-8 border-t border-[#E8E4DC]">
        <h2 className="font-serif text-2xl text-[#1A1714]">
          2. The Multi-Agent Audit Engine
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {/* Pillar 1 */}
          <div className="bg-white border border-[#E8E4DC] p-6 space-y-3">
            <Cpu className="w-5 h-5 text-[#7A5F2B]" aria-hidden="true" />
            <h3 className="font-sans font-semibold text-sm text-[#1A1714]">
              Multi-Agent Orchestration
            </h3>
            <p className="font-sans text-xs text-[#5C5752] leading-relaxed">
              LangGraph coordinates audit workflows; CrewAI runs specialized investigation crews; Microsoft Agent Framework acts as the independent reviewer. All agents challenge preliminary findings.
            </p>
            <div className="font-mono text-[10px] text-[#7A746A]">
              Architecture: Independent-context challenge
            </div>
          </div>

          {/* Pillar 2 */}
          <div className="bg-white border border-[#E8E4DC] p-6 space-y-3">
            <Scale className="w-5 h-5 text-[#7A5F2B]" aria-hidden="true" />
            <h3 className="font-sans font-semibold text-sm text-[#1A1714]">
              Deterministic Decimal Math
            </h3>
            <p className="font-sans text-xs text-[#5C5752] leading-relaxed">
              All financial additions, depreciations, and ratio analyses execute strictly with Python Decimal arithmetic. Zero floating-point drift or inaccurate rounding errors.
            </p>
            <div className="font-mono text-[10px] text-[#7A746A]">
              Precision: Exact Decimal (no float)
            </div>
          </div>

          {/* Pillar 3 */}
          <div className="bg-white border border-[#E8E4DC] p-6 space-y-3">
            <ShieldCheck className="w-5 h-5 text-[#7A5F2B]" aria-hidden="true" />
            <h3 className="font-sans font-semibold text-sm text-[#1A1714]">
              Counter-Evidence Scrutiny
            </h3>
            <p className="font-sans text-xs text-[#5C5752] leading-relaxed">
              Before an observation is shown to an auditor, an independent agent searches for contradictory evidence and alternative legitimate explanations.
            </p>
            <div className="font-mono text-[10px] text-[#7A746A]">
              Verdicts: SUPPORTED, CONTRADICTED, etc.
            </div>
          </div>

          {/* Pillar 4 */}
          <div className="bg-white border border-[#E8E4DC] p-6 space-y-3">
            <CheckSquare className="w-5 h-5 text-[#7A5F2B]" aria-hidden="true" />
            <h3 className="font-sans font-semibold text-sm text-[#1A1714]">
              GAP RADAR & Completeness Gate
            </h3>
            <p className="font-sans text-xs text-[#5C5752] leading-relaxed">
              Enforces audit completeness before report generation. Procedures not performed are cataloged in an exportable Not-Checked Register with reasons and risk classifications.
            </p>
            <div className="font-mono text-[10px] text-[#7A746A]">
              Standard: Count basis (e.g. 18 of 24)
            </div>
          </div>

          {/* Pillar 5 */}
          <div className="bg-white border border-[#E8E4DC] p-6 space-y-3">
            <FileCheck2 className="w-5 h-5 text-[#7A5F2B]" aria-hidden="true" />
            <h3 className="font-sans font-semibold text-sm text-[#1A1714]">
              Statutory Tax Rulebooks
            </h3>
            <p className="font-sans text-xs text-[#5C5752] leading-relaxed">
              Codified statutory tax calculation engine covering Corporate Tax (Section 115BAA), Depreciation (Section 32), Block Depletion (Section 50), and Tax Audit Limits (Section 44AB).
            </p>
            <div className="font-mono text-[10px] text-[#7A746A]">
              Jurisdiction: Income-tax Act, 1961
            </div>
          </div>

          {/* Pillar 6 */}
          <div className="bg-white border border-[#E8E4DC] p-6 space-y-3">
            <ShieldCheck className="w-5 h-5 text-[#B08D4F]" aria-hidden="true" />
            <h3 className="font-sans font-semibold text-sm text-[#1A1714]">
              Human Reviewer Sovereignty
            </h3>
            <p className="font-sans text-xs text-[#5C5752] leading-relaxed">
              AUDRYN never issues an audit opinion. All conclusions require statutory sign-off by a licensed Chartered Accountant with recorded reasoning and ICAI registration.
            </p>
            <div className="font-mono text-[10px] text-[#7A5F2B]">
              Role: Decision-support tool
            </div>
          </div>
        </div>
      </section>

      {/* Mandatory Statutory Limits Block */}
      <section className="bg-[#F6F3EB] border border-[#7A746A] p-6 space-y-3">
        <div className="flex items-center gap-2 text-xs font-mono font-bold text-[#1A1714]">
          <AlertCircle className="w-4 h-4 text-[#B77F0A]" aria-hidden="true" />
          <span>STATUTORY LIMITS & AUDITOR SAFEGUARDS</span>
        </div>
        <p className="font-sans text-xs text-[#5C5752] leading-relaxed">
          AUDRYN does not issue statutory audit opinions or replace professional skepticism. Proposed findings are automated suggestions subject to partner evaluation. A verified calculation does not certify source document validity. A matching SHA-256 hash certifies only that a document has not been altered since ingestion; it does not certify genuine authenticity.
        </p>
      </section>

      {/* Call to Action */}
      <div className="flex items-center justify-between pt-6 border-t border-[#E8E4DC]">
        <button
          onClick={() => onNavigate('/trust')}
          className="text-xs font-mono text-[#7A5F2B] hover:underline"
        >
          Read about Trust, Privacy & DPDP Status →
        </button>

        <button
          onClick={() => onNavigate('/app')}
          className="px-5 py-2.5 bg-[#1A1714] text-[#F6F3EB] text-xs font-mono font-semibold hover:bg-[#2A2826] transition-colors"
        >
          Open Auditor Workspace (Prototype)
        </button>
      </div>
    </div>
  );
};
