import { EvidenceRecord, Finding, NotCheckedItem, CalculationRecord, ReportManifest } from '../types';

export const SYNTHETIC_EVIDENCE: EvidenceRecord[] = [
  {
    evidence_id: 'EV-2024-001',
    source_filename: 'trial_balance_FY2023_24_final.xlsx',
    sha256_hash: 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
    extraction_status: 'EXTRACTED',
    record_count: 1420,
    uploaded_at: '2024-04-12T10:15:00Z',
    provenance_coordinates: { page: 1 },
  },
  {
    evidence_id: 'EV-2024-002',
    source_filename: 'bank_statement_hdfc_q4.pdf',
    sha256_hash: '8f434346648f6b96df89dda901c5176b10a6d83961dd3c1ac88b59b2dc327aa4',
    extraction_status: 'EXTRACTED',
    record_count: 384,
    uploaded_at: '2024-04-12T10:18:22Z',
    provenance_coordinates: { page: 14 },
  },
  {
    evidence_id: 'EV-2024-003',
    source_filename: 'gstr_2b_reconciliation_fy24.xlsx',
    sha256_hash: 'ca978112ca1bbdcafac231b39a23dc4da786eff8147c4e72b9807785afee48bb',
    extraction_status: 'EXTRACTED',
    record_count: 890,
    uploaded_at: '2024-04-12T10:22:05Z',
    provenance_coordinates: { page: 3 },
  },
  {
    evidence_id: 'EV-2024-004',
    source_filename: 'fixed_assets_register_fy24.pdf',
    sha256_hash: '3e23e8160039594a33894f6564e1b1348bbd7a0088d42c4acb73eeaed59c009d',
    extraction_status: 'EXTRACTED',
    record_count: 156,
    uploaded_at: '2024-04-12T10:25:40Z',
    provenance_coordinates: { page: 6 },
  },
];

export const SYNTHETIC_FINDINGS: Finding[] = [
  {
    finding_id: 'ANOMALY-001',
    title: 'Revenue Recognition — Cut-Off Timing Discrepancy',
    category: 'REVENUE',
    severity: 'HIGH',
    source_evidence_ids: ['EV-2024-001', 'EV-2024-002'],
    calculation_id: 'CALC-REV-01',
    observed_variance_inr: '4500000.00',
    counter_evidence: {
      verdict: 'PARTIALLY_SUPPORTED',
      supporting_points: [
        'Sales invoice INV-2024-889 dated 31 Mar 2024 booked in Q4 revenue for ₹45,00,000.00.',
        'Customer purchase order confirmed Q4 acceptance terms.',
      ],
      contradicting_points: [
        'Lorry receipt / e-Way bill dated 03 Apr 2024 proves dispatch occurred in subsequent FY 2024-25.',
      ],
      alternative_explanation:
        'Goods were staged at warehouse on 31 March but physical carrier gate-out occurred post-midnight on 3 April.',
      remaining_unknowns: [
        'Warehouse CCTV dispatch log not yet furnished by management.',
        'Auditor confirmation letter from counterparty pending receipt.',
      ],
    },
    human_review: {
      status: 'PENDING',
    },
  },
  {
    finding_id: 'ANOMALY-002',
    title: 'Section 32 Depreciation — 180-Day Rule Addition Mismatch',
    category: 'TAX',
    severity: 'MEDIUM',
    source_evidence_ids: ['EV-2024-004'],
    calculation_id: 'CALC-TAX-02',
    observed_variance_inr: '1250000.00',
    counter_evidence: {
      verdict: 'CONTRADICTED',
      supporting_points: [
        'Asset put-to-use certificate was originally filed with date 15 Oct 2023 (less than 180 days).',
      ],
      contradicting_points: [
        'Installation log and electricity sub-meter readings prove trial production began 28 Sep 2023 (used >= 180 days).',
      ],
      alternative_explanation:
        'Clerical error on commissioning certificate header: inspection signed in October but trial run active since September.',
      remaining_unknowns: [],
    },
    human_review: {
      status: 'APPROVED',
      reviewer_name: 'Rajesh K. Sharma, FCA',
      reviewer_membership_no: 'ICAI-084920',
      decided_at: '2024-04-15T14:30:00Z',
      reason: 'Verified electricity sub-meter data and factory logbook confirming commercial trial run on 28 September 2023. Full 100% depreciation rate under Section 32 confirmed.',
    },
  },
  {
    finding_id: 'ANOMALY-003',
    title: 'Input Tax Credit (ITC) Variance — GSTR-2B vs Books',
    category: 'TAX',
    severity: 'CRITICAL',
    source_evidence_ids: ['EV-2024-003'],
    calculation_id: 'CALC-ITC-03',
    observed_variance_inr: '7820450.00',
    counter_evidence: {
      verdict: 'SUPPORTED',
      supporting_points: [
        '₹78,20,450.00 ITC claimed in GSTR-3B does not reflect in auto-populated GSTR-2B statement.',
        'Three suppliers failed to file their GSTR-1 returns for Q3 and Q4.',
      ],
      contradicting_points: [],
      alternative_explanation:
        'Suppliers have delayed quarterly returns; ITC is inadmissible under Section 16(2)(aa) of CGST Act until supplier files.',
      remaining_unknowns: [
        'Possibility of supplier late-filing in subsequent month has not been reconciled.',
      ],
    },
    human_review: {
      status: 'PENDING',
    },
  },
];

export const SYNTHETIC_NOT_CHECKED: NotCheckedItem[] = [
  {
    procedure_id: 'NC-001',
    audit_area: 'Physical Inventory Verification',
    procedure_name: 'Year-End Stock Count at Bhiwandi Depot',
    omission_reason: 'Depot under statutory fumigation lockdown on 31 March 2024; auditor physical attendance precluded.',
    risk_level: 'HIGH',
    mitigating_notes: 'Roll-forward procedure scheduled with management perpetual inventory records and independent spot-check.',
    assigned_reviewer: 'Priya Sundaram, ACA',
  },
  {
    procedure_id: 'NC-002',
    audit_area: 'Statutory Dues — ESIC & EPF',
    procedure_name: 'Third-Party Contractor Challan Inspection',
    omission_reason: 'Contractor portal login tokens expired during field audit; challans pending electronic submission.',
    risk_level: 'MEDIUM',
    mitigating_notes: 'Indemnity bond secured from vendor; portal reconciliation assigned to Q1 follow-up.',
    assigned_reviewer: 'Amitav Sen, FCA',
  },
  {
    procedure_id: 'NC-003',
    audit_area: 'Foreign Exchange Hedging',
    procedure_name: 'Mark-to-Market Bank Valuations',
    omission_reason: 'Direct bank confirmation letter for Singapore branch derivatives pending dispatch.',
    risk_level: 'LOW',
    mitigating_notes: 'Management internal valuation verified against Bloomberg spot rates on 31 March 2024.',
    assigned_reviewer: 'Rajesh K. Sharma, FCA',
  },
];

export const SYNTHETIC_CALCULATIONS: CalculationRecord[] = [
  {
    calculation_id: 'CALC-REV-01',
    formula_name: 'Quarterly Revenue Cut-Off Variance',
    input_values: {
      'Gross_Revenue_Per_Books': '124567890.00',
      'Dispatched_Pre_March_31': '120067890.00',
      'Post_Period_Dispatches': '4500000.00',
    },
    result: '4500000.00',
    variance: '3.61%',
    is_verified: true,
    notes: 'Calculated using Decimal arithmetic. Cut-off threshold exceeded (> ₹10,00,000.00).',
  },
  {
    calculation_id: 'CALC-TAX-02',
    formula_name: 'Section 115BAA Corporate Tax Computation',
    statutory_section: 'Section 115BAA, Income-tax Act, 1961',
    input_values: {
      'Gross_Total_Income': '48500000.00',
      'Base_Tax_Rate': '22.00%',
      'Surcharge_Rate': '10.00%',
      'Health_Education_Cess': '4.00%',
      'Effective_Tax_Rate': '25.168%',
    },
    result: '12206480.00',
    is_verified: true,
    notes: 'No Chapter VI-A deductions (except 80JJAA) or Section 32(1)(iia) additional depreciation claimed.',
  },
];

export const SYNTHETIC_MANIFEST: ReportManifest = {
  manifest_id: 'MNF-2024-AY2024-25',
  generated_at: '2024-04-18T18:00:00Z',
  report_hash: '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08',
  evidence_hashes: [
    'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
    '8f434346648f6b96df89dda901c5176b10a6d83961dd3c1ac88b59b2dc327aa4',
    'ca978112ca1bbdcafac231b39a23dc4da786eff8147c4e72b9807785afee48bb',
    '3e23e8160039594a33894f6564e1b1348bbd7a0088d42c4acb73eeaed59c009d',
  ],
  total_evidence_files: 4,
  unresolved_findings_count: 2,
  status: 'DRAFT',
};
