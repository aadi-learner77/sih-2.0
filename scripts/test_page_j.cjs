const puppeteer = require('puppeteer-core');
const fs = require('fs');
const path = require('path');

const CHROME_PATH = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const SCREENSHOT_DIR = path.resolve(__dirname, '..', 'evidence_pack', 'screenshots');

(async () => {
  console.log(`\n============================================================`);
  console.log(`[TESTING PAGE J] Rules Catalog & What-If Simulator (Role: "senior_officer")`);
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

  // Clean login as senior_officer
  await page.goto('http://localhost:5173');
  await page.evaluate(() => localStorage.clear());
  await page.goto('http://localhost:5173', { waitUntil: 'networkidle0' });

  await page.click('#preset-role-senior_officer');
  await new Promise(r => setTimeout(r, 300));
  await page.click('#login-submit-btn');
  await new Promise(r => setTimeout(r, 1200));

  // Click #sidebar-tab-regulations
  await page.click('#sidebar-tab-regulations');
  await new Promise(r => setTimeout(r, 1000));

  // Test Search Box in Rules Catalog
  const searchBox = await page.$('input[placeholder*="Search clause citation"]');
  if (searchBox) {
    await searchBox.type('Clause 4.1');
    await new Promise(r => setTimeout(r, 400));
    await searchBox.click({ clickCount: 3 });
    await page.keyboard.press('Backspace');
  }

  // Test switching to What-If Simulator tab
  await page.evaluate(() => {
    const btns = Array.from(document.querySelectorAll('button'));
    const whatIf = btns.find(b => b.innerText.includes('What-If') || b.innerText.includes('Simulator'));
    if (whatIf) whatIf.click();
  });
  await new Promise(r => setTimeout(r, 800));

  // Run DOM checks
  const domChecks = await page.evaluate(() => {
    const text = document.body.innerText || '';
    const forbidden = [];
    ['undefined', 'NaN', 'null', '[object Object]'].forEach(w => {
      if (w === '[object Object]') {
        const count = (text.match(/\[object Object\]/g) || []).length;
        if (count > 0) forbidden.push({ word: w, count });
      } else {
        const matches = text.match(new RegExp(`\\b${w}\\b`, 'g'));
        if (matches) forbidden.push({ word: w, count: matches.length });
      }
    });

    const docWidth = document.documentElement.clientWidth;
    const scrollWidth = document.body.scrollWidth;
    const hasOverflow = scrollWidth > docWidth + 3;

    const imgs = Array.from(document.querySelectorAll('img')).map(i => ({
      src: i.src, complete: i.complete, naturalWidth: i.naturalWidth, broken: i.complete && i.naturalWidth === 0
    }));

    return {
      forbidden,
      hasOverflow,
      brokenImgs: imgs.filter(i => i.broken),
      totalImgs: imgs.length
    };
  });

  const screenshotPath = path.join(SCREENSHOT_DIR, 'regulations.png');
  await page.screenshot({ path: screenshotPath, fullPage: false });

  await browser.close();

  const isPass = consoleErrors.length === 0 &&
                 networkFailures.length === 0 &&
                 !domChecks.hasOverflow &&
                 domChecks.brokenImgs.length === 0 &&
                 domChecks.forbidden.length === 0;

  console.log(`[STATUS] Page J (Rules & What-If): ${isPass ? 'PASS' : 'FAIL'}`);
  console.log(`  Screenshot saved: ${screenshotPath}`);
  console.log(JSON.stringify({ consoleErrors, networkFailures, domChecks, passed: isPass }, null, 2));
})();
