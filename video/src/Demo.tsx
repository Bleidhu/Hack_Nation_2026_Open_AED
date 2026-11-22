// Kolejność części wideo. Długość całości wynika z sumy.
import React from 'react';
import {Series} from 'remotion';
import {COPY} from './copy';
import {Card, CARD_FRAMES, Intro, INTRO_FRAMES, Outro, OUTRO_FRAMES} from './scenes/Cards';
import {Dostawca, DOSTAWCA_FRAMES} from './scenes/Dostawca';
import {Odbiorca, ODBIORCA_FRAMES} from './scenes/Odbiorca';
import {Prototyp, PROTOTYP_FRAMES} from './scenes/Prototyp';

const PARTS: [name: string, node: React.ReactNode, frames: number][] = [
  ['intro', <Intro />, INTRO_FRAMES],
  ['card 01', <Card {...COPY.dostawca.card} />, CARD_FRAMES],
  ['dostawca', <Dostawca />, DOSTAWCA_FRAMES],
  ['card 02', <Card {...COPY.odbiorca.card} />, CARD_FRAMES],
  ['odbiorca', <Odbiorca />, ODBIORCA_FRAMES],
  ['card 03', <Card {...COPY.prototyp.card} />, CARD_FRAMES],
  ['prototyp', <Prototyp />, PROTOTYP_FRAMES],
  ['outro', <Outro />, OUTRO_FRAMES],
];
export const DEMO_FRAMES = PARTS.reduce((n, p) => n + p[2], 0);
/** Name, first frame and length of each part. Passed as a prop only so the tools can print a map of the video. */
export const PART_MAP = PARTS.map((p, i) => ({name: p[0], start: PARTS.slice(0, i).reduce((n, q) => n + q[2], 0), frames: p[2]}));

export const Demo: React.FC<{parts?: typeof PART_MAP}> = () => (
  <Series>
    {PARTS.map(([name, node, frames]) => (
      <Series.Sequence key={name} durationInFrames={frames}>{node}</Series.Sequence>
    ))}
  </Series>
);
