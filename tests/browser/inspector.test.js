// Browser tests for inspector.js in real Chromium (Playwright).
// Usage: cd tests/browser && npm install && npx playwright install chromium && npm test
// Set CHROMIUM_PATH to use an existing Chromium binary instead of the Playwright download.
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const assert = require('assert');

const INSPECTOR = path.join(__dirname, '../../plugins/game-gui/skills/game-gui-design/scripts/inspector.js');
const FIX = path.join(__dirname, 'fixtures');

// Fixture stage: 1920x1080, scaled to fit the viewport. HUD layer has pointer-events:none,
// a full-screen vignette sits on top, and a hidden menu has opacity 0.
function page(html) {
  return fs.readFileSync(path.join(FIX, html), 'utf8')
    .replace('<script src="INSPECTOR"></script>', `<script>${fs.readFileSync(INSPECTOR, 'utf8')}</script>`);
}
const selected = p => p.$$eval('.uii-sel', e => e.map(x => x.dataset.id));
const field = p => p.$eval('#uii-selector', e => e.value);

const tests = [];
const test = (name, fn) => tests.push({ name, fn });

for (const [w, h] of [[960, 540], [1920, 1080], [2560, 1440]]) {
  test(`picks through pointer-events:none and overlays at ${w}x${h}`, async b => {
    const p = await b.newPage({ viewport: { width: w, height: h } });
    await p.setContent(page('hud-overlay.html'));
    await p.click('#uii-btn');
    const s = Math.min(w / 1920, h / 1080);
    await p.mouse.click(150 * s, (1080 - 72) * s);
    assert.deepStrictEqual(await selected(p), ['hud.layer.health-bar.fill']);
    assert.strictEqual(await field(p), 'hud.layer.health-bar.fill');
    await p.mouse.click(420 * s, (1080 - 72) * s);
    assert.deepStrictEqual(await selected(p), ['hud.layer.health-bar']);
    // opacity:0 menu is skipped: the click lands on its visible parent layer
    await p.mouse.click(950 * s, 330 * s);
    assert.deepStrictEqual(await selected(p), ['hud.layer']);
    await p.close();
  });
}

test('selector field follows scope and accepts edits', async b => {
  const p = await b.newPage({ viewport: { width: 960, height: 540 } });
  await p.setContent(page('hud-overlay.html'));
  await p.click('#uii-btn');
  await p.mouse.click(210, 504);
  await p.selectOption('#uii-scope', '@bar');
  assert.strictEqual(await field(p), '@bar');
  await p.fill('#uii-selector', '@bar:low');
  await p.fill('#uii-note', 'red fill');
  await p.click('[data-a=add]');
  const edits = await p.$$eval('#uii-panel .row:last-child div', e => e.map(x => x.textContent.replace(/ x$/, '').trim()));
  assert.deepStrictEqual(edits, ['@bar:low: red fill']);
  await p.close();
});

test('alt+click selects parent, shift+click adds', async b => {
  const p = await b.newPage({ viewport: { width: 960, height: 540 } });
  await p.setContent(page('hud-overlay.html'));
  await p.click('#uii-btn');
  await p.keyboard.down('Alt'); await p.mouse.click(75, 504); await p.keyboard.up('Alt');
  assert.deepStrictEqual(await selected(p), ['hud.layer.health-bar']);
  await p.keyboard.down('Shift'); await p.mouse.click(900, 495); await p.keyboard.up('Shift');
  assert.deepStrictEqual(await selected(p), ['hud.layer.health-bar', 'hud.layer.ammo']);
  assert.strictEqual(await field(p), 'hud.layer.health-bar, hud.layer.ammo');
  await p.close();
});

test('move panel uncovers the bottom-right corner', async b => {
  const p = await b.newPage({ viewport: { width: 1920, height: 1080 } });
  await p.setContent(page('hud-overlay.html'));
  await p.click('#uii-btn');
  await p.mouse.click(1800, 990);
  assert.deepStrictEqual(await selected(p), [], 'panel should cover the ammo counter first');
  await p.click('[data-a=dock]');
  await p.mouse.click(1800, 990);
  assert.deepStrictEqual(await selected(p), ['hud.layer.ammo']);
  await p.close();
});

test('background test covers the backdrop and keeps picking', async b => {
  const p = await b.newPage({ viewport: { width: 960, height: 540 } });
  await p.setContent(page('hud-backdrop.html'));
  await p.click('#uii-btn');
  for (const k of ['bright', 'busy', 'mid-gray', 'dark']) {
    await p.selectOption('#uii-bg', k);
    assert.strictEqual(await p.$$eval('.uii-bgtest', e => e.length), 1, k);
    await p.mouse.click(75, 504);
    assert.deepStrictEqual(await selected(p), ['hud.layer.health-bar.fill'], k);
  }
  await p.selectOption('#uii-bg', 'original');
  assert.strictEqual(await p.$$eval('.uii-bgtest', e => e.length), 0);
  await p.close();
});

test('motion controls: speed, reduced motion, replay', async b => {
  const p = await b.newPage({ viewport: { width: 960, height: 540 } });
  await p.setContent(page('hud-overlay.html'));
  await p.evaluate(() => { window.__replayed = null; window.uiiReplay = ids => { window.__replayed = ids; }; });
  await p.click('#uii-btn');
  await p.selectOption('#uii-speed', '0.25');
  assert.strictEqual(await p.evaluate(() => document.documentElement.style.getPropertyValue('--motion-slow')), '0.25');
  await p.click('[data-a=reduced]');
  assert.strictEqual(await p.evaluate(() => document.documentElement.hasAttribute('data-reduced-motion')), true);
  await p.mouse.click(210, 504);
  await p.click('[data-a=replay]');
  assert.deepStrictEqual(await p.evaluate(() => window.__replayed), ['hud.layer.health-bar']);
  await p.close();
});

test('inspect mode blocks clicks on the mockup', async b => {
  const p = await b.newPage({ viewport: { width: 960, height: 540 } });
  await p.setContent(page('hud-overlay.html'));
  await p.evaluate(() => { window.__clicks = 0; document.getElementById('stage').addEventListener('click', () => window.__clicks++); });
  await p.click('#uii-btn');
  await p.mouse.click(210, 504);
  assert.strictEqual(await p.evaluate(() => window.__clicks), 0);
  await p.close();
});

test('page CSS for .row, .flex, button etc. does not break the panel', async b => {
  const p = await b.newPage({ viewport: { width: 960, height: 540 } });
  await p.setContent(page('hostile-css.html'));
  await p.click('#uii-btn');
  await p.click('text=Click me');
  await p.fill('#uii-note', 'x');
  await p.click('[data-a=add]');
  const r = await p.$eval('#uii-panel', el => ({
    over: el.scrollWidth - el.clientWidth,
    rows: [...el.children].map(c => getComputedStyle(c).display),
    copy: el.querySelector('[data-a=copy]').getBoundingClientRect().right <= el.getBoundingClientRect().right
  }));
  assert.strictEqual(r.over, 0, 'panel scrolls horizontally');
  assert.ok(r.rows.every(d => d === 'block' || d === 'flex'), r.rows.join());
  assert.ok(r.copy, 'Copy edits is clipped');
  await p.close();
});

(async () => {
  const b = await chromium.launch(process.env.CHROMIUM_PATH ? { executablePath: process.env.CHROMIUM_PATH } : {});
  let failed = 0;
  for (const t of tests) {
    try { await t.fn(b); console.log(`ok   ${t.name}`); }
    catch (e) { failed++; console.log(`FAIL ${t.name}\n     ${e.message.split('\n')[0]}`); }
  }
  await b.close();
  console.log(failed ? `\n${failed} test(s) failed.` : `\nAll ${tests.length} browser tests passed.`);
  process.exit(failed ? 1 : 0);
})();
