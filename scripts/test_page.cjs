const puppeteer = require('puppeteer-core');
const fs = require('fs');
const path = require('path');

const CHROME_PATH = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const SCREENSHOT_DIR = path.resolve(__dirname, '..', 'evidence_pack', 'screenshots');

if (!fs.existsSync(SCREENSHOT_DIR)) {
  fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
}

async function runDOMTest(tabId, pageName, role = 'scrutiny_officer', actionFn = null) {
  console.log(`\n============================================================`);
  console.log(`[TESTING] ${pageName} (tab: "${tabId}", role: "${role}")`);
  console.log(`============================================================`);

  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--window-size=1440,900']
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1440, height: 900 });

  const consoleLogs = [];
  const consoleErrors = [];
  const networkFailures = [];

  page.on('console', msg => {
    const text = msg.text();
    const type = msg.type();
    consoleLogs.push({ type, text });
    if (type === 'error') {
      consoleErrors.push(text);
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
    // Ignore vite hot reload or optional favicon
    if (status >= 400 && !url.includes('favicon') && !url.includes('@vite')) {
      networkFailures.push({ url, status, statusText: resp.statusText() });
    }
  });

  // Navigate to application
  await page.goto('http://localhost:5173', { waitUntil: 'networkidle0', timeout: 15000 });

  // If role is not scrutiny_officer, select it from the header role dropdown
  if (role) {
    try {
      const selectHandle = await page.$('select#header-role-select, select.role-selector, select');
      if (selectHandle) {
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
        }, role);
        await new Promise(r => setTimeout(r, 600));
      }
    } catch (e) {
      console.warn('Role switch exception:', e.message);
    }
  }

  // Navigate to tab if tabId is provided
  if (tabId) {
    const navigated = await page.evaluate((targetTab) => {
      // Look for sidebar button or nav button with data-tab or id or text
      const buttons = Array.from(document.querySelectorAll('button, a'));
      for (const b of buttons) {
        const id = b.id || '';
        const dataTab = b.getAttribute('data-tab') || '';
        const onclickStr = b.getAttribute('onclick') || '';
        if (id.includes(targetTab) || dataTab === targetTab) {
          b.click();
          return true;
        }
      }
      // Try text match in sidebar
      const sidebarLinks = Array.from(document.querySelectorAll('aside button, nav button, .sidebar-item'));
      for (const s of sidebarLinks) {
        const text = s.innerText.toLowerCase();
        if (
          (targetTab === 'evidence-lens' && text.includes('evidence lens')) ||
          (targetTab === 'preflight' && text.includes('pre-flight')) ||
          (targetTab === 'audit-ledger' && text.includes('audit')) ||
          (targetTab === 'photo-radar' && text.includes('photo radar')) ||
          (targetTab === 'dashboard' && text.includes('dashboard')) ||
          (targetTab === 'impossibility-engine' && text.includes('impossibility')) ||
          (targetTab === 'document-intelligence' && text.includes('document intelligence')) ||
          (targetTab === 'manual-review-queue' && text.includes('manual review')) ||
          (targetTab === 'regulations' && text.includes('regulation')) ||
          (targetTab === 'inspection-planner' && text.includes('inspection'))
        ) {
          s.click();
          return true;
        }
      }
      return false;
    }, tabId);

    if (!navigated) {
      console.warn(`Could not find sidebar nav for tab "${tabId}"`);
    }
    // Wait for tab content to render and settle network
    await new Promise(r => setTimeout(r, 1200));
  }

  // Execute custom action if provided (e.g., clicking modals, tabs, toggles)
  let actionResult = null;
  if (actionFn) {
    actionResult = await actionFn(page);
  }

  // Perform Comprehensive DOM Checks
  const domReport = await page.evaluate(() => {
    // 1. Text checks for forbidden values
    const bodyText = document.body.innerText || '';
    const forbiddenMatches = [];
    const forbiddenPatterns = [
      /\bundefined\b/g,
      /\bNaN\b/g,
      /\bnull\b/g,
      /\[object Object\]/g
    ];
    forbiddenPatterns.forEach(pattern => {
      const match = bodyText.match(pattern);
      if (match) {
        forbiddenMatches.push({ pattern: pattern.toString(), count: match.length });
      }
    });

    // 2. Demo data badge check
    const demoBadges = Array.from(document.querySelectorAll('*')).filter(el => {
      const text = (el.innerText || '').trim();
      return text.includes('Demo data') || text.includes('Demo Fallback');
    }).map(el => el.innerText.trim());

    // 3. Overflow check
    const docWidth = document.documentElement.clientWidth;
    const bodyScrollWidth = document.body.scrollWidth;
    const hasHorizontalOverflow = bodyScrollWidth > docWidth + 2;

    // Elements overflowing window
    const overflowingElements = [];
    document.querySelectorAll('*').forEach(el => {
      const rect = el.getBoundingClientRect();
      if (rect.right > docWidth + 5 && el.tagName !== 'svg' && el.tagName !== 'path') {
        overflowingElements.push({
          tag: el.tagName,
          id: el.id,
          className: el.className,
          right: rect.right,
          docWidth
        });
      }
    });

    // 4. Image check
    const images = Array.from(document.querySelectorAll('img')).map(img => ({
      src: img.src,
      alt: img.alt,
      complete: img.complete,
      naturalWidth: img.naturalWidth,
      naturalHeight: img.naturalHeight,
      broken: img.complete && img.naturalWidth === 0
    }));
    const brokenImages = images.filter(img => img.broken);

    // 5. Clipped or single-letter-per-line text detection
    const verticalTexts = [];
    document.querySelectorAll('p, span, div, h1, h2, h3, h4').forEach(el => {
      // Only leaf or low-depth elements with direct text
      if (el.children.length === 0 && el.innerText && el.innerText.trim().length > 5) {
        const rect = el.getBoundingClientRect();
        // If width is tiny (< 35px) but height is large (> 60px), letters are wrapping per char
        if (rect.width > 0 && rect.width < 35 && rect.height > 60) {
          verticalTexts.push({
            text: el.innerText.trim().slice(0, 30),
            width: rect.width,
            height: rect.height,
            tag: el.tagName,
            id: el.id,
            className: el.className
          });
        }
      }
    });

    // 6. Number and badge consistency data
    const bellBadge = document.querySelector('#alert-bell-btn span.rounded-full')?.innerText?.trim() || '0';
    const navbarLedgerBadge = document.querySelector('#navbar-ledger-badge')?.innerText?.trim() || '';

    return {
      forbiddenMatches,
      demoBadges,
      hasHorizontalOverflow,
      overflowingElements: overflowingElements.slice(0, 5),
      totalImages: images.length,
      brokenImages,
      verticalTexts,
      bellBadge,
      navbarLedgerBadge,
      title: document.title
    };
  });

  // Save screenshot
  const screenshotPath = path.join(SCREENSHOT_DIR, `${tabId || pageName}.png`);
  await page.screenshot({ path: screenshotPath, fullPage: false });

  await browser.close();

  const report = {
    page: pageName,
    tabId,
    role,
    consoleErrors,
    networkFailures,
    domReport,
    actionResult,
    screenshotSaved: screenshotPath,
    passed: consoleErrors.length === 0 &&
            networkFailures.length === 0 &&
            !domReport.hasHorizontalOverflow &&
            domReport.brokenImages.length === 0 &&
            domReport.verticalTexts.length === 0 &&
            domReport.forbiddenMatches.length === 0
  };

  console.log(`[RESULT] ${pageName}: ${report.passed ? 'PASS' : 'FAIL'}`);
  if (consoleErrors.length > 0) console.log('  Console Errors:', consoleErrors);
  if (networkFailures.length > 0) console.log('  Network Failures:', networkFailures);
  if (domReport.brokenImages.length > 0) console.log('  Broken Images:', domReport.brokenImages);
  if (domReport.hasHorizontalOverflow) console.log('  Horizontal Overflow detected!');
  if (domReport.verticalTexts.length > 0) console.log('  Vertical text detected:', domReport.verticalTexts);
  if (domReport.forbiddenMatches.length > 0) console.log('  Forbidden strings in DOM:', domReport.forbiddenMatches);
  if (domReport.demoBadges.length > 0) console.log('  Demo Badges visible:', domReport.demoBadges);
  console.log(`  Screenshot: ${screenshotPath}`);

  return report;
}

module.exports = { runDOMTest };
if (require.main === module) {
  const targetTab = process.argv[2] || 'evidence-lens';
  const targetName = process.argv[3] || 'Evidence Lens';
  runDOMTest(targetTab, targetName);
}

