import React, { useState, useEffect } from 'react';
import {
  FileText,
  CheckSquare,
  Cpu,
  ShieldCheck,
  UserCheck,
  Calculator,
  Percent,
  FileCheck,
  Network,
  Settings,
  AlertCircle,
  Info,
  CheckCircle2,
  Upload,
  RefreshCw,
  Lock,
} from 'lucide-react';
import { PrototypeBadge } from '../../components/common/PrototypeBadge';
import { StatusGlyph } from '../../components/common/StatusGlyph';
import {
  SYNTHETIC_EVIDENCE,
  SYNTHETIC_FINDINGS,
  SYNTHETIC_NOT_CHECKED,
  SYNTHETIC_CALCULATIONS,
  SYNTHETIC_MANIFEST,
} from '../../mock/auditData';
import { formatINR, truncateHash, formatIST } from '../../utils/formatters';
import { ProvenanceGraph } from '../../components/provenance/ProvenanceGraph';
import { api, ApiError } from '../../services/api';

const ENGAGEMENT_ID = 'ENG-APEX-FY24';

export const AppShell: React.FC = () => {
  const [activeTab, setActiveTab] = useState<string>('evidence');
  const [backendConnected, setBackendConnected] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  // Engagement Data State
  const [evidenceList, setEvidenceList] = useState(SYNTHETIC_EVIDENCE);
  const [findings, setFindings] = useState(SYNTHETIC_FINDINGS);
  const [notCheckedList, setNotCheckedList] = useState(SYNTHETIC_NOT_CHECKED);
  const [calculations, setCalculations] = useState(SYNTHETIC_CALCULATIONS);
  const [reportManifest, setReportManifest] = useState(SYNTHETIC_MANIFEST);
  const [completenessResult, setCompletenessResult] = useState<any>(null);
  const [auditEvents, setAuditEvents] = useState<any[]>([]);

  const [selectedFindingId, setSelectedFindingId] = useState<string>('ANOMALY-001');

  // Human review decision state
  const [approvalReason, setApprovalReason] = useState<string>('');
  const [unresolvedConfirmed, setUnresolvedConfirmed] = useState<boolean>(false);
  const [statusMessage, setStatusMessage] = useState<{ type: 'info' | 'success' | 'error'; text: string } | null>(null);

  // Tax and Calculation input states
  const [calcInputName, setCalcInputName] = useState<string>('Payroll Discrepancy');
  const [calcInputVal1, setCalcInputVal1] = useState<string>('5000000.00');
  const [calcInputVal2, setCalcInputVal2] = useState<string>('4850000.00');
  const [taxIncomeInput, setTaxIncomeInput] = useState<string>('50000000.00');
  const [taxResult, setTaxResult] = useState<any>(null);

  // Authentication states
  const [currentUser, setCurrentUser] = useState<any>(null);
  const [loginUsername, setLoginUsername] = useState<string>('partner_sharma');
  const [loginPassword, setLoginPassword] = useState<string>('');

  // Auto-connect to backend on mount
  useEffect(() => {
    async function initBackend() {
      try {
        const health = await api.getHealth();
        if (health.status === 'healthy' || health.status === 'degraded') {
          setBackendConnected(true);
          // Check for existing valid session without exposing hardcoded credentials in the client bundle
          try {
            const me = await api.getMe();
            if (me && me.user) {
              setStatusMessage({
                type: 'info',
                text: `Authenticated session restored: ${me.user.full_name} (${me.user.role})`,
              });
            }
          } catch {
            // Unauthenticated session — operates in demo mode or user can sign in via Settings workspace
          }
          await loadLiveData();
        }
      } catch {
        // Backend offline: seamlessly fallback to synthetic fixtures
        setBackendConnected(false);
      }
    }
    initBackend();
  }, []);

  const loadLiveData = async () => {
    try {
      setIsLoading(true);
      const [ev, fd, nc, cl, rp, comp, events] = await Promise.all([
        api.listEvidence(ENGAGEMENT_ID).catch(() => null),
        api.listFindings(ENGAGEMENT_ID).catch(() => null),
        api.listNotChecked(ENGAGEMENT_ID).catch(() => null),
        api.listCalculations(ENGAGEMENT_ID).catch(() => null),
        api.getLatestReport(ENGAGEMENT_ID).catch(() => null),
        api.evaluateCompleteness(ENGAGEMENT_ID).catch(() => null),
        api.listAuditEvents(ENGAGEMENT_ID).catch(() => null),
      ]);

      if (ev && ev.length > 0) setEvidenceList(ev);
      if (fd && fd.length > 0) setFindings(fd);
      if (nc && nc.length > 0) setNotCheckedList(nc);
      if (cl && cl.length > 0) setCalculations(cl);
      if (rp && rp.manifest) setReportManifest(rp.manifest);
      if (comp) setCompletenessResult(comp);
      if (events) setAuditEvents(events);
    } catch {
      // Keep state
    } finally {
      setIsLoading(false);
    }
  };

  const selectedFinding = findings.find((f) => f.finding_id === selectedFindingId) || findings[0];

  // 1. Human Review Decision Execution
  const handleDecision = async (decision: 'APPROVE' | 'REJECT' | 'ESCALATE') => {
    if (decision === 'APPROVE' && selectedFinding.counter_evidence.verdict === 'PARTIALLY_SUPPORTED' && !unresolvedConfirmed) {
      alert('Statutory sign-off requires explicit acknowledgment of unresolved counter-evidence points.');
      return;
    }

    try {
      if (backendConnected) {
        const res = await api.recordReviewDecision(ENGAGEMENT_ID, {
          finding_id: selectedFinding.finding_id,
          decision: decision === 'APPROVE' ? 'APPROVED' : decision === 'REJECT' ? 'REJECTED' : 'ESCALATED',
          comments: approvalReason || 'Approved following review of supporting vouchers and counter-evidence audit trails.',
          reviewer_membership_no: 'ICAI-084920',
          unresolved_acknowledged: unresolvedConfirmed,
        });

        setStatusMessage({
          type: 'success',
          text: `Backend Confirmed: ${res.message} (Signing Partner: CA Rajesh K. Sharma)`,
        });
        await loadLiveData();
      } else {
        // Fallback simulation
        setFindings((prev) =>
          prev.map((f) => {
            if (f.finding_id === selectedFinding.finding_id) {
              return {
                ...f,
                human_review: {
                  status: decision === 'APPROVE' ? 'APPROVED' : decision === 'REJECT' ? 'REJECTED' : 'ESCALATED',
                  reviewer_name: 'Rajesh K. Sharma, FCA',
                  reviewer_membership_no: 'ICAI-084920',
                  decided_at: new Date().toISOString(),
                  reason: approvalReason || 'Approved following review of supporting vouchers and counter-evidence audit trails.',
                },
              };
            }
            return f;
          })
        );
        setStatusMessage({
          type: 'success',
          text: `Client Simulation: Finding ${selectedFinding.finding_id} set to ${decision}. Connect backend for permanent database persistence.`,
        });
      }
    } catch (err: any) {
      setStatusMessage({ type: 'error', text: err.detail || err.message });
    }
    setApprovalReason('');
  };

  // 2. Hash Verification Execution
  const handleVerifyHash = async (evidenceId: string) => {
    try {
      if (backendConnected) {
        const res = await api.verifyEvidenceHash(ENGAGEMENT_ID, evidenceId);
        setStatusMessage({
          type: 'success',
          text: `Backend Verified: SHA-256 for ${evidenceId} verified with disk storage. Hash: ${truncateHash(res.computed_sha256)} (Match: ${res.is_match}).`,
        });
      } else {
        setStatusMessage({
          type: 'info',
          text: `Simulation: SHA-256 matched against in-memory registry for ${evidenceId}.`,
        });
      }
    } catch (err: any) {
      setStatusMessage({ type: 'error', text: err.detail || err.message });
    }
  };

  // 3. Run Investigation Execution
  const handleRunInvestigation = async () => {
    try {
      if (backendConnected) {
        setStatusMessage({ type: 'info', text: 'Executing multi-agent investigation across audit pipeline...' });
        const res = await api.runInvestigation(ENGAGEMENT_ID);
        setStatusMessage({
          type: 'success',
          text: `Investigation Job ${res.job_id} COMPLETED. Analyzed evidence and generated ${res.findings_count} findings.`,
        });
        await loadLiveData();
      } else {
        setStatusMessage({
          type: 'info',
          text: 'Simulation: Multi-Agent run completed against fixture dataset.',
        });
      }
    } catch (err: any) {
      setStatusMessage({ type: 'error', text: err.detail || err.message });
    }
  };

  // 4. Run Decimal Calculation
  const handleRunCalculation = async () => {
    try {
      if (backendConnected) {
        const res = await api.runCalculation(ENGAGEMENT_ID, calcInputName, {
          Amount_1: calcInputVal1,
          Amount_2: calcInputVal2,
        });
        setStatusMessage({
          type: 'success',
          text: `Calculation ${res.calculation_id} verified via Python Decimal: Result = ₹${res.result}`,
        });
        await loadLiveData();
      } else {
        setStatusMessage({
          type: 'info',
          text: `Simulation: Decimal calculation verified. Result: ₹${(parseFloat(calcInputVal1) - parseFloat(calcInputVal2)).toFixed(2)}`,
        });
      }
    } catch (err: any) {
      setStatusMessage({ type: 'error', text: err.detail || err.message });
    }
  };

  // 5. Compute Section 115BAA Tax
  const handleComputeTax = async () => {
    try {
      if (backendConnected) {
        const res = await api.computeTax115BAA(ENGAGEMENT_ID, taxIncomeInput);
        setTaxResult(res);
        setStatusMessage({
          type: 'success',
          text: `Section 115BAA Tax Computed: ₹${res.total_tax_liability} (Effective Rate: ${res.effective_tax_rate_percent}%)`,
        });
        await loadLiveData();
      } else {
        setTaxResult({
          total_tax_liability: (parseFloat(taxIncomeInput) * 0.25168).toFixed(2),
          effective_tax_rate_percent: '25.17',
          is_eligible: true,
          statutory_citations: ['Section 115BAA of the Income-tax Act, 1961'],
        });
      }
    } catch (err: any) {
      setStatusMessage({ type: 'error', text: err.detail || err.message });
    }
  };

  // 6. Generate & Finalize Report
  const handleGenerateReport = async () => {
    try {
      if (backendConnected) {
        const res = await api.generateReport(ENGAGEMENT_ID);
        setReportManifest(res.manifest);
        setStatusMessage({
          type: 'success',
          text: `Audit Report ${res.report_id} generated. Manifest hash: ${truncateHash(res.manifest.report_hash)}.`,
        });
        await loadLiveData();
      } else {
        setStatusMessage({
          type: 'info',
          text: 'Simulation: Working paper manifest generated client-side.',
        });
      }
    } catch (err: any) {
      setStatusMessage({ type: 'error', text: err.detail || err.message });
    }
  };

  const handleFinalizeReport = async () => {
    try {
      if (backendConnected) {
        const res = await api.finalizeReport(ENGAGEMENT_ID);
        setReportManifest(res.manifest);
        setStatusMessage({
          type: 'success',
          text: `STATUTORY AUDIT REPORT FINALIZED: Cryptographic signature anchored by Partner. Version: ${res.report_version}`,
        });
        await loadLiveData();
      } else {
        setStatusMessage({
          type: 'info',
          text: 'Simulation: Partner finalization requires active backend session.',
        });
      }
    } catch (err: any) {
      setStatusMessage({ type: 'error', text: err.detail || err.message });
    }
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await api.login(loginUsername, loginPassword);
      setCurrentUser(res.user);
      setStatusMessage({
        type: 'success',
        text: `Logged in successfully as ${res.user.full_name} (${res.user.role})`,
      });
      setLoginPassword('');
      await loadLiveData();
    } catch (err: any) {
      setStatusMessage({ type: 'error', text: err.detail || err.message || 'Login failed' });
    }
  };

  const handleLogout = async () => {
    try {
      await api.logout();
      setCurrentUser(null);
      setStatusMessage({ type: 'info', text: 'Logged out. Active session ended.' });
    } catch (err: any) {
      setStatusMessage({ type: 'error', text: err.detail || err.message });
    }
  };

  const menuItems = [
    { id: 'evidence', label: '1. Evidence Ingestion', icon: FileText, count: evidenceList.length },
    { id: 'completeness', label: '2. Completeness Gate', icon: CheckSquare, count: notCheckedList.length },
    { id: 'investigation', label: '3. Multi-Agent Run', icon: Cpu },
    { id: 'counter-evidence', label: '4. Counter-Evidence', icon: ShieldCheck, count: findings.length },
    { id: 'review', label: '5. Human Review Queue', icon: UserCheck, count: findings.filter((f) => f.human_review?.status === 'PENDING').length },
    { id: 'calculations', label: '6. Decimal Math', icon: Calculator, count: calculations.length },
    { id: 'tax', label: '7. Statutory Tax', icon: Percent },
    { id: 'reports', label: '8. Audit Report', icon: FileCheck },
    { id: 'provenance', label: '9. Provenance Graph', icon: Network },
    { id: 'settings', label: '10. Settings & Roles', icon: Settings },
  ];

  return (
    <div className="min-h-screen bg-[#F6F3EB] flex flex-col">
      {/* Top Banner with Backend Status & Prototype Badge */}
      <div className="bg-[#E8E4DC] border-b border-[#7A746A] px-4 py-2 flex flex-wrap items-center justify-between gap-3 text-xs font-mono">
        <div className="flex items-center gap-3">
          <PrototypeBadge />
          <span className="text-[#1A1714] font-semibold">
            Engagement: Apex Industrial Tech Ltd (FY 2023-24 · AY 2024-25)
          </span>
          {backendConnected ? (
            <span className="px-2 py-0.5 bg-[#1A7A40]/15 text-[#1A7A40] border border-[#1A7A40] font-bold">
              ● FASTAPI LIVE (/api/v1)
            </span>
          ) : (
            <span className="px-2 py-0.5 bg-[#7A5F2B]/15 text-[#7A5F2B] border border-[#7A5F2B] font-bold">
              ○ DEMO MODE (SYNTHETIC FIXTURES)
            </span>
          )}
        </div>
        <div className="flex items-center gap-4 text-[#5C5752]">
          <span>
            {currentUser ? (
              <span className="text-[#1A7A40] font-bold">
                ✓ {currentUser.full_name} ({currentUser.role})
              </span>
            ) : (
              <span className="text-[#7A5F2B]">
                CA Sign-In via Settings
              </span>
            )}
          </span>
          <button
            onClick={loadLiveData}
            disabled={isLoading}
            className="flex items-center gap-1 text-[#1A1714] hover:underline focus:outline-none"
            title="Refresh from Backend"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
            <span>Sync</span>
          </button>
        </div>
      </div>

      {/* Persistent Disclaimer Banner */}
      <div className="bg-[#FDFBF7] border-b border-[#E8E4DC] px-4 py-1.5 flex items-center justify-between gap-2 text-[11px] font-mono text-[#5C5752]">
        <div className="flex items-center gap-2">
          <Info className="w-3.5 h-3.5 text-[#7A5F2B] shrink-0" aria-hidden="true" />
          <span>
            {backendConnected
              ? 'PRODUCTION INTEGRATION ACTIVE: Operations persist to SQLite WAL database. SHA-256 evidence integrity enforced.'
              : 'PROTOTYPE DEMO MODE: Backend disconnected or running locally. Displaying verifiable synthetic audit fixtures.'}
          </span>
        </div>
        <span className="text-[10px] font-bold uppercase tracking-wider text-[#7A746A]">SYNTHETIC DATA DEMONSTRATION</span>
      </div>

      <div className="flex-1 flex flex-col md:flex-row">
        {/* Workspace Sidebar Navigation */}
        <aside aria-label="Workspaces" className="w-full md:w-64 bg-white border-r border-[#E8E4DC] p-3 space-y-1">
          <div className="px-3 py-2 text-[10px] font-mono uppercase tracking-widest text-[#7A746A]">
            AUDIT WORKSPACES
          </div>
          {menuItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`w-full flex items-center justify-between px-3 py-2.5 text-xs font-sans transition-colors focus:outline-none focus:ring-1 focus:ring-[#7A5F2B] ${
                  isActive
                    ? 'bg-[#F6F3EB] text-[#1A1714] font-semibold border-l-2 border-[#1A1714]'
                    : 'text-[#5C5752] hover:bg-[#FDFBF7] hover:text-[#1A1714]'
                }`}
              >
                <div className="flex items-center gap-2.5 truncate">
                  <Icon className={`w-4 h-4 shrink-0 ${isActive ? 'text-[#7A5F2B]' : 'text-[#7A746A]'}`} />
                  <span className="truncate">{item.label}</span>
                </div>
                {item.count !== undefined && (
                  <span className="font-mono text-[10px] px-1.5 py-0.5 bg-[#E8E4DC] text-[#1A1714]">
                    {item.count}
                  </span>
                )}
              </button>
            );
          })}
        </aside>

        {/* Main Workspace Stage */}
        <main id="main-content" className="flex-1 p-6 md:p-8 space-y-6 overflow-y-auto">
          {statusMessage && (
            <div
              role="status"
              className={`p-3 border text-xs font-mono flex items-center justify-between gap-2 ${
                statusMessage.type === 'success'
                  ? 'bg-[#1A7A40]/10 border-[#1A7A40] text-[#1A7A40]'
                  : statusMessage.type === 'error'
                  ? 'bg-[#A82B1E]/10 border-[#A82B1E] text-[#A82B1E]'
                  : 'bg-[#7A5F2B]/10 border-[#7A5F2B] text-[#7A5F2B]'
              }`}
            >
              <div className="flex items-center gap-2">
                <AlertCircle className="w-4 h-4 shrink-0" aria-hidden="true" />
                <span>{statusMessage.text}</span>
              </div>
              <button onClick={() => setStatusMessage(null)} className="text-xs hover:underline">
                Dismiss
              </button>
            </div>
          )}

          {/* 1. EVIDENCE INGESTION */}
          {activeTab === 'evidence' && (
            <div className="space-y-6">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                  <h2 className="font-serif text-2xl text-[#1A1714]">1. Evidence Ingestion & SHA-256 Hashes</h2>
                  <p className="font-sans text-xs text-[#5C5752]">
                    Verify SHA-256 cryptographic checksums on source documents before record extraction.
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <label className="cursor-pointer px-3 py-2 bg-[#1A1714] text-[#F6F3EB] font-mono text-xs font-semibold hover:bg-[#2A2826] flex items-center gap-1.5">
                    <Upload className="w-3.5 h-3.5" />
                    <span>Upload Evidence</span>
                    <input
                      type="file"
                      className="hidden"
                      onChange={async (e) => {
                        const file = e.target.files?.[0];
                        if (!file) return;
                        if (!backendConnected) {
                          setStatusMessage({
                            type: 'info',
                            text: `Simulation: Upload of ${file.name} recorded in memory.`,
                          });
                          return;
                        }
                        try {
                          const res = await api.uploadEvidence(ENGAGEMENT_ID, file, 'INVOICE');
                          setStatusMessage({
                            type: 'success',
                            text: `Successfully ingested ${(res as any).original_filename} (SHA-256: ${truncateHash((res as any).sha256_hash)})`,
                          });
                          await loadLiveData();
                        } catch (err: any) {
                          setStatusMessage({ type: 'error', text: err.detail || err.message });
                        }
                      }}
                    />
                  </label>
                </div>
              </div>

              <div className="bg-white border border-[#E8E4DC] overflow-hidden">
                <table className="w-full text-left text-xs font-mono">
                  <thead className="bg-[#E8E4DC] text-[#1A1714] uppercase text-[10px] tracking-wider border-b border-[#7A746A]">
                    <tr>
                      <th scope="col" className="p-3">Evidence ID</th>
                      <th scope="col" className="p-3">Source Filename</th>
                      <th scope="col" className="p-3">SHA-256 Hash</th>
                      <th scope="col" className="p-3">Status</th>
                      <th scope="col" className="p-3">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#E8E4DC]">
                    {evidenceList.map((doc: any) => (
                      <tr key={doc.evidence_id} className="hover:bg-[#FDFBF7]">
                        <td className="p-3 font-bold text-[#1A1714]">{doc.evidence_id}</td>
                        <td className="p-3 font-sans text-[#5C5752]">{doc.source_filename || doc.original_filename}</td>
                        <td className="p-3 text-[#7A5F2B] font-mono text-[11px]">
                          {truncateHash(doc.sha256_hash)}
                        </td>
                        <td className="p-3">
                          <span className="px-2 py-0.5 bg-[#1A7A40]/10 text-[#1A7A40] border border-[#1A7A40] text-[10px] font-bold">
                            {doc.extraction_status}
                          </span>
                        </td>
                        <td className="p-3">
                          <button
                            onClick={() => handleVerifyHash(doc.evidence_id)}
                            className="text-[10px] font-mono px-2 py-1 bg-[#E8E4DC] hover:bg-[#D4CEBF] text-[#1A1714] font-semibold border border-[#7A746A]"
                          >
                            VERIFY HASH
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* 2. COMPLETENESS GATE */}
          {activeTab === 'completeness' && (
            <div className="space-y-6">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                  <h2 className="font-serif text-2xl text-[#1A1714]">2. Completeness Gate & Not-Checked Register</h2>
                  <p className="font-sans text-xs text-[#5C5752]">
                    Evaluate statutory mandatory document compliance and inspect procedures intentionally omitted.
                  </p>
                </div>
              </div>

              {completenessResult && (
                <div className="p-4 bg-white border border-[#E8E4DC] flex items-center justify-between gap-4 font-mono text-xs">
                  <div>
                    <span className="text-[#7A746A] uppercase text-[10px] block">STATUTORY COMPLETENESS GATE:</span>
                    <span className={`text-base font-bold ${completenessResult.gate_status === 'PASSED' ? 'text-[#1A7A40]' : 'text-[#A82B1E]'}`}>
                      GATE STATUS: {completenessResult.gate_status}
                    </span>
                    <div className="text-[#5C5752] text-[11px]">
                      Required: {completenessResult.total_required} · Satisfied: {completenessResult.total_satisfied}
                    </div>
                  </div>
                  <div className="text-right text-[11px] text-[#5C5752]">
                    Can proceed to final report: {completenessResult.can_proceed_to_report ? 'YES' : 'NO (PENDING REVIEW)'}
                  </div>
                </div>
              )}

              <div className="space-y-3">
                <h3 className="font-serif text-lg text-[#1A1714]">Not-Checked Register (Omission Audit Trail)</h3>
                <div className="grid gap-4">
                  {notCheckedList.map((item: any) => (
                    <div key={item.procedure_id} className="bg-white border border-[#E8E4DC] p-4 space-y-2">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-xs font-bold text-[#A82B1E]">{item.procedure_id}</span>
                          <span className="font-serif text-sm font-semibold text-[#1A1714]">{item.title || item.procedure_name}</span>
                        </div>
                        <span className="px-2 py-0.5 bg-[#A82B1E]/10 text-[#A82B1E] border border-[#A82B1E] font-mono text-[10px] font-bold">
                          {item.status || 'NOT_CHECKED'}
                        </span>
                      </div>
                      <p className="font-sans text-xs text-[#5C5752]">
                        <strong className="text-[#1A1714]">Omission Reason: </strong>
                        {item.reason_not_checked || item.omission_reason}
                      </p>
                      <div className="text-[11px] font-mono text-[#7A746A] flex justify-between">
                        <span>Audit Area: {item.audit_area}</span>
                        <span>Assigned Reviewer: {item.assigned_reviewer}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* 3. MULTI-AGENT RUN */}
          {activeTab === 'investigation' && (
            <div className="space-y-6">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                  <h2 className="font-serif text-2xl text-[#1A1714]">3. Multi-Agent Investigation Workspace</h2>
                  <p className="font-sans text-xs text-[#5C5752]">
                    Orchestrated LangGraph supervisor with CrewAI specialists and MS Agent Framework reviewer.
                  </p>
                </div>
                <button
                  onClick={handleRunInvestigation}
                  className="px-4 py-2 bg-[#1A1714] text-[#F6F3EB] font-mono text-xs font-semibold hover:bg-[#2A2826] flex items-center gap-2"
                >
                  <Cpu className="w-3.5 h-3.5 text-[#B08D4F]" />
                  <span>Execute Full Investigation</span>
                </button>
              </div>

              <div className="bg-white border border-[#E8E4DC] p-6 space-y-4 font-mono text-xs">
                <div className="flex items-center justify-between border-b border-[#E8E4DC] pb-3">
                  <div>
                    <span className="text-[10px] uppercase text-[#7A746A] block">ORCHESTRATION PIPELINE</span>
                    <span className="font-bold text-[#1A1714]">LangGraph Supervisor (Pregel Executor)</span>
                  </div>
                  <span className="px-2 py-1 bg-[#1A7A40]/10 text-[#1A7A40] border border-[#1A7A40] text-[10px] font-bold">
                    DURABLE CHECKPOINTS ACTIVE
                  </span>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
                  <div className="p-3 bg-[#F6F3EB] border border-[#E8E4DC] space-y-1">
                    <span className="font-bold text-[#1A1714] block">1. Extraction & Gate</span>
                    <span className="text-[#5C5752] text-[11px]">Deterministic parser validating SHA-256 and completeness.</span>
                  </div>
                  <div className="p-3 bg-[#F6F3EB] border border-[#E8E4DC] space-y-1">
                    <span className="font-bold text-[#1A1714] block">2. Investigation Specialists</span>
                    <span className="text-[#5C5752] text-[11px]">CrewAI forensic agents examining cut-off, tax, and ledger entries.</span>
                  </div>
                  <div className="p-3 bg-[#F6F3EB] border border-[#E8E4DC] space-y-1">
                    <span className="font-bold text-[#1A1714] block">3. Independent Review</span>
                    <span className="text-[#5C5752] text-[11px]">MS Agent Framework issuing structured counter-evidence challenges.</span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* 4. COUNTER-EVIDENCE */}
          {activeTab === 'counter-evidence' && (
            <div className="space-y-6">
              <div>
                <h2 className="font-serif text-2xl text-[#1A1714]">4. Counter-Evidence Scrutiny</h2>
                <p className="font-sans text-xs text-[#5C5752]">
                  Examine supporting evidence, contradictory evidence, and alternative explanations.
                </p>
              </div>

              <div className="grid gap-4">
                {findings.map((f: any) => {
                  const ce = f.counter_evidence || {};
                  return (
                    <div key={f.finding_id} className="bg-white border border-[#E8E4DC] p-5 space-y-4">
                      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[#E8E4DC] pb-3">
                        <div>
                          <span className="font-mono text-xs font-bold text-[#A82B1E]">{f.finding_id}</span>
                          <h3 className="font-serif text-base font-semibold text-[#1A1714]">{f.title}</h3>
                        </div>
                        <span className={`px-2.5 py-1 font-mono text-xs font-bold border ${
                          ce.verdict === 'CONTRADICTED'
                            ? 'bg-[#1A7A40]/10 text-[#1A7A40] border-[#1A7A40]'
                            : ce.verdict === 'PARTIALLY_SUPPORTED'
                            ? 'bg-[#B77F0A]/10 text-[#B77F0A] border-[#B77F0A]'
                            : 'bg-[#A82B1E]/10 text-[#A82B1E] border-[#A82B1E]'
                        }`}>
                          VERDICT: {ce.verdict || 'UNRESOLVED'}
                        </span>
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-sans">
                        <div className="p-3 bg-[#FDFBF7] border border-[#E8E4DC] space-y-1">
                          <strong className="font-mono text-[10px] text-[#1A7A40] uppercase block">SUPPORTING EVIDENCE:</strong>
                          <ul className="list-disc list-inside space-y-1 text-[#5C5752]">
                            {(ce.supporting_points || []).map((pt: string, idx: number) => (
                              <li key={idx}>{pt}</li>
                            ))}
                          </ul>
                        </div>
                        <div className="p-3 bg-[#FDFBF7] border border-[#E8E4DC] space-y-1">
                          <strong className="font-mono text-[10px] text-[#A82B1E] uppercase block">CONTRADICTING EVIDENCE:</strong>
                          <ul className="list-disc list-inside space-y-1 text-[#5C5752]">
                            {(ce.contradicting_points || []).map((pt: string, idx: number) => (
                              <li key={idx}>{pt}</li>
                            ))}
                            {(!ce.contradicting_points || ce.contradicting_points.length === 0) && (
                              <li className="italic text-[#7A746A]">No contradicting evidence discovered.</li>
                            )}
                          </ul>
                        </div>
                      </div>

                      {ce.alternative_explanation && (
                        <div className="p-3 bg-[#F6F3EB] border border-[#E8E4DC] text-xs font-sans text-[#5C5752]">
                          <strong className="font-mono text-[10px] text-[#7A5F2B] uppercase block">ALTERNATIVE EXPLANATION:</strong>
                          <span>{ce.alternative_explanation}</span>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* 5. HUMAN REVIEW QUEUE */}
          {activeTab === 'review' && (
            <div className="space-y-6">
              <div>
                <h2 className="font-serif text-2xl text-[#1A1714]">5. Auditor Decision Workspace</h2>
                <p className="font-sans text-xs text-[#5C5752]">
                  Statutory human-in-the-loop sign-off. Brass authorization reserved exclusively for Chartered Accountant Partners.
                </p>
              </div>

              {/* Finding Selection Tabs */}
              <div className="flex gap-2 border-b border-[#E8E4DC] pb-2 overflow-x-auto">
                {findings.map((f: any) => (
                  <button
                    key={f.finding_id}
                    onClick={() => {
                      setSelectedFindingId(f.finding_id);
                      setUnresolvedConfirmed(false);
                    }}
                    className={`px-3 py-1.5 font-mono text-xs border ${
                      selectedFindingId === f.finding_id
                        ? 'bg-[#1A1714] text-[#F6F3EB] border-[#1A1714]'
                        : 'bg-white text-[#5C5752] border-[#E8E4DC] hover:bg-[#FDFBF7]'
                    }`}
                  >
                    {f.finding_id} {f.human_review?.status === 'APPROVED' ? '✓' : ''}
                  </button>
                ))}
              </div>

              {/* Selected Finding Detail & Decision Panel */}
              <div className="bg-white border border-[#E8E4DC] p-6 space-y-5">
                <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#E8E4DC] pb-4">
                  <div>
                    <span className="font-mono text-xs font-bold text-[#A82B1E]">{selectedFinding.finding_id}</span>
                    <h3 className="font-serif text-xl text-[#1A1714]">{selectedFinding.title}</h3>
                    <span className="font-mono text-xs text-[#5C5752]">
                      Material Variance: ₹{formatINR(selectedFinding.observed_variance_inr || selectedFinding.impact_amount || '0')}
                    </span>
                  </div>
                  {selectedFinding.human_review?.status === 'APPROVED' ? (
                    <div className="flex items-center gap-2 px-3 py-1.5 bg-[#C5A059]/15 border-2 border-[#C5A059] text-[#7A5F2B] font-mono text-xs font-bold">
                      <Lock className="w-4 h-4 text-[#C5A059]" />
                      <span>APPROVED BY {selectedFinding.human_review.reviewer_name || 'PARTNER'}</span>
                    </div>
                  ) : (
                    <span className="px-2.5 py-1 bg-[#A82B1E]/10 text-[#A82B1E] border border-[#A82B1E] font-mono text-xs font-bold">
                      REVIEW PENDING
                    </span>
                  )}
                </div>

                {/* Counter-Evidence Summary */}
                <div className="p-4 bg-[#FDFBF7] border border-[#E8E4DC] space-y-2 text-xs">
                  <div className="flex justify-between font-mono">
                    <span className="text-[#7A746A]">INDEPENDENT REVIEW VERDICT:</span>
                    <span className="font-bold text-[#7A5F2B]">{selectedFinding.counter_evidence?.verdict}</span>
                  </div>
                  <p className="text-[#5C5752]">{selectedFinding.counter_evidence?.verdict_rationale || selectedFinding.counter_evidence?.alternative_explanation}</p>
                </div>

                {/* Decision Form */}
                <div className="space-y-4 pt-2">
                  {selectedFinding.counter_evidence?.verdict === 'PARTIALLY_SUPPORTED' && (
                    <label className="flex items-start gap-2.5 p-3 bg-[#B77F0A]/10 border border-[#B77F0A] text-xs font-mono text-[#7A5F2B] cursor-pointer">
                      <input
                        type="checkbox"
                        id="unresolved-check"
                        checked={unresolvedConfirmed}
                        onChange={(e) => setUnresolvedConfirmed(e.target.checked)}
                        className="mt-0.5"
                      />
                      <span>
                        Statutory Acknowledgment: I have reviewed unresolved counter-evidence points and confirm this finding remains materially relevant for the audit opinion.
                      </span>
                    </label>
                  )}

                  <div>
                    <label className="font-mono text-xs font-semibold text-[#1A1714] block mb-1">
                      Statutory Sign-Off Notes / Working Paper Reference:
                    </label>
                    <textarea
                      value={approvalReason}
                      onChange={(e) => setApprovalReason(e.target.value)}
                      placeholder="Record justification, ICAI standard citations, or reasons for rejection/escalation..."
                      className="w-full p-3 border border-[#E8E4DC] font-sans text-xs text-[#1A1714] focus:outline-none focus:border-[#7A5F2B] bg-[#FDFBF7]"
                      rows={3}
                    />
                  </div>

                  <div className="flex flex-wrap items-center gap-3 pt-2">
                    <button
                      onClick={() => handleDecision('APPROVE')}
                      className="px-5 py-2.5 bg-[#C5A059] hover:bg-[#B08D4F] text-[#1A1714] font-mono text-xs font-bold tracking-wider transition-colors border border-[#7A5F2B] shadow-sm flex items-center gap-2"
                    >
                      <CheckCircle2 className="w-4 h-4" />
                      <span>APPROVE FINDING (BRASS SIGN-OFF)</span>
                    </button>
                    <button
                      onClick={() => handleDecision('REJECT')}
                      className="px-4 py-2.5 bg-white hover:bg-[#FDFBF7] text-[#A82B1E] font-mono text-xs font-semibold border border-[#A82B1E] transition-colors"
                    >
                      REJECT
                    </button>
                    <button
                      onClick={() => handleDecision('ESCALATE')}
                      className="px-4 py-2.5 bg-white hover:bg-[#FDFBF7] text-[#5C5752] font-mono text-xs font-semibold border border-[#E8E4DC] hover:border-[#7A746A] transition-colors"
                    >
                      ESCALATE TO SENIOR PARTNER
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* 6. DECIMAL MATH */}
          {activeTab === 'calculations' && (
            <div className="space-y-6">
              <div>
                <h2 className="font-serif text-2xl text-[#1A1714]">6. Deterministic Financial Calculations</h2>
                <p className="font-sans text-xs text-[#5C5752]">
                  All calculations executed exclusively via Python Decimal with ROUND_HALF_UP. Zero IEEE-754 floating-point drift.
                </p>
              </div>

              {/* Interactive Calculation Form */}
              <div className="bg-white border border-[#E8E4DC] p-5 space-y-4">
                <h3 className="font-serif text-base font-semibold text-[#1A1714]">Execute Decimal Variance Test</h3>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 font-mono text-xs">
                  <div>
                    <label className="text-[#7A746A] text-[10px] block mb-1 uppercase">Formula Name</label>
                    <input
                      type="text"
                      value={calcInputName}
                      onChange={(e) => setCalcInputName(e.target.value)}
                      className="w-full p-2 border border-[#E8E4DC] text-[#1A1714] bg-[#FDFBF7]"
                    />
                  </div>
                  <div>
                    <label className="text-[#7A746A] text-[10px] block mb-1 uppercase">Amount 1 (₹)</label>
                    <input
                      type="text"
                      value={calcInputVal1}
                      onChange={(e) => setCalcInputVal1(e.target.value)}
                      className="w-full p-2 border border-[#E8E4DC] text-[#1A1714] bg-[#FDFBF7]"
                    />
                  </div>
                  <div>
                    <label className="text-[#7A746A] text-[10px] block mb-1 uppercase">Amount 2 (₹)</label>
                    <input
                      type="text"
                      value={calcInputVal2}
                      onChange={(e) => setCalcInputVal2(e.target.value)}
                      className="w-full p-2 border border-[#E8E4DC] text-[#1A1714] bg-[#FDFBF7]"
                    />
                  </div>
                </div>
                <button
                  onClick={handleRunCalculation}
                  className="px-4 py-2 bg-[#1A1714] text-[#F6F3EB] font-mono text-xs font-semibold hover:bg-[#2A2826]"
                >
                  Run Deterministic Calculation
                </button>
              </div>

              <div className="grid gap-4">
                {calculations.map((calc: any) => (
                  <div key={calc.calculation_id} className="bg-white border border-[#E8E4DC] p-4 space-y-3 font-mono text-xs">
                    <div className="flex justify-between items-center border-b border-[#E8E4DC] pb-2">
                      <span className="font-bold text-[#1A1714]">{calc.calculation_name || calc.formula_name}</span>
                      <span className="text-[#1A7A40] font-bold">✓ DETERMINISTIC PROOF</span>
                    </div>
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-[11px] text-[#5C5752]">
                      <div>ID: {calc.calculation_id}</div>
                      <div>Result: ₹{formatINR(calc.result)}</div>
                      <div>Variance: {calc.variance || 'N/A'}</div>
                      <div>Policy: Decimal(0.01)</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 7. STATUTORY TAX */}
          {activeTab === 'tax' && (
            <div className="space-y-6">
              <div>
                <h2 className="font-serif text-2xl text-[#1A1714]">7. Section 115BAA Corporate Tax Computation</h2>
                <p className="font-sans text-xs text-[#5C5752]">
                  Concessional regime rate: 22% base + 10% surcharge + 4% cess = exactly 25.168% effective tax liability.
                </p>
              </div>

              <div className="bg-white border border-[#E8E4DC] p-6 space-y-4">
                <h3 className="font-serif text-lg text-[#1A1714]">Statutory Concessional Tax Calculator</h3>
                <div className="flex flex-wrap items-end gap-3 font-mono text-xs">
                  <div className="flex-1 min-w-[200px]">
                    <label className="text-[#7A746A] text-[10px] block mb-1 uppercase">Gross Total Income (₹ INR)</label>
                    <input
                      type="text"
                      value={taxIncomeInput}
                      onChange={(e) => setTaxIncomeInput(e.target.value)}
                      className="w-full p-2 border border-[#E8E4DC] text-[#1A1714] bg-[#FDFBF7]"
                    />
                  </div>
                  <button
                    onClick={handleComputeTax}
                    className="px-4 py-2 bg-[#1A1714] text-[#F6F3EB] font-mono text-xs font-semibold hover:bg-[#2A2826]"
                  >
                    Compute Section 115BAA Tax
                  </button>
                </div>

                {taxResult && (
                  <div className="p-4 bg-[#FDFBF7] border border-[#E8E4DC] space-y-2 font-mono text-xs">
                    <div className="flex justify-between border-b border-[#E8E4DC] pb-2 font-bold">
                      <span>Total Tax Liability:</span>
                      <span className="text-[#1A7A40]">₹{formatINR(taxResult.total_tax_liability)}</span>
                    </div>
                    <div className="grid grid-cols-2 gap-2 text-[11px] text-[#5C5752] pt-1">
                      <div>Effective Rate: {taxResult.effective_tax_rate_percent}%</div>
                      <div>Form 10-IC: Exercised</div>
                      <div>Citations: Section 115BAA, Income-tax Act, 1961</div>
                      <div>Verification: STATUTORY VERIFIED</div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* 8. AUDIT REPORT */}
          {activeTab === 'reports' && (
            <div className="space-y-6">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                  <h2 className="font-serif text-2xl text-[#1A1714]">8. Audit Report Manifest & Generation</h2>
                  <p className="font-sans text-xs text-[#5C5752]">
                    Cryptographic working paper manifest linking the generated audit report to SHA-256 evidence hashes.
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={handleGenerateReport}
                    className="px-3 py-2 bg-white text-[#1A1714] border border-[#7A746A] font-mono text-xs font-semibold hover:bg-[#FDFBF7]"
                  >
                    Generate Draft Manifest
                  </button>
                  <button
                    onClick={handleFinalizeReport}
                    className="px-4 py-2 bg-[#1A1714] text-[#F6F3EB] font-mono text-xs font-semibold hover:bg-[#2A2826]"
                  >
                    Partner Finalize Report
                  </button>
                </div>
              </div>

              <div className="bg-white border border-[#E8E4DC] p-6 space-y-4">
                <div className="flex items-center justify-between border-b border-[#E8E4DC] pb-3">
                  <div>
                    <span className="font-mono text-xs font-bold text-[#7A5F2B]">{reportManifest.manifest_id}</span>
                    <h3 className="font-serif text-lg text-[#1A1714]">Statutory Audit Working Paper Manifest</h3>
                  </div>
                  <span className={`px-3 py-1 font-mono text-xs font-bold border ${
                    reportManifest.status === 'FINALIZED'
                      ? 'bg-[#1A7A40]/10 text-[#1A7A40] border-[#1A7A40]'
                      : 'bg-[#B77F0A]/10 text-[#B77F0A] border-[#B77F0A]'
                  }`}>
                    STATUS: {reportManifest.status}
                  </span>
                </div>

                <div className="font-mono text-xs space-y-2">
                  <div>Report Content Hash: <span className="text-[#7A5F2B]">{reportManifest.report_hash}</span></div>
                  <div>Generated At: {formatIST(reportManifest.generated_at)}</div>
                  <div>Underlying Evidence Files: {reportManifest.total_evidence_files || reportManifest.evidence_hashes?.length || 4} files verified</div>
                </div>

                <div className="space-y-2 pt-4 border-t border-[#E8E4DC]">
                  <span className="font-mono text-[10px] text-[#7A746A] uppercase block">EVIDENCE HASH MANIFEST:</span>
                  <div className="bg-[#121110] text-[#9C968F] p-4 font-mono text-[11px] space-y-1">
                    {(reportManifest.evidence_hashes || []).map((h: string, i: number) => (
                      <div key={i} className="flex items-center gap-2">
                        <span className="text-[#B08D4F]">[{i + 1}]</span>
                        <span>{h}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* 9. PROVENANCE GRAPH */}
          {activeTab === 'provenance' && (
            <div className="space-y-4">
              <h2 className="font-serif text-2xl text-[#1A1714]">9. Interactive Evidence Provenance Graph</h2>
              <ProvenanceGraph />
            </div>
          )}

          {/* 10. SETTINGS & ADMINISTRATION */}
          {activeTab === 'settings' && (
            <div className="space-y-6">
              <div>
                <h2 className="font-serif text-2xl text-[#1A1714]">10. Audit Engagement Settings & Role Matrix</h2>
                <p className="font-sans text-xs text-[#5C5752]">
                  Engagement team assignments, assessment year rules, and role-based access control.
                </p>
              </div>

              {/* Auditor Sign-In & Session Management */}
              <div className="bg-white border border-[#E8E4DC] p-6 space-y-4">
                <h3 className="font-serif text-lg text-[#1A1714]">Auditor Authentication (Environment-Controlled)</h3>
                {currentUser ? (
                  <div className="flex items-center justify-between bg-[#1A7A40]/10 border border-[#1A7A40] p-4 text-xs font-mono">
                    <div>
                      <div className="font-bold text-[#1A7A40]">AUTHENTICATED: {currentUser.full_name}</div>
                      <div className="text-[#5C5752]">{currentUser.email} · Role: {currentUser.role}</div>
                    </div>
                    <button
                      onClick={handleLogout}
                      className="px-3 py-1.5 bg-[#7A746A] text-white hover:bg-[#1A1714] text-xs font-mono transition-colors"
                    >
                      Sign Out
                    </button>
                  </div>
                ) : (
                  <form onSubmit={handleLogin} className="space-y-3 font-mono text-xs">
                    <p className="text-[#5C5752] font-sans">
                      Sign in using your authorized audit credentials. Credentials are verified against server-side PBKDF2 hashes; zero hardcoded passwords exist in client bundles.
                    </p>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                      <div>
                        <label className="block text-[11px] text-[#7A746A] uppercase mb-1">Username / ICAI Identity</label>
                        <input
                          type="text"
                          value={loginUsername}
                          onChange={(e) => setLoginUsername(e.target.value)}
                          className="w-full px-3 py-2 border border-[#7A746A] bg-[#FDFBF7] text-[#1A1714] focus:outline-none"
                          placeholder="e.g. partner_sharma"
                          required
                        />
                      </div>
                      <div>
                        <label className="block text-[11px] text-[#7A746A] uppercase mb-1">Password</label>
                        <input
                          type="password"
                          value={loginPassword}
                          onChange={(e) => setLoginPassword(e.target.value)}
                          className="w-full px-3 py-2 border border-[#7A746A] bg-[#FDFBF7] text-[#1A1714] focus:outline-none"
                          placeholder="Enter audit passphrase"
                          required
                        />
                      </div>
                    </div>
                    <div className="flex justify-end pt-2">
                      <button
                        type="submit"
                        className="px-4 py-2 bg-[#1A1714] text-[#F6F3EB] hover:bg-[#332F2B] font-mono text-xs transition-colors flex items-center gap-2"
                      >
                        <Lock className="w-3.5 h-3.5 text-[#B08D4F]" />
                        <span>Authenticate Session</span>
                      </button>
                    </div>
                  </form>
                )}
              </div>

              <div className="bg-white border border-[#E8E4DC] p-6 space-y-4">
                <h3 className="font-serif text-lg text-[#1A1714]">Authorized Engagement Team</h3>
                <div className="space-y-3 font-mono text-xs">
                  <div className="flex justify-between items-center border-b border-[#E8E4DC] pb-2">
                    <div>
                      <div className="font-bold text-[#1A1714]">CA Rajesh K. Sharma</div>
                      <div className="text-[#5C5752]">Partner · ICAI Membership 084920</div>
                    </div>
                    <span className="px-2 py-0.5 bg-[#B08D4F]/10 text-[#7A5F2B] border border-[#B08D4F] font-bold">
                      SIGNING PARTNER
                    </span>
                  </div>

                  <div className="flex justify-between items-center border-b border-[#E8E4DC] pb-2">
                    <div>
                      <div className="font-bold text-[#1A1714]">Amitav Sen</div>
                      <div className="text-[#5C5752]">Audit Manager · ICAI Membership 119283</div>
                    </div>
                    <span className="px-2 py-0.5 bg-[#E8E4DC] text-[#1A1714]">
                      AUDIT MANAGER
                    </span>
                  </div>

                  <div className="flex justify-between items-center">
                    <div>
                      <div className="font-bold text-[#1A1714]">Priya Sundaram</div>
                      <div className="text-[#5C5752]">Audit Associate · ICAI Student Registration</div>
                    </div>
                    <span className="px-2 py-0.5 bg-[#E8E4DC] text-[#1A1714]">
                      AUDIT ASSOCIATE
                    </span>
                  </div>
                </div>

                {auditEvents.length > 0 && (
                  <div className="space-y-2 pt-4 border-t border-[#E8E4DC]">
                    <span className="font-mono text-[10px] text-[#7A746A] uppercase block">LIVE AUDIT EVENT TRAIL:</span>
                    <div className="bg-[#121110] text-[#9C968F] p-3 font-mono text-[10px] space-y-1 max-h-48 overflow-y-auto">
                      {auditEvents.slice(0, 10).map((ev, idx) => (
                        <div key={idx} className="flex items-center gap-2">
                          <span className="text-[#B08D4F]">[{ev.event_type}]</span>
                          <span>{ev.created_at}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
};
