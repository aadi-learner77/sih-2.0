const { testSinglePage } = require('./comprehensive_dom_runner.cjs');

(async () => {
  const result = await testSinglePage({
    id: 'K',
    name: 'Inspection Planner',
    tabId: 'inspection-planner',
    defaultRole: 'scrutiny_officer',
    interactFn: async (page) => {
      const logs = [];
      // 1. Look for dispatch squad order buttons
      const dispatchButtons = await page.$$('button[id^="btn-schedule-inspection-"]');
      logs.push(`Found ${dispatchButtons.length} squad order dispatch buttons.`);
      if (dispatchButtons.length > 0) {
        await dispatchButtons[0].click();
        logs.push('Clicked first Dispatch Squad Order button.');
        await new Promise(r => setTimeout(r, 600));
      }

      // 2. Look for state/cluster pills
      const clusterPills = await page.$$('.cluster-card, button:has(svg.lucide-map-pin)');
      logs.push(`Found ${clusterPills.length} inspection cluster elements.`);

      return logs;
    }
  });
  console.log(JSON.stringify(result, null, 2));
})();

