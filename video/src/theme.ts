// Wygląd wszystkiego, co nie jest nagraniem. Kolory i krój pisma pochodzą z akcji „Dane (prze)życie”
// (branding/ksiega_znaku.pdf) i z prototypu demo/index.html (zmienne CSS --granat, --zielen, --tlo, --ramka).
export const C = {
  bg: '#f4f6f8',        // --tlo
  dot: '#f4f6f8',       // płaskie tło, bez faktury (prototyp jej nie ma)
  panel: '#ffffff',
  bar: '#0E2A47',       // --granat: pasek okna jak nagłówki tabel prototypu
  onBar: '#ffffff',
  ink: '#1b2430',       // --tekst
  muted: '#4f5a68',     // --szary
  line: '#c3ccd6',      // --ramka
  accent: '#007A45',    // --zielen
  onAccent: '#ffffff',
  navy: '#0E2A47',
  red: '#C8102E',
};
// Atkinson Hyperlegible (SIL OFL, branding/fonty/), ładowany w Root.tsx.
export const DISPLAY = '"Atkinson Hyperlegible", sans-serif';
export const BODY = '"Atkinson Hyperlegible", sans-serif';
export const MONO = 'Consolas, "Cascadia Mono", monospace';

export const LOOK = {
  border: 2,
  radius: 6,
  shadow: '0 24px 60px rgba(14,42,71,.18), 0 4px 14px rgba(14,42,71,.10)',
  stepped: false,
};

export const FPS = 60;
export const W = 1920;
export const H = 1080;

/**
 * Where recorded footage sits on the stage. The content area keeps the recording's 16:9 shape:
 * 1536x864 shows a 1280x720 page at 1.2x, and the recording is 2560x1440, so the camera can zoom to
 * 1.67x before a single pixel is upscaled.
 */
export const WIN = {x: 190, y: 34, bar: 46, border: LOOK.border, contentW: 1536, contentH: 864};
export const CAPTION = {x: 190, y: 968, w: 1536 + LOOK.border * 2, h: 80};

/** Screen-recording zoom: reaches 90% in about 0.3 s and settles without overshoot. */
export const ZOOM_SPRING = {stiffness: 205, damping: 33.3, mass: 1.5};

/** Frame used by stage furniture; footage, camera and cursor always stay smooth. */
export const tick = (frame: number) => (LOOK.stepped ? Math.floor(frame / 2) * 2 : frame);
