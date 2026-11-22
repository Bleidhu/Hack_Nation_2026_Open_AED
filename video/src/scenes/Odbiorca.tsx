// Scena 2: odbiorca we froncie portalu. Zasób zbiorczy: opis, pobieranie, tabela, mapa; potem stały adres API.
import React from 'react';
import capJson from '../../public/captures/odbiorca.json';
import {at, clickAt, cutting, part, rectOf, timeline, type Capture, type Shot} from '../capture';
import {Appear, Captions, Stage} from '../chrome';
import {COPY} from '../copy';
import {Footage} from '../Footage';

const cap = capJson as unknown as Capture;
const T = COPY.odbiorca;

const pobierz = at(cap, 'pobierz'), scroll = at(cap, 'scroll-start'), tabela = at(cap, 'tabela');
const przedMapa = at(cap, 'przed-mapa'), mapClick = clickAt(cap, 0), mapaStart = at(cap, 'mapa-start'), mapa = at(cap, 'mapa');
const navStart = at(cap, 'nav-start'), surowe = at(cap, 'api-surowe'), api = at(cap, 'api');

// Dwa cięcia: czekanie na wczytanie mapy (oznaczone napisem z liczbą sekund) i przejście do innej domeny (API),
// gdzie obraz przygasa (zmiana tematu).
const tl = timeline(cutting(at(cap, 'naglowek') + 0.05, cap.duration - 0.3, [
  {from: mapClick + 1.2, to: mapaStart - 0.15, wait: true},
  {from: navStart + 0.05, to: surowe - 0.05},
], 0.3));
export const ODBIORCA_FRAMES = tl.frames;

const shots: Shot[] = [
  {t: 0},
  {t: 0.4, rect: rectOf(cap, 'naglowek'), maxZoom: 1.45},
  {t: pobierz - 0.1, rect: part(rectOf(cap, 'pobierz'), -0.4, -2.5, 4.5, 3), maxZoom: 1.8},
  {t: scroll - 0.4},
  {t: tabela + 0.2, rect: rectOf(cap, 'tabela'), maxZoom: 1.25},
  {t: przedMapa},
  {t: mapa + 0.3, rect: rectOf(cap, 'mapa'), maxZoom: 1.15},
  {t: surowe, cut: true},
  {t: api + 0.1, rect: part(rectOf(cap, 'api'), -0.05, -0.3, 1.15, 1.3), maxZoom: 2},
];

const f = tl.frameOf;
const lines = [
  {from: f(0.2), to: f(pobierz), text: T.zasob},
  {from: f(pobierz), to: f(scroll + 0.3), text: T.pobierz},
  {from: f(scroll + 0.3), to: f(przedMapa), text: T.tabela},
  {from: f(przedMapa), to: f(navStart), text: T.mapa},
  {from: f(surowe), to: tl.frames, text: T.api},
];

const outlines = [
  {from: pobierz + 0.4, to: scroll, rect: rectOf(cap, 'pobierz')},
  {from: mapa + 0.6, to: navStart, rect: rectOf(cap, 'mapa')},
];

export const Odbiorca: React.FC = () => (
  <Stage>
    <Appear>
      <Footage capture={cap} tl={tl} shots={shots} outlines={outlines} title={T.window} right="mcod.local · api.mcod.local"
        skipLabel={COPY.skipped} />
      <Captions lines={lines} tag={T.tag} />
    </Appear>
  </Stage>
);

