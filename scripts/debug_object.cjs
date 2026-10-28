const puppeteer = require('puppeteer-core');
const CHROME_PATH = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';

(async () => {
  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: 'new',
    args: ['--no-sandbox']
  });
  const page = await browser.newPage();
  await page.goto('http://localhost:5173');
  await page.evaluate(() => {
    const email = document.querySelector('input[type="email"]');
    const pass = document.querySelector('input[type="password"]');
    if (email && pass) {
      email.value = 'scrutiny.officer@aicte-india.org';
      email.dispatchEvent(new Event('input', { bubbles: true }));
      pass.value = 'AicteOfficer@2025';
      pass.dispatchEvent(new Event('input', { bubbles: true }));
      document.querySelector('button[type="submit"]').click();
    }
  });
  await new Promise(r => setTimeout(r, 1200));
  await page.evaluate(() => {
    const btn = document.querySelector('#sidebar-tab-evidence-lens');
    if (btn) btn.click();
  });
  await new Promise(r => setTimeout(r, 1500));
  const occurrences = await page.evaluate(() => {
    const found = [];
    document.querySelectorAll('*').forEach(el => {
      if (el.children.length === 0 && (el.innerText || '').includes('[object Object]')) {
        found.push({
          tag: el.tagName,
          id: el.id,
          className: el.className,
          text: el.innerText.slice(0, 100),
          parent: el.parentElement ? el.parentElement.className : ''
        });
      }
    });
    return found;
  });
  console.log('Occurrences of [object Object]:', occurrences.length);
  occurrences.slice(0, 5).forEach((o, i) => console.log(i, o));
  await browser.close();
})();

