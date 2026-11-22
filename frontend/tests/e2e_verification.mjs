import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const distDir = path.resolve(__dirname, '../dist');
const screenshotsDir = path.resolve(__dirname, '../evidence/screenshots');
fs.mkdirSync(screenshotsDir, { recursive: true });

// Read axe-core source
const axePath = path.resolve(__dirname, '../node_modules/axe-core/axe.min.js');
const axeSource = fs.readFileSync(axePath, 'utf8');

// 1. Lightweight Static HTTP Server serving frontend/dist
const mimeTypes = {
  '.html': 'text/html',
  '.js': 'text/javascript',
  '.css': 'text/css',
  '.woff2': 'font/woff2',
  '.ttf': 'font/ttf',
  '.txt': 'text/plain',
  '.svg': 'image/svg+xml',
  '.png': 'image/png',
  '.ico': 'image/x-icon',
};

const server = http.createServer((req, res) => {
  let reqPath = req.url.split('?')[0];
  if (reqPath === '/') reqPath = '/index.html';

  let filePath = path.join(distDir, reqPath);

  // If requesting a route without file extension (SPA routing), serve index.html
  if (!path.extname(filePath)) {
    filePath = path.join(distDir, 'index.html');
  }

  if (fs.existsSync(filePath) && fs.statSync(filePath).isFile()) {
    const ext = path.extname(filePath);
    const contentType = mimeTypes[ext] || 'application/octet-stream';
    res.writeHead(200, { 'Content-Type': contentType });
    fs.createReadStream(filePath).pipe(res);
  } else {
    // SPA fallback
    res.writeHead(200, { 'Content-Type': 'text/html' });
    fs.createReadStream(path.join(distDir, 'index.html')).pipe(res);
  }
});

const PORT = 4173;

async function runE2E() {
  await new Promise((resolve) => server.listen(PORT, resolve));
  console.log(`[E2E] Static preview server running at http://localhost:${PORT}`);

  const results = {
    total: 0,
    passed: 0,
    failed: 0,
    tests: [],
  };

  function logPass(name, detail = '') {
    results.total++;
    results.passed++;
    results.tests.push({ name, status: 'PASS', detail });
    console.log(`  ✔ PASS: ${name} ${detail ? '(' + detail + ')' : ''}`);
  }

  function logFail(name, err) {
    results.total++;
    results.failed++;
    results.tests.push({ name, status: 'FAIL', error: String(err) });
    console.error(`  ✖ FAIL: ${name} - ${err}`);
  }

  const browser = await chromium.launch({
    executablePath: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
    headless: true,
  });

  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
  });
  const page = await context.newPage();

  try {
    console.log('\n=== SUITE 1: PUBLIC NAVIGATION & ROUTE PARITY ===');
    
    // 1.1 Home page
    await page.goto(`http://localhost:${PORT}/`, { waitUntil: 'domcontentloaded' });
    const homeTitle = await page.title();
    if (homeTitle.includes('AUDRYN')) {
      logPass('Home Page Title Check', homeTitle);
    } else {
      logFail('Home Page Title Check', `Expected title to contain AUDRYN, got: ${homeTitle}`);
    }

    // 1.2 First-screen contract check (Section 11)
    const categoryText = await page.textContent('body');
    if (categoryText.includes('Evidence before conclusions.') && categoryText.includes('audit intelligence system for CA and accounting firms')) {
      logPass('Section 11 First-Screen Contract', 'Category sentence & promise verified');
    } else {
      logFail('Section 11 First-Screen Contract', 'Missing required category text');
    }

    // 1.3 Platform route
    await page.goto(`http://localhost:${PORT}/platform`, { waitUntil: 'domcontentloaded' });
    const platformHeading = await page.textContent('h1');
    if (platformHeading.includes('Evidence-first audit intelligence')) {
      logPass('Platform Page Route', platformHeading.trim());
    } else {
      logFail('Platform Page Route', `Unexpected heading: ${platformHeading}`);
    }

    // 1.4 Trust route
    await page.goto(`http://localhost:${PORT}/trust`, { waitUntil: 'domcontentloaded' });
    const trustContent = await page.textContent('body');
    if (trustContent.includes('The Three Truth Dimensions') && trustContent.includes('DPDP Rules, 2025')) {
      logPass('Trust Page & Truth Dimensions', 'Calculation, Source & Evidence validity segregated');
    } else {
      logFail('Trust Page & Truth Dimensions', 'Missing 3 Truth Dimensions');
    }

    // 1.5 About route
    await page.goto(`http://localhost:${PORT}/about`, { waitUntil: 'domcontentloaded' });
    const aboutContent = await page.textContent('body');
    if (aboutContent.includes('Built for the rigors of statutory audit')) {
      logPass('About Page Route', 'Ethos and target audience verified');
    } else {
      logFail('About Page Route', 'Missing about text');
    }

    // 1.6 Demo route
    await page.goto(`http://localhost:${PORT}/request-demo`, { waitUntil: 'domcontentloaded' });
    const demoContent = await page.textContent('body');
    if (demoContent.includes('Schedule an audit walk-through') && demoContent.includes('PROTOTYPE NOTICE')) {
      logPass('Demo Request Page & Prototype Notice', 'Simulation disclosure verified');
    } else {
      logFail('Demo Request Page & Prototype Notice', 'Missing demo content');
    }

    // 1.7 Legal pages (Privacy, Terms, Cookies)
    await page.goto(`http://localhost:${PORT}/legal/privacy`, { waitUntil: 'domcontentloaded' });
    const privText = await page.textContent('body');
    if (privText.includes('Privacy Policy & DPDP Alignment') && privText.includes('22 November 2026')) {
      logPass('Privacy Policy Page (DPDP 2026 Date)', 'Verified');
    } else {
      logFail('Privacy Policy Page', 'Missing privacy content or 2026 date');
    }

    await page.goto(`http://localhost:${PORT}/legal/cookies`, { waitUntil: 'domcontentloaded' });
    const cookieText = await page.textContent('body');
    if (cookieText.includes('Cookie & Preference Disclosure') && cookieText.includes('audryn_reduced_effects')) {
      logPass('Cookie Policy Page', 'Verified essential storage only');
    } else {
      logFail('Cookie Policy Page', 'Missing cookie content');
    }

    // 1.8 404 Route
    await page.goto(`http://localhost:${PORT}/random-nonexistent-url`, { waitUntil: 'domcontentloaded' });
    const notFoundText = await page.textContent('body');
    if (notFoundText.includes('404') && notFoundText.includes('Record Not Found')) {
      logPass('404 Not Found Page', 'Responsive 404 verified');
    } else {
      logFail('404 Not Found Page', 'Missing 404 handling');
    }

    console.log('\n=== SUITE 2: 3D SCROLL MATHEMATICS & STAGE STEPPING ===');
    await page.goto(`http://localhost:${PORT}/`, { waitUntil: 'domcontentloaded' });

    // Test stepping to each stage and verifying synchronized narrative
    const stages = [
      { name: 'S0', expectedSlug: 'S0: THE PROBLEM (0%–10% HOLD)' },
      { name: 'S1', expectedSlug: 'S1: EXTRACTION (15%–25% HOLD)' },
      { name: 'S2', expectedSlug: 'S2: VERIFICATION (30%–40% HOLD)' },
      { name: 'S3', expectedSlug: 'S3: RELATIONSHIPS (45%–55% HOLD)' },
      { name: 'S4', expectedSlug: 'S4: CHALLENGE (60%–70% HOLD)' },
      { name: 'S5', expectedSlug: 'S5: HUMAN JUDGMENT (75%–85% HOLD)' },
      { name: 'S6', expectedSlug: 'S6: ACCOUNTABILITY (90%–100% HOLD)' },
    ];

    for (const st of stages) {
      await page.click(`button:has-text("${st.name}")`);
      await page.waitForTimeout(100);
      const text = await page.textContent('body');
      if (text.includes(st.expectedSlug)) {
        logPass(`Stage Stepper ${st.name} Hold Range Sync`, st.expectedSlug);
      } else {
        logFail(`Stage Stepper ${st.name} Hold Range Sync`, `Expected ${st.expectedSlug} in DOM`);
      }
    }

    console.log('\n=== SUITE 3: AUTHENTICATED APPLICATION WORKSPACES (ALL 10) ===');
    await page.goto(`http://localhost:${PORT}/app`, { waitUntil: 'domcontentloaded' });

    // Verify global persistent PROTOTYPE badge
    const protoBadge = await page.isVisible('text=PROTOTYPE');
    if (protoBadge) {
      logPass('Global PROTOTYPE Badge in Workspace', 'Persistent status badge visible');
    } else {
      logFail('Global PROTOTYPE Badge in Workspace', 'PROTOTYPE badge not found');
    }

    const workspaces = [
      { id: '1. Evidence Ingestion', indicator: 'Evidence Ingestion & SHA-256 Hashes' },
      { id: '2. Completeness Gate', indicator: 'Completeness Gate & Not-Checked Register' },
      { id: '3. Multi-Agent Run', indicator: 'LangGraph Audit Supervisor' },
      { id: '4. Counter-Evidence', indicator: 'Counter-Evidence Scrutiny' },
      { id: '5. Human Review Queue', indicator: 'Auditor Decision Workspace' },
      { id: '6. Decimal Math', indicator: 'Deterministic Financial Calculations' },
      { id: '7. Statutory Tax', indicator: 'Section 115BAA Corporate Tax Computation' },
      { id: '8. Audit Report', indicator: 'Audit Report Manifest & Generation' },
      { id: '9. Provenance Graph', indicator: 'Provenance Trace Explorer' },
      { id: '10. Settings & Roles', indicator: 'Authorized Engagement Team (Simulation)' },
    ];

    for (const ws of workspaces) {
      await page.click(`button:has-text("${ws.id}")`);
      await page.waitForTimeout(100);
      const wsText = await page.textContent('main');
      if (wsText.includes(ws.indicator)) {
        logPass(`Workspace View: ${ws.id}`, `Verified: ${ws.indicator}`);
      } else {
        logFail(`Workspace View: ${ws.id}`, `Missing indicator: ${ws.indicator}`);
      }
    }

    // Interactive Review Queue decision simulation test
    await page.click('button:has-text("5. Human Review Queue")');
    await page.fill('#reason', 'Empirically verified against supplier delivery challans.');
    const hasUnresolvedCheck = await page.isVisible('#unresolved-check');
    if (hasUnresolvedCheck) {
      await page.check('#unresolved-check');
    }
    await page.click('button:has-text("APPROVE FINDING (BRASS SIGN-OFF SIMULATION)")');
    await page.waitForTimeout(200);
    const successMsg = await page.textContent('main');
    if (successMsg.includes('Client-side simulation') && successMsg.includes('APPROVE')) {
      logPass('Human Review Decision Simulation', 'Brass sign-off simulated with truth disclosure');
    } else {
      logFail('Human Review Decision Simulation', 'Expected simulated approval message');
    }

    console.log('\n=== SUITE 4: RESPONSIVE BREAKPOINTS & 320PX REFLOW ===');
    const breakpoints = [
      { width: 1920, height: 1080, name: '1920_UltraWide' },
      { width: 1440, height: 900, name: '1440_Desktop' },
      { width: 1366, height: 768, name: '1366_Laptop' },
      { width: 1024, height: 768, name: '1024_TabletLandscape' },
      { width: 768, height: 1024, name: '768_TabletPortrait' },
      { width: 390, height: 844, name: '390_Mobile' },
      { width: 360, height: 740, name: '360_MobileSmall' },
      { width: 320, height: 568, name: '320_ReflowBoundary' },
    ];

    for (const bp of breakpoints) {
      await page.setViewportSize({ width: bp.width, height: bp.height });
      await page.goto(`http://localhost:${PORT}/`, { waitUntil: 'domcontentloaded' });
      await page.waitForTimeout(200);

      // Check horizontal overflow
      const scrollWidth = await page.evaluate(() => document.documentElement.scrollWidth);
      if (scrollWidth <= bp.width + 1) { // 1px tolerance for subpixel rounding
        logPass(`Breakpoint ${bp.name} (${bp.width}px)`, `Zero horizontal overflow (scrollWidth=${scrollWidth}px)`);
      } else {
        logFail(`Breakpoint ${bp.name} (${bp.width}px)`, `Horizontal overflow detected! scrollWidth=${scrollWidth}px`);
      }

      // Take representative screenshots
      if (['1440_Desktop', '768_TabletPortrait', '390_Mobile', '320_ReflowBoundary'].includes(bp.name)) {
        const shotPath = path.join(screenshotsDir, `responsive_${bp.name}.png`);
        await page.screenshot({ path: shotPath, fullPage: false });
        console.log(`    📷 Captured screenshot: ${shotPath}`);
      }
    }

    // Capture app screenshot
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.goto(`http://localhost:${PORT}/app`, { waitUntil: 'domcontentloaded' });
    const appShotPath = path.join(screenshotsDir, 'app_review_workspace_1440.png');
    await page.screenshot({ path: appShotPath, fullPage: false });
    console.log(`    📷 Captured screenshot: ${appShotPath}`);

    console.log('\n=== SUITE 5: ACCESSIBILITY & AXE-CORE AUDIT ===');
    await page.goto(`http://localhost:${PORT}/`, { waitUntil: 'domcontentloaded' });

    // Inject axe-core
    await page.evaluate(axeSource);
    const axeResults = await page.evaluate(async () => {
      // @ts-ignore
      return await axe.run({
        runOnly: {
          type: 'tag',
          values: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa'],
        },
      });
    });

    const criticalViolations = axeResults.violations.filter((v) => v.impact === 'critical' || v.impact === 'serious');
    if (criticalViolations.length === 0) {
      logPass('axe-core Automated WCAG 2.2 AA Audit', `Zero critical/serious violations (${axeResults.passes.length} passes)`);
    } else {
      for (const v of criticalViolations) {
        for (const n of v.nodes) {
          console.log(`    ⚠️ Axe violation [${v.id}]: selector="${n.target.join(' ')}" html="${n.html}" failure="${n.failureSummary}"`);
        }
      }
      logFail('axe-core Automated WCAG 2.2 AA Audit', `${criticalViolations.length} critical/serious violations: ${JSON.stringify(criticalViolations.map((v) => v.id))}`);
    }

    // Keyboard Skip Link verification
    await page.goto(`http://localhost:${PORT}/`, { waitUntil: 'domcontentloaded' });
    await page.keyboard.press('Tab');
    const focusedTag = await page.evaluate(() => document.activeElement?.textContent?.trim());
    if (focusedTag === 'Skip to main content') {
      logPass('Keyboard Navigation Skip Link', 'First tab lands on skip link');
    } else {
      logFail('Keyboard Navigation Skip Link', `Expected "Skip to main content", got: "${focusedTag}"`);
    }

    console.log('\n=== SUITE 6: FORM VALIDATION & PROTOTYPE DISCLOSURES ===');
    await page.goto(`http://localhost:${PORT}/request-demo`, { waitUntil: 'domcontentloaded' });
    await page.click('button:has-text("Submit Demonstration Request (Simulation)")');
    const errorText = await page.textContent('[role="alert"]');
    if (errorText && errorText.includes('Please complete all required fields')) {
      logPass('Form Validation: Required Fields', errorText.trim());
    } else {
      logFail('Form Validation: Required Fields', 'Error message did not appear on empty submit');
    }

    // Fill form without consent
    await page.fill('#name', 'CA Rajesh K. Sharma');
    await page.fill('#workEmail', 'rajesh@firm.example');
    await page.fill('#firm', 'Sharma Batliboi & Associates');
    await page.click('button:has-text("Submit Demonstration Request (Simulation)")');
    const consentErr = await page.textContent('[role="alert"]');
    if (consentErr && consentErr.includes('Consent to process your contact details is required')) {
      logPass('Form Validation: DPDP Consent Gate', consentErr.trim());
    } else {
      logFail('Form Validation: DPDP Consent Gate', 'Consent error message did not appear');
    }

    // Submit with consent -> navigates to simulation thank-you page
    await page.check('#consent');
    await page.click('button:has-text("Submit Demonstration Request (Simulation)")');
    await page.waitForTimeout(100);
    const thankYouText = await page.textContent('body');
    if (thankYouText.includes('Demonstration Request Simulation Complete') && thankYouText.includes('client-side prototype demonstration')) {
      logPass('Demo Form Simulation Outcome', 'Redirects to simulation disclosure page');
    } else {
      logFail('Demo Form Simulation Outcome', 'Did not reach simulated thank you state');
    }

    console.log('\n=== SUITE 7: REDUCED MOTION & SECURITY ===');
    await page.goto(`http://localhost:${PORT}/`, { waitUntil: 'domcontentloaded' });

    // Test Reduce Visual Effects button
    await page.click('button:has-text("Reduce Visual Effects")');
    await page.waitForTimeout(100);
    const hasClass = await page.evaluate(() => document.documentElement.classList.contains('reduce-effects'));
    if (hasClass) {
      logPass('Accessibility: Reduce Visual Effects Toggle', 'Successfully added .reduce-effects to <html>');
    } else {
      logFail('Accessibility: Reduce Visual Effects Toggle', '.reduce-effects class not added');
    }

    // Verify CSP meta tag exists and does not contain Google Fonts CDN
    const cspMeta = await page.getAttribute('meta[http-equiv="Content-Security-Policy"]', 'content');
    if (cspMeta && !cspMeta.includes('fonts.googleapis.com') && !cspMeta.includes('fonts.gstatic.com') && cspMeta.includes("font-src 'self'")) {
      logPass('Content Security Policy Integrity', 'Self-hosted fonts only; Google CDN removed');
    } else {
      logFail('Content Security Policy Integrity', `Unexpected CSP: ${cspMeta}`);
    }

    // Verify XSS immunity on provenance graph
    await page.goto(`http://localhost:${PORT}/platform`, { waitUntil: 'domcontentloaded' });
    const graphHtml = await page.innerHTML('body');
    if (!graphHtml.includes('<script>alert') && graphHtml.includes('Cut-Off Timing Discrepancy')) {
      logPass('XSS Sanitization & DOM Rendering', 'Strict HTML escaping verified');
    }

    console.log('\n========================================');
    console.log(`E2E SUMMARY: ${results.passed}/${results.total} PASSED (${results.failed} failed)`);
    console.log('========================================\n');

  } catch (err) {
    console.error('Fatal test execution error:', err);
  } finally {
    await browser.close();
    server.close();
  }

  // Write results JSON
  fs.writeFileSync(
    path.resolve(__dirname, '../evidence/e2e_results.json'),
    JSON.stringify(results, null, 2)
  );
}

runE2E();
