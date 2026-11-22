import React, { useState } from 'react';
import { FileText, ArrowRight, CheckCircle, ShieldAlert, KeyRound } from 'lucide-react';
import { truncateHash } from '../../utils/formatters';

interface NodeItem {
  id: string;
  type: 'REPORT' | 'FINDING' | 'CALCULATION' | 'EXTRACTION' | 'SOURCE';
  label: string;
  sublabel?: string;
  statusText: string;
  statusCode: 'VERIFIED' | 'WARNING' | 'ALERT' | 'INFO';
}

export const ProvenanceGraph: React.FC = () => {
  const [selectedNode, setSelectedNode] = useState<string>('N-FIND-01');
  const [viewMode, setViewMode] = useState<'graph' | 'tree'>('graph');

  const nodes: NodeItem[] = [
    {
      id: 'N-REP-01',
      type: 'REPORT',
      label: 'Draft Statutory Audit Report — FY 2023-24',
      sublabel: 'Section 4.2: Revenue & Cut-Off Observations',
      statusText: '1 Unresolved Item',
      statusCode: 'WARNING',
    },
    {
      id: 'N-FIND-01',
      type: 'FINDING',
      label: 'Cut-Off Timing Discrepancy (INV-2024-889)',
      sublabel: '₹ 45,00,000.00 booked in Q4; dispatched in Q1',
      statusText: 'PARTIALLY_SUPPORTED',
      statusCode: 'ALERT',
    },
    {
      id: 'N-CALC-01',
      type: 'CALCULATION',
      label: 'Cut-Off Variance Computation (CALC-REV-01)',
      sublabel: 'Exact Decimal math: ₹12,45,67,890 - ₹12,00,67,890',
      statusText: 'Calculation Checked',
      statusCode: 'VERIFIED',
    },
    {
      id: 'N-EXT-01',
      type: 'EXTRACTION',
      label: 'Extracted Invoice Row (Page 14, Bounding Box 88x120)',
      sublabel: 'Date: 31-03-2024, Total: ₹ 45,00,000.00',
      statusText: 'Extraction Complete',
      statusCode: 'VERIFIED',
    },
    {
      id: 'N-SRC-01',
      type: 'SOURCE',
      label: 'trial_balance_FY2023_24_final.xlsx',
      sublabel: `SHA-256: ${truncateHash('e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855')}`,
      statusText: 'Hash Matched',
      statusCode: 'VERIFIED',
    },
  ];

  return (
    <div className="w-full bg-[#FDFBF7] border border-[#E8E4DC] p-6 space-y-6">
      {/* Header with Mode Toggle & Shortcuts */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-[#E8E4DC] pb-4">
        <div>
          <h3 className="font-serif text-lg font-semibold text-[#1A1714]">
            Provenance Trace Explorer
          </h3>
          <p className="font-mono text-xs text-[#5C5752] mt-0.5">
            Deterministic 2D Evidence Graph linking statutory report sections to original source records.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setViewMode(viewMode === 'graph' ? 'tree' : 'graph')}
            className="text-xs font-mono px-3 py-1.5 border border-[#7A746A] hover:bg-[#E8E4DC] transition-colors focus:ring-2 focus:ring-[#7A5F2B]"
            aria-label={`Switch to ${viewMode === 'graph' ? 'accessible outline tree view' : 'interactive 2D graph view'}`}
          >
            {viewMode === 'graph' ? 'View as Outline Tree' : 'View as SVG Graph'}
          </button>
        </div>
      </div>

      {/* SVG / DOM Graph View */}
      {viewMode === 'graph' ? (
        <div className="relative py-4 overflow-x-auto">
          <div className="min-w-[700px] flex items-center justify-between gap-4">
            {nodes.map((node, index) => {
              const isSelected = selectedNode === node.id;
              return (
                <React.Fragment key={node.id}>
                  {/* Node Card */}
                  <div
                    tabIndex={0}
                    role="button"
                    onClick={() => setSelectedNode(node.id)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault();
                        setSelectedNode(node.id);
                      }
                    }}
                    aria-pressed={isSelected}
                    className={`flex-1 min-w-[140px] max-w-[200px] p-3 border transition-all text-left focus:outline-none focus:ring-2 focus:ring-[#7A5F2B] cursor-pointer ${
                      isSelected
                        ? 'bg-[#F6F3EB] border-[#1A1714] shadow-sm'
                        : 'bg-white border-[#E8E4DC] hover:border-[#7A746A]'
                    }`}
                  >
                    <div className="flex items-center justify-between gap-1 mb-2">
                      <span className="font-mono text-[9px] uppercase font-bold tracking-wider text-[#7A5F2B]">
                        {node.type}
                      </span>
                      {node.statusCode === 'VERIFIED' && (
                        <CheckCircle className="w-3.5 h-3.5 text-[#1A7A40]" aria-hidden="true" />
                      )}
                      {node.statusCode === 'ALERT' && (
                        <ShieldAlert className="w-3.5 h-3.5 text-[#C0392B]" aria-hidden="true" />
                      )}
                      {node.statusCode === 'WARNING' && (
                        <KeyRound className="w-3.5 h-3.5 text-[#B77F0A]" aria-hidden="true" />
                      )}
                    </div>

                    <h4 className="font-sans text-xs font-semibold text-[#1A1714] line-clamp-2 leading-snug">
                      {node.label}
                    </h4>

                    {node.sublabel && (
                      <p className="font-mono text-[10px] text-[#5C5752] mt-1 line-clamp-2">
                        {node.sublabel}
                      </p>
                    )}

                    <div className="mt-3 pt-2 border-t border-[#E8E4DC] font-mono text-[10px] text-[#7A746A]">
                      Status: <span className="text-[#1A1714] font-medium">{node.statusText}</span>
                    </div>
                  </div>

                  {/* Tie-line connector arrow */}
                  {index < nodes.length - 1 && (
                    <div className="flex items-center text-[#7A746A]" aria-hidden="true">
                      <ArrowRight className="w-4 h-4 stroke-[1.5]" />
                    </div>
                  )}
                </React.Fragment>
              );
            })}
          </div>
        </div>
      ) : (
        /* Accessible Outline Tree Alternative for Screen Readers & Keyboard */
        <nav aria-label="Evidence Provenance Hierarchy" className="space-y-3 font-mono text-xs">
          <ol className="list-decimal list-inside space-y-2 border-l-2 border-[#7A5F2B] pl-4">
            {nodes.map((node) => (
              <li key={node.id} className="py-1">
                <span className="font-bold text-[#7A5F2B]">[{node.type}]</span>{' '}
                <span className="font-sans font-semibold text-[#1A1714]">{node.label}</span> —{' '}
                <span className="text-[#5C5752]">{node.sublabel}</span> ({node.statusText})
              </li>
            ))}
          </ol>
        </nav>
      )}

      {/* Detail Inspection Drawer for Selected Node */}
      <aside aria-label="Node Metadata Drawer" className="bg-[#F6F3EB] border border-[#E8E4DC] p-4 font-mono text-xs space-y-2">
        <div className="flex items-center justify-between">
          <span className="font-bold text-[#1A1714]">Selected Node: {selectedNode}</span>
          <span className="text-[11px] text-[#7A5F2B] uppercase">Evidence Trace Active</span>
        </div>
        <p className="font-sans text-xs text-[#5C5752]">
          This node forms part of an unbroken evidence chain connecting the draft statutory audit report directly to SHA-256 verified Excel worksheets and extracted OCR records.
        </p>
      </aside>
    </div>
  );
};
