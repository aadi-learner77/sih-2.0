const { testSinglePage } = require('./comprehensive_dom_runner.cjs');

(async () => {
  const result = await testSinglePage({
    id: 'F',
    name: 'Photo Radar & Forensics',
    tabId: 'photo-radar',
    defaultRole: 'scrutiny_officer',
    interactFn: async (page) => {
      const logs = [];
      // Test clicking quick select reuse case buttons
      const clusterButtons = await page.$$('button:has(span.font-mono)');
      logs.push(`Found ${clusterButtons.length} cluster buttons.`);
      if (clusterButtons.length > 1) {
        await clusterButtons[1].click();
        logs.push('Clicked second reuse cluster pill.');
        await new Promise(r => setTimeout(r, 600));
      }

      // Test switching comparison view mode
      const overlayBtn = await page.$('#view-mode-difference-overlay');
      if (overlayBtn) {
        await overlayBtn.click();
        logs.push('Switched to Difference Overlay view.');
        await new Promise(r => setTimeout(r, 500));
      }

      const sideBySideBtn = await page.$('#view-mode-side-by-side');
      if (sideBySideBtn) {
        await sideBySideBtn.click();
        logs.push('Switched back to Side-by-Side view.');
        await new Promise(r => setTimeout(r, 500));
      }

      return logs;
    }
  });
  console.log(JSON.stringify(result, null, 2));
})();

