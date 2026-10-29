/** Local deterministic fixture runner. No external URLs, cookies or accounts. */
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const http = require('node:http');
const { createRequire } = require('node:module');

async function run() {
  if (process.argv.includes('--help')) {
    console.log('node browser_qa.cjs --tool-root /path/locked-env --output /tmp/new-directory');
    return;
  }
  const option = name => process.argv[process.argv.indexOf(name) + 1];
  if (!process.argv.includes('--tool-root') || !process.argv.includes('--output')) throw Error('explicit tool root and fresh output required');
  const root = path.resolve(option('--tool-root'));
  const output = path.resolve(option('--output'));
  fs.mkdirSync(output); // Never overwrite an existing output or baseline.
  const requireLocal = createRequire(path.join(root, 'package.json'));
  const { chromium, expect } = requireLocal('@playwright/test');
  const html = fs.readFileSync(path.resolve(__dirname, '../../tools/choms-skills/fixtures/browser.html'));
  const server = http.createServer((req, res) => {
    if (req.url === '/favicon.ico') { res.writeHead(204); res.end(); return; }
    if (req.url !== '/') { res.writeHead(404); res.end(); return; }
    res.writeHead(200, {'Content-Type':'text/html; charset=utf-8'}); res.end(html);
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  let browser;
  let checks = 0;
  try {
    browser = await chromium.launch({headless:true});
    for (const width of [390, 1440]) {
      const context = await browser.newContext({viewport:{width,height:900},reducedMotion:'reduce'});
      const page = await context.newPage();
      const errors = [];
      page.on('pageerror', e => errors.push(e.message));
      page.on('console', message => { if (message.type() === 'error') errors.push(message.text()); });
      await context.route('**/*', route => {
        const url = new URL(route.request().url());
        return url.hostname === '127.0.0.1' ? route.continue() : route.abort();
      });
      await page.goto(`http://127.0.0.1:${server.address().port}/`);
      const status = page.getByRole('status');
      await expect(status).toHaveText('Sin validar'); checks++;
      await page.getByRole('button', {name:'Validar'}).click();
      await expect(status).toHaveText('Sin validar'); checks++;
      await page.getByLabel('Nombre del fixture').fill('sintético');
      await page.keyboard.press('Tab');
      await expect(page.getByRole('button')).toBeFocused(); checks++;
      await page.keyboard.press('Enter');
      await expect(status).toHaveText('Fixture válido'); checks++;
      await page.getByLabel('Nombre del fixture').fill('error');
      await page.getByRole('button').click();
      await expect(status).toHaveText('Error sintético'); checks++;
      expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true); checks++;
      expect(await status.evaluate(el => getComputedStyle(el).transitionDuration)).toBe('0s'); checks++;
      expect(errors).toEqual([]); checks++;
      const first = await page.screenshot({path:path.join(output, `${width}.png`)});
      const repeat = await page.screenshot();
      expect(first.equals(repeat)).toBe(true); checks++;
      // Demonstrate that the visual comparison detects a real change.
      await page.locator('h1').evaluate(el => el.style.color = 'red');
      expect(first.equals(await page.screenshot())).toBe(false); checks++;
      await context.close();
    }
    console.log(JSON.stringify({status:'PASS',checks,viewports:[390,1440],network:'loopback-only',inferences:0}));
  } finally {
    if (browser) await browser.close();
    await new Promise(resolve => server.close(resolve));
  }
}
run().catch(e => { console.error(e.message); process.exitCode = 1; });
