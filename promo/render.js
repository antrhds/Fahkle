// usage: node render.js stills 0.5,1.2,...   |   node render.js video out.mp4 [sub] [audio.wav]
const { chromium } = require('/opt/node22/lib/node_modules/playwright');
const { spawn } = require('child_process');
const path = require('path');
const FFMPEG = process.env.FFMPEG || 'ffmpeg';

(async () => {
  const [mode, arg, subArg, audio] = process.argv.slice(2);
  const browser = await chromium.launch({ args: ['--allow-file-access-from-files'] });
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
  page.on('console', m => console.log('[page]', m.text()));
  page.on('pageerror', e => { console.error('[pageerror]', e); process.exit(1); });
  await page.goto('file://' + path.join(__dirname, 'scene.html'));
  console.log('particles', await page.evaluate(() => window.ready));
  if (mode === 'stills') {
    for (const ts of arg.split(',')) {
      const f = Math.round(parseFloat(ts) * 60);
      await page.evaluate(f => window.renderFrame(f, 1), f);
      await page.screenshot({ path: path.join(__dirname, 'stills', `t${ts}.png`) });
    }
  } else {
    const sub = parseInt(subArg || '4');
    const outArgs = ['-y', '-f', 'rawvideo', '-pix_fmt', 'rgba', '-s', '1920x1080', '-r', '60', '-i', '-'];
    if (audio) outArgs.push('-i', audio);
    outArgs.push('-c:v', 'libx264', '-preset', 'slow', '-crf', '15', '-pix_fmt', 'yuv420p', '-profile:v', 'high', '-movflags', '+faststart');
    if (audio) outArgs.push('-c:a', 'aac', '-b:a', '256k', '-shortest');
    outArgs.push(arg);
    const ff = spawn(FFMPEG, outArgs, { stdio: ['pipe', 'ignore', 'inherit'] });
    const t0 = Date.now();
    for (let f = 0; f < 900; f++) {
      const b64 = await page.evaluate(async ([f, sub]) => { window.renderFrame(f, sub); return await window.grab(); }, [f, sub]);
      const buf = Buffer.from(b64, 'base64');
      if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
      if (f % 60 === 0) console.log(`frame ${f} ${((Date.now() - t0) / 1000).toFixed(1)}s`);
    }
    ff.stdin.end();
    await new Promise(r => ff.on('close', r));
  }
  await browser.close();
})();
