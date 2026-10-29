const puppeteer = require('puppeteer-core');
const fs = require('fs');
const path = require('path');

const CHROME_PATH = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const SCREENSHOT_DIR = path.resolve(__dirname, '..', 'evidence_pack', 'screenshots');

if (!fs.existsSync(SCREENSHOT_DIR)) {
  fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
}

// Preset accounts for role testing
const PRESETS = {
  scrutiny_officer: { email: 'scrutiny.officer@aicte-india.org', pass: 'AicteOfficer@2025' },
  senior_officer: { email: 'regional.officer@aicte-india.org', pass: 'AicteRegional@2025' },
  admin: { email: 'admin@aicte-india.org', pass: 'AicteAdmin@2025' },
  auditor: { email: 'auditor@aicte-india.org', pass: 'AicteAuditor@2025' },
  institution_user: { email: 'registrar@apextech.edu.in', pass: 'ApexPass@2025' }
};

async function testSinglePage(pageConfig) {
  const { id, name, tabId, defaultRole = 'scrutiny_officer', interactFn } = pageConfig;
  console.log(`\n============================================================`);
  console.log(`[TESTING PAGE ${id}] ${name} (Tab: "${tabId}", Role: "${defaultRole}")`);
  console.log(`============================================================`);

  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--window-size=1440,900']
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1440, height: 900 });

  const consoleErrors = [];
  const networkFailures = [];

  page.on('console', msg => {
    if (msg.type() === 'error') {
      const txt = msg.text();
      consoleErrors.push(txt);
    }
  });

  page.on('requestfailed', req => {
    networkFailures.push({
      url: req.url(),
      errorText: req.failure() ? req.failure().errorText : 'failed'
    });
  });

  page.on('response', resp => {
    const status = resp.status();
    const url = resp.url();
    if (status >= 400 && !url.includes('favicon') && !url.includes('@vite')) {
      networkFailures.push({ url, status, statusText: resp.statusText() });
    }
  });

  // 1. Navigate to app
  await page.goto('http://localhost:5173', { waitUntil: 'networkidle0', timeout: 15000 });

  // 2. Check if on Login page; log in with preset
  const isLoginPage = await page.evaluate(() => {
    return document.querySelector('input[type="email"]') !== null ||
           document.querySelector('button[type="submit"]') !== null ||
           document.body.innerText.includes('Sign In to PRAMAAN-X');
  });

  if (isLoginPage) {
    const creds = PRESETS[defaultRole] || PRESETS.scrutiny_officer;
    await page.evaluate((c) => {
      const emailInput = document.querySelector('input[type="email"]');
      const passInput = document.querySelector('input[type="password"]');
      if (emailInput) {
        emailInput.value = c.email;
        emailInput.dispatchEvent(new Event('input', { bubbles: true }));
      }
      if (passInput) {
        passInput.value = c.pass;
        passInput.dispatchEvent(new Event('input', { bubbles: true }));
      }
      const submitBtn = document.querySelector('button[type="submit"]');
      if (submitBtn) submitBtn.click();
    }, creds);
    await new Promise(r => setTimeout(r, 1200));
  } else {
    // Switch role via header selector
    await page.evaluate((r) => {
      const selects = Array.from(document.querySelectorAll('select'));
      for (const s of selects) {
        const options = Array.from(s.options).map(o => o.value);
        if (options.includes(r)) {
          s.value = r;
          s.dispatchEvent(new Event('change', { bubbles: true }));
          break;
        }
      }
    }, defaultRole);
    await new Promise(r => setTimeout(r, 600));
  }

  // 3. Navigate to target tab
  if (tabId) {
    const clicked = await page.evaluate((target) => {
      const btn = document.querySelector(`#sidebar-tab-${target}`);
      if (btn) {
        btn.click();
        return true;
      }
      return false;
    }, tabId);

    if (!clicked) {
      console.warn(`  Warning: #sidebar-tab-${tabId} not found directly.`);
    }
    await new Promise(r => setTimeout(r, 1200));
  }

  // 4. Custom Interaction Hook
  let interactionLog = [];
  if (interactFn) {
    try {
      interactionLog = await interactFn(page);
    } catch (err) {
      interactionLog.push(`Interaction error: ${err.message}`);
    }
  }

  // 5. Run Deep DOM Checks
  const domChecks = await page.evaluate(() => {
    const text = document.body.innerText || '';

    // A. Literal Forbidden Strings check
    const forbidden = [];
    ['undefined', 'NaN', 'null', '[object Object]'].forEach(w => {
      if (w === '[object Object]') {
        const count = (text.match(/\[object Object\]/g) || []).length;
        if (count > 0) forbidden.push({ word: w, count });
      } else {
        const regex = new RegExp(`\\b${w}\\b`, 'g');
        const matches = text.match(regex);
        if (matches) forbidden.push({ word: w, count: matches.length });
      }
    });

    // B. Demo Data Badges check (only count if visible in viewport / non-hidden)
    const demoBadges = [];
    document.querySelectorAll('*').forEach(el => {
      if (el.children.length === 0 && el.innerText) {
        const t = el.innerText.trim();
        if ((t === 'Demo data' || t === 'Demo Fallback Data') && el.offsetParent !== null) {
          demoBadges.push(t);
        }
      }
    });

    // C. Horizontal Overflow
    const docWidth = document.documentElement.clientWidth;
    const scrollWidth = document.body.scrollWidth;
    const hasOverflow = scrollWidth > docWidth + 3;

    // D. Broken Images
    const imgs = Array.from(document.querySelectorAll('img')).map(i => ({
      src: i.src,
      alt: i.alt,
      complete: i.complete,
      naturalWidth: i.naturalWidth,
      broken: i.complete && i.naturalWidth === 0
    }));
    const brokenImgs = imgs.filter(i => i.broken);

    // E. Clipped / Vertical One-Char-Per-Line Text
    const verticalTexts = [];
    document.querySelectorAll('p, span, div, h1, h2, h3, h4').forEach(el => {
      if (el.children.length === 0 && el.innerText && el.innerText.trim().length > 5) {
        const rect = el.getBoundingClientRect();
        if (rect.width > 0 && rect.width < 35 && rect.height > 60) {
          verticalTexts.push({
            text: el.innerText.trim().slice(0, 30),
            width: rect.width,
            height: rect.height,
            tag: el.tagName
          });
        }
      }
    });

    // F. Consistency Values
    const bellBadge = document.querySelector('#alert-bell-btn span.rounded-full')?.innerText?.trim() || '0';
    const navbarLedger = document.querySelector('#navbar-ledger-badge')?.innerText?.trim() || '';

    return {
      forbidden,
      demoBadges,
      hasOverflow,
      totalImages: imgs.length,
      brokenImgs,
      verticalTexts,
      bellBadge,
      navbarLedger
    };
  });

  // 6. Save Artifact Screenshot
  const screenshotFileName = `${(tabId || name).toLowerCase().replace(/[^a-z0-9]/g, '_')}.png`;
  const screenshotPath = path.join(SCREENSHOT_DIR, screenshotFileName);
  await page.screenshot({ path: screenshotPath, fullPage: false });

  await browser.close();

  const isPass = consoleErrors.length === 0 &&
                 networkFailures.length === 0 &&
                 !domChecks.hasOverflow &&
                 domChecks.brokenImgs.length === 0 &&
                 domChecks.verticalTexts.length === 0 &&
                 domChecks.forbidden.length === 0 &&
                 domChecks.demoBadges.length === 0;

  const resultSummary = {
    id,
    page: name,
    tabId,
    role: defaultRole,
    consoleErrors,
    networkFailures,
    domChecks,
    interactionLog,
    screenshotPath: `evidence_pack/screenshots/${screenshotFileName}`,
    passed: isPass
  };

  console.log(`[STATUS] Page ${id} (${name}): ${isPass ? 'PASS' : 'FAIL / PARTIAL'}`);
  if (consoleErrors.length > 0) console.log('  -> Console Errors:', consoleErrors);
  if (networkFailures.length > 0) console.log('  -> Network Failures:', networkFailures);
  if (domChecks.demoBadges.length > 0) console.log('  -> Demo Badges:', domChecks.demoBadges);
  if (domChecks.brokenImgs.length > 0) console.log('  -> Broken Images:', domChecks.brokenImgs);
  if (domChecks.hasOverflow) console.log('  -> Horizontal Overflow!');
  if (domChecks.verticalTexts.length > 0) console.log('  -> Vertical Text Detected:', domChecks.verticalTexts);
  if (domChecks.forbidden.length > 0) console.log('  -> Forbidden DOM Strings:', domChecks.forbidden);
  console.log(`  -> Screenshot saved: ${resultSummary.screenshotPath}`);

  return resultSummary;
}

module.exports = { testSinglePage };
