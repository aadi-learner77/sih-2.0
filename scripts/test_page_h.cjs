const { testSinglePage } = require('./comprehensive_dom_runner.cjs');

(async () => {
  const result = await testSinglePage({
    id: 'H',
    name: 'Manual Review Queue',
    tabId: 'manual-review-queue',
    defaultRole: 'scrutiny_officer',
    interactFn: async (page) => {
      const logs = [];
      // Test search filter
      const searchInput = await page.$('input[placeholder*="Search queue ID"]');
      if (searchInput) {
        await searchInput.type('Fire');
        logs.push('Typed "Fire" into manual review search input.');
        await new Promise(r => setTimeout(r, 400));
        await searchInput.click({ clickCount: 3 });
        await page.keyboard.press('Backspace');
        logs.push('Cleared search input.');
      }

      // Test priority filter dropdown
      const prioritySelect = await page.$('select:has(option[value="CRITICAL"])');
      if (prioritySelect) {
        await page.evaluate((el) => {
          el.value = 'CRITICAL';
          el.dispatchEvent(new Event('change', { bubbles: true }));
        }, prioritySelect);
        logs.push('Selected CRITICAL priority filter.');
        await new Promise(r => setTimeout(r, 500));
      }

      return logs;
    }
  });
  console.log(JSON.stringify(result, null, 2));
})();

