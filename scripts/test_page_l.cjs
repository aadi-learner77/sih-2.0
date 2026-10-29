const { testSinglePage } = require('./comprehensive_dom_runner.cjs');

(async () => {
  const result = await testSinglePage({
    id: 'L',
    name: 'Audit and Receipts Ledger',
    tabId: 'audit-ledger',
    defaultRole: 'auditor', // Tested with auditor role for immutability ledger
    interactFn: async (page) => {
      const logs = [];
      // Test clicking Verify Chain Integrity button
      const verifyBtn = await page.$('#verify-audit-chain-btn');
      if (verifyBtn) {
        await verifyBtn.click();
        logs.push('Clicked #verify-audit-chain-btn');
        await new Promise(r => setTimeout(r, 800));
      }

      // Test switching to Raw Table View
      const tableViewBtn = await page.evaluate(() => {
        const btns = Array.from(document.querySelectorAll('button'));
        const target = btns.find(b => b.innerText.includes('Raw Table') || b.innerText.includes('Grid View'));
        if (target) {
          target.click();
          return true;
        }
        return false;
      });
      if (tableViewBtn) {
        logs.push('Switched to Raw Table View.');
        await new Promise(r => setTimeout(r, 600));
      }

      return logs;
    }
  });
  console.log(JSON.stringify(result, null, 2));
})();

