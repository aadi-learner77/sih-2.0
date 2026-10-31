import fs from 'fs';
import path from 'path';
import { createRequire } from 'module';
const require = createRequire(import.meta.url);
const puppeteer = require('c:/Users/Tejas/Desktop/sih-2.0/frontend/node_modules/puppeteer-core');

const CHROME_PATH = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const OUT_DIR = path.resolve('audit_screenshots');

if (!fs.existsSync(OUT_DIR)) {
  fs.mkdirSync(OUT_DIR, { recursive: true });
}

const TABS = [
  { id: 'dashboard', name: 'dashboard' },
  { id: 'evidence-lens', name: 'evidence-lens' },
  { id: 'manual-review-queue', name: 'manual-review-queue' },
  { id: 'document-intelligence', name: 'document-intelligence' },
  { id: 'audit-ledger', name: 'audit-ledger' },
  { id: 'regulations', name: 'regulations' },
];

async function capture() {
  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1366, height: 768 });

  // 1. Login as Admin
  await page.goto('http://127.0.0.1:5173', { waitUntil: 'networkidle2' });
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

  // 2. Capture Tabs (Light & Dark)
  for (const theme of ['light', 'dark']) {
    await page.evaluate((th) => {
      document.documentElement.setAttribute('data-theme', th);
      if (th === 'dark') document.documentElement.classList.add('dark');
      else document.documentElement.classList.remove('dark');
      localStorage.setItem('theme', th);
    }, theme);

    for (const tab of TABS) {
      await page.evaluate((tabId) => {
        const btn = document.querySelector(`#sidebar-tab-${tabId}`);
        if (btn) btn.click();
      }, tab.id);
      await new Promise(r => setTimeout(r, 600));

      const outPath = path.join(OUT_DIR, `v2_after_${tab.name}_${theme}.png`);
      await page.screenshot({ path: outPath });
      console.log(`Captured: ${outPath}`);
    }
  }

  // 3. Capture Interactions:
  // 3a. KPI Card Mid-Hover (Light & Dark)
  for (const theme of ['light', 'dark']) {
    await page.evaluate((th) => {
      document.documentElement.setAttribute('data-theme', th);
      if (th === 'dark') document.documentElement.classList.add('dark');
      else document.documentElement.classList.remove('dark');
      const btn = document.querySelector('#sidebar-tab-dashboard');
      if (btn) btn.click();
    }, theme);
    await new Promise(r => setTimeout(r, 600));

    // Hover over the first KPI card
    const kpiCard = await page.$('.kpi-glass-card');
    if (kpiCard) {
      const box = await kpiCard.boundingBox();
      if (box) {
        await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2);
        await new Promise(r => setTimeout(r, 400));
        const outPath = path.join(OUT_DIR, `v2_after_kpi_hover_${theme}.png`);
        await page.screenshot({ path: outPath });
        console.log(`Captured KPI hover: ${outPath}`);
      }
    }
  }

  // 3b. Dashboard Scrolled (Glass Header)
  await page.evaluate(() => {
    const mainEl = document.querySelector('main');
    if (mainEl) mainEl.scrollTop = 250;
  });
  await new Promise(r => setTimeout(r, 400));
  await page.screenshot({ path: path.join(OUT_DIR, 'v2_after_dashboard_scrolled.png') });
  console.log('Captured dashboard scrolled');

  // 3c. Sidebar Mid-Slide
  const sidebarBtn = await page.$('#sidebar-tab-evidence-lens');
  if (sidebarBtn) {
    const sBox = await sidebarBtn.boundingBox();
    if (sBox) {
      await page.mouse.move(sBox.x + sBox.width / 2, sBox.y + sBox.height / 2);
      await new Promise(r => setTimeout(r, 100));
      await page.screenshot({ path: path.join(OUT_DIR, 'v2_after_sidebar_mid_slide.png') });
      console.log('Captured sidebar mid-slide');
    }
  }

  // 3d. Tab Switch Mid-Slide (Regulations Page)
  await page.evaluate(() => {
    const regBtn = document.querySelector('#sidebar-tab-regulations');
    if (regBtn) regBtn.click();
  });
  await new Promise(r => setTimeout(r, 500));
  const simulatorTab = await page.$('#tab-what-if-simulator');
  if (simulatorTab) {
    await simulatorTab.click();
    await new Promise(r => setTimeout(r, 150));
    await page.screenshot({ path: path.join(OUT_DIR, 'v2_after_tab_switch_mid_slide.png') });
    console.log('Captured tab switch mid-slide');
  }

  // 3e. Theme Toggle Mid-Morph
  const themeBtn = await page.$('#theme-toggle-btn');
  if (themeBtn) {
    await themeBtn.click();
    await new Promise(r => setTimeout(r, 120));
    await page.screenshot({ path: path.join(OUT_DIR, 'v2_after_theme_toggle_mid_morph.png') });
    console.log('Captured theme toggle mid-morph');
  }

  await browser.close();
  console.log('All screenshots captured successfully.');
}

capture().catch(err => {
  console.error('Screenshot capture failed:', err);
  process.exit(1);
});

