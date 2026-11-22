// Data models and types matching AUDRYN backend Pydantic schemas

export type ExtractionStatus = 'PENDING' | 'EXTRACTED' | 'FAILED';

export type ReviewVerdict =
  | 'SUPPORTED'
  | 'CONTRADICTED'
  | 'PARTIALLY_SUPPORTED'
  | 'UNRESOLVED'
  | 'INSUFFICIENT_EVIDENCE';

export type HumanReviewDecision = 'APPROVE' | 'REJECT' | 'REQUEST_EVIDENCE' | 'ESCALATE';

export type ReportStatus = 'BLOCKED' | 'DRAFT' | 'REVIEW_READY' | 'FINALIZED';

export interface EvidenceRecord {
  evidence_id: string;
  source_filename: string;
  sha256_hash: string;
  extraction_status: ExtractionStatus;
  record_count: number;
  uploaded_at: string;
  provenance_coordinates?: {
    page: number;
    bbox?: [number, number, number, number];
  };
}

export interface CalculationRecord {
  calculation_id: string;
  formula_name: string;
  statutory_section?: string;
  input_values: Record<string, string>; // Exact Decimal strings
  result: string; // Exact Decimal string
  variance?: string;
  is_verified: boolean;
  notes: string;
}

export interface Finding {
  finding_id: string;
  title: string;
  category: 'REVENUE' | 'TAX' | 'DEPRECIATION' | 'JOURNAL_ENTRY' | 'CROSS_YEAR';
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  source_evidence_ids: string[];
  calculation_id?: string;
  observed_variance_inr?: string; // Decimal string
  impact_amount?: string;
  counter_evidence: {
    verdict: ReviewVerdict;
    supporting_points: string[];
    contradicting_points: string[];
    alternative_explanation: string;
    verdict_rationale?: string;
    remaining_unknowns: string[];
  };
  human_review?: {
    status: 'PENDING' | 'APPROVED' | 'REJECTED' | 'ESCALATED';
    reviewer_name?: string;
    reviewer_membership_no?: string;
    decided_at?: string;
    reason?: string;
  };
}

export interface NotCheckedItem {
  procedure_id: string;
  audit_area: string;
  procedure_name: string;
  omission_reason: string;
  risk_level: 'HIGH' | 'MEDIUM' | 'LOW';
  mitigating_notes: string;
  assigned_reviewer: string;
}

export interface ReportManifest {
  manifest_id: string;
  generated_at: string;
  report_hash: string;
  evidence_hashes: string[];
  total_evidence_files: number;
  unresolved_findings_count: number;
  status: ReportStatus;
}
