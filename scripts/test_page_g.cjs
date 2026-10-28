const { testSinglePage } = require('./comprehensive_dom_runner.cjs');

(async () => {
  const result = await testSinglePage({
    id: 'G',
    name: 'Document Intelligence',
    tabId: 'document-intelligence',
    defaultRole: 'scrutiny_officer',
    interactFn: async (page) => {
      const logs = [];
      // Test search OCR text
      const searchBox = await page.$('input[placeholder*="Search OCR"]');
      if (searchBox) {
        await searchBox.type('AICTE');
        logs.push('Typed "AICTE" into OCR text search box.');
        await new Promise(r => setTimeout(r, 400));
        await searchBox.click({ clickCount: 3 });
        await page.keyboard.press('Backspace');
        logs.push('Cleared OCR search box.');
      }

      // Test clicking document tabs or pills
      const docTabs = await page.$$('button:has(svg.lucide-file-text), button.doc-tab');
      logs.push(`Found ${docTabs.length} document selector tabs.`);
      if (docTabs.length > 1) {
        await docTabs[1].click();
        logs.push('Switched to second document in OCR queue.');
        await new Promise(r => setTimeout(r, 600));
      }

      return logs;
    }
  });
  console.log(JSON.stringify(result, null, 2));
})();

