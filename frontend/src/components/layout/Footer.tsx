import React, { useState, useEffect } from 'react';
import { EyeOff, Eye, CheckCircle2 } from 'lucide-react';

interface FooterProps {
  onNavigate: (path: string) => void;
}

export const Footer: React.FC<FooterProps> = ({ onNavigate }) => {
  const [reducedEffects, setReducedEffects] = useState<boolean>(() => {
    return localStorage.getItem('audryn_reduced_effects') === 'true';
  });

  useEffect(() => {
    if (reducedEffects) {
      document.documentElement.classList.add('reduce-effects');
      localStorage.setItem('audryn_reduced_effects', 'true');
    } else {
      document.documentElement.classList.remove('reduce-effects');
      localStorage.setItem('audryn_reduced_effects', 'false');
    }
  }, [reducedEffects]);

  const currentYear = new Date().getFullYear();

  return (
    <footer role="contentinfo" className="bg-[#121110] text-[#9C968F] border-t border-[#2A2826] mt-24">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-14">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-10">
          {/* Brand & Mandate */}
          <div className="space-y-4 md:col-span-1">
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 bg-[#F6F3EB] text-[#121110] font-serif font-bold text-xs flex items-center justify-center">
                A
              </div>
              <span className="font-serif font-semibold text-lg text-[#F6F3EB] tracking-tight">
                AUDRYN
              </span>
            </div>
            <p className="text-xs leading-relaxed text-[#9C968F] font-sans">
              Evidence-First Multi-Agent Financial Audit Intelligence System. Designed for Chartered Accountants and statutory auditors.
            </p>
            <p className="text-[11px] font-mono tracking-wider text-[#B08D4F] uppercase">
              EVIDENCE BEFORE CONCLUSIONS
            </p>
          </div>

          {/* Navigation Links */}
          <div>
            <h3 className="font-mono text-xs font-semibold uppercase tracking-wider text-[#F6F3EB] mb-4">
              Platform & System
            </h3>
            <ul className="space-y-2.5 text-xs">
              <li>
                <button onClick={() => onNavigate('/platform')} className="hover:text-[#F6F3EB] transition-colors focus:outline-none focus:ring-1 focus:ring-[#B08D4F]">
                  How AUDRYN Works
                </button>
              </li>
              <li>
                <button onClick={() => onNavigate('/trust')} className="hover:text-[#F6F3EB] transition-colors focus:outline-none focus:ring-1 focus:ring-[#B08D4F]">
                  Truth Dimensions & Trust
                </button>
              </li>
              <li>
                <button onClick={() => onNavigate('/request-demo')} className="hover:text-[#F6F3EB] transition-colors focus:outline-none focus:ring-1 focus:ring-[#B08D4F]">
                  Request a Demonstration
                </button>
              </li>
              <li>
                <button onClick={() => onNavigate('/app')} className="hover:text-[#F6F3EB] transition-colors focus:outline-none focus:ring-1 focus:ring-[#B08D4F]">
                  Auditor Workspace (Prototype)
                </button>
              </li>
            </ul>
          </div>

          {/* Governance & Legal */}
          <div>
            <h3 className="font-mono text-xs font-semibold uppercase tracking-wider text-[#F6F3EB] mb-4">
              Governance & Legal
            </h3>
            <ul className="space-y-2.5 text-xs">
              <li>
                <button onClick={() => onNavigate('/legal/privacy')} className="hover:text-[#F6F3EB] transition-colors focus:outline-none focus:ring-1 focus:ring-[#B08D4F]">
                  Privacy Policy (DPDP 2025)
                </button>
              </li>
              <li>
                <button onClick={() => onNavigate('/legal/terms')} className="hover:text-[#F6F3EB] transition-colors focus:outline-none focus:ring-1 focus:ring-[#B08D4F]">
                  Terms of Service
                </button>
              </li>
              <li>
                <button onClick={() => onNavigate('/legal/cookies')} className="hover:text-[#F6F3EB] transition-colors focus:outline-none focus:ring-1 focus:ring-[#B08D4F]">
                  Cookie & Storage Policy
                </button>
              </li>
              <li>
                <button onClick={() => onNavigate('/legal/security')} className="hover:text-[#F6F3EB] transition-colors focus:outline-none focus:ring-1 focus:ring-[#B08D4F]">
                  Responsible Disclosure
                </button>
              </li>
            </ul>
          </div>

          {/* Regulatory Limits & Accessibility Toggle */}
          <div className="space-y-4">
            <h3 className="font-mono text-xs font-semibold uppercase tracking-wider text-[#F6F3EB] mb-2">
              Auditor Safeguard
            </h3>
            <p className="text-[11px] leading-relaxed text-[#9C968F]">
              AUDRYN is a decision-support system. It does not issue statutory audit opinions or replace professional skepticism. Proposed findings require licensed CA review.
            </p>

            {/* Accessibility: Reduce Visual Effects Toggle */}
            <div className="pt-2">
              <button
                onClick={() => setReducedEffects(!reducedEffects)}
                className="inline-flex items-center gap-2 text-xs font-mono px-3 py-1.5 border border-[#3A3632] hover:border-[#B08D4F] text-[#F6F3EB] transition-colors focus:outline-none focus:ring-2 focus:ring-[#B08D4F]"
                aria-pressed={reducedEffects}
              >
                {reducedEffects ? (
                  <>
                    <EyeOff className="w-3.5 h-3.5 text-[#B08D4F]" aria-hidden="true" />
                    <span>Visual Effects: Reduced</span>
                  </>
                ) : (
                  <>
                    <Eye className="w-3.5 h-3.5 text-[#9C968F]" aria-hidden="true" />
                    <span>Reduce Visual Effects</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>

        {/* Bottom Bar with Dynamic Copyright (text-[#9C968F] for 6.2:1 contrast against #121110) */}
        <div className="border-t border-[#2A2826] mt-10 pt-6 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs font-mono text-[#9C968F]">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-3.5 h-3.5 text-[#1A7A40]" aria-hidden="true" />
            <span>Deterministic Decimal Engine · SHA-256 Provenance Active</span>
          </div>
          <div>
            © {currentYear} AUDRYN Intelligence Systems. All rights reserved.
          </div>
        </div>
      </div>
    </footer>
  );
};
