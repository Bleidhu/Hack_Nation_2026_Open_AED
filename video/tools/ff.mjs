// Which ffmpeg/ffprobe to run. On this machine there is no system FFmpeg, so the tools use the binaries that
// ship with Remotion (@remotion/compositor-*), which Remotion itself uses to encode. That build has no `fps`,
// `tile`, `blackdetect`, `freezedetect` or `select` filters; the kit's tools were adapted not to need them
// (capture: output `-r`; sheets: tiled by Chromium; qa: raw grey frames analysed in Node).
// FFMPEG / FFPROBE environment variables override the choice (e.g. a full system FFmpeg).
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const exe = process.platform === 'win32' ? '.exe' : '';

function bundled(name) {
  const dirs = fs.existsSync(path.join(ROOT, 'node_modules', '@remotion'))
    ? fs.readdirSync(path.join(ROOT, 'node_modules', '@remotion')).filter(d => d.startsWith('compositor-')) : [];
  for (const d of dirs) {
    const p = path.join(ROOT, 'node_modules', '@remotion', d, name + exe);
    if (fs.existsSync(p)) return p;
  }
  return null;
}

export const FFMPEG = process.env.FFMPEG || bundled('ffmpeg') || 'ffmpeg';
export const FFPROBE = process.env.FFPROBE || bundled('ffprobe') || 'ffprobe';
