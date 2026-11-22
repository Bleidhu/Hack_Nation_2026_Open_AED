// Shared by the tools: running ffmpeg/ffprobe, grabbing frames, tiling images into contact sheets.
import {spawnSync} from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {fileURLToPath, pathToFileURL} from 'node:url';
import {FFMPEG, FFPROBE} from './ff.mjs';

export const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');

export function run(cmd, args, {allowFail = false, encoding = 'utf8'} = {}) {
  const bin = cmd === 'ffmpeg' ? FFMPEG : cmd === 'ffprobe' ? FFPROBE : cmd;
  const r = spawnSync(bin, args, {encoding, maxBuffer: 1024 * 1024 * 1024});
  if (r.error) throw new Error(`${cmd} could not be started (${r.error.code}). Is it installed and on PATH?`);
  if (r.status !== 0 && !allowFail) throw new Error(`${cmd} ${args.join(' ')}\n${r.stderr.slice(-2000)}`);
  return r;
}

/** Arguments of the form `--name value` and bare words. */
export function parseArgs(argv = process.argv.slice(2)) {
  const opts = {}, rest = [];
  for (let i = 0; i < argv.length; i++) {
    if (argv[i].startsWith('--')) { const k = argv[i].slice(2); opts[k] = argv[i + 1] && !argv[i + 1].startsWith('--') ? argv[++i] : true; }
    else rest.push(argv[i]);
  }
  return {opts, rest};
}

export function probe(video) {
  const r = run('ffprobe', ['-v', 'error', '-show_streams', '-show_format', '-of', 'json', video]);
  const j = JSON.parse(r.stdout), v = j.streams.find(s => s.codec_type === 'video');
  const [n, d] = v.r_frame_rate.split('/').map(Number);
  return {
    width: v.width, height: v.height, fps: n / d, codec: v.codec_name, pixFmt: v.pix_fmt, frames: Number(v.nb_frames),
    duration: Number(j.format.duration), bytes: Number(j.format.size), audio: j.streams.some(s => s.codec_type === 'audio'),
  };
}

/** One frame of a video at `t` seconds, scaled to `width`. */
export function grab(video, t, out, width = 960) {
  run('ffmpeg', ['-y', '-loglevel', 'error', '-ss', String(Math.max(0, t)), '-i', video, '-frames:v', '1', '-update', '1',
    '-vf', `scale=${width}:-2`, out]);
}

/** `count` consecutive frames starting at `t`, tiled in one image: the way to look at motion without a player. */
export async function burst(video, t, out, {count = 12, cols = 6, width = 480} = {}) {
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'burst-'));
  run('ffmpeg', ['-y', '-loglevel', 'error', '-ss', String(Math.max(0, t)), '-i', video, '-frames:v', String(count),
    '-vf', `scale=${width}:-2`, '-q:v', '3', path.join(tmp, 'b-%03d.jpg')]);
  const files = fs.readdirSync(tmp).sort().map(f => path.join(tmp, f));
  await tile(files, out, {cols, width});
  fs.rmSync(tmp, {recursive: true, force: true});
}

/**
 * Tiles image files (same size, any names) into one contact sheet, reading order left to right, top to bottom.
 * The bundled FFmpeg has no `tile` filter, so Chromium lays the images out and takes the screenshot.
 */
let browser = null;
export async function tile(files, out, {cols = 2, width = 960} = {}) {
  const {chromium} = await import('playwright-core');
  const {chromePath} = await import('../capture/lib.mjs');
  browser ??= await chromium.launch({executablePath: chromePath()});
  const cell = width;  // each image is scaled to `width`, as the ffmpeg `scale=W:-2,tile=` version did
  const html = `<!doctype html><body style="margin:0;background:#000;display:grid;grid-template-columns:repeat(${cols},${cell}px);gap:0">`
    + files.map(f => `<img style="width:${cell}px;display:block" src="${pathToFileURL(f).href}">`).join('') + '</body>';
  const page = await browser.newPage({viewport: {width: cell * cols, height: 200}});
  const tmp = path.join(os.tmpdir(), `sheet-${process.pid}-${Date.now()}.html`);
  fs.writeFileSync(tmp, html);
  await page.goto(pathToFileURL(tmp).href);
  await page.waitForFunction(() => [...document.images].every(i => i.complete));
  fs.mkdirSync(path.dirname(out), {recursive: true});
  await page.screenshot({path: out, fullPage: true, type: 'jpeg', quality: 85});
  await page.close();
  fs.rmSync(tmp, {force: true});
}
export async function closeTiler() { await browser?.close(); browser = null; }

/** Splits `items` into sheets of `per`, tiles each, and returns [{file, items}] so the caller can say what is where. */
export async function sheets(items, dir, prefix, {per = 6, cols = 2, width = 960} = {}) {
  const out = [];
  for (let i = 0; i < items.length; i += per) {
    const part = items.slice(i, i + per), file = path.join(dir, `${prefix}-${String(i / per + 1).padStart(2, '0')}.jpg`);
    await tile(part.map(p => p.file), file, {cols, width});
    out.push({file, items: part});
  }
  return out;
}

export const rel = p => path.relative(process.cwd(), p) || '.';
export const clock = s => `${Math.floor(s / 60)}:${(s % 60).toFixed(1).padStart(4, '0')}`;
