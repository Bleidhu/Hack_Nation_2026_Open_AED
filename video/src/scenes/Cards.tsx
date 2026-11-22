// Części wideo, które nie są nagraniem: otwarcie, karty sekcji, zamknięcie.
import React from 'react';
import {Img, staticFile} from 'remotion';
import {After, Appear, Stage, Typed, Window} from '../chrome';
import {COPY} from '../copy';
import {C, DISPLAY, FPS, H, LOOK, W} from '../theme';

export const INTRO_FRAMES = Math.round(6.4 * FPS);
export const CARD_FRAMES = Math.round(3.4 * FPS);
export const OUTRO_FRAMES = Math.round(8.5 * FPS);

/** Logotyp akcji (branding/logo/), białe tło pliku leży na białym panelu. */
const Logo: React.FC<{width: number; haslo?: boolean}> = ({width, haslo = true}) => (
  <Img src={staticFile(`marka/dane-przezycie_logo_poziome${haslo ? '_haslo' : ''}.png`)} style={{width, display: 'block'}} />
);

export const Intro: React.FC = () => (
  <Stage>
    <div style={{position: 'absolute', left: 0, top: 0, width: W, height: 14, background: C.navy}} />
    <div style={{position: 'absolute', left: 0, top: 14, width: W, height: 6, background: C.accent}} />
    <div style={{position: 'absolute', left: 170, top: 190, width: 1580}}>
      <After frame={4}><div style={{font: `700 26px ${DISPLAY}`, color: C.muted, letterSpacing: '0.03em'}}>{COPY.intro.kicker}</div></After>
      <div style={{font: `700 150px/1.05 ${DISPLAY}`, color: C.navy, letterSpacing: '-0.03em', whiteSpace: 'nowrap', marginTop: 14}}>
        <Typed text={COPY.brand} start={10} cps={14} />&nbsp;
      </div>
      <After frame={64}><div style={{fontSize: 50, letterSpacing: '-0.01em', marginTop: 22, color: C.ink}}>{COPY.intro.lead}</div></After>
      <After frame={96}><div style={{fontSize: 32, color: C.muted, marginTop: 14}}>{COPY.intro.sub}</div></After>
      <div style={{display: 'flex', gap: 18, marginTop: 52}}>
        {COPY.intro.chips.map((name, i) => (
          <After key={name} frame={128 + i * 14}>
            <div style={{display: 'flex', alignItems: 'center', gap: 12, padding: '14px 26px', borderRadius: LOOK.radius,
              background: i === 0 ? C.accent : C.panel, color: i === 0 ? C.onAccent : C.ink,
              border: `${LOOK.border}px solid ${i === 0 ? C.accent : C.line}`, font: `700 28px ${DISPLAY}`}}>
              <span style={{fontSize: 21, opacity: 0.75}}>0{i + 1}</span>{name}
            </div>
          </After>
        ))}
      </div>
    </div>
    <div style={{position: 'absolute', right: 120, bottom: 70}}>
      <After frame={150}>
        <div style={{display: 'flex', alignItems: 'center', gap: 22, font: `400 22px ${DISPLAY}`, color: C.muted}}>
          akcja promocyjna
          <div style={{background: C.panel, border: `1px solid ${C.line}`, borderRadius: LOOK.radius, padding: '2px 10px'}}><Logo width={420} /></div>
        </div>
      </After>
    </div>
  </Stage>
);

export const Card: React.FC<{no: string; title: string; sub: string}> = ({no, title, sub}) => {
  const rect = {x: (W - 1240) / 2, y: (H - 440) / 2, w: 1240, h: 440};
  return (
    <Stage>
      <Appear>
        <Window rect={rect} title={`${COPY.brand} · dane.gov.pl`}>
          <div style={{display: 'flex', alignItems: 'center', gap: 48, padding: '0 64px', height: '100%'}}>
            <div style={{width: 180, height: 180, borderRadius: LOOK.radius * 2, background: C.accent, color: C.onAccent, display: 'grid', placeItems: 'center',
              font: `700 96px/1 ${DISPLAY}`, flexShrink: 0}}>{no}</div>
            <div>
              <div style={{font: `700 88px/1.05 ${DISPLAY}`, letterSpacing: '-0.02em', color: C.navy, whiteSpace: 'nowrap'}}>
                <Typed text={title} start={16} cps={20} caret={false} />&nbsp;
              </div>
              <After frame={62}><div style={{fontSize: 38, marginTop: 20, color: C.muted}}>{sub}</div></After>
            </div>
          </div>
        </Window>
      </Appear>
    </Stage>
  );
};

export const Outro: React.FC = () => {
  const O = COPY.outro;
  const rect = {x: 980, y: 210, w: 800, h: 104 * O.rows.length + 46 + LOOK.border * 2 + 4};
  return (
    <Stage>
      <div style={{position: 'absolute', left: 0, top: 0, width: W, height: 14, background: C.navy}} />
      <div style={{position: 'absolute', left: 0, top: 14, width: W, height: 6, background: C.accent}} />
      <div style={{position: 'absolute', left: 140, top: 210, width: 780}}>
        <div style={{background: C.panel, border: `1px solid ${C.line}`, borderRadius: LOOK.radius, padding: '4px 14px', display: 'inline-block'}}>
          <Logo width={460} haslo={false} />
        </div>
        <div style={{font: `700 84px/1.1 ${DISPLAY}`, color: C.navy, letterSpacing: '-0.025em', whiteSpace: 'nowrap', marginTop: 36}}>
          <Typed text={O.title} start={8} cps={20} caret={false} /><br />
          <span style={{color: C.accent}}><Typed text={O.title2} start={8 + Math.round((O.title.length / 20) * FPS)} cps={20} caret={false} /></span>&nbsp;
        </div>
        <After frame={170}>
          <div style={{background: C.panel, border: `${LOOK.border}px solid ${C.line}`, borderRadius: LOOK.radius, padding: '16px 22px', marginTop: 36,
            fontSize: 24, lineHeight: 1.4, color: C.muted}}>{O.note}</div>
        </After>
      </div>
      <Appear delay={30}>
        <Window rect={rect} title="Co oddajemy (repozytorium)">
          {O.rows.map(([name, what], i) => (
            <After key={name} frame={60 + i * 20}>
              <div style={{display: 'flex', alignItems: 'center', gap: 26, padding: '0 32px', height: 104, boxSizing: 'border-box',
                borderBottom: i < O.rows.length - 1 ? `1px solid ${C.line}` : 'none'}}>
                <span style={{font: `700 40px ${DISPLAY}`, color: C.accent, width: 64}}>0{i + 1}</span>
                <span>
                  <span style={{display: 'block', font: `700 34px ${DISPLAY}`, color: C.navy}}>{name}</span>
                  <span style={{display: 'block', fontSize: 24, color: C.muted, marginTop: 4}}>{what}</span>
                </span>
              </div>
            </After>
          ))}
        </Window>
      </Appear>
    </Stage>
  );
};
