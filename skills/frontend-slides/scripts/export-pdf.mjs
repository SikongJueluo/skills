#!/usr/bin/env node
/**
 * Screenshot an HTML deck and build a PDF, using Chromium's DevTools Protocol.
 *
 * No Playwright, no npm install, no browser download. Chromium/Chrome must be
 * installed; set FRONTEND_SLIDES_CHROMIUM to choose a specific executable.
 *
 * Usage:
 *   node export-pdf.mjs <deck.html> [out.pdf] [--compact] [--png-dir DIR]
 *                        [--viewport 1280x720]
 */

import { spawn } from 'node:child_process';
import { createServer } from 'node:http';
import fs from 'node:fs';
import fsp from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';

const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.htm': 'text/html; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.mjs': 'text/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.gif': 'image/gif',
  '.svg': 'image/svg+xml',
  '.webp': 'image/webp',
  '.avif': 'image/avif',
  '.ico': 'image/x-icon',
  '.woff': 'font/woff',
  '.woff2': 'font/woff2',
  '.ttf': 'font/ttf',
  '.otf': 'font/otf',
  '.mp4': 'video/mp4',
  '.webm': 'video/webm',
};

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function parseArgs(argv) {
  const opts = { input: null, output: null, compact: false, pngDir: null, viewport: null };
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === '--help' || arg === '-h') {
      opts.help = true;
    } else if (arg === '--compact') {
      opts.compact = true;
    } else if (arg === '--png-dir' || arg === '--viewport') {
      const value = argv[++i];
      if (!value) throw new Error(`${arg} needs a value`);
      if (arg === '--png-dir') opts.pngDir = value;
      else opts.viewport = value;
    } else if (arg.startsWith('--png-dir=')) {
      opts.pngDir = arg.slice('--png-dir='.length);
    } else if (arg.startsWith('--viewport=')) {
      opts.viewport = arg.slice('--viewport='.length);
    } else if (arg.startsWith('-')) {
      throw new Error(`unknown option: ${arg}`);
    } else if (!opts.input) {
      opts.input = arg;
    } else if (!opts.output) {
      opts.output = arg;
    } else {
      throw new Error(`unexpected argument: ${arg}`);
    }
  }
  return opts;
}

function usage() {
  return `Usage: node export-pdf.mjs <deck.html> [out.pdf] [options]

Options:
  --compact           Render at 1280x720 instead of 1920x1080
  --png-dir DIR       Save one PNG per slide (verification mode)
  --viewport WxH      Screenshot viewport, e.g. 1280x720 or 390x844
  -h, --help          Show this help

Environment:
  FRONTEND_SLIDES_CHROMIUM   Path to a Chromium/Chrome executable`;
}

function findOnPath(name) {
  const exts = process.platform === 'win32' ? ['.exe', '.cmd', '.bat', ''] : [''];
  for (const dir of (process.env.PATH || '').split(path.delimiter)) {
    if (!dir) continue;
    for (const ext of exts) {
      const candidate = path.join(dir, name + ext);
      try {
        fs.accessSync(candidate, fs.constants.X_OK);
        return candidate;
      } catch {
        // keep looking
      }
    }
  }
  return null;
}

function findBrowser() {
  const override = process.env.FRONTEND_SLIDES_CHROMIUM;
  if (override) {
    try {
      fs.accessSync(override, fs.constants.X_OK);
      return override;
    } catch {
      throw new Error(`FRONTEND_SLIDES_CHROMIUM is not executable: ${override}`);
    }
  }

  const absolute = [];
  if (process.platform === 'darwin') {
    absolute.push(
      '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
      '/Applications/Chromium.app/Contents/MacOS/Chromium',
      '/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge',
    );
  } else if (process.platform === 'win32') {
    for (const root of [process.env.PROGRAMFILES, process.env['PROGRAMFILES(X86)'], process.env.LOCALAPPDATA]) {
      if (!root) continue;
      absolute.push(
        path.join(root, 'Google', 'Chrome', 'Application', 'chrome.exe'),
        path.join(root, 'Chromium', 'Application', 'chrome.exe'),
        path.join(root, 'Microsoft', 'Edge', 'Application', 'msedge.exe'),
      );
    }
  } else {
    absolute.push(
      '/usr/bin/chromium',
      '/usr/bin/chromium-browser',
      '/usr/bin/google-chrome',
      '/usr/bin/google-chrome-stable',
      '/run/current-system/sw/bin/chromium',
    );
  }

  for (const candidate of absolute) {
    try {
      fs.accessSync(candidate, fs.constants.X_OK);
      return candidate;
    } catch {
      // keep looking
    }
  }

  for (const name of ['chromium', 'chromium-browser', 'google-chrome', 'google-chrome-stable', 'chrome', 'msedge']) {
    const found = findOnPath(name);
    if (found) return found;
  }

  throw new Error(
    'No Chromium/Chrome executable found. Install one or set FRONTEND_SLIDES_CHROMIUM to its path.',
  );
}

class CDP {
  constructor(url) {
    this.url = url;
    this.ws = null;
    this.nextId = 1;
    this.pending = new Map();
  }

  connect() {
    return new Promise((resolve, reject) => {
      this.ws = new WebSocket(this.url);
      const timer = setTimeout(() => reject(new Error('timed out connecting to Chromium DevTools')), 10000);
      this.ws.onopen = () => {
        clearTimeout(timer);
        resolve();
      };
      this.ws.onerror = () => {
        clearTimeout(timer);
        reject(new Error('failed to connect to Chromium DevTools'));
      };
      this.ws.onmessage = (event) => {
        const message = JSON.parse(String(event.data));
        if (message.id && this.pending.has(message.id)) {
          const { resolve: done, reject: fail, timer: requestTimer } = this.pending.get(message.id);
          this.pending.delete(message.id);
          clearTimeout(requestTimer);
          if (message.error) fail(new Error(`${message.error.message || 'CDP error'} (${JSON.stringify(message.error)})`));
          else done(message.result);
        }
      };
      this.ws.onclose = () => {
        for (const { reject: fail, timer: requestTimer } of this.pending.values()) {
          clearTimeout(requestTimer);
          fail(new Error('Chromium DevTools connection closed'));
        }
        this.pending.clear();
      };
    });
  }

  send(method, params = {}, sessionId = null, timeoutMs = 30000) {
    return new Promise((resolve, reject) => {
      const id = this.nextId++;
      const timer = setTimeout(() => {
        this.pending.delete(id);
        reject(new Error(`CDP timeout: ${method}`));
      }, timeoutMs);
      this.pending.set(id, { resolve, reject, timer });
      const message = { id, method, params };
      if (sessionId) message.sessionId = sessionId;
      this.ws.send(JSON.stringify(message));
    });
  }

  close() {
    if (this.ws) {
      try { this.ws.close(); } catch { /* ignore */ }
      this.ws = null;
    }
  }
}

async function startServer(rootDir, htmlFile) {
  const root = await fsp.realpath(rootDir);
  const server = createServer(async (req, res) => {
    try {
      const pathname = decodeURIComponent(new URL(req.url, 'http://127.0.0.1').pathname);
      const relative = pathname === '/' ? htmlFile : pathname.replace(/^\/+/, '');
      const candidate = path.resolve(root, relative);
      if (candidate !== root && !candidate.startsWith(root + path.sep)) {
        res.writeHead(404, { 'Content-Type': 'text/plain; charset=utf-8' });
        res.end('Not found');
        return;
      }
      const real = await fsp.realpath(candidate);
      if (real !== root && !real.startsWith(root + path.sep)) {
        res.writeHead(404, { 'Content-Type': 'text/plain; charset=utf-8' });
        res.end('Not found');
        return;
      }
      const content = await fsp.readFile(real);
      res.writeHead(200, {
        'Content-Type': MIME[path.extname(real).toLowerCase()] || 'application/octet-stream',
        'Cache-Control': 'no-store',
      });
      res.end(content);
    } catch {
      res.writeHead(404, { 'Content-Type': 'text/plain; charset=utf-8' });
      res.end('Not found');
    }
  });

  await new Promise((resolve, reject) => {
    server.once('error', reject);
    server.listen(0, '127.0.0.1', resolve);
  });
  return { server, root, port: server.address().port };
}

async function launchBrowser(browserPath, tempDir) {
  const profileDir = path.join(tempDir, 'profile');
  await fsp.mkdir(profileDir, { recursive: true });
  const args = [
    '--headless=new',
    '--remote-debugging-port=0',
    `--user-data-dir=${profileDir}`,
    '--no-first-run',
    '--no-default-browser-check',
    '--disable-gpu',
    '--hide-scrollbars',
    '--mute-audio',
    '--disable-background-networking',
    '--disable-sync',
    '--disable-dev-shm-usage',
    'about:blank',
  ];
  const child = spawn(browserPath, args, { stdio: ['ignore', 'ignore', 'pipe'] });
  let stderr = '';
  child.stderr.on('data', (chunk) => {
    stderr += chunk.toString();
    if (stderr.length > 20000) stderr = stderr.slice(-20000);
  });

  const portFile = path.join(profileDir, 'DevToolsActivePort');
  const deadline = Date.now() + 20000;
  while (Date.now() < deadline) {
    if (fs.existsSync(portFile)) break;
    if (child.exitCode !== null) {
      throw new Error(`Chromium exited during startup (code ${child.exitCode}).\n${stderr.trim()}`);
    }
    await sleep(100);
  }
  if (!fs.existsSync(portFile)) {
    throw new Error(`Chromium did not expose DevTools within 20s.\n${stderr.trim()}`);
  }

  const [port, wsPath] = (await fsp.readFile(portFile, 'utf8')).trim().split('\n');
  return { child, stderr, url: `ws://127.0.0.1:${port}${wsPath}` };
}

async function openPage(cdp, url, viewport) {
  const { targetId } = await cdp.send('Target.createTarget', { url: 'about:blank' });
  const { sessionId } = await cdp.send('Target.attachToTarget', { targetId, flatten: true });
  await cdp.send('Page.enable', {}, sessionId);
  await cdp.send('Runtime.enable', {}, sessionId);
  await cdp.send(
    'Emulation.setDeviceMetricsOverride',
    { width: viewport.width, height: viewport.height, deviceScaleFactor: 1, mobile: false },
    sessionId,
  );
  await cdp.send('Page.navigate', { url }, sessionId);

  const deadline = Date.now() + 20000;
  while (Date.now() < deadline) {
    const { result } = await cdp.send(
      'Runtime.evaluate',
      { expression: 'document.readyState', returnByValue: true },
      sessionId,
    );
    if (result.value === 'complete') break;
    await sleep(100);
  }

  // Give the deck a moment to install its own controller.
  await sleep(300);
  const { result } = await cdp.send(
    'Runtime.evaluate',
    {
      expression: `(() => {
        if (window.deck && typeof window.deck.goToSlide === 'function') return 'native';
        const slides = Array.from(document.querySelectorAll('.slide'));
        window.deck = {
          get count() { return slides.length; },
          get index() { return Math.max(0, slides.findIndex((s) => s.classList.contains('active'))); },
          goToSlide(i) {
            slides.forEach((slide, n) => {
              slide.classList.toggle('active', n === i);
              slide.classList.toggle('visible', n === i);
            });
            return new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve)));
          },
          ready: Promise.resolve(),
        };
        return 'fallback';
      })()`,
      returnByValue: true,
    },
    sessionId,
  );

  await cdp.send(
    'Runtime.evaluate',
    {
      expression: `(async () => {
        await document.fonts.ready;
        if (window.deck && window.deck.ready) await window.deck.ready;
        return true;
      })()`,
      awaitPromise: true,
      returnByValue: true,
    },
    sessionId,
    30000,
  );

  return { targetId, sessionId, mode: result.value };
}

async function evaluate(cdp, sessionId, expression, { awaitPromise = false, timeoutMs = 30000 } = {}) {
  const { result, exceptionDetails } = await cdp.send(
    'Runtime.evaluate',
    { expression, awaitPromise, returnByValue: true },
    sessionId,
    timeoutMs,
  );
  if (exceptionDetails) {
    throw new Error(exceptionDetails.exception?.description || exceptionDetails.text || 'page evaluation failed');
  }
  return result.value;
}

function makePdf(images, pageWidth, pageHeight) {
  const objects = [];
  const kids = [];
  for (let i = 0; i < images.length; i += 1) kids.push(`${3 + i * 3} 0 R`);

  objects.push(Buffer.from('<< /Type /Catalog /Pages 2 0 R >>'));
  objects.push(Buffer.from(`<< /Type /Pages /Kids [${kids.join(' ')}] /Count ${images.length} >>`));

  images.forEach((image, i) => {
    const pageId = 3 + i * 3;
    const contentId = pageId + 1;
    const imageId = pageId + 2;
    objects.push(Buffer.from(
      `<< /Type /Page /Parent 2 0 R /MediaBox [0 0 ${pageWidth} ${pageHeight}] ` +
      `/Resources << /XObject << /Im0 ${imageId} 0 R >> >> /Contents ${contentId} 0 R >>`,
    ));
    const content = `q\n${pageWidth} 0 0 ${pageHeight} 0 0 cm\n/Im0 Do\nQ\n`;
    objects.push(Buffer.from(`<< /Length ${Buffer.byteLength(content)} >>\nstream\n${content}endstream`));
    objects.push(Buffer.concat([
      Buffer.from(
        `<< /Type /XObject /Subtype /Image /Width ${image.width} /Height ${image.height} ` +
        `/ColorSpace /DeviceRGB /BitsPerComponent 8 /Filter /DCTDecode /Length ${image.jpeg.length} >>\nstream\n`,
      ),
      image.jpeg,
      Buffer.from('\nendstream'),
    ]));
  });

  const parts = [];
  let offset = 0;
  const push = (buffer) => {
    parts.push(buffer);
    offset += buffer.length;
  };
  push(Buffer.from('%PDF-1.4\n%\xE2\xE3\xCF\xD3\n', 'binary'));

  const offsets = [];
  objects.forEach((object, index) => {
    offsets[index] = offset;
    push(Buffer.from(`${index + 1} 0 obj\n`));
    push(object);
    push(Buffer.from('\nendobj\n'));
  });

  const xrefOffset = offset;
  let xref = `xref\n0 ${objects.length + 1}\n0000000000 65535 f \n`;
  for (const objectOffset of offsets) {
    xref += `${String(objectOffset).padStart(10, '0')} 00000 n \n`;
  }
  xref += `trailer\n<< /Size ${objects.length + 1} /Root 1 0 R >>\nstartxref\n${xrefOffset}\n%%EOF\n`;
  push(Buffer.from(xref, 'utf8'));

  return Buffer.concat(parts);
}

async function stopBrowser(child) {
  if (!child || child.exitCode !== null) return;
  child.kill('SIGTERM');
  const deadline = Date.now() + 3000;
  while (child.exitCode === null && Date.now() < deadline) await sleep(100);
  if (child.exitCode === null) child.kill('SIGKILL');
}

async function main() {
  const opts = parseArgs(process.argv.slice(2));
  if (opts.help) {
    console.log(usage());
    return;
  }
  if (!opts.input) throw new Error(`missing input HTML\n\n${usage()}`);

  const inputPath = path.resolve(opts.input);
  const stat = await fsp.stat(inputPath).catch(() => null);
  if (!stat || !stat.isFile()) throw new Error(`cannot read HTML file: ${inputPath}`);

  let viewport = opts.compact ? { width: 1280, height: 720 } : { width: 1920, height: 1080 };
  if (opts.viewport) {
    const match = /^(\d+)x(\d+)$/i.exec(opts.viewport);
    if (!match) throw new Error(`--viewport must look like 1280x720, got: ${opts.viewport}`);
    viewport = { width: Number(match[1]), height: Number(match[2]) };
  }
  if (viewport.width < 200 || viewport.height < 200) throw new Error('viewport is too small');

  const pngDir = opts.pngDir ? path.resolve(opts.pngDir) : null;
  const wantsPdf = Boolean(opts.output) || !pngDir;
  const outputPath = opts.output
    ? path.resolve(opts.output)
    : path.join(path.dirname(inputPath), `${path.basename(inputPath, path.extname(inputPath))}.pdf`);

  if (wantsPdf) await fsp.mkdir(path.dirname(outputPath), { recursive: true });
  if (pngDir) await fsp.mkdir(pngDir, { recursive: true });

  const browserPath = findBrowser();
  const tempDir = await fsp.mkdtemp(path.join(os.tmpdir(), 'frontend-slides-'));
  const htmlFile = path.basename(inputPath);
  let serverInfo = null;
  let browser = null;
  let cdp = null;

  try {
    serverInfo = await startServer(path.dirname(inputPath), htmlFile);
    browser = await launchBrowser(browserPath, tempDir);
    cdp = new CDP(browser.url);
    await cdp.connect();

    const targetUrl =
      `http://127.0.0.1:${serverInfo.port}/${encodeURIComponent(htmlFile)}?export=1`;
    const page = await openPage(cdp, targetUrl, viewport);
    const count = await evaluate(cdp, page.sessionId, `window.deck.count || document.querySelectorAll('.slide').length`);

    if (!Number.isInteger(count) || count <= 0) {
      throw new Error('0 slides found. The deck needs elements with class="slide".');
    }

    const audit = await evaluate(cdp, page.sessionId, `(() => {
      const broken = Array.from(document.images)
        .filter((img) => !img.complete || img.naturalWidth === 0)
        .map((img) => img.getAttribute('src') || '(inline)');
      const overflowing = Array.from(document.querySelectorAll('.slide'))
        .map((slide, index) => ({
          index: index + 1,
          x: slide.scrollWidth - slide.clientWidth,
          y: slide.scrollHeight - slide.clientHeight,
        }))
        .filter((item) => item.x > 1 || item.y > 1);
      return { broken, overflowing };
    })()`);
    if (audit.broken.length) {
      console.warn(`warning: ${audit.broken.length} image(s) failed to load: ${audit.broken.join(', ')}`);
    }
    for (const item of audit.overflowing) {
      console.warn(
        `warning: slide ${item.index} content exceeds the 1920x1080 stage ` +
        `(+${item.x}px wide, +${item.y}px high); inspect the screenshot`,
      );
    }

    console.log(`Rendering ${count} slide(s) at ${viewport.width}x${viewport.height} (${page.mode} controller)`);
    if (pngDir) console.log(`PNG output: ${pngDir}`);

    const pdfImages = [];
    for (let i = 0; i < count; i += 1) {
      await evaluate(
        cdp,
        page.sessionId,
        `(async () => { await window.deck.goToSlide(${i}); await new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r))); return true; })()`,
        { awaitPromise: true },
      );
      // Export mode freezes CSS transitions. This pause also lets simple JS
      // counters settle in decks that do not implement the export contract.
      await sleep(80);

      const stem = `slide-${String(i + 1).padStart(3, '0')}`;
      if (pngDir) {
        const png = await cdp.send(
          'Page.captureScreenshot',
          { format: 'png', fromSurface: true, captureBeyondViewport: false },
          page.sessionId,
        );
        await fsp.writeFile(path.join(pngDir, `${stem}.png`), Buffer.from(png.data, 'base64'));
      }
      if (wantsPdf) {
        const jpeg = await cdp.send(
          'Page.captureScreenshot',
          { format: 'jpeg', quality: 92, fromSurface: true, captureBeyondViewport: false },
          page.sessionId,
        );
        pdfImages.push({
          width: viewport.width,
          height: viewport.height,
          jpeg: Buffer.from(jpeg.data, 'base64'),
        });
      }
      console.log(`  captured ${i + 1}/${count}`);
    }

    if (wantsPdf) {
      const pdf = makePdf(pdfImages, viewport.width / 2, viewport.height / 2);
      await fsp.writeFile(outputPath, pdf);
      const size = (pdf.length / 1024 / 1024).toFixed(1);
      console.log(`PDF: ${outputPath} (${size} MB, ${count} pages)`);
    }
    if (pngDir) console.log(`Screenshots: ${pngDir}`);
  } finally {
    if (cdp) cdp.close();
    if (browser) await stopBrowser(browser.child);
    if (serverInfo) await new Promise((resolve) => serverInfo.server.close(resolve));
    await fsp.rm(tempDir, { recursive: true, force: true });
  }
}

main().catch((error) => {
  console.error(`error: ${error.message}`);
  process.exitCode = 1;
});
