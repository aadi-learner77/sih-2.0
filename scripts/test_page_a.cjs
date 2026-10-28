const puppeteer = require('puppeteer-core');
const fs = require('fs');
const path = require('path');

const CHROME_PATH = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const SCREENSHOT_DIR = path.resolve(__dirname, '..', 'evidence_pack', 'screenshots');

(async () => {
  console.log(`\n============================================================`);
  console.log(`[TESTING PAGE A] Login & Authentication Gateway`);
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
    if (msg.type() === 'error') consoleErrors.push(msg.text());
  });

  page.on('requestfailed', req => {
    networkFailures.push({ url: req.url(), errorText: req.failure()?.errorText });
  });

  // Navigate & ensure logged out
  await page.goto('http://localhost:5173');
  await page.evaluate(() => {
    localStorage.clear();
  });
  await page.goto('http://localhost:5173', { waitUntil: 'networkidle0' });

  // Verify LoginPage DOM
  const domChecks = await page.evaluate(() => {
    const text = document.body.innerText || '';
    const hasSignInHeading = text.includes('Sign In to PRAMAAN-X');
    const hasPresetButtons = document.querySelectorAll('button[id^="preset-role-"]').length;
    const hasEmailInput = document.querySelector('input[type="email"]') !== null;
    const hasPassInput = document.querySelector('input[type="password"]') !== null;

    // Check overflow
    const docWidth = document.documentElement.clientWidth;
    const scrollWidth = document.body.scrollWidth;
    const hasOverflow = scrollWidth > docWidth + 3;

    // Check broken images
    const imgs = Array.from(document.querySelectorAll('img')).map(i => ({
      src: i.src,
      complete: i.complete,
      naturalWidth: i.naturalWidth,
      broken: i.complete && i.naturalWidth === 0
    }));

    return {
      hasSignInHeading,
      hasPresetButtons,
      hasEmailInput,
      hasPassInput,
      hasOverflow,
      brokenImgs: imgs.filter(i => i.broken),
      totalImgs: imgs.length
    };
  });

  // Take screenshot of clean Login Page
  const screenshotPath = path.join(SCREENSHOT_DIR, 'login.png');
  await page.screenshot({ path: screenshotPath, fullPage: false });

  // Test preset click
  await page.click('#preset-role-scrutiny_officer');
  await new Promise(r => setTimeout(r, 400));

  // Test submit
  await page.click('#login-submit-btn');
  await new Promise(r => setTimeout(r, 1200));

  // Verify successful authentication lands on dashboard
  const isAuthenticatedNow = await page.evaluate(() => {
    return document.querySelector('#sidebar-tab-dashboard') !== null;
  });

  await browser.close();

  const isPass = domChecks.hasSignInHeading &&
                 domChecks.hasPresetButtons >= 5 &&
                 domChecks.hasEmailInput &&
                 domChecks.hasPassInput &&
                 !domChecks.hasOverflow &&
                 domChecks.brokenImgs.length === 0 &&
                 isAuthenticatedNow;

  const result = {
    id: 'A',
    page: 'Login Gateway',
    consoleErrors,
    networkFailures,
    domChecks,
    isAuthenticatedNow,
    screenshotPath: 'evidence_pack/screenshots/login.png',
    passed: isPass
  };

  console.log(`[STATUS] Page A (Login Gateway): ${isPass ? 'PASS' : 'FAIL'}`);
  console.log(`  Screenshot saved: ${screenshotPath}`);
  console.log(JSON.stringify(result, null, 2));
})();

