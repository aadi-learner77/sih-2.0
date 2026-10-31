import { createRequire } from 'module';
const require = createRequire(import.meta.url);
const puppeteer = require('c:/Users/Tejas/Desktop/sih-2.0/frontend/node_modules/puppeteer-core');

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

const ROLES = [
  { name: 'Admin', role: 'admin', email: 'admin@aicte-india.org', pass: 'AicteAdmin@2025' },
  { name: 'Scrutiny Officer', role: 'scrutiny_officer', email: 'scrutiny.officer@aicte-india.org', pass: 'AicteOfficer@2025' },
  { name: 'Regional Officer', role: 'senior_officer', email: 'regional.officer@aicte-india.org', pass: 'AicteRegional@2025' },
  { name: 'Auditor', role: 'auditor', email: 'auditor@aicte-india.org', pass: 'AicteAuditor@2025' },
  { name: 'Institution User', role: 'institution_user', email: 'registrar@apextech.edu.in', pass: 'ApexPass@2025' }
];

const VIEWPORTS = [
  { width: 1366, height: 768 },
  { width: 1920, height: 1080 }
];

async function runRegressionCheck() {
  const browser = await puppeteer.launch({
    executablePath: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
  });

  const page = await browser.newPage();
  const consoleErrors = [];
  page.on('pageerror', err => {
    consoleErrors.push(err.message || String(err));
  });

  const checkResults = {
    contrast: { pass: true, failures: [] },
    triageOverlapAndScroll: { pass: true, failures: [] },
    headerAndUserMenu: { pass: true, failures: [] },
    hamburger: { pass: true, failures: [] },
    searchIconOverlap: { pass: true, failures: [] },
    stuckFocusOutline: { pass: true, failures: [] },
    infiniteAnimations: { pass: true, failures: [] },
    backdropFilterRestrictions: { pass: true, failures: [] },
    noConicGradient: { pass: true, failures: [] },
    darkSurfacesCarbon: { pass: true, failures: [] },
    forbiddenWords: { pass: true, failures: [] },
    consoleErrors: { pass: true, errors: [] }
  };

  for (const vp of VIEWPORTS) {
    await page.setViewport(vp);
    for (const r of ROLES) {
      // Login as role
      await page.goto('http://127.0.0.1:5173', { waitUntil: 'networkidle2' });
      await page.evaluate(async (credentials) => {
        const res = await fetch('http://127.0.0.1:8000/api/v1/auth/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email: credentials.email, password: credentials.pass })
        });
        const data = await res.json();
        localStorage.setItem('pramaan_token', data.access_token);
        localStorage.setItem('pramaan_user', JSON.stringify(data.user));
      }, r);

      await page.reload({ waitUntil: 'networkidle2' });
      await page.waitForSelector('#app-header-bar', { timeout: 8000 });

      for (const theme of ['light', 'dark']) {
        await page.evaluate((th) => {
          document.documentElement.setAttribute('data-theme', th);
          if (th === 'dark') document.documentElement.classList.add('dark');
          else document.documentElement.classList.remove('dark');
          localStorage.setItem('theme', th);
        }, theme);
        await new Promise(res => setTimeout(res, 200));

        // 1. Contrast Check for active view
        const contrastItems = await page.evaluate(() => {
          const items = [];
          const targets = Array.from(document.querySelectorAll('button, [role="tab"], .tab, a.btn, [class*="badge"], [class*="pill"], input'));
          for (const el of targets) {
            if (!el.offsetParent && el.getBoundingClientRect().width === 0) continue;
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
            const csChild = window.getComputedStyle(childSpan);
            const fg = csChild.color || csEl.color;
            items.push({
              tag: el.tagName.toLowerCase() + (el.id ? '#' + el.id : ''),
              text: (el.innerText || el.placeholder || '').trim().slice(0, 25),
              fg,
              bg
            });
          }
          return items;
        });

        for (const item of contrastItems) {
          const fg = parseRgb(item.fg);
          const bg = parseRgb(item.bg);
          const ratio = contrastRatio(fg, bg);
          if (ratio < 4.5 && item.text) {
            checkResults.contrast.pass = false;
            checkResults.contrast.failures.push(`${r.name} (${theme}, ${vp.width}px): ${item.tag} ("${item.text}") has ratio ${ratio}:1 [fg: ${item.fg}, bg: ${item.bg}]`);
          }
        }

        // 2. Header and User Menu
        const wordmark = await page.$('#header-wordmark');
        const toggle = await page.$('#theme-toggle-btn');
        const toggleSvg = await page.$('#theme-toggle-btn svg');
        const userMenuBtn = await page.$('#user-menu-btn');
        
        let signoutPresent = false;
        let switchRolePresent = false;
        if (userMenuBtn) {
          await userMenuBtn.click();
          await new Promise(res => setTimeout(res, 200));
          const signoutBtn = await page.$('#user-menu-signout-btn');
          signoutPresent = !!signoutBtn;
          switchRolePresent = await page.evaluate(() => {
            return !!Array.from(document.querySelectorAll('*')).find(b => b.innerText && b.innerText.includes('Switch demo role'));
          });
          await userMenuBtn.click(); // Close
          await new Promise(res => setTimeout(res, 100));
        }

        const wordmarkBox = wordmark ? await wordmark.boundingBox() : null;
        const toggleBox = toggleSvg ? await toggleSvg.boundingBox() : null;
        const headerCheck = {
          wordmarkVisible: !!wordmarkBox && wordmarkBox.width > 0,
          toggleIconVisible: !!toggleBox && toggleBox.width > 0,
          signoutPresent,
          switchRoleAllowed: r.role === 'admin' ? true : !switchRolePresent
        };

        if (!headerCheck.wordmarkVisible || !headerCheck.toggleIconVisible || !headerCheck.signoutPresent || !headerCheck.switchRoleAllowed) {
          checkResults.headerAndUserMenu.pass = false;
          checkResults.headerAndUserMenu.failures.push(`${r.name} (${theme}, ${vp.width}px): ${JSON.stringify(headerCheck)}`);
        }

        // 3. Hamburger Toggle
        if (vp.width >= 1024) {
          const sidebarWidthBefore = await page.evaluate(() => document.querySelector('aside')?.getBoundingClientRect().width || 0);
          const hambToggle = await page.$('#sidebar-toggle-btn');
          if (hambToggle) {
            await hambToggle.click();
            await new Promise(res => setTimeout(res, 250));
            const sidebarWidthAfter = await page.evaluate(() => document.querySelector('aside')?.getBoundingClientRect().width || 0);
            if (sidebarWidthBefore === sidebarWidthAfter) {
              checkResults.hamburger.pass = false;
              checkResults.hamburger.failures.push(`Sidebar did not collapse on toggle click (${sidebarWidthBefore} -> ${sidebarWidthAfter})`);
            }
            await hambToggle.click(); // Restore
            await new Promise(res => setTimeout(res, 250));
          }
        }

        // 4. Stuck Focus Outline after mouse click
        const themeBtn = await page.$('#theme-toggle-btn');
        if (themeBtn) {
          await themeBtn.click();
          await new Promise(res => setTimeout(res, 100));
          const outlineCheck = await page.evaluate(() => {
            const el = document.querySelector('#theme-toggle-btn');
            const cs = window.getComputedStyle(el);
            const boxShadow = cs.boxShadow;
            const outline = cs.outlineStyle;
            return { outline, boxShadow };
          });
          if (outlineCheck.outline !== 'none' && outlineCheck.outline !== '') {
            checkResults.stuckFocusOutline.pass = false;
            checkResults.stuckFocusOutline.failures.push(`Theme toggle retained stuck outline after click: ${JSON.stringify(outlineCheck)}`);
          }
        }

        // 5. CSS & Forbidden Checks
        const domInspection = await page.evaluate(() => {
          // Check forbidden words in content
          const bodyText = document.body.innerText;
          const forbidden = ['fraud', 'forged', 'fake', 'REJECTED'].filter(w => new RegExp('\\b' + w + '\\b', 'i').test(bodyText));

          // Check backdrop-filter restrictions
          const restrictedTags = Array.from(document.querySelectorAll('tr, td, input, select, textarea, .doc-preview, #document-intelligence-paper'));
          const illegalBackdrop = restrictedTags.filter(el => {
            const cs = window.getComputedStyle(el);
            return cs.backdropFilter && cs.backdropFilter !== 'none';
          }).map(el => el.tagName.toLowerCase() + (el.id ? '#' + el.id : ''));

          // Check conic gradient
          const allEls = Array.from(document.querySelectorAll('*'));
          const hasConic = allEls.filter(el => {
            const cs = window.getComputedStyle(el);
            return (cs.backgroundImage && cs.backgroundImage.includes('conic-gradient'));
          }).map(el => el.tagName.toLowerCase());

          // Check infinite animations (only status dots / loaders allowed)
          const infiniteAnim = allEls.filter(el => {
            const cs = window.getComputedStyle(el);
            if (cs.animationIterationCount !== 'infinite') return false;
            const isDot = el.classList.contains('animate-pulse') || el.classList.contains('animate-ping') || el.classList.contains('rounded-full');
            const isSpinner = el.classList.contains('animate-spin') || el.tagName.toLowerCase() === 'svg';
            return !isDot && !isSpinner;
          }).map(el => el.tagName.toLowerCase() + (el.id ? '#' + el.id : '') + (el.className ? '.' + el.className.split(' ').slice(0, 2).join('.') : ''));

          // Check search icon overlap with input text
          const inputsWithSearch = Array.from(document.querySelectorAll('input[type="text"]')).filter(input => {
            const prevIcon = input.parentElement?.querySelector('svg');
            if (!prevIcon) return false;
            const paddingLeft = parseFloat(window.getComputedStyle(input).paddingLeft) || 0;
            return paddingLeft < 32; // Should have at least pl-10 (40px)
          }).map(el => el.placeholder || el.id);

          // Check dark carbon surfaces (no blue tint in surface variables)
          let darkBlueTint = false;
          if (document.documentElement.getAttribute('data-theme') === 'dark') {
            const surface = window.getComputedStyle(document.documentElement).getPropertyValue('--surface').trim();
            if (surface.toLowerCase().includes('#0f172a') || surface.toLowerCase().includes('#0a192f')) {
              darkBlueTint = true;
            }
          }

          // Check horizontal scroll at >= 1280px
          const hasHScroll = window.innerWidth >= 1280 && document.documentElement.scrollWidth > window.innerWidth;

          return {
            forbidden,
            illegalBackdrop,
            hasConic,
            infiniteAnim,
            inputsWithSearch,
            darkBlueTint,
            hasHScroll
          };
        });

        if (domInspection.forbidden.length > 0) {
          checkResults.forbiddenWords.pass = false;
          checkResults.forbiddenWords.failures.push(`${r.name} (${theme}): Forbidden words found: ${domInspection.forbidden.join(', ')}`);
        }
        if (domInspection.illegalBackdrop.length > 0) {
          checkResults.backdropFilterRestrictions.pass = false;
          checkResults.backdropFilterRestrictions.failures.push(`Illegal backdrop-filter on: ${domInspection.illegalBackdrop.join(', ')}`);
        }
        if (domInspection.hasConic.length > 0) {
          checkResults.noConicGradient.pass = false;
          checkResults.noConicGradient.failures.push(`Conic gradient found on: ${domInspection.hasConic.join(', ')}`);
        }
        if (domInspection.infiniteAnim.length > 0) {
          checkResults.infiniteAnimations.pass = false;
          checkResults.infiniteAnimations.failures.push(`Illegal infinite animation on: ${domInspection.infiniteAnim.join(', ')}`);
        }
        if (domInspection.inputsWithSearch.length > 0) {
          checkResults.searchIconOverlap.pass = false;
          checkResults.searchIconOverlap.failures.push(`Search icon overlap on input: ${domInspection.inputsWithSearch.join(', ')}`);
        }
        if (domInspection.darkBlueTint) {
          checkResults.darkSurfacesCarbon.pass = false;
          checkResults.darkSurfacesCarbon.failures.push(`Dark mode surface has blue tint`);
        }
        if (domInspection.hasHScroll) {
          checkResults.triageOverlapAndScroll.pass = false;
          checkResults.triageOverlapAndScroll.failures.push(`Horizontal scroll detected at ${vp.width}px`);
        }
      }
    }
  }

  if (consoleErrors.length > 0) {
    checkResults.consoleErrors.pass = false;
    checkResults.consoleErrors.errors = consoleErrors;
  }

  await browser.close();

  // Print Summary Table
  console.log('\n================ UI REGRESSION CHECK REPORT ================');
  let allPass = true;
  for (const [checkName, res] of Object.entries(checkResults)) {
    const status = res.pass ? 'PASS' : 'FAIL';
    if (!res.pass) allPass = false;
    console.log(`[${status}] ${checkName}`);
    if (!res.pass && res.failures?.length > 0) {
      res.failures.slice(0, 5).forEach(f => console.log(`   - ${f}`));
    }
    if (!res.pass && res.errors?.length > 0) {
      res.errors.slice(0, 5).forEach(e => console.log(`   - Console: ${e}`));
    }
  }
  console.log('============================================================');
  console.log(`OVERALL RESULT: ${allPass ? 'PASS' : 'FAIL'}\n`);

  if (!allPass) process.exit(1);
}

runRegressionCheck().catch(err => {
  console.error('Regression check execution error:', err);
  process.exit(1);
});
