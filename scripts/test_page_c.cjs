const { testSinglePage } = require('./comprehensive_dom_runner.cjs');

(async () => {
  const result = await testSinglePage({
    id: 'C',
    name: 'Scrutiny Dashboard',
    tabId: 'dashboard',
    defaultRole: 'scrutiny_officer',
    interactFn: async (page) => {
      const logs = [];
      // Test search filter
      const searchInput = await page.$('input[placeholder*="Search by college"]');
      if (searchInput) {
        await searchInput.type('Apex');
        logs.push('Typed "Apex" into dashboard search input.');
        await new Promise(r => setTimeout(r, 400));
        await searchInput.click({ clickCount: 3 });
        await page.keyboard.press('Backspace');
        logs.push('Cleared search input.');
      }

      // Test status filter pill
      const statusPillClicked = await page.evaluate(() => {
        const pills = Array.from(document.querySelectorAll('button'));
        const pill = pills.find(p => p.innerText.includes('Deficiencies Found') || p.innerText.includes('Under Review'));
        if (pill) {
          pill.click();
          return true;
        }
        return false;
      });
      logs.push(`Clicked status filter pill: ${statusPillClicked}`);
      await new Promise(r => setTimeout(r, 600));

      return logs;
    }
  });
  console.log(JSON.stringify(result, null, 2));
})();

