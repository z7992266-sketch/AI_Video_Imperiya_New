// run 4 (site in Russian): record phone-screen videos of our site and the demo menu (prices hidden) for the B2B ad side screen
const { chromium } = require('playwright'); const fs = require('fs');
const sleep = ms => new Promise(r => setTimeout(r, ms));
async function rec(b, name, url, prep, steps) {
  const ctx = await b.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true,
    recordVideo: { dir: 'fetch/shots/rec_' + name, size: { width: 780, height: 1688 } } });
  const p = await ctx.newPage(); const logs = [];
  p.on('pageerror', e => logs.push('pageerror: ' + e.message));
  await ctx.addInitScript(() => { try { localStorage.setItem('b2b_lang', 'ru'); } catch (e) {} });
  try { await p.goto(url, { waitUntil: 'load', timeout: 60000 }); } catch (e) { logs.push('goto ' + e.message); }
  try { await p.click('[data-lang="ru"]', { timeout: 3000 }); } catch (e) { logs.push('no ru btn'); }
  await sleep(prep);
  // hide prices / street address (no prices in ads)
  await p.addStyleTag({ content: '*{scroll-behavior:auto!important}' });
  await p.evaluate(() => {
    const walk = n => { for (const c of n.childNodes) { if (c.nodeType === 3) { if (/[₽$]|сум|so'm|\bул\.|ул\. /i.test(c.textContent)) c.textContent = c.textContent.replace(/.*(₽|\$|сум|so'm).*/i, '').replace(/,?\s*ул\..*/i, ''); } else walk(c); } };
    walk(document.body);
    document.querySelectorAll('*').forEach(e => { const t = (e.innerText || '').trim(); if (/^\d[\d\s]*₽$/.test(t)) e.style.visibility = 'hidden'; });
  });
  await sleep(1200);
  for (const [dy, ms] of steps) {   // finger-like swipes: eased scroll
    const n = Math.max(1, Math.round(ms / 16));
    for (let i = 1; i <= n; i++) { const k = i / n; const e = 1 - Math.pow(1 - k, 3); const prev = 1 - Math.pow(1 - (i - 1) / n, 3);
      await p.mouse.wheel(0, dy * (e - prev)); await sleep(16); }
    await sleep(700);
  }
  await sleep(800);
  await ctx.close();
  const dir = 'fetch/shots/rec_' + name; const f = fs.readdirSync(dir).find(x => x.endsWith('.webm'));
  if (f) fs.renameSync(dir + '/' + f, 'fetch/shots/' + name + '.webm');
  fs.writeFileSync('fetch/shots/' + name + '.rec.log', logs.join('\n'));
}
(async () => {
  const b = await chromium.launch();
  const steps = [[420, 600], [520, 650], [480, 600], [560, 650], [500, 600], [520, 650], [480, 600], [-900, 700], [600, 650], [520, 600]];
    await rec(b, 'site_scroll_ru', 'https://b2bsasagency.com/?lang=ru&t=' + Date.now(), 4000, steps);
  await b.close();
})();
