import React from 'react';
import { ReviewVerdict } from '../../types';

interface StatusGlyphProps {
  verdict: ReviewVerdict | 'APPROVED';
  showLabel?: boolean;
  className?: string;
}

/**
 * Audit Tie-Line Status Glyph Component
 * Governed by Section 5.1 & Section 10.2:
 * — : Unreviewed / Unresolved
 * ↓ : Contradicted
 * ≈ : Partially Supported
 * ↑ : Supported
 * ✓ : Human Approved (Brass only)
 */
export const StatusGlyph: React.FC<StatusGlyphProps> = ({
  verdict,
  showLabel = true,
  className = '',
}) => {
  switch (verdict) {
    case 'SUPPORTED':
      return (
        <span
          className={`inline-flex items-center gap-1.5 font-mono text-xs font-semibold text-[#1A7A40] ${className}`}
          title="Finding supported by evidence gathered by counter-evidence agent. Does not imply matter is cleared."
        >
          <span className="text-sm font-bold" aria-hidden="true">↑</span>
          {showLabel && <span>SUPPORTED</span>}
        </span>
      );
    case 'CONTRADICTED':
      return (
        <span
          className={`inline-flex items-center gap-1.5 font-mono text-xs font-semibold text-[#C0392B] ${className}`}
          title="Counter-evidence challenges original finding. Auditor judgment required."
        >
          <span className="text-sm font-bold" aria-hidden="true">↓</span>
          {showLabel && <span>CONTRADICTED</span>}
        </span>
      );
    case 'PARTIALLY_SUPPORTED':
      return (
        <span
          className={`inline-flex items-center gap-1.5 font-mono text-xs font-semibold text-[#B77F0A] ${className}`}
          title="Mixed evidence: some points support, others challenge. Auditor review mandatory."
        >
          <span className="text-sm font-bold" aria-hidden="true">≈</span>
          {showLabel && <span>PARTIALLY SUPPORTED</span>}
        </span>
      );
    case 'UNRESOLVED':
    case 'INSUFFICIENT_EVIDENCE':
      return (
        <span
          className={`inline-flex items-center gap-1.5 font-mono text-xs font-medium text-[#7A746A] ${className}`}
          title="Investigation could not reach a conclusion due to insufficient evidence."
        >
          <span className="text-sm" aria-hidden="true">—</span>
          {showLabel && <span>{verdict === 'UNRESOLVED' ? 'UNRESOLVED' : 'INSUFFICIENT EVIDENCE'}</span>}
        </span>
      );
    case 'APPROVED':
      return (
        <span
          className={`inline-flex items-center gap-1.5 font-mono text-xs font-bold text-[#7A5F2B] bg-[#F6F3EB] px-2 py-0.5 border border-[#B08D4F] ${className}`}
          title="Approved with statutory sign-off by licensed Chartered Accountant."
        >
          <span className="text-sm" aria-hidden="true">✓</span>
          {showLabel && <span>HUMAN SIGN-OFF</span>}
        </span>
      );
    default:
      return null;
  }
};
