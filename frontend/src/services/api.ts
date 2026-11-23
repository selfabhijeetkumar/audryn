/**
 * AUDRYN API Client Service.
 * Typed HTTP client interfacing with versioned FastAPI backend (/api/v1).
 * Supports automatic CSRF token propagation, session cookies, and correlation IDs.
 */

const API_BASE = '/api/v1';

export class ApiError extends Error {
  status: number;
  detail: string;

  constructor(status: number, detail: string) {
    super(`API Error ${status}: ${detail}`);
    this.name = 'ApiError';
    this.status = status;
    this.detail = detail;
  }
}

class AudrynApiClient {
  private csrfToken: string | null = null;

  setCsrfToken(token: string) {
    this.csrfToken = token;
  }

  getCsrfToken(): string | null {
    return this.csrfToken;
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const headers = new Headers(options.headers || {});
    headers.set('X-Correlation-ID', `REQ-${Date.now()}-${Math.random().toString(36).substring(2, 7)}`);

    if (this.csrfToken && ['POST', 'PUT', 'DELETE', 'PATCH'].includes(options.method?.toUpperCase() || '')) {
      headers.set('X-CSRF-Token', this.csrfToken);
    }

    const response = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers,
      credentials: 'include', // Always send and accept session cookies
    });

    // Check for updated CSRF token in response header
    const newCsrf = response.headers.get('X-CSRF-Token');
    if (newCsrf) {
      this.csrfToken = newCsrf;
    }

    if (!response.ok) {
      let detail = `Request failed with status ${response.status}`;
      try {
        const errorData = await response.json();
        detail = errorData.detail || errorData.message || detail;
      } catch {
        // use default detail
      }
      throw new ApiError(response.status, detail);
    }

    return response.json() as Promise<T>;
  }

  // 1. Health
  async getHealth() {
    return this.request<{
      status: string;
      service: string;
      version: string;
      database: { connected: boolean };
      inference: { provider: string; connected: boolean; model: string };
    }>('/health');
  }

  // 2. Auth
  async login(username: string, password: string) {
    const res = await this.request<{
      message: string;
      user: {
        user_id: string;
        username: string;
        email: string;
        full_name: string;
        role: string;
        is_active: boolean;
        permissions: string[];
      };
      csrf_token: string;
    }>('/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    });
    this.csrfToken = res.csrf_token;
    return res;
  }

  async logout() {
    const res = await this.request<{ message: string }>('/auth/logout', { method: 'POST' });
    this.csrfToken = null;
    return res;
  }

  async getMe() {
    return this.request<{
      user: {
        user_id: string;
        username: string;
        email: string;
        full_name: string;
        role: string;
        is_active: boolean;
        permissions: string[];
      };
      csrf_token: string;
    }>('/auth/me');
  }

  // 3. Engagements
  async listEngagements() {
    return this.request<any[]>('/engagements');
  }

  async getEngagement(id: string) {
    return this.request<any>(`/engagements/${id}`);
  }

  async getEngagementMembers(id: string) {
    return this.request<any[]>(`/engagements/${id}/members`);
  }

  // 4. Evidence
  async listEvidence(engagementId: string) {
    return this.request<any[]>(`/engagements/${engagementId}/evidence`);
  }

  async verifyEvidenceHash(engagementId: string, evidenceId: string) {
    return this.request<{
      evidence_id: string;
      recorded_sha256: string;
      computed_sha256: string;
      is_match: boolean;
      verified_at: string;
    }>(`/engagements/${engagementId}/evidence/${evidenceId}/verify-hash`, {
      method: 'POST',
    });
  }

  async recordEvidenceValidity(
    engagementId: string,
    evidenceId: string,
    status: string,
    purposeScope: string,
    rationale: string
  ) {
    return this.request<any>(`/engagements/${engagementId}/evidence/${evidenceId}/validity`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status, purpose_scope: purposeScope, rationale }),
    });
  }

  // 5. Completeness & Not-Checked
  async evaluateCompleteness(engagementId: string) {
    return this.request<any>(`/engagements/${engagementId}/completeness`);
  }

  async listNotChecked(engagementId: string) {
    return this.request<any[]>(`/engagements/${engagementId}/not-checked`);
  }

  async updateNotChecked(engagementId: string, procedureId: string, updates: Record<string, any>) {
    return this.request<any>(`/engagements/${engagementId}/not-checked/${procedureId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(updates),
    });
  }

  // 6. Investigations & Findings
  async runInvestigation(engagementId: string) {
    return this.request<{
      job_id: string;
      status: string;
      progress: number;
      completed_at: string;
      findings_count: number;
    }>(`/engagements/${engagementId}/investigations/run`, {
      method: 'POST',
    });
  }

  async listFindings(engagementId: string) {
    return this.request<any[]>(`/engagements/${engagementId}/findings`);
  }

  // 7. Human Review
  async recordReviewDecision(
    engagementId: string,
    payload: {
      finding_id: string;
      decision: string;
      comments: string;
      reviewer_membership_no?: string;
      unresolved_acknowledged?: boolean;
    }
  ) {
    return this.request<{
      message: string;
      review: any;
      is_brass_signoff_active: boolean;
    }>(`/engagements/${engagementId}/human-review/decide`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
  }

  async listReviewHistory(engagementId: string) {
    return this.request<any[]>(`/engagements/${engagementId}/human-review/history`);
  }

  // 8. Calculations & Tax
  async listCalculations(engagementId: string) {
    return this.request<any[]>(`/engagements/${engagementId}/calculations`);
  }

  async runCalculation(
    engagementId: string,
    formulaName: string,
    inputValues: Record<string, string>,
    statutorySection?: string
  ) {
    return this.request<any>(`/engagements/${engagementId}/calculations/run`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        formula_name: formulaName,
        input_values: inputValues,
        statutory_section: statutorySection,
      }),
    });
  }

  async computeTax115BAA(
    engagementId: string,
    grossTotalIncome: string,
    claimedDeductions: string[] = [],
    deductionAmounts: Record<string, string> = {}
  ) {
    return this.request<any>(`/engagements/${engagementId}/tax/section115baa`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        gross_total_income: grossTotalIncome,
        claimed_deductions: claimedDeductions,
        deduction_amounts: deductionAmounts,
      }),
    });
  }

  async computeSection32Depreciation(
    engagementId: string,
    payload: {
      block_id: string;
      opening_wdv: string;
      additions_used_gte_180_days: string;
      additions_used_lt_180_days: string;
      sales_realized: string;
    }
  ) {
    return this.request<any>(`/engagements/${engagementId}/tax/section32`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
  }

  // 9. Provenance Graph
  async getProvenanceGraph(engagementId: string) {
    return this.request<{
      engagement_id: string;
      nodes: any[];
      links: any[];
      total_nodes: number;
      total_links: number;
    }>(`/engagements/${engagementId}/provenance`);
  }

  // 10. Reports
  async getLatestReport(engagementId: string) {
    return this.request<any>(`/engagements/${engagementId}/reports/latest`);
  }

  async generateReport(engagementId: string) {
    return this.request<any>(`/engagements/${engagementId}/reports/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ include_counter_evidence: true, include_not_checked: true }),
    });
  }

  async finalizeReport(engagementId: string) {
    return this.request<any>(`/engagements/${engagementId}/reports/finalize`, {
      method: 'POST',
    });
  }

  // 11. Audit Events
  async listAuditEvents(engagementId: string) {
    return this.request<any[]>(`/engagements/${engagementId}/audit-events`);
  }

  // 12. File Upload (public wrapper)
  async uploadEvidence(engagementId: string, file: File, documentType: string = 'INVOICE') {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('document_type', documentType);
    // Note: Do NOT set Content-Type header; browser sets multipart/form-data boundary automatically
    return this.request<any>(`/engagements/${engagementId}/evidence/upload`, {
      method: 'POST',
      body: formData,
    });
  }

  // 13. AI Providers & Failover Telemetry
  async getProviderStatus() {
    return this.request<{
      mode: string;
      confidentiality_mode: string;
      priority_chain: string[];
      active_primary_provider: string;
      providers: Record<string, {
        name: string;
        display_name: string;
        type: string;
        model: string;
        configured: boolean;
        last_status: string;
        circuit_state: string;
        consecutive_failures: number;
        blocked_seconds_remaining: number;
        priority: number;
      }>;
      recent_failovers: Array<{
        timestamp: string;
        from_provider: string;
        to_provider: string;
        reason: string;
        status: string;
        latency_ms: number;
      }>;
    }>('/providers/status');
  }

  async getProviderHealth() {
    return this.request<{
      status: string;
      timestamp_utc: string;
      total_providers: number;
      configured_providers: number;
      available_providers: number;
      active_mode: string;
      deterministic_engine_fallback: string;
      providers: Record<string, any>;
    }>('/providers/health');
  }

  async testFailover(fromProvider: string, toProvider: string, reason: string) {
    return this.request<any>('/providers/failover/test', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ from_provider: fromProvider, to_provider: toProvider, reason }),
    });
  }
}

export const api = new AudrynApiClient();
