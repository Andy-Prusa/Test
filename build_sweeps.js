// Copyright (c) 2026 A. M. B. Heard. All rights reserved.
// Unpublished research software. See LICENSE: use in any publication
// requires prior written permission. Cite as in CITATION.cff.
//
// build_sweeps.js -- generate the per-slider survival sweeps the page's Graphs
// tab plots. RULED 2026-10-05: one page of graph per slider, computed ONCE and
// regenerated only when the engine changes.
//
//   node build_sweeps.js            write sweeps.json
//   node build_sweeps.js --check    exit 1 if sweeps.json is stale or missing
//
// WHY THIS IS A BUILD STEP AND NOT DONE IN THE BROWSER. One simulation costs
// about 4 s when it dies early and about 33 s when it survives the full hour.
// Ten sliders x 11 points x 2 arms is 220 simulations, so a sweep rendered on
// tab-open would hang the browser for over an hour. Measured, not guessed.
//
// WHY NODE AND model.js RATHER THAN PYTHON AND apnoea_core.py. Two reasons, and
// the second matters more than the first. Python is ~37 s per simulation
// against model.js's ~4, so the same sweep would take about 2.25 hours. And
// THE PAGE RUNS model.js: generating from the same engine means the baked
// curves and the live Run button cannot disagree. test_parity.py still holds
// model.js to the Python reference, so this does not escape the arbiter.
//
// THE ENDPOINT IS LOSS OF CARDIAC OUTPUT -- death, ruled 2026-10-05, not
// desaturation. A run that reaches the horizon without arresting is recorded as
// null and drawn as ">60 min", NOT as exactly 60: the model cannot say when
// that patient dies, and plotting 60 would assert something it does not know.
//
// AND THE pH LIMB IS CARRIED ALONGSIDE, because the death endpoint alone cannot
// show what actually limits the device arm. The device arm does not lose
// cardiac output within the hour at ANY slider extreme -- it sits at SpO2 100%,
// PaCO2 167, pH 6.95 with cardiac output RISING -- because THE MODEL HAS NO
// DEATH-FROM-ACIDOSIS MECHANISM. "Time to death" here means time to HYPOXIC
// death only, and buccal oxygen abolishes that. The pH crossing is read off the
// same runs at no extra cost and is drawn dashed, so the graph shows both why
// the device arm survives and what would really kill it. See HANDOVER entry 30
// (the buccal arm is CO2-limited) and entry 38.

'use strict';
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const model = require(path.join(__dirname, 'model.js'));

const OUT = path.join(__dirname, 'sweeps.json');
const HORIZON = 3600;          // s -- the 60-minute axis
const POINTS = 11;             // both ends exactly, nine interior
const PH_DEAD = 7.0;           // the acidosis limb, ruled
const SPO2_DEAD = 90;          // the hypoxia limb, for reference

// ---- the page's own dials and base, kept in step with build_page.py --------
// A copy, and that is a risk: if build_page.py's DIALS and BASE change and
// these do not, the sweep describes a patient the page no longer offers. The
// --check below hashes build_page.py for exactly that reason.
const DIALS = [
  ['weight', 'Body weight', 45, 180, 0.5, 76.5, 'kg'],
  ['height', 'Height', 1.45, 2.05, 0.01, 1.75, 'm'],
  ['frcScale', 'FRC', 0.55, 1.5, 0.01, 1.0, 'x'],
  ['bmrScale', 'Metabolic rate', 0.6, 1.7, 0.01, 1.0, 'x'],
  ['hb', 'Haemoglobin', 4.0, 18.0, 0.5, 14.0, 'g/dL'],
  ['ccScale', 'Closing capacity', 0.6, 1.6, 0.01, 1.0, 'x'],
  ['maxClosed', 'Lung collapsibility', 0.10, 0.65, 0.01, 0.25, ''],
  ['fgBuccal', 'Pharyngeal O2 (device arm)', 0.21, 1.00, 0.01, 1.00, ''],
  ['tiltDeg', 'Bed tilt (head up)', -20, 45, 1, 25, 'deg'],
  ['buccalIdx', 'Buccal switched on', 0, 4, 1, 0, ''],
];
const STARTS = [[0, 'From induction'], [120, 'After mask ventilation fails'],
                [160, 'After the LMA fails'], [280, 'At laryngoscopy'],
                [370, 'After failed intubation attempts']];
const BASE = {
  age: 45, lmaOpens: true, frcRef: 2860, frcDrop: 400, tiltDeg: 25,
  ccAt20: 1800, ccPerYear: 20, ccPerBmi: 45, ccK: 1.5, vo2Ref: 250, coRef: 5,
  crs: 75, vArt: 1.0, vVen: 2.0, vTisO2: 1.5, feo2: 0.87, rv: 1100,
  kRvBmi: 0.0198, pCollapse: -149.5461, nVq: 80, tauMix: 45,
  inflowMechFrac: 0.18,
};
DIALS.forEach(d => { BASE[d[0]] = d[5]; });

// ---- the cico preset's airway timeline, verbatim from build_page.py --------
const OBS = 1e9;
const AIRWAY_R = { patent: () => 2, partial: () => 8, obstructed: () => OBS };
const SEGS = [[0, 'obstructed'], [120, 'partial'], [130, 'obstructed'],
              [160, 'obstructed'], [220, 'obstructed'], [280, 'patent'],
              [430, 'patent']];
const REOBSTRUCT_AT = 430;

function segAirwayAt(t) {
  let a = 'obstructed';
  for (const [s, aw] of SEGS) if (t >= s) a = aw;
  return a;
}

// tl() from build_page.py. OBS is 1e9 and FINITE: model.js branches on
// isFinite(R), so substituting Infinity here would model a different airway
// from the one the page models.
function tl(P, end, fg, startAt, keep) {
  const cuts = [...new Set([0, ...SEGS.map(s => s[0]), REOBSTRUCT_AT, startAt, end])]
    .filter(v => v >= 0 && v <= end).sort((a, b) => a - b);
  const ep = [];
  for (let i = 0; i < cuts.length - 1; i++) {
    const a = cuts[i], b = cuts[i + 1];
    let st = segAirwayAt(a);
    if (st === 'partial' && P.lmaOpens === false) st = 'obstructed';
    let R = AIRWAY_R[st]();
    if (REOBSTRUCT_AT != null && a >= REOBSTRUCT_AT && !keep) R = OBS;
    ep.push({ d: b - a, R: R, fg: (a >= startAt ? fg : 0.21) });
  }
  return ep;
}

// ---- readings off one run --------------------------------------------------
function firstDown(out, key, thr) {
  const v = out[key], t = out.t;
  for (let i = 1; i < v.length; i++) {
    if (v[i - 1] >= thr && v[i] < thr) {
      return t[i - 1] + (t[i] - t[i - 1]) * (v[i - 1] - thr) / (v[i - 1] - v[i]);
    }
  }
  return null;
}
function deathAt(out) {
  for (let i = 0; i < out.t.length; i++) {
    if (out.co[i] <= 0.001 || out.hr[i] <= 0) return out.t[i];
  }
  return null;   // never arrested within the horizon
}

function runOne(P, keep) {
  const fg = keep ? P.fgBuccal : 0.21;
  const startAt = keep ? STARTS[Math.round(P.buccalIdx)][0] : 0;
  const out = model.simulate(P, tl(P, HORIZON, fg, startAt, keep), 0.1);
  const n = out.t.length - 1;
  return {
    death: deathAt(out),
    ph: firstDown(out, 'ph', PH_DEAD),
    spo2: firstDown(out, 'spo2', SPO2_DEAD),
    derived: { bmi: out.bmi, frc: out.frc, cc: out.cc, vo2: out.vo2,
               co: out.coBase },
    endPh: out.ph[n], endSpo2: out.spo2[n], endPaco2: out.paco2[n],
  };
}

// ---- staleness: what counts as "the engine changed" -----------------------
// model.js is hashed RAW. A comment-only edit to it therefore forces a
// regeneration, which is accepted: model.js is a port that changes when the
// reference changes and is rarely commented on its own. build_page.py is
// hashed too, because DIALS and BASE are COPIED above -- if the page starts
// offering a different range or a different default patient, a sweep generated
// against the old one is describing a patient nobody can select.
// This is deliberately NOT the AST-keyed approach used for the simulate cache:
// there is no JS parser in this repo's toolchain, and inventing a regex
// comment-stripper would be a silent-wrong-answer risk for a saving that does
// not matter here.
function engineHash() {
  const h = crypto.createHash('sha256');
  for (const f of ['model.js', 'build_page.py']) {
    h.update(fs.readFileSync(path.join(__dirname, f)));
  }
  return h.digest('hex').slice(0, 16);
}

function linspace(lo, hi, n) {
  const out = [];
  for (let i = 0; i < n; i++) out.push(lo + (hi - lo) * i / (n - 1));
  return out;
}

const SMOKE = process.argv.includes('--smoke');

// ---- checkpointing, because two 70-minute runs were lost -----------------
// Each completed slider is written to sweeps.partial.json, and a run that finds
// a partial built against the SAME engine hash resumes from it. The hash guard
// is the point: resuming onto a changed engine would silently mix results from
// two different models, which is worse than losing the time.
//
// This exists because of an operational mistake, not a model problem: the first
// two attempts were launched with `nohup ... &` behind a harness background
// call whose wrapper exited immediately, and the detached child was reaped with
// it. Memory was never the cause -- 15.6 GB free, no cgroup limit, zero OOM
// events. The job must run AS the backgrounded command, not detached behind it.
const PART = path.join(__dirname, 'sweeps.partial.json');

function loadPartial(hash) {
  if (!fs.existsSync(PART)) return [];
  try {
    const p = JSON.parse(fs.readFileSync(PART, 'utf8'));
    if (p.engineHash !== hash) {
      process.stderr.write('  partial was built against a different engine; '
        + 'discarding it rather than mixing two models\n');
      return [];
    }
    process.stderr.write(`  resuming: ${p.dials.length} slider(s) already done\n`);
    return p.dials;
  } catch (e) {
    process.stderr.write(`  partial unreadable (${e.message}); starting over\n`);
    return [];
  }
}

function build() {
  const hash = engineHash();
  const dials = SMOKE ? [] : loadPartial(hash);
  const done = new Set(dials.map(d => d.key));
  const t0 = Date.now();
  let sims = 0;
  const dialList = SMOKE ? [DIALS[4]] : DIALS;   // --smoke: haemoglobin only
  for (const [key, label, lo, hi, step, def, unit] of dialList) {
    if (done.has(key)) continue;          // already in the partial
    let xs = linspace(lo, hi, SMOKE ? 3 : POINTS);
    if (key === 'buccalIdx') xs = [0, 1, 2, 3, 4];          // it is an index
    if (step >= 1) xs = xs.map(v => Math.round(v));
    const control = { death: [], ph: [], spo2: [] };
    const device = { death: [], ph: [], spo2: [] };
    const derived = { bmi: [], frc: [], cc: [], vo2: [], co: [] };
    for (const x of xs) {
      const P = Object.assign({}, BASE); P[key] = x;
      const c = runOne(P, false), d = runOne(P, true);
      sims += 2;
      for (const k of ['death', 'ph', 'spo2']) { control[k].push(c[k]); device[k].push(d[k]); }
      for (const k of Object.keys(derived)) derived[k].push(c.derived[k]);
      process.stderr.write(`  ${key}=${x}  control ${c.death === null ? '>60m' :
        (c.death / 60).toFixed(1) + 'm'}  device ${d.death === null ? '>60m' :
        (d.death / 60).toFixed(1) + 'm'}  (${sims}/220, ${((Date.now() - t0) / 60000).toFixed(1)} min)\n`);
    }
    // which derived quantities actually MOVE across this slider's range --
    // the page lists them, so the reader can see what else the slider changed
    const moved = Object.keys(derived).filter(k => {
      const v = derived[k], mn = Math.min(...v), mx = Math.max(...v);
      return mx - mn > Math.abs(mn) * 1e-6 + 1e-9;
    });
    dials.push({ key, label, unit, min: lo, max: hi, def, x: xs,
                 control, device, derived, moved,
                 deviceOnly: (key === 'fgBuccal' || key === 'buccalIdx'),
                 xlabels: key === 'buccalIdx' ? STARTS.map(s => s[1]) : null });
    if (!SMOKE) {
      // written after EVERY slider, so at most one slider's work is ever lost
      fs.writeFileSync(PART, JSON.stringify({ engineHash: hash, dials }));
    }
  }
  return {
    generated: new Date().toISOString().slice(0, 10),
    engineHash: hash, horizon: HORIZON, points: POINTS,
    phDead: PH_DEAD, spo2Dead: SPO2_DEAD,
    endpoint: 'loss of cardiac output (co<=0 or hr<=0); null means it did not '
            + 'arrest within the horizon',
    scenario: 'cico preset: control re-obstructs at 430 s, device keeps the '
            + 'blade in', dials,
    sims, minutes: +((Date.now() - t0) / 60000).toFixed(1),
  };
}

if (process.argv.includes('--check')) {
  if (!fs.existsSync(OUT)) {
    console.error(`STALE: ${path.basename(OUT)} does not exist; run: node build_sweeps.js`);
    process.exit(1);
  }
  const have = JSON.parse(fs.readFileSync(OUT, 'utf8'));
  const want = engineHash();
  if (have.engineHash !== want) {
    console.error(`STALE: ${path.basename(OUT)} was built against engine `
      + `${have.engineHash}, the tree is now ${want}. Run: node build_sweeps.js`);
    process.exit(1);
  }
  console.log(`up to date: ${path.basename(OUT)} matches the engine (${want})`);
  process.exit(0);
}

const data = build();
if (SMOKE) {
  console.log(JSON.stringify(data.dials[0], null, 1).slice(0, 1400));
  console.log(`\nSMOKE: ${data.sims} sims in ${data.minutes} min -- `
    + `nothing written. Projected full run: `
    + `${(data.minutes / data.sims * 220).toFixed(0)} min.`);
  process.exit(0);
}
fs.writeFileSync(OUT, JSON.stringify(data));
if (fs.existsSync(PART)) fs.unlinkSync(PART);   // the real file supersedes it
console.log(`built ${OUT}: ${data.dials.length} sliders, ${data.sims} simulations, `
  + `${data.minutes} min, engine ${data.engineHash}`);
