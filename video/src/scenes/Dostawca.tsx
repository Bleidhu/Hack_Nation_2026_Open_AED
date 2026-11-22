// Scena 1: dostawca w panelu. Zbiór oznaczony w „Polach niestandardowych”, potem lista zasobów AED.
import React from 'react';
import capJson from '../../public/captures/dostawca.json';
import {at, clickAt, cutting, part, rectOf, timeline, type Capture, type Shot} from '../capture';
import {Appear, Captions, Stage} from '../chrome';
import {COPY} from '../copy';
import {Footage} from '../Footage';

const cap = capJson as unknown as Capture;
const T = COPY.dostawca;

const scrollDown = at(cap, 'scroll-start'), standard = at(cap, 'standard'), pomoc = at(cap, 'pomoc');
const scrollUp = at(cap, 'scroll-start', 1), menuClick = clickAt(cap, 0), searchClick = clickAt(cap, 1);
const szukaj = at(cap, 'szukaj'), lista = at(cap, 'lista'), wykaz = at(cap, 'wykaz');

// Bez cięć: ładowanie stron panelu trwa poniżej sekundy i zostaje w kadrze.
const tl = timeline(cutting(at(cap, 'zbior') + 0.05, cap.duration - 0.3, []));
export const DOSTAWCA_FRAMES = tl.frames;

const shots: Shot[] = [
  {t: 0},
  {t: 0.5, rect: rectOf(cap, 'zbior'), maxZoom: 1.4},
  {t: scrollDown - 0.4},
  {t: standard - 0.1, rect: rectOf(cap, 'pola'), maxZoom: 1.8},
  {t: pomoc + 0.1, rect: rectOf(cap, 'pomoc'), maxZoom: 1.9},
  {t: scrollUp - 0.4},
  {t: searchClick - 0.6, rect: part(rectOf(cap, 'lista-pusta'), 0, -1.5, 3.2, 3), maxZoom: 1.7},
  {t: szukaj + 0.1},
  {t: lista + 0.4, rect: rectOf(cap, 'lista'), maxZoom: 1.3},
  {t: wykaz + 0.2, rect: rectOf(cap, 'wykaz'), maxZoom: 1.6},
];

const f = tl.frameOf;
const lines = [
  {from: f(0.2), to: f(scrollDown), text: T.zbior},
  {from: f(standard), to: f(pomoc), text: T.standard},
  {from: f(pomoc), to: f(scrollUp + 0.2), text: T.pomoc},
  {from: f(scrollUp + 0.2), to: f(lista), text: T.zasoby},
  {from: f(lista), to: f(wykaz), text: T.walidacja},
  {from: f(wykaz), to: tl.frames, text: T.wykaz},
];

const outlines = [
  {from: standard + 0.3, to: pomoc, rect: rectOf(cap, 'standard')},
  {from: pomoc + 0.4, to: scrollUp, rect: rectOf(cap, 'pomoc')},
  {from: menuClick - 0.9, to: menuClick + 0.05, rect: rectOf(cap, 'menu')},
  {from: wykaz + 0.5, to: cap.duration, rect: rectOf(cap, 'wykaz')},
];

export const Dostawca: React.FC = () => (
  <Stage>
    <Appear>
      <Footage capture={cap} tl={tl} shots={shots} outlines={outlines} title={T.window} right="admin.mcod.local" skipLabel={COPY.skipped} />
      <Captions lines={lines} tag={T.tag} />
    </Appear>
  </Stage>
);
