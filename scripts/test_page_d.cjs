const { testSinglePage } = require('./comprehensive_dom_runner.cjs');

(async () => {
  const result = await testSinglePage({
    id: 'D',
    name: 'Evidence Lens',
    tabId: 'evidence-lens',
    defaultRole: 'scrutiny_officer',
    interactFn: async (page) => {
      const logs = [];
      // Test selecting findings or application dossier dropdown
      const findingButtons = await page.$$('button[id^="finding-pill-"], button.finding-item, div.finding-card');
      logs.push(`Found ${findingButtons.length} interactive finding selectors.`);
      if (findingButtons.length > 0) {
        await findingButtons[0].click();
        logs.push('Clicked first finding.');
      }
      return logs;
    }
  });
  console.log(JSON.stringify(result, null, 2));
})();

