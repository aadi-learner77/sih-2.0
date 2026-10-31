const puppeteer = require('c:/Users/Tejas/Desktop/sih-2.0/frontend/node_modules/puppeteer-core');
const fs = require('fs');
const path = require('path');

function getLuminance(r, g, b) {
  const [rs, gs, bs] = [r, g, b].map(c => {
    c = c / 255;
    return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
  });
  return 0.2126 * rs + 0.7152 * gs + 0.0722 * bs;
}

function parseRgb(colorStr) {
  if (!colorStr) return [0, 0, 0];
  const match = colorStr.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)/);
  if (match) {
    return [parseInt(match[1]), parseInt(match[2]), parseInt(match[3])];
  }
  return [0, 0, 0];
}

function contrastRatio(rgb1, rgb2) {
  const lum1 = getLuminance(rgb1[0], rgb1[1], rgb1[2]);
  const lum2 = getLuminance(rgb2[0], rgb2[1], rgb2[2]);
  const brightest = Math.max(lum1, lum2);
  const darkest = Math.min(lum1, lum2);
  return Number(((brightest + 0.05) / (darkest + 0.05)).toFixed(2));
}

const screenshotDir = path.join(__dirname, '..', 'audit_screenshots');
if (!fs.existsSync(screenshotDir)) {
  fs.mkdirSync(screenshotDir, { recursive: true });
}

async function runAudit() {
  const browser = await puppeteer.launch({
    executablePath: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--window-size=1920,1080'],
    defaultViewport: { width: 1920, height: 1080 }
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

  const tabsToVisit = [
    { name: 'Dashboard', id: '#sidebar-tab-dashboard' },
    { name: 'Rules Catalog', id: '#sidebar-tab-regulations' },
    { name: 'Review Queue', id: '#sidebar-tab-manual-review-queue' },
    { name: 'Doc Intelligence', id: '#sidebar-tab-document-intelligence' },
    { name: 'Audit & Receipts', id: '#sidebar-tab-audit-ledger' },
    { name: 'Evidence Lens', id: '#sidebar-tab-evidence-lens' }
  ];

  const results = { light: [], dark: [] };

  for (const theme of ['light', 'dark']) {
    console.log(`Auditing theme: ${theme}`);
    await page.evaluate((th) => {
      document.documentElement.setAttribute('data-theme', th);
      if (th === 'dark') document.documentElement.classList.add('dark');
      else document.documentElement.classList.remove('dark');
      localStorage.setItem('theme', th);
    }, theme);
    await new Promise(r => setTimeout(r, 400));

    // Deliverable Screenshot: Hero
    const heroTab = await page.$('#sidebar-tab-dashboard');
    if (heroTab) await heroTab.click();
    await new Promise(r => setTimeout(r, 600));
    
    // Screenshot Hero
    const heroEl = await page.$('#launch-evidence-lens-btn');
    if (heroEl) {
      await page.screenshot({
        path: path.join(screenshotDir, `polish_hero_${theme}.png`),
        clip: { x: 260, y: 64, width: 1400, height: 260 }
      });
    }

    // Deliverable Screenshot: KPI hover
    const kpiEl = await page.$('.kpi-glass-card');
    if (kpiEl) {
      await kpiEl.hover();
      await new Promise(r => setTimeout(r, 200));
      await page.screenshot({
        path: path.join(screenshotDir, `polish_kpi_hover_${theme}.png`),
        clip: { x: 260, y: 320, width: 1400, height: 220 }
      });
    }

    // Deliverable Screenshot: Dashboard Scrolled
    await page.evaluate(() => {
      const scrollEl = document.querySelector('#main-content-scroll');
      if (scrollEl) scrollEl.scrollTop = 300;
    });
    await new Promise(r => setTimeout(r, 300));
    await page.screenshot({
      path: path.join(screenshotDir, `polish_dashboard_scrolled_${theme}.png`)
    });

    // Reset scroll
    await page.evaluate(() => {
      const scrollEl = document.querySelector('#main-content-scroll');
      if (scrollEl) scrollEl.scrollTop = 0;
    });

    // Deliverable Screenshot: Collapsed sidebar with tooltip
    const toggleBtn = await page.$('#sidebar-toggle-btn');
    if (toggleBtn) {
      await toggleBtn.click();
      await new Promise(r => setTimeout(r, 350));
      const sidebarItem = await page.$('#sidebar-tab-evidence-lens');
      if (sidebarItem) {
        await sidebarItem.hover();
        await new Promise(r => setTimeout(r, 250));
        await page.screenshot({
          path: path.join(screenshotDir, `polish_collapsed_sidebar_tooltip_${theme}.png`),
          clip: { x: 0, y: 0, width: 350, height: 600 }
        });
      }
      // Re-expand sidebar
      await toggleBtn.click();
      await new Promise(r => setTimeout(r, 350));
    }

    // Rules Catalog Tabs Screenshots (both catalog and simulator states)
    const regTab = await page.$('#sidebar-tab-regulations');
    if (regTab) {
      await regTab.click();
      await new Promise(r => setTimeout(r, 600));

      const catalogBtn = await page.$('#tab-rules-catalog');
      if (catalogBtn) {
        await catalogBtn.click();
        await new Promise(r => setTimeout(r, 300));
        await page.screenshot({
          path: path.join(screenshotDir, `polish_rules_catalog_tabs_catalog_${theme}.png`),
          clip: { x: 260, y: 64, width: 800, height: 160 }
        });
      }

      const simBtn = await page.$('#tab-what-if-simulator');
      if (simBtn) {
        await simBtn.click();
        await new Promise(r => setTimeout(r, 300));
        await page.screenshot({
          path: path.join(screenshotDir, `polish_rules_catalog_tabs_simulator_${theme}.png`),
          clip: { x: 260, y: 64, width: 800, height: 160 }
        });
      }
    }

    // Audit elements across all pages
    for (const tab of tabsToVisit) {
      const tabEl = await page.$(tab.id);
      if (tabEl) {
        await tabEl.click();
        await new Promise(r => setTimeout(r, 500));
      }

      const elements = await page.evaluate((tabName) => {
        const items = [];
        const targets = Array.from(document.querySelectorAll('button, [role="tab"], .tab, a.btn, [class*="badge"], [class*="pill"]'));

        for (const el of targets) {
          if (!el.offsetParent && el.getBoundingClientRect().width === 0) continue;
          const text = (el.innerText || '').trim().replace(/\s+/g, ' ').slice(0, 35);
          if (!text && !el.querySelector('svg')) continue;

          // Find effective background
          let cur = el;
          let bg = 'rgba(0, 0, 0, 0)';
          while (cur && cur !== document.body) {
            const cs = window.getComputedStyle(cur);
            if (cs.backgroundColor && cs.backgroundColor !== 'rgba(0, 0, 0, 0)' && cs.backgroundColor !== 'transparent') {
              bg = cs.backgroundColor;
              break;
            }
            cur = cur.parentElement;
          }
          if (bg === 'rgba(0, 0, 0, 0)' || bg === 'transparent') {
            bg = window.getComputedStyle(document.body).backgroundColor;
          }

          const csEl = window.getComputedStyle(el);
          const childSpan = el.querySelector('span') || el;
          const childSvg = el.querySelector('svg');
          const csChild = window.getComputedStyle(childSpan);
          const fg = csChild.color || csEl.color;

          items.push({
            page: tabName,
            element: el.tagName.toLowerCase() + (el.id ? '#' + el.id : '') + (el.className ? '.' + el.className.split(' ').slice(0, 2).join('.') : ''),
            label: text || (childSvg ? '<Icon>' : ''),
            fg,
            bg,
            svgStroke: childSvg ? window.getComputedStyle(childSvg).stroke : null
          });
        }
        return items;
      }, tab.name);

      for (const item of elements) {
        const fgRgb = parseRgb(item.fg);
        const bgRgb = parseRgb(item.bg);
        const ratio = contrastRatio(fgRgb, bgRgb);
        const pass = ratio >= 4.5;
        results[theme].push({
          ...item,
          ratio,
          pass
        });
      }
    }
  }

  // Verification across viewports (1366px & 1920px) and roles
  const roles = [
    { name: 'Admin', email: 'admin@aicte-india.org', pass: 'AicteAdmin@2025' },
    { name: 'Scrutiny Officer', email: 'scrutiny.officer@aicte-india.org', pass: 'AicteOfficer@2025' },
    { name: 'Regional Officer', email: 'regional.officer@aicte-india.org', pass: 'AicteRegional@2025' },
    { name: 'Independent Auditor', email: 'auditor@aicte-india.org', pass: 'AicteAuditor@2025' },
    { name: 'Institution User', email: 'registrar@apextech.edu.in', pass: 'ApexPass@2025' }
  ];

  console.log('Verifying all 5 roles across 1366px and 1920px...');
  for (const vp of [{ width: 1366, height: 768 }, { width: 1920, height: 1080 }]) {
    await page.setViewport(vp);
    for (const r of roles) {
      await page.evaluate(async (role) => {
        const res = await fetch('http://127.0.0.1:8000/api/v1/auth/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email: role.email, password: role.pass })
        });
        const data = await res.json();
        localStorage.setItem('pramaan_token', data.access_token);
        localStorage.setItem('pramaan_user', JSON.stringify(data.user));
      }, r);
      await page.reload({ waitUntil: 'networkidle2' });
      const headerExists = await page.waitForSelector('#app-header-bar', { timeout: 6000 });
      if (!headerExists) {
        console.error(`FAILED: Role ${r.name} at ${vp.width}px could not find header.`);
      } else {
        console.log(`Verified Role ${r.name} at ${vp.width}x${vp.height}: OK`);
      }
    }
  }
  console.log('Role and viewport verification passed.');

  await browser.close();

  fs.writeFileSync(
    path.join(__dirname, 'contrast_audit_after.json'),
    JSON.stringify(results, null, 2)
  );

  const lightFails = results.light.filter(r => !r.pass);
  const darkFails = results.dark.filter(r => !r.pass);
  console.log(`Audit complete:`);
  console.log(`Light Mode: ${results.light.length} items checked. Failing AA (<4.5): ${lightFails.length}`);
  console.log(`Dark Mode: ${results.dark.length} items checked. Failing AA (<4.5): ${darkFails.length}`);

  if (lightFails.length > 0) {
    console.log('Light failures:', lightFails.slice(0, 10).map(f => `${f.element} ("${f.label}"): ${f.ratio}:1 [fg: ${f.fg}, bg: ${f.bg}]`));
  }
  if (darkFails.length > 0) {
    console.log('Dark failures:', darkFails.slice(0, 10).map(f => `${f.element} ("${f.label}"): ${f.ratio}:1 [fg: ${f.fg}, bg: ${f.bg}]`));
  }
}

runAudit().catch(err => {
  console.error('Audit failed with error:', err);
  process.exit(1);
});
