import React from 'react';

interface PrototypeBadgeProps {
  className?: string;
}

/**
 * Universal PROTOTYPE Badge
 * Displays persistent, high-contrast, real HTML text badge on all
 * application workspaces that lack active HTTP backend API contracts.
 */
export const PrototypeBadge: React.FC<PrototypeBadgeProps> = ({ className = '' }) => {
  return (
    <span
      role="status"
      aria-label="Prototype feature — backend HTTP API pending deployment"
      className={`inline-flex items-center gap-1.5 px-2 py-0.5 text-[11px] font-mono tracking-wider font-semibold uppercase bg-[#E8E4DC] text-[#1A1714] border border-[#7A746A] select-none ${className}`}
      title="This workspace is operating on mock contracts and local fixtures. Backend FastAPI endpoints are pending deployment."
    >
      <span className="w-1.5 h-1.5 rounded-full bg-[#B77F0A] animate-pulse" aria-hidden="true" />
      PROTOTYPE
    </span>
  );
};
