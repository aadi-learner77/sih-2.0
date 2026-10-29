const { testSinglePage } = require('./comprehensive_dom_runner.cjs');

(async () => {
  const result = await testSinglePage({
    id: 'M',
    name: 'Alerts Drawer & Header Navbar',
    tabId: 'dashboard',
    defaultRole: 'scrutiny_officer',
    interactFn: async (page) => {
      const logs = [];
      // 1. Click Alert Bell Button to open drawer
      const bellBtn = await page.$('#alert-bell-btn');
      if (bellBtn) {
        await bellBtn.click();
        logs.push('Clicked #alert-bell-btn to open modal drawer.');
        await new Promise(r => setTimeout(r, 800));
      }

      // 2. Check modal existence
      const drawerVisible = await page.evaluate(() => {
        const modal = document.querySelector('#alert-bell-drawer-modal');
        return modal !== null;
      });
      logs.push(`Alert drawer modal visible: ${drawerVisible}`);

      // 3. Count alert cards in drawer
      const drawerCount = await page.evaluate(() => {
        const cards = document.querySelectorAll('.alert-item-card, div.alert-card, #alert-bell-drawer-modal .border-slate-200');
        return cards.length;
      });
      logs.push(`Alert items displayed in drawer: ${drawerCount}`);

      // 4. Click a severity filter inside drawer
      const filterClicked = await page.evaluate(() => {
        const criticalBtn = Array.from(document.querySelectorAll('#alert-bell-drawer-modal button')).find(b => b.innerText.includes('CRITICAL'));
        if (criticalBtn) {
          criticalBtn.click();
          return true;
        }
        return false;
      });
      logs.push(`Clicked CRITICAL severity filter: ${filterClicked}`);
      await new Promise(r => setTimeout(r, 500));

      return logs;
    }
  });
  console.log(JSON.stringify(result, null, 2));
})();

