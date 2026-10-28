const { testSinglePage } = require('./comprehensive_dom_runner.cjs');

(async () => {
  const result = await testSinglePage({
    id: 'I',
    name: 'Pre-Flight Scorecard',
    tabId: 'preflight',
    defaultRole: 'institution_user', // Pre-flight is an institution self-assessment tool
    interactFn: async (page) => {
      const logs = [];
      // Click Re-check compliance audit button
      const recheckBtn = await page.$('#recheck-preflight-btn');
      if (recheckBtn) {
        await recheckBtn.click();
        logs.push('Clicked #recheck-preflight-btn');
        await new Promise(r => setTimeout(r, 1000));
      }
      return logs;
    }
  });
  console.log(JSON.stringify(result, null, 2));
})();

