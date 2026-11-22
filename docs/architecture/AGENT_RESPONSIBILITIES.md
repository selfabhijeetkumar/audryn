# Agent Responsibilities Matrix — AUDRYN

| Agent / Subsystem | Framework | Primary Responsibility | Input Artifacts | Output Artifacts | Deterministic Control |
|---|---|---|---|---|---|
| **Document Ingestion Coordinator** | LangGraph | Coordinates OCR, table parsing, and metadata extraction across PDFs and Excels | Raw PDF / .xlsx files | Structured JSON balance sheets & trial balances | High (regex + table parsers) |
| **Cross-Year Reconciliation Agent** | LangGraph Node | Ties out PY (Prior Year) to CY (Current Year) closing/opening balances | PY & CY financial statements | Reconciliation Variance Matrix | Pure deterministic Python math |
| **Tax Audit Specialist** | CrewAI | Formulates tax disallowance hypotheses, TDS reconciliations, and expense audits | Trial balance, expense ledgers | Flagged Tax Anomalies & Notes | LLM reasoning + rule checks |
| **Forensic Investigator** | CrewAI | Identifies irregular journal entries, round-sum transactions, and timing anomalies | Journal ledgers, bank statements | Anomaly Investigation Dossier | LLM pattern analysis |
| **Counter-Evidence Challenger** | MS Agent Framework | Adversarially seeks contradictory evidence to disprove associate/specialist findings | Findings list + source documents | Challenge Verdicts & Disproofs | Independent isolated prompt |
| **Audit Completeness Gatekeeper** | MS Agent Framework + LangGraph | Enforces threshold verification: verifies no high-risk items remain in "Not Checked Register" | Evidence Graph + Not Checked Reg. | Gate Approval / Rejection Pack | Hard rule-based gate |
| **Report Synthesis Engine** | LangGraph Node | Compiles audit workpapers, linking every claim to Evidence Graph coordinates | Verified findings + Evidence Graph | Markdown & PDF Audit Pack | Deterministic template synthesis |
