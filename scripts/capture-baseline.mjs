import { createRequire } from 'module';
const require = createRequire(import.meta.url);
const puppeteer = require('c:/Users/Tejas/Desktop/sih-2.0/frontend/node_modules/puppeteer-core');
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const screenshotDir = path.join(__dirname, '..', 'audit_screenshots');
if (!fs.existsSync(screenshotDir)) {
  fs.mkdirSync(screenshotDir, { recursive: true });
}

async function captureBaseline() {
  const browser = await puppeteer.launch({
    executablePath: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--window-size=1366,768'],
    defaultViewport: { width: 1366, height: 768 }
  });

  const page = await browser.newPage();
  await page.goto('http://127.0.0.1:5173', { waitUntil: 'networkidle2' });

  // Login as admin
  await page.evaluate(async () => {
    const res = await fetch('http://127.0.0.1:8000/api/v1/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: 'admin@aicte-india.org', password: 'AicteAdmin@2025' })
    });
    const data = await res.json();
    localStorage.setItem('pramaan_token', data.access_token);
    localStorage.setItem('pramaan_user', JSON.stringify(data.user));
  });

  await page.reload({ waitUntil: 'networkidle2' });
  await page.waitForSelector('#app-header-bar', { timeout: 10000 });

  const pages = [
    { name: 'dashboard', id: '#sidebar-tab-dashboard' },
    { name: 'evidence-lens', id: '#sidebar-tab-evidence-lens' },
    { name: 'manual-review-queue', id: '#sidebar-tab-manual-review-queue' },
    { name: 'document-intelligence', id: '#sidebar-tab-document-intelligence' },
    { name: 'audit-ledger', id: '#sidebar-tab-audit-ledger' },
    { name: 'regulations', id: '#sidebar-tab-regulations' }
  ];

  for (const theme of ['light', 'dark']) {
    console.log(`Capturing baseline for theme: ${theme}`);
    await page.evaluate((th) => {
      document.documentElement.setAttribute('data-theme', th);
      if (th === 'dark') document.documentElement.classList.add('dark');
      else document.documentElement.classList.remove('dark');
      localStorage.setItem('theme', th);
    }, theme);
    await new Promise(r => setTimeout(r, 400));

    for (const p of pages) {
      const btn = await page.$(p.id);
      if (btn) {
        await btn.click();
        await new Promise(r => setTimeout(r, 600));
      }
      const outPath = path.join(screenshotDir, `v2_before_${p.name}_${theme}.png`);
      await page.screenshot({ path: outPath });
      console.log(`Saved: ${outPath}`);
    }
  }

  await browser.close();
  console.log('Baseline screenshots captured successfully.');
}

captureBaseline().catch(err => {
  console.error('Error capturing baseline:', err);
  process.exit(1);
});
