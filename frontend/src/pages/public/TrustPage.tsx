import React, { useState } from 'react';
import { Shield, Lock, FileCode, CheckCircle2, AlertTriangle, ChevronDown, ChevronUp } from 'lucide-react';

interface TrustPageProps {
  onNavigate: (path: string) => void;
}

export const TrustPage: React.FC<TrustPageProps> = ({ onNavigate }) => {
  const [openFaq, setOpenFaq] = useState<number | null>(0);

  const buyerFaqs = [
    {
      q: 'Does AUDRYN issue statutory audit opinions or replace the auditor?',
      a: 'No. AUDRYN is exclusively an audit decision-support system. It never issues an audit opinion, certifies financial statements, or replaces professional skepticism. All findings are automated proposals that require review and formal sign-off by a qualified Chartered Accountant.',
    },
    {
      q: 'Where is client financial data processed, and does it leave our network?',
      a: 'In AUDRYN’s current implementation, LLM inference runs locally on the host workstation via Ollama (Qwen3:4B). No external paid AI APIs (e.g. OpenAI, Anthropic) are configured. While no client data is transmitted to third-party AI gateways, complete zero-egress across all operating system services requires network-level packet capture verification in your specific deployment environment.',
    },
    {
      q: 'What is the distinction between calculation correctness and evidence validity?',
      a: 'AUDRYN strictly separates three truth dimensions. Calculation Correctness proves that the mathematical formula executed without floating-point error. Source Integrity (SHA-256) proves the ingested file has not been altered since upload. Evidence Validity is the professional auditor judgment that a document is genuine and legally sufficient. A correct calculation never proves its inputs are genuine.',
    },
    {
      q: 'What happens to unresolved audit items and gaps in evidence?',
      a: 'AUDRYN never hides or forces ambiguous outcomes into binary categories. Incomplete procedures are compiled into an exportable Not-Checked Register with stated reasons and assigned risk. Findings with incomplete or ambiguous counter-evidence are flagged as UNRESOLVED and explicitly disclosed on the face of the audit report.',
    },
    {
      q: 'How does AUDRYN align with India’s DPDP Rules, 2025?',
      a: 'India’s Digital Personal Data Protection Rules, 2025 were officially notified on 13 November 2025 (G.S.R. 846(E)). AUDRYN is engineered with data minimization and localized execution to facilitate compliance as substantive provisions (Notice, Consent, and Breach Reporting) commence in May 2027. AUDRYN does not make unsubstantiated compliance claims; formal legal counsel review is required prior to commercial production deployment.',
    },
  ];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16 space-y-16">
      {/* Page Header */}
      <div className="max-w-3xl space-y-4">
        <span className="font-mono text-xs uppercase tracking-widest text-[#7A5F2B]">
          GOVERNANCE, INTEGRITY & SECURITY
        </span>
        <h1 className="font-serif text-3xl sm:text-4xl lg:text-5xl font-medium text-[#1A1714] tracking-tight">
          Trust & verification standards.
        </h1>
        <p className="font-sans text-base text-[#5C5752] leading-relaxed">
          AUDRYN treats audit data as a sacred trust. Our engineering safeguards separate mathematical calculations from human evidence judgment and maintain complete audit traceability.
        </p>
      </div>

      {/* The 3 Truth Dimensions Table */}
      <section className="space-y-6">
        <h2 className="font-serif text-2xl text-[#1A1714]">
          1. The Three Truth Dimensions
        </h2>
        <p className="font-sans text-xs text-[#5C5752]">
          A fundamental safeguard in AUDRYN is that these three dimensions are never combined into a single ambiguous "VERIFIED" badge.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white border border-[#E8E4DC] p-6 space-y-3">
            <div className="flex items-center justify-between">
              <span className="font-mono text-xs font-bold text-[#1A7A40]">DIMENSION 1</span>
              <span className="text-[10px] font-mono px-2 py-0.5 bg-[#E8E4DC] text-[#1A1714]">OPERATIONAL</span>
            </div>
            <h3 className="font-serif text-lg text-[#1A1714]">
              Calculation Correctness
            </h3>
            <p className="font-sans text-xs text-[#5C5752] leading-relaxed">
              Verifies that financial math executed without floating-point error. Checked deterministically using Python Decimal arithmetic.
            </p>
            <div className="font-mono text-[11px] text-[#1A7A40] pt-2 border-t border-[#E8E4DC]">
              ✓ Decimal Verified
            </div>
          </div>

          <div className="bg-white border border-[#E8E4DC] p-6 space-y-3">
            <div className="flex items-center justify-between">
              <span className="font-mono text-xs font-bold text-[#1A7A40]">DIMENSION 2</span>
              <span className="text-[10px] font-mono px-2 py-0.5 bg-[#E8E4DC] text-[#1A1714]">OPERATIONAL</span>
            </div>
            <h3 className="font-serif text-lg text-[#1A1714]">
              Source Integrity
            </h3>
            <p className="font-sans text-xs text-[#5C5752] leading-relaxed">
              Verifies that the source file has not been modified since ingestion. Validated using cryptographic SHA-256 checksums.
            </p>
            <div className="font-mono text-[11px] text-[#1A7A40] pt-2 border-t border-[#E8E4DC]">
              ✓ SHA-256 Hash Matched
            </div>
          </div>

          <div className="bg-white border border-[#E8E4DC] p-6 space-y-3">
            <div className="flex items-center justify-between">
              <span className="font-mono text-xs font-bold text-[#B77F0A]">DIMENSION 3</span>
              <span className="text-[10px] font-mono px-2 py-0.5 bg-[#E8E4DC] text-[#7A5F2B] font-bold">PLANNED / PROTOTYPE</span>
            </div>
            <h3 className="font-serif text-lg text-[#1A1714]">
              Evidence Validity
            </h3>
            <p className="font-sans text-xs text-[#5C5752] leading-relaxed">
              Professional judgment that a document is genuine, legally admissible, and sufficient. Requires human auditor review.
            </p>
            <div className="font-mono text-[11px] text-[#B77F0A] pt-2 border-t border-[#E8E4DC]">
              Pending Human Verification
            </div>
          </div>
        </div>
      </section>

      {/* DPDP Legal Status & Phased Commencement */}
      <section className="bg-white border border-[#E8E4DC] p-8 space-y-6">
        <div className="space-y-2">
          <span className="font-mono text-xs uppercase tracking-widest text-[#7A5F2B]">
            STATUTORY COMPLIANCE ROADMAP
          </span>
          <h2 className="font-serif text-2xl text-[#1A1714]">
            India Digital Personal Data Protection (DPDP) Rules, 2025
          </h2>
          <p className="font-sans text-xs text-[#5C5752]">
            Gazette Notification G.S.R. 846(E), notified on 13 November 2025.
          </p>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left font-mono text-xs border-collapse">
            <thead className="bg-[#F6F3EB] border-b border-[#E8E4DC] text-[#1A1714]">
              <tr>
                <th className="p-3">Phase</th>
                <th className="p-3">Commencement Date</th>
                <th className="p-3">Rules Covered</th>
                <th className="p-3">Statutory Scope & Legal Effect</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#E8E4DC] text-[#5C5752]">
              <tr>
                <td className="p-3 font-bold text-[#1A1714]">Phase 1</td>
                <td className="p-3 text-[#1A7A40] font-semibold">13 November 2025 (Immediate)</td>
                <td className="p-3">Rules 1, 2, 17–21</td>
                <td className="p-3 font-sans">
                  Definitions; operationalization of the Data Protection Board of India (DPBI); inquiry timelines and complaint handling.
                </td>
              </tr>
              <tr>
                <td className="p-3 font-bold text-[#1A1714]">Phase 2</td>
                <td className="p-3">13 November 2026 (+12 months)</td>
                <td className="p-3">Rule 4</td>
                <td className="p-3 font-sans">
                  Consent Managers registration framework, technical standards, and DPBI compliance monitoring.
                </td>
              </tr>
              <tr>
                <td className="p-3 font-bold text-[#1A1714]">Phase 3</td>
                <td className="p-3">13 May 2027 (+18 months)</td>
                <td className="p-3">Rules 3, 5–16, 22, 23</td>
                <td className="p-3 font-sans">
                  Substantive obligations: standalone notice & consent, data minimization, mandatory security safeguards, breach reporting to DPBI, children's data, and DPO appointments.
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div className="text-[11px] font-mono text-[#7A746A] bg-[#F6F3EB] p-3 border border-[#E8E4DC]">
          AUDRYN makes no formal regulatory compliance claim. Firms must conduct independent legal review before handling live client personal data.
        </div>
      </section>

      {/* Buyer Questions & Answers */}
      <section className="space-y-4">
        <h2 className="font-serif text-2xl text-[#1A1714]">
          2. Verified Answers to Buyer Questions
        </h2>

        <div className="space-y-3">
          {buyerFaqs.map((faq, idx) => {
            const isOpen = openFaq === idx;
            return (
              <div key={idx} className="border border-[#E8E4DC] bg-white">
                <button
                  onClick={() => setOpenFaq(isOpen ? null : idx)}
                  className="w-full p-4 text-left flex items-center justify-between gap-4 focus:outline-none focus:ring-2 focus:ring-[#7A5F2B]"
                  aria-expanded={isOpen}
                >
                  <span className="font-sans font-semibold text-sm text-[#1A1714]">
                    {faq.q}
                  </span>
                  {isOpen ? (
                    <ChevronUp className="w-4 h-4 text-[#7A5F2B] shrink-0" aria-hidden="true" />
                  ) : (
                    <ChevronDown className="w-4 h-4 text-[#7A746A] shrink-0" aria-hidden="true" />
                  )}
                </button>

                {isOpen && (
                  <div className="px-4 pb-4 font-sans text-xs text-[#5C5752] leading-relaxed border-t border-[#E8E4DC]/60 pt-3">
                    {faq.a}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </section>

      {/* Responsible Disclosure & Security Contacts */}
      <section className="bg-[#121110] text-[#F6F3EB] p-8 space-y-4 border border-[#2A2724]">
        <h3 className="font-serif text-xl text-[#F6F3EB]">
          Responsible Disclosure & Security Reporting
        </h3>
        <p className="font-sans text-xs text-[#9C968F] leading-relaxed">
          AUDRYN welcomes independent security researchers and audit professionals to test system boundaries. To report vulnerabilities or data integrity issues:
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 font-mono text-xs pt-2">
          <div className="p-3 bg-[#1A1816] border border-[#2A2724]">
            <span className="text-[#7A746A] block text-[10px]">VULNERABILITY REPORTING:</span>
            <span className="text-[#B08D4F]">[Owner to supply: security@firm.example]</span>
          </div>
          <div className="p-3 bg-[#1A1816] border border-[#2A2724]">
            <span className="text-[#7A746A] block text-[10px]">PGP FINGERPRINT:</span>
            <span className="text-[#9C968F]">[Owner to supply: PGP Key ID]</span>
          </div>
        </div>
      </section>
    </div>
  );
};
