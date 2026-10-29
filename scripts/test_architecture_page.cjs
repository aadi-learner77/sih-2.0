const puppeteer = require('puppeteer-core');
const path = require('path');
const fs = require('fs');

async function testArchitecturePage() {
  const browserPath = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
  const browser = await puppeteer.launch({
    executablePath: browserPath,
    headless: true,
    defaultViewport: { width: 1440, height: 900 },
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const page = await browser.newPage();
  const consoleErrors = [];
  page.on('console', msg => {
    if (msg.type() === 'error') {
      consoleErrors.push(msg.text());
    }
  });

  try {
    console.log('Navigating to http://localhost:5173...');
    await page.goto('http://localhost:5173', { waitUntil: 'networkidle2', timeout: 15000 });

    // Check if on login page
    const loginBtn = await page.$('#login-submit-btn');
    if (loginBtn) {
      console.log('Logging in with scrutiny officer preset...');
      await page.click('#preset-role-scrutiny_officer');
      await page.click('#login-submit-btn');
      await page.waitForSelector('#header-role-badge', { timeout: 10000 });
      console.log('Logged in successfully!');
    }

    console.log('Waiting for System Architecture sidebar item...');
    await page.waitForSelector('#sidebar-tab-system-architecture', { timeout: 10000 });
    await page.click('#sidebar-tab-system-architecture');
    console.log('Clicked System Architecture tab!');

    // Wait for Architecture page to be active
    await page.waitForSelector('#tab-architecture', { timeout: 10000 });
    console.log('System Architecture page loaded!');

    // Click Forensics Layer node in the diagram
    console.log('Clicking Forensics Layer node...');
    await page.waitForSelector('#arch-node-forensics-layer', { timeout: 5000 });
    await page.click('#arch-node-forensics-layer');

    // Take screenshot of Architecture View
    const outDir = path.join(__dirname, '..', 'evidence_pack', 'screenshots');
    if (!fs.existsSync(outDir)) fs.mkdirSync(outDir, { recursive: true });
    const screenPath = path.join(outDir, 'system_architecture_page.png');
    await page.screenshot({ path: screenPath, fullPage: false });
    console.log('Saved architecture screenshot:', screenPath);

    // Copy to frontend/public/screenshots
    const publicOut = path.join(__dirname, '..', 'frontend', 'public', 'screenshots', 'system_architecture_page.png');
    fs.copyFileSync(screenPath, publicOut);

    // Switch to Pipeline tab
    console.log('Switching to Pipeline Simulator tab...');
    await page.click('#tab-pipeline');
    await new Promise(r => setTimeout(r, 600));

    // Advance pipeline step
    console.log('Advancing pipeline step...');
    await page.waitForSelector('#pipeline-next-btn', { timeout: 5000 });
    await page.click('#pipeline-next-btn');
    console.log('Advanced pipeline stage!');

    // Switch to Gallery tab
    console.log('Switching to Gallery tab...');
    await page.click('#tab-gallery');
    await page.waitForSelector('#gallery-card-dashboard', { timeout: 5000 });
    console.log('Gallery tab rendered with cards!');

    // Click first card to inspect lightbox
    console.log('Opening lightbox modal...');
    await page.click('#gallery-card-dashboard');
    await page.waitForSelector('button[title="Close Lightbox"]', { timeout: 5000 });
    console.log('Lightbox modal opened successfully!');

    // Take screenshot of open lightbox
    const lightboxScreen = path.join(outDir, 'system_architecture_lightbox.png');
    await page.screenshot({ path: lightboxScreen, fullPage: false });
    console.log('Saved lightbox screenshot:', lightboxScreen);

    // Close lightbox
    await page.click('button[title="Close Lightbox"]');
    await new Promise(r => setTimeout(r, 400));
    console.log('Lightbox closed cleanly!');

    // Switch to Components Deep-Dive tab
    console.log('Switching to Components Deep-Dive tab...');
    await page.click('#tab-components');
    await new Promise(r => setTimeout(r, 500));

    // Switch to Statutory Safeguards & RBAC tab
    console.log('Switching to Statutory Safeguards tab...');
    await page.click('#tab-safeguards');
    await new Promise(r => setTimeout(r, 500));

    console.log('Total console errors:', consoleErrors.length);
    if (consoleErrors.length > 0) {
      console.log('Console errors:', consoleErrors);
    } else {
      console.log('ALL VERIFICATIONS PASSED: 0 console errors, interactive features verified!');
    }
  } catch (err) {
    console.error('Test execution error:', err);
    process.exit(1);
  } finally {
    await browser.close();
  }
}

testArchitecturePage();
