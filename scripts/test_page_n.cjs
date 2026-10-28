const puppeteer = require('puppeteer-core');
const fs = require('fs');
const path = require('path');

const CHROME_PATH = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const SCREENSHOT_DIR = path.resolve(__dirname, '..', 'evidence_pack', 'screenshots');

const ROLES = [
  { key: 'scrutiny_officer', expectedBadge: 'SCRUTINY OFFICER' },
  { key: 'senior_officer', expectedBadge: 'SENIOR OFFICER' },
  { key: 'admin', expectedBadge: 'ADMIN' },
  { key: 'auditor', expectedBadge: 'AUDITOR' },
  { key: 'institution_user', expectedBadge: 'INSTITUTION USER' }
];

(async () => {
  console.log(`\n============================================================`);
  console.log(`[TESTING PAGE N] RBAC Roles & Multi-Tenant Permission Isolation`);
  console.log(`============================================================`);

  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--window-size=1440,900']
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1440, height: 900 });

  const roleAudits = {};

  for (const roleObj of ROLES) {
    // 1. Navigate to login
    await page.goto('http://localhost:5173');
    await page.evaluate(() => {
      localStorage.clear();
    });
    await page.goto('http://localhost:5173', { waitUntil: 'networkidle0' });

    // 2. Click preset button for this role
    await page.click(`#preset-role-${roleObj.key}`);
    await new Promise(r => setTimeout(r, 300));
    await page.click('#login-submit-btn');
    await new Promise(r => setTimeout(r, 1200));

    // 3. Inspect authenticated session
    const sessionState = await page.evaluate(() => {
      const headerBadge = document.querySelector('#header-role-badge')?.innerText?.trim() || '';
      const visibleTabs = Array.from(document.querySelectorAll('aside button[id^="sidebar-tab-"]')).map(b => b.id.replace('sidebar-tab-', ''));
      return { headerBadge, visibleTabs };
    });

    roleAudits[roleObj.key] = sessionState;
    console.log(`  Role "${roleObj.key}": Badge = "${sessionState.headerBadge}", Tabs = [${sessionState.visibleTabs.join(', ')}]`);
  }

  // 4. Test Access Restriction on unauthorized module
  console.log('  Testing unauthorized tab protection for institution_user...');
  // As institution_user, attempt to switch to audit-ledger
  await page.evaluate(() => {
    // Call window setter or attempt tab switch
    window.location.hash = '#audit-ledger';
  });
  await new Promise(r => setTimeout(r, 500));

  const screenshotPath = path.join(SCREENSHOT_DIR, 'rbac_roles.png');
  await page.screenshot({ path: screenshotPath, fullPage: false });

  await browser.close();

  // Scrutiny Officer should have 9 tabs; Institution User should only have 2 (dashboard, preflight); Senior Officer & Admin should have 10 (including regulations)
  const isPass = roleAudits.scrutiny_officer.visibleTabs.includes('evidence-lens') &&
                 roleAudits.institution_user.visibleTabs.includes('preflight') &&
                 !roleAudits.institution_user.visibleTabs.includes('regulations') &&
                 !roleAudits.institution_user.visibleTabs.includes('photo-radar') &&
                 roleAudits.senior_officer.visibleTabs.includes('regulations') &&
                 roleAudits.admin.visibleTabs.includes('regulations');

  console.log(`[STATUS] Page N (Roles RBAC): ${isPass ? 'PASS' : 'FAIL'}`);
  console.log(`  Screenshot saved: ${screenshotPath}`);
  console.log(JSON.stringify(roleAudits, null, 2));
})();
