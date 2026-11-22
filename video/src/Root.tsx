import React from 'react';
import {Composition, staticFile} from 'remotion';
import {loadFont} from '@remotion/fonts';
import {Demo, DEMO_FRAMES, PART_MAP} from './Demo';
import {FPS, H, W} from './theme';

// Krój akcji „Dane (prze)życie”: Atkinson Hyperlegible, SIL Open Font License (public/fonts/OFL.txt).
loadFont({family: 'Atkinson Hyperlegible', url: staticFile('fonts/AtkinsonHyperlegible-Regular.ttf'), weight: '400'});
loadFont({family: 'Atkinson Hyperlegible', url: staticFile('fonts/AtkinsonHyperlegible-Bold.ttf'), weight: '700'});

export const Root: React.FC = () => (
  <Composition id="Demo" component={Demo} durationInFrames={DEMO_FRAMES} fps={FPS} width={W} height={H}
    defaultProps={{parts: PART_MAP}} />
);
