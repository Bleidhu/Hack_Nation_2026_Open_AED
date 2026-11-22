// Checks a rendered video and lays it out for inspection.
//   node tools/qa.mjs [out/demo.mp4] [--expect 1920x1080@60] [--every 5]
// Automatic: container and stream properties, blank frames, where the cuts are, long motionless stretches.
// For your eyes (out/qa/): overview sheets every few seconds and a strip of consecutive frames across every cut.
// Exit code 1 if an automatic check fails. Passing them does not mean the video is good — look at the images.
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {closeTiler, ROOT, burst, clock, grab, parseArgs, probe, rel, run, sheets} from './util.mjs';

const {opts, rest} = parseArgs();
const video = path.resolve(rest[0] || path.join(ROOT, 'out', 'demo.mp4'));
if (!fs.existsSync(video)) { console.error(`No video at ${video}. Run \`npm run render\` first.`); await closeTiler(); process.exit(1); }
const outDir = path.resolve(opts.out || path.join(ROOT, 'out', 'qa'));
fs.rmSync(outDir, {recursive: true, force: true});
fs.mkdirSync(outDir, {recursive: true});

let failed = 0;
const pass = msg => console.log(`  ok    ${msg}`);
const fail = msg => { failed++; console.log(`  FAIL  ${msg}`); };
const note = msg => console.log(`  note  ${msg}`);

// 1. The file is what was asked for.
const v = probe(video);
const [, ew, eh, efps] = /^(\d+)x(\d+)@(\d+(?:\.\d+)?)$/.exec(String(opts.expect || '1920x1080@60')) || [];
console.log(`${rel(video)}: ${v.width}x${v.height}, ${v.fps} fps, ${clock(v.duration)} (${v.frames} frames), ${v.codec}/${v.pixFmt}, ${(v.bytes / 2 ** 20).toFixed(1)} MB`);
v.width === Number(ew) && v.height === Number(eh) ? pass(`size ${ew}x${eh}`) : fail(`size is ${v.width}x${v.height}, expected ${ew}x${eh}`);
Math.abs(v.fps - Number(efps)) < 0.01 ? pass(`${efps} fps`) : fail(`frame rate is ${v.fps}, expected ${efps}`);
v.codec === 'h264' && v.pixFmt === 'yuv420p' ? pass('H.264 / yuv420p (plays everywhere)') : fail(`codec ${v.codec}/${v.pixFmt}: use H.264 yuv420p for players and chat apps`);
Math.abs(v.frames / v.fps - v.duration) < 0.1 ? pass('frame count matches duration') : fail(`${v.frames} frames at ${v.fps} fps is not ${v.duration}s — the render was interrupted?`);
note(v.audio ? 'has an audio track' : 'no audio track');

// 2. One decode pass: blank frames, cuts, motionless stretches. The bundled FFmpeg has no blackdetect,
// freezedetect or scene filters, so every frame is decoded to a tiny grey image and measured here instead.
const GW = 64, GH = 36, N = GW * GH;
// Raw grey frames wrapped in AVI (the bundled FFmpeg has no `rawvideo` muxer); each frame is a '00db' chunk.
const avi = run('ffmpeg', ['-hide_banner', '-loglevel', 'error', '-i', video, '-an', '-vf', `scale=${GW}:${GH}:flags=area,format=gray`,
  '-c:v', 'rawvideo', '-pix_fmt', 'gray', '-f', 'avi', '-'], {encoding: 'buffer'}).stdout;
const chunks = [];
for (let i = 0; i + 8 + N <= avi.length;) {
  if (avi[i] === 0x30 && avi[i + 1] === 0x30 && avi[i + 2] === 0x64 && (avi[i + 3] === 0x62 || avi[i + 3] === 0x63) && avi.readUInt32LE(i + 4) === N) {
    chunks.push(avi.subarray(i + 8, i + 8 + N)); i += 8 + N;
  } else i++;
}
const raw = Buffer.concat(chunks);
const count = chunks.length;
count === v.frames ? pass(`decoded all ${count} frames for analysis`) : note(`decoded ${count} of ${v.frames} frames for analysis`);
const stats = [], diffs = [0];
for (let k = 0; k < count; k++) {
  let sum = 0, sq = 0, d = 0;
  for (let p = k * N; p < (k + 1) * N; p++) {
    const x = raw[p]; sum += x; sq += x * x;
    if (k) d += Math.abs(x - raw[p - N]);
  }
  const mean = sum / N;
  stats.push({mean, sd: Math.sqrt(Math.max(0, sq / N - mean * mean))});
  if (k) diffs.push(d / N);
}
const t = k => k / v.fps;
// blank: a uniform dark frame (as blackdetect: footage missing, the window body is black). A uniform light
// frame is the flat stage at the first frame of a part's entrance: reported, not failed.
const runs = pred => { const out = []; for (let k = 0; k < count; k++) if (pred(stats[k])) { const last = out.at(-1); if (last && last[1] === k - 1) last[1] = k; else out.push([k, k]); } return out; };
const span = rs => rs.map(b => `${clock(t(b[0]))}–${clock(t(b[1]))}`).join(', ');
const black = runs(st => st.sd < 1.5 && st.mean < 40), stage = runs(st => st.sd < 1.5 && st.mean >= 40);
black.length ? fail(`blank frames at ${span(black)} — footage missing or not loaded at a clip boundary`) : pass('no blank (black) frames');
if (stage.length) note(`uniform light frames (flat stage) at ${span(stage)} — expected only at the start of a part`);
// cuts: a frame that differs from the previous one far more than motion does
const cuts = [];
for (let k = 1; k < count; k++) if (diffs[k] > Number(opts.scene || 18) && (!cuts.length || t(k) - cuts.at(-1) > 0.25)) cuts.push(t(k));
// motionless: 4 s or more with (almost) no change
let run0 = null;
const freezes = [];
for (let k = 1; k <= count; k++) {
  const still = k < count && diffs[k] < 0.02;
  if (still && run0 === null) run0 = k;
  if (!still && run0 !== null) { if ((k - run0) / v.fps >= 4) freezes.push([t(run0), (k - run0) / v.fps]); run0 = null; }
}
for (const [s0, d] of freezes) note(`nothing moves for ${d.toFixed(1)} s from ${clock(s0)} — fine if a caption is typing or the viewer is meant to read; otherwise footage has stalled`);

// 3. For your eyes.
const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'qa-'));

const every = Number(opts.every || 5);
const times = Array.from({length: Math.ceil(v.duration / every)}, (_, i) => (i + 0.5) * every).filter(t => t < v.duration);
const items = times.map((t, i) => { const file = path.join(tmp, `g${i}.png`); grab(video, t, file); return {file, label: clock(t)}; });
console.log('\nOverview (reading order):');
for (const s of await sheets(items, outDir, 'overview')) console.log(`  ${rel(s.file)}: ${s.items.map(i => i.label).join(' | ')}`);
console.log(`\n${cuts.length} abrupt picture change(s) (cuts between parts or clips, or content that changes all at once):`);
for (const t of cuts.slice(0, Number(opts.cuts || 24))) {
  const file = path.join(outDir, `cut-${t.toFixed(2).padStart(7, '0')}.jpg`);
  await burst(video, t - 6 / v.fps, file, {count: 12, cols: 6});
  console.log(`  ${rel(file)}: 6 frames before and after ${clock(t)}`);
}
fs.rmSync(tmp, {recursive: true, force: true});

console.log(failed ? `\n${failed} automatic check(s) FAILED.` : '\nAutomatic checks passed. Now open the images above and go through docs/QA.md — these checks cannot see a wrong zoom target, a clipped caption or a cursor in the wrong place.');
await closeTiler(); process.exit(failed ? 1 : 0);
