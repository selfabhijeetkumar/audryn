# Security Baseline & Protection Policy — AUDRYN

## 1. Data Classification & Privacy
- **Financial Documents:** Strictly classified as CONFIDENTIAL.
- **Local Storage:** All uploaded documents and processed vouchers must reside in gitignored local paths (`uploads/private/`, `data/private/`).
- **No Third-Party Transmission:** No client financial data or extracted numbers may be sent to remote public LLMs or external cloud storage in default operation.

## 2. Secrets Management & Environment Isolation
- `.env` files are strictly excluded from Git tracking via `.gitignore`.
- `.env.example` is committed with zero real credentials and documented placeholder defaults.
- All configuration is validated at runtime via `pydantic-settings` to prevent invalid or default insecure settings from reaching production.

## 3. Stitch MCP Credential Security Assessment
- **Finding:** Stitch MCP API key is present in local user configuration (`~/.gemini/antigravity/mcp_config.json`).
- **Analysis:** Antigravity executes `mcp-remote` directly with `--header X-Goog-Api-Key:...` passed in command line arguments. Antigravity's current MCP configuration format does not support `${env:VAR}` variable expansion inside the `args` array for remote servers.
- **Status:** **BLOCKED for automated in-place migration**.
- **Remediation Plan:**
  1. Never duplicate or commit this key to project files, Git, or logs.
  2. Maintain configuration in user-local `~/.gemini/` configuration files only (which are outside git trees).
  3. When Antigravity native secret store or environment interpolation is released for `args`, migrate the key to a system environment variable `STITCH_API_KEY`.

## 4. Git Security & Historical Scan Status
- **Repository Type:** Fresh Git repository initialized in `C:\FAI AGENT\audryn\`.
- **Historical Git Commit Scanning:** Not applicable — no prior commit history exists in this repository.
- **Pre-Commit Scan:** Verified that no `.env`, `.pem`, `.key`, or secret files exist in the tracked workspace.

## 5. Dependency Vulnerability Management
- All installed packages will be audited via `pip-audit`.
- Any critical or high CVEs will be documented in the Phase 1 report with explicit remediation paths.
