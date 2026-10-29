// run 1: Mia web chat test
const { chromium } = require('playwright'); const fs = require('fs');
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 390, height: 844 } });
  const logs = [];
  p.on('console', m => logs.push(m.type() + ': ' + m.text()));
  p.on('pageerror', e => logs.push('pageerror: ' + e.message));
  p.on('response', r => { if (r.url().includes('n8n.cloud')) logs.push('resp ' + r.status() + ' ' + r.url() + ' ' + (r.headers()['content-type'] || '')); });
  await p.goto('https://b2bsasagency.com/mia/?t=' + Date.now(), { waitUntil: 'load', timeout: 60000 });
  await p.waitForTimeout(3000);
  await p.screenshot({ path: 'fetch/shots/e2e_mia_1.png' });
  await p.fill('#oName', 'Test'); await p.fill('#oAge', '30'); await p.selectOption('#oAddr', 'Boss');
  await p.click('#oGo');
  await p.fill('#q', 'Salom Mia, bugun kayfiyating qanday?');
  await p.click('#send');
  await p.waitForTimeout(20000);
  await p.screenshot({ path: 'fetch/shots/e2e_mia_2.png' });
  const texts = await p.$$eval('.b', els => els.map(e => e.className + ' | ' + e.textContent));
  fs.writeFileSync('fetch/shots/e2e_mia.log', logs.concat(texts).join('\n'));
  await b.close();
})();
