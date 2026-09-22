# Copyright (c) 2026 A. M. B. Heard. All rights reserved.
# Unpublished research software. See LICENSE: use in any publication
# requires prior written permission. Cite as in CITATION.cff.
"""
vq_chart.py -- regenerates vq_comparison.html, the four-panel picture of what
the V/Q spread does to every reported variable.

Two runs of THIS model, identical but for `vq_log_sd`, the width of the
ventilation-to-perfusion distribution across the lung -- in plain terms, how
unevenly air and blood are matched region to region:

    A   vq_log_sd 0.70   what the model ships
    B   vq_log_sd 0.01   one effectively uniform alveolar compartment, which
                         is the STRUCTURE Hardman 1998 Appendix 1 describes
                         for the Nottingham simulator. It is our code
                         emulating their structure. It is NOT their model and
                         NOT their output, and nothing here may be reported as
                         an ICSM result.

Configuration is the one in test_validation.test_stock_1989 -- 70 kg, 1.75 m,
45 y, Hb 15.0, complete obstruction, room air in the airway -- so the Stock
1989 reference marks on the chart are like-for-like with the benchmark. Stock
is the ONLY human measurement in this regime: 14 anaesthetised adults with the
tracheal tube clamped.

The numbers this chart draws are checked in handover_numbers.py, under
"REMOVING THE V/Q SPREAD". This file draws them; that file is the arbiter.

    python3 vq_chart.py

Writes vq_comparison.html next to itself. The HTML is a build product and is
not tracked; regenerate it rather than editing it.
"""
import json
from pathlib import Path

import numpy as np
import apnoea_core as A
from apnoea_core import Patient, AirwayEpoch, simulate, time_to

print(A.provenance())

OBS = np.inf
# Stock 1989 configuration, matching test_validation.test_stock_1989.
STOCK_CFG = dict(weight=70, height=1.75, age=45, hb=15.0)
DT = 0.05
T_END = 1400.0          # long enough for both arms to reach SaO2 40%
GRID = list(range(0, 670, 10))


def run(vq_log_sd):
    """One apnoea with the airway completely obstructed.

    `vq_log_sd` is the standard deviation of the log-normal
    ventilation-to-perfusion distribution: 0.70 is the shipped spread, 0.01
    is effectively no spread at all.
    """
    p = Patient(vq_log_sd=vq_log_sd, **STOCK_CFG)
    return simulate(p, [AirwayEpoch(T_END, resistance=OBS, fgo2=0.21)],
                    dt=DT, stop_sao2=0.0)


def at(r, key, t):
    return float(np.interp(t, r['t'], r[key]))


def main():
    a, b = run(0.70), run(0.01)
    d = {'t': GRID}
    for label, r in (('A', a), ('B', b)):
        for key in ('pao2', 'paco2', 'sao2', 'ph'):
            d[f'{label}_{key}'] = [round(at(r, key, t), 3) for t in GRID]
    d['t40_A'] = round(time_to(a, 'sao2', 40), 1)
    d['t40_B'] = round(time_to(b, 'sao2', 40), 1)

    out = Path(__file__).resolve().parent / 'vq_comparison.html'
    out.write_text(TEMPLATE.replace('__DATA__', json.dumps(d)))
    print(f"wrote {out}")
    print(f"  SaO2 40% at {d['t40_A']} s (spread on) and {d['t40_B']} s (off)")
    for key, dec in (('pao2', 1), ('paco2', 1), ('sao2', 1), ('ph', 3)):
        i = GRID.index(300)
        print(f"  {key:>6} at 300 s: {d['A_'+key][i]:>9.{dec}f}"
              f"  {d['B_'+key][i]:>9.{dec}f}")


TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>V/Q Spread Effects</title>
<style>
  :root { color-scheme: light; }
  .viz-root {
    color-scheme: light;
    --surface-1:      #fcfcfb;
    --page:           #f9f9f7;
    --text-primary:   #0b0b0b;
    --text-secondary: #52514e;
    --muted:          #898781;
    --grid:           #e1e0d9;
    --axis:           #c3c2b7;
    --series-1:       #2a78d6;
    --series-2:       #eb6834;
    --border:         rgba(11,11,11,0.10);
    --band:           rgba(11,11,11,0.06);
  }
  @media (prefers-color-scheme: dark) {
    :root:where(:not([data-theme="light"])) .viz-root {
      color-scheme: dark;
      --surface-1:      #1a1a19;
      --page:           #0d0d0d;
      --text-primary:   #ffffff;
      --text-secondary: #c3c2b7;
      --muted:          #898781;
      --grid:           #2c2c2a;
      --axis:           #383835;
      --series-1:       #3987e5;
      --series-2:       #d95926;
      --border:         rgba(255,255,255,0.10);
      --band:           rgba(255,255,255,0.08);
    }
  }
  :root[data-theme="dark"] .viz-root {
    color-scheme: dark;
    --surface-1:      #1a1a19;
    --page:           #0d0d0d;
    --text-primary:   #ffffff;
    --text-secondary: #c3c2b7;
    --muted:          #898781;
    --grid:           #2c2c2a;
    --axis:           #383835;
    --series-1:       #3987e5;
    --series-2:       #d95926;
    --border:         rgba(255,255,255,0.10);
    --band:           rgba(255,255,255,0.08);
  }
  * { box-sizing: border-box; }
  body {
    margin: 0; padding: 0;
    font-family: system-ui, -apple-system, "Segoe UI", sans-serif;
    background: var(--page, #f9f9f7);
  }
  .viz-root { background: var(--page); padding: 24px 16px 40px; min-height: 100vh; }
  .wrap { max-width: 1060px; margin: 0 auto; }
  h1 { font-size: 20px; line-height: 1.3; margin: 0 0 6px; color: var(--text-primary); font-weight: 650; }
  .sub { font-size: 13px; line-height: 1.5; color: var(--text-secondary); margin: 0 0 18px; max-width: 76ch; }
  .legend { display: flex; flex-wrap: wrap; gap: 8px 20px; align-items: center; margin: 0 0 18px; }
  .lg { display: flex; align-items: center; gap: 7px; font-size: 12.5px; color: var(--text-secondary); }
  .sw { width: 22px; height: 3px; border-radius: 2px; flex: none; }
  .grid2 { display: grid; grid-template-columns: repeat(2, minmax(0,1fr)); gap: 14px; }
  @media (max-width: 760px) { .grid2 { grid-template-columns: 1fr; } }
  .panel {
    background: var(--surface-1);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 14px 14px 8px;
    position: relative;
  }
  .ptitle { font-size: 13.5px; font-weight: 620; color: var(--text-primary); margin: 0 0 1px; }
  .pnote { font-size: 11.5px; color: var(--muted); margin: 0 0 6px; }
  svg { display: block; width: 100%; height: auto; overflow: visible; }
  .tt {
    position: absolute; pointer-events: none; opacity: 0;
    transition: opacity .09s linear;
    background: var(--surface-1);
    border: 1px solid var(--border);
    border-radius: 7px;
    padding: 7px 9px;
    font-size: 11.5px; line-height: 1.45;
    color: var(--text-primary);
    box-shadow: 0 3px 12px rgba(0,0,0,0.13);
    white-space: nowrap; z-index: 6;
  }
  .tt b { font-weight: 620; }
  .tt .row { display: flex; align-items: center; gap: 6px; }
  .tt .dot { width: 8px; height: 8px; border-radius: 50%; flex: none; }
  .tt .v { margin-left: auto; padding-left: 12px; font-variant-numeric: tabular-nums; }
  details { margin-top: 22px; }
  summary { font-size: 13px; color: var(--text-secondary); cursor: pointer; padding: 6px 0; }
  table { border-collapse: collapse; font-size: 12px; margin-top: 8px; width: 100%; color: var(--text-primary); }
  th, td { text-align: right; padding: 4px 9px; border-bottom: 1px solid var(--grid); font-variant-numeric: tabular-nums; }
  th:first-child, td:first-child { text-align: left; }
  th { color: var(--text-secondary); font-weight: 600; }
  .foot { font-size: 11.5px; color: var(--muted); margin-top: 20px; line-height: 1.6; max-width: 86ch; }
</style>
</head>
<body data-palette="#2a78d6,#eb6834">
<div class="viz-root">
<div class="wrap">

<h1>What the V/Q spread does to every reported variable</h1>
<p class="sub">Obstructed apnoea from a fully pre-oxygenated start, 70&nbsp;kg / 1.75&nbsp;m / 45&nbsp;y, haemoglobin 15&nbsp;g/dL &mdash; the exact configuration of the Stock benchmark in <code>test_validation.py</code>.
Both lines are <b>our model</b>. The only difference between them is <code>vq_log_sd</code> &mdash; the spread of ventilation-to-perfusion
ratios across the lung, i.e. how unevenly air and blood are matched region to region. Blue is what we ship (0.70).
Orange collapses that spread to nothing (0.01), which is the single-well-mixed-alveolus structure the other simulator uses.
The black diamonds are what was <b>measured in people</b> (Stock 1989, n&nbsp;=&nbsp;14, at 5&nbsp;minutes).</p>

<div class="legend">
  <span class="lg"><span class="sw" style="background:var(--series-1)"></span>Ours &mdash; V/Q spread on (0.70)</span>
  <span class="lg"><span class="sw" style="background:var(--series-2)"></span>Spread off (0.01) &mdash; their structure</span>
  <span class="lg"><svg width="15" height="15" style="width:15px;height:15px"><polygon points="7.5,1.5 13,7.5 7.5,13.5 2,7.5" fill="var(--text-primary)"/></svg>Stock 1989, measured (&plusmn;1 SD)</span>
  <span class="lg"><svg width="15" height="15" style="width:15px;height:15px"><rect x="2.5" y="2.5" width="10" height="10" fill="none" stroke="var(--text-secondary)" stroke-width="2"/></svg>Laviola 2026, simulated</span>
</div>

<div class="grid2" id="grid"></div>

<details>
  <summary>Table view &mdash; every 60 s</summary>
  <div id="tablehost"></div>
</details>

<p class="foot" id="foot"></p>

</div>
</div>

<script>
const D = __DATA__;

// PANELS reads D.t40_A, so it must be defined after D.
const PANELS = [
  { key:'pao2',  title:'Arterial oxygen tension (PaO₂)',
    note:'mmHg — how much oxygen is dissolved in arterial blood',
    unit:'mmHg', ymin:0, ymax:560, ticks:[0,100,200,300,400,500], dec:0,
    refs:[ {kind:'stock', t:300, v:314, sd:87, label:'Stock 314 (87)'},
           {kind:'lav',   t:D.t40_A, v:28.3, sd:0.4, label:'Laviola 28.3'} ] },
  { key:'paco2', title:'Arterial carbon dioxide tension (PaCO₂)',
    note:'mmHg — the waste gas building up; drives the acid load',
    unit:'mmHg', ymin:35, ymax:95, ticks:[40,50,60,70,80,90], dec:1,
    refs:[ {kind:'stock', t:300, v:63, sd:9, label:'Stock 63 (9)'},
           {kind:'lav',   t:D.t40_A, v:84.6, sd:4.4, label:'Laviola 84.6'} ] },
  { key:'sao2',  title:'Arterial oxygen saturation (SaO₂)',
    note:'% — the number on the pulse oximeter',
    unit:'%', ymin:25, ymax:103, ticks:[30,40,60,80,100], dec:1,
    refs:[ {kind:'bound', t:300, v:92, label:'Stock: > 92%'} ] },
  { key:'ph',    title:'Arterial pH',
    note:'the acidity of the blood; 7.35–7.45 is normal',
    unit:'', ymin:7.19, ymax:7.42, ticks:[7.20,7.25,7.30,7.35,7.40], dec:3,
    refs:[ {kind:'stock', t:300, v:7.26, sd:0.06, label:'Stock 7.26 (0.06)'} ] }
];

const W = 500, H = 300, M = { t: 12, r: 66, b: 34, l: 50 };
const PW = W - M.l - M.r, PH = H - M.t - M.b;
const TMAX = 660;
const NS = 'http://www.w3.org/2000/svg';
const el = (n, a) => { const e = document.createElementNS(NS, n); for (const k in a) e.setAttribute(k, a[k]); return e; };
const fmt = (v, d) => v == null ? '—' : v.toFixed(d);

function build(p) {
  const host = document.createElement('div');
  host.className = 'panel';
  host.innerHTML = '<p class="ptitle">' + p.title + '</p><p class="pnote">' + p.note + '</p>';

  const svg = el('svg', { viewBox: '0 0 ' + W + ' ' + H, role: 'img',
    'aria-label': p.title + ': two model configurations over 11 minutes of apnoea' });
  const x = t => M.l + (t / TMAX) * PW;
  const y = v => M.t + PH - ((v - p.ymin) / (p.ymax - p.ymin)) * PH;

  // gridlines + y ticks
  p.ticks.forEach(v => {
    svg.appendChild(el('line', { x1: M.l, x2: M.l + PW, y1: y(v), y2: y(v),
      stroke: 'var(--grid)', 'stroke-width': 1 }));
    const tx = el('text', { x: M.l - 8, y: y(v) + 3.6, 'text-anchor': 'end',
      fill: 'var(--muted)', 'font-size': 10.5, 'font-variant-numeric': 'tabular-nums' });
    tx.textContent = p.key === 'ph' ? v.toFixed(2) : v;
    svg.appendChild(tx);
  });

  // x axis
  svg.appendChild(el('line', { x1: M.l, x2: M.l + PW, y1: M.t + PH, y2: M.t + PH,
    stroke: 'var(--axis)', 'stroke-width': 1 }));
  [0, 120, 240, 360, 480, 600].forEach(t => {
    const tx = el('text', { x: x(t), y: M.t + PH + 16, 'text-anchor': 'middle',
      fill: 'var(--muted)', 'font-size': 10.5, 'font-variant-numeric': 'tabular-nums' });
    tx.textContent = (t / 60) + '';
    svg.appendChild(tx);
  });
  const xl = el('text', { x: M.l + PW / 2, y: M.t + PH + 30, 'text-anchor': 'middle',
    fill: 'var(--muted)', 'font-size': 10.5 });
  xl.textContent = 'minutes of apnoea';
  svg.appendChild(xl);

  // Stock measurement moment marker
  svg.appendChild(el('line', { x1: x(300), x2: x(300), y1: M.t, y2: M.t + PH,
    stroke: 'var(--axis)', 'stroke-width': 1, 'stroke-dasharray': '3 4' }));

  // series
  const S = [
    { id: 'A', color: 'var(--series-1)', name: 'Ours (0.70)' },
    { id: 'B', color: 'var(--series-2)', name: 'Spread off (0.01)' }
  ];
  const ends = [];
  S.forEach(s => {
    const arr = D[s.id + '_' + p.key];
    let d = '';
    arr.forEach((v, i) => { d += (i ? 'L' : 'M') + x(D.t[i]).toFixed(2) + ' ' + y(v).toFixed(2); });
    // 2px surface ring so the overlapping segment stays readable
    svg.appendChild(el('path', { d, fill: 'none', stroke: 'var(--surface-1)', 'stroke-width': 6,
      'stroke-linecap': 'round', 'stroke-linejoin': 'round', opacity: 0.85 }));
    svg.appendChild(el('path', { d, fill: 'none', stroke: s.color, 'stroke-width': 2,
      'stroke-linecap': 'round', 'stroke-linejoin': 'round' }));
    const last = arr[arr.length - 1];
    ends.push({ s, v: last, ty: y(last), my: y(last) });
  });
  // direct labels at the line ends, nudged apart when the curves converge
  ends.sort((a, b) => a.ty - b.ty);
  const GAP = 13;
  if (ends.length === 2 && ends[1].ty - ends[0].ty < GAP) {
    const mid = (ends[0].ty + ends[1].ty) / 2;
    ends[0].ty = mid - GAP / 2; ends[1].ty = mid + GAP / 2;
  }
  ends.forEach(e => {
    const lx = M.l + PW + 8;
    if (Math.abs(e.ty - e.my) > 1.5) {
      svg.appendChild(el('line', { x1: M.l + PW + 1, x2: lx - 2, y1: e.my, y2: e.ty,
        stroke: 'var(--axis)', 'stroke-width': 1 }));
    }
    const lb = el('text', { x: lx, y: e.ty + 3.6, fill: 'var(--text-secondary)',
      'font-size': 10.5, 'font-variant-numeric': 'tabular-nums' });
    lb.textContent = fmt(e.v, p.dec);
    svg.appendChild(lb);
    const wpx = String(fmt(e.v, p.dec)).length * 6.2 + 4;
    const lb2 = el('text', { x: lx + wpx, y: e.ty + 3.6, fill: 'var(--muted)', 'font-size': 9.5 });
    lb2.textContent = e.s.id === 'A' ? 'ours' : 'off';
    svg.appendChild(lb2);
  });

  // reference marks
  (p.refs || []).forEach(r => {
    if (r.kind === 'bound') {
      svg.appendChild(el('line', { x1: x(220), x2: x(400), y1: y(r.v), y2: y(r.v),
        stroke: 'var(--text-primary)', 'stroke-width': 1.5, 'stroke-dasharray': '5 3' }));
      const ax = x(300);
      svg.appendChild(el('path', { d: 'M' + ax + ' ' + (y(r.v) - 3) + 'l0 -13 M' + (ax - 3.5) + ' ' +
        (y(r.v) - 12) + 'L' + ax + ' ' + (y(r.v) - 17) + 'l3.5 5',
        fill: 'none', stroke: 'var(--text-primary)', 'stroke-width': 1.5,
        'stroke-linecap': 'round', 'stroke-linejoin': 'round' }));
      const tb = el('text', { x: x(400) + 7, y: y(r.v) + 3.6, fill: 'var(--text-secondary)', 'font-size': 10 });
      tb.textContent = r.label;
      svg.appendChild(tb);
      return;
    }
    const stroke = r.kind === 'stock' ? 'var(--text-primary)' : 'var(--text-secondary)';
    if (r.sd) {
      const hi = Math.min(r.v + r.sd, p.ymax), lo = Math.max(r.v - r.sd, p.ymin);
      svg.appendChild(el('line', { x1: x(r.t), x2: x(r.t), y1: y(hi), y2: y(lo),
        stroke, 'stroke-width': 1.5 }));
      [hi, lo].forEach(v => svg.appendChild(el('line', { x1: x(r.t) - 4, x2: x(r.t) + 4,
        y1: y(v), y2: y(v), stroke, 'stroke-width': 1.5 })));
    }
    if (r.kind === 'stock') {
      const cx = x(r.t), cy = y(r.v);
      svg.appendChild(el('polygon', { points: [cx,cy-6, cx+6,cy, cx,cy+6, cx-6,cy].join(' '),
        fill: 'var(--text-primary)', stroke: 'var(--surface-1)', 'stroke-width': 2 }));
    } else {
      svg.appendChild(el('rect', { x: x(r.t) - 5, y: y(r.v) - 5, width: 10, height: 10,
        fill: 'none', stroke, 'stroke-width': 2 }));
    }
    const anchor = r.t > TMAX * 0.7 ? 'end' : 'start';
    const dx = anchor === 'end' ? -10 : 10;
    const tl = el('text', { x: x(r.t) + dx, y: y(r.v) + (r.kind === 'lav' ? -13 : 3.6),
      'text-anchor': anchor, fill: 'var(--text-secondary)', 'font-size': 10 });
    tl.textContent = r.label;
    svg.appendChild(tl);
  });

  // hover layer
  const cross = el('line', { x1: 0, x2: 0, y1: M.t, y2: M.t + PH, stroke: 'var(--axis)',
    'stroke-width': 1, opacity: 0 });
  svg.appendChild(cross);
  const dots = S.map(s => {
    const c = el('circle', { r: 4.5, fill: s.color, stroke: 'var(--surface-1)',
      'stroke-width': 2, opacity: 0 });
    svg.appendChild(c); return c;
  });
  const hit = el('rect', { x: M.l, y: M.t, width: PW, height: PH, fill: 'transparent' });
  svg.appendChild(hit);

  host.appendChild(svg);
  const tip = document.createElement('div');
  tip.className = 'tt';
  host.appendChild(tip);

  function move(ev) {
    const bb = svg.getBoundingClientRect();
    const px = ((ev.clientX - bb.left) / bb.width) * W;
    let t = ((px - M.l) / PW) * TMAX;
    let i = Math.round(t / 10);
    i = Math.max(0, Math.min(D.t.length - 1, i));
    const tx = x(D.t[i]);
    cross.setAttribute('x1', tx); cross.setAttribute('x2', tx); cross.setAttribute('opacity', 1);
    S.forEach((s, k) => {
      const v = D[s.id + '_' + p.key][i];
      dots[k].setAttribute('cx', tx); dots[k].setAttribute('cy', y(v)); dots[k].setAttribute('opacity', 1);
    });
    tip.innerHTML = '<b>' + (D.t[i] / 60).toFixed(1) + ' min</b> (' + D.t[i] + ' s)' +
      S.map(s => '<div class="row"><span class="dot" style="background:' + s.color + '"></span>' +
        s.name + '<span class="v">' + fmt(D[s.id + '_' + p.key][i], p.dec) + ' ' + p.unit + '</span></div>').join('');
    tip.style.opacity = 1;
    const hb = host.getBoundingClientRect();
    let lx = (tx / W) * bb.width + (bb.left - hb.left) + 14;
    if (lx + 210 > hb.width) lx -= 228;
    tip.style.left = Math.max(4, lx) + 'px';
    tip.style.top = (ev.clientY - hb.top - 12) + 'px';
  }
  function out() {
    cross.setAttribute('opacity', 0);
    dots.forEach(d => d.setAttribute('opacity', 0));
    tip.style.opacity = 0;
  }
  hit.addEventListener('pointermove', move);
  hit.addEventListener('pointerleave', out);
  return host;
}

PANELS.forEach(p => document.getElementById('grid').appendChild(build(p)));

// table view
(function () {
  const rows = [];
  for (let i = 0; i < D.t.length; i++) if (D.t[i] % 60 === 0) rows.push(i);
  let h = '<table><thead><tr><th>min</th>' +
    PANELS.map(p => '<th>' + p.key.toUpperCase() + ' ours</th><th>' + p.key.toUpperCase() + ' off</th>').join('') +
    '</tr></thead><tbody>';
  rows.forEach(i => {
    h += '<tr><td>' + (D.t[i] / 60) + '</td>' +
      PANELS.map(p => '<td>' + fmt(D['A_' + p.key][i], p.dec) + '</td><td>' +
        fmt(D['B_' + p.key][i], p.dec) + '</td>').join('') + '</tr>';
  });
  h += '</tbody></table>';
  document.getElementById('tablehost').innerHTML = h;
})();

document.getElementById('foot').innerHTML =
  'Saturation falls to 40% at <b>' + D.t40_A + ' s</b> with the spread on and <b>' + D.t40_B +
  ' s</b> with it off — the spread barely changes <i>when</i> the patient desaturates, but changes almost everything about ' +
  'the numbers reported along the way. The dashed vertical line at 5 minutes is the moment Stock 1989 drew blood. ' +
  'The orange curve is our code emulating the other simulator’s <i>structure</i> (one well-mixed alveolar compartment); ' +
  'it is not their model and not their output. The Laviola squares are their published state at SaO\u2082 40%, plotted at the moment our spread-on arm reaches 40%; their cohort is Hb 14, ours here is Hb 15 to match Stock, so treat their position on the time axis as indicative.';
</script>
</body>
</html>
"""


if __name__ == '__main__':
    main()
