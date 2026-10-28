const { testSinglePage } = require('./comprehensive_dom_runner.cjs');

(async () => {
  const result = await testSinglePage({
    id: 'E',
    name: 'Impossibility Engine',
    tabId: 'impossibility-engine',
    defaultRole: 'scrutiny_officer',
    interactFn: async (page) => {
      const logs = [];
      // Look for conflict buttons or cluster selector pills
      const conflictPills = await page.$$('button:has(span.font-mono), .conflict-pill');
      logs.push(`Found ${conflictPills.length} interactive graph/conflict elements.`);
      if (conflictPills.length > 0) {
        await conflictPills[0].click();
        logs.push('Clicked first conflict pill.');
        await new Promise(r => setTimeout(r, 600));
      }
      return logs;
    }
  });
  console.log(JSON.stringify(result, null, 2));
})();

