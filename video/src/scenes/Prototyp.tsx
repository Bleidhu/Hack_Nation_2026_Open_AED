// Scena 3: prototyp offline dla jury (demo/index.html otwarty z dysku).
import React from 'react';
import capJson from '../../public/captures/prototyp.json';
import {at, clickAt, cutting, rectOf, timeline, type Capture, type Shot} from '../capture';
import {Appear, Captions, Stage} from '../chrome';
import {COPY} from '../copy';
import {Footage} from '../Footage';

const cap = capJson as unknown as Capture;
const T = COPY.prototyp;

const krok4 = clickAt(cap, 0), schemat = at(cap, 'schemat'), krok5 = clickAt(cap, 1), wybrano = at(cap, 'wybrano');
const scroll = at(cap, 'scroll-start'), mapa = at(cap, 'mapa'), wiersz = at(cap, 'wiersz'), rekord = clickAt(cap, 2);
const szczegoly = at(cap, 'szczegoly'), powrot = at(cap, 'scroll-start', 2), krok7 = clickAt(cap, 3), zmiany = at(cap, 'zmiany');

// Długie przewijanie z powrotem do menu kroków wycięte (zmiana tematu: obraz przygasa).
const tl = timeline(cutting(at(cap, 'start') + 0.05, cap.duration - 0.3, [{from: powrot - 0.05, to: krok7 - 0.7}]));
export const PROTOTYP_FRAMES = tl.frames;

const shots: Shot[] = [
  {t: 0},
  {t: krok4 - 0.7},
  {t: schemat + 0.1, rect: rectOf(cap, 'schemat'), maxZoom: 1.5},
  {t: krok5 - 0.7},
  {t: wybrano - 0.6, rect: rectOf(cap, 'wybrano'), maxZoom: 1.6},
  {t: scroll - 0.3},
  {t: mapa + 0.2, rect: rectOf(cap, 'mapa'), maxZoom: 1.1},
  {t: wiersz, rect: rectOf(cap, 'wiersz'), maxZoom: 1.5},
  {t: szczegoly + 0.1, rect: rectOf(cap, 'pochodzenie'), maxZoom: 1.7},
  {t: krok7 - 0.7, cut: true},
  {t: zmiany + 0.1, rect: rectOf(cap, 'zmiany'), maxZoom: 1.5},
];

const f = tl.frameOf;
const lines = [
  {from: f(0.2), to: f(krok4), text: T.start},
  {from: f(krok4), to: f(krok5), text: T.schemat},
  {from: f(krok5), to: f(wiersz), text: T.filtr},
  {from: f(wiersz), to: f(powrot), text: T.pochodzenie},
  {from: f(krok7 - 0.7), to: tl.frames, text: T.zmiany},
];

const outlines = [
  {from: wybrano + 0.1, to: scroll, rect: rectOf(cap, 'wybrano')},
  {from: wiersz + 0.1, to: rekord, rect: rectOf(cap, 'wiersz')},
  {from: szczegoly + 0.6, to: powrot, rect: rectOf(cap, 'pochodzenie')},
];

export const Prototyp: React.FC = () => (
  <Stage>
    <Appear>
      <Footage capture={cap} tl={tl} shots={shots} outlines={outlines} title={T.window} right="file:// · bez sieci" skipLabel={COPY.skipped} />
      <Captions lines={lines} tag={T.tag} />
    </Appear>
  </Stage>
);
