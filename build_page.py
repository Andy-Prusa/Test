# Copyright (c) 2026 A. M. B. Heard. All rights reserved.
# Unpublished research software. See LICENSE: use in any publication
# requires prior written permission. Cite as in CITATION.cff.
import os
import sys

# Paths are relative to this file, not to the shell's working directory, so
# that "re-run build_page.py after any change to model.js" (HANDOVER.md) works
# from anywhere and lands in the repo. It previously wrote to an absolute
# /mnt/user-data/outputs path left over from the machine it was written on,
# which meant it silently did not update the page it is supposed to build.
HERE = os.path.dirname(os.path.abspath(__file__))
MODEL_JS = os.path.join(HERE, 'model.js')
OUT_HTML = os.path.join(HERE, 'airway_scenario.html')

model = open(MODEL_JS).read().split("if(typeof module")[0]

HTML = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Airway obstruction: where the oxygen goes</title>
<!-- NO EXTERNAL REFERENCES. The Google Fonts links that used to sit here were
     removed 2026-09-22 so the built page is a single self-contained file: it
     opens from a USB stick, an email attachment or an air-gapped machine, and
     makes no network request of any kind. Barlow and Barlow Condensed are
     still NAMED in the CSS below and are used if the viewer happens to have
     them installed; otherwise the system sans is substituted and nothing else
     changes. If you ever put the fonts back, the page stops being shareable
     as a file and starts phoning Google on every open. -->
<style>
:root{--screen:#060a0d;--panel:#0d151b;--rule:#16242e;--rule2:#223743;
--spo2:#4fd8e8;--co2:#dda23c;--ecg-line:#4ade5e;--sat:#ecdf49;--alarm:#ff4d3d;--o2:#a8ecff;--inert:#41586a;
--ink:#c8d6de;--dim:#6b8494}
*{box-sizing:border-box}
html,body{height:100%}
body{margin:0;background:var(--screen);color:var(--ink);
font-family:Barlow,system-ui,sans-serif;-webkit-font-smoothing:antialiased}
.wrap{max-width:1180px;margin:0 auto;padding:10px 12px 22px}
/* On a wide screen the controls sit beside the patients rather than above
   them, so the whole thing fits one screen without scrolling. */
@media(min-width:1050px){
 .wrap{max-width:none;height:100vh;height:100dvh;padding:10px 14px;
  display:grid;grid-template-columns:minmax(300px,24%) minmax(0,1fr);
  gap:16px;align-items:stretch}
 .side{overflow-y:auto;min-height:0;padding-right:4px}
 /* The sliders panel folds away to the left, giving its width to the
    patients. Animating the grid column rather than translating the panel
    means the arms actually grow into the space instead of being overlapped. */
 .wrap{transition:grid-template-columns .28s ease}
 body.sidehid .wrap{grid-template-columns:0 minmax(0,1fr)}
 body.sidehid .side{opacity:0;pointer-events:none;overflow:hidden;padding-right:0}
 .main{display:flex;flex-direction:column;min-height:0;gap:6px}
 .arms{flex:1 1 auto;min-height:0}
 .main .transport,.main .steps,.main .caption{flex:none}
 .main .caption{margin-bottom:0}
 .arm{min-height:0;overflow-y:auto}
 .dials{grid-template-columns:1fr;gap:9px 0}
 .transport{gap:8px}
 .transport button{padding:5px 12px;font-size:15px}
 #scrub{width:100%;flex:1 1 100%;min-width:0}
 /* One icon and a label need 34px, not 62. The old rule here said 52 and
    never applied: a later base rule of the same specificity overrode it, so
    the compact height had been written but was dead. Scoping to .main is what
    makes it win. */
 .main .steps{height:34px;margin-bottom:0}
 .sb{margin:10px 0;border:1px solid #d7d7d7;border-radius:6px;background:#fafafa;
     font-size:13px}
 .sb summary{cursor:pointer;padding:8px 10px;font-weight:600}
 .sb .sbnote{margin:0 10px 8px;color:#555;font-size:12px;line-height:1.45}
 .sbrow{display:flex;gap:8px;align-items:center;flex-wrap:wrap;padding:6px 10px}
 .sbrow label{color:#555}
 .sbrow input[type=number]{width:80px}
 .sbt{width:calc(100% - 20px);margin:4px 10px 0;border-collapse:collapse}
 .sbt th{text-align:left;font-weight:600;color:#555;font-size:12px;
         border-bottom:1px solid #ddd;padding:3px 4px}
 .sbt td{padding:2px 4px;border-bottom:1px solid #eee}
 .sbt input[type=text]{width:100%;box-sizing:border-box}
 .sbt input[type=number]{width:70px}
 .sberr{color:#b00;font-size:12px}
 .main .transport{margin-bottom:2px}
 /* THE SAME DEAD-RULE BUG AS .steps ABOVE, found 2026-09-22 from a
    screenshot on an iPad: the figure was drawn straight over the readout
    labels, so "alveolar N2" read "olar N2" and "lung volume" read "g volume".
    This block sets the canvas column to auto, but the BASE `.stage` rule
    further down has the same specificity (0,1,0) and comes later in source
    order, so it won and the column stayed pinned at 126px. Meanwhile the
    canvas rule below DID apply, because the only base rule for it is a bare
    `canvas` selector it outranks -- so the canvas grew to its clamped height
    and took its aspect-ratio width (252/404 = 0.624) while its track did not
    grow with it. At 1366x1024 that is a 192px canvas in a 126px track: 54px
    of overlap, straight across the labels.
    Scoping to `.main` (0,2,0) is what makes it win, exactly as for .steps.
    The track is sized by the SAME expression as the canvas height times the
    aspect ratio, so the two cannot drift apart again; `auto` is not used
    because grid auto-sizing of a replaced element with an aspect ratio is
    where this went wrong in the first place. */
 .main .stage{grid-template-columns:calc(clamp(150px,30vh,400px)*252/404)
   minmax(0,1fr);margin-top:8px}
 .main .stage canvas:not(.ecg){height:clamp(150px,30vh,400px);width:auto}
 .ecg{height:clamp(38px,7vh,80px)}
 .plethw{height:clamp(24px,4.5vh,54px)}
 .foot{margin-top:14px;padding-top:11px;font-size:11.5px;max-width:none}
 .legend{margin-top:8px}
}
h1{font-family:'Barlow Condensed',sans-serif;font-weight:600;
font-size:clamp(18px,2.6vw,28px);line-height:1.12;margin:0 0 4px}
.sub{color:var(--dim);font-size:13px;max-width:66ch;margin:0 0 12px;line-height:1.45}
.transport{display:flex;align-items:center;gap:12px;flex-wrap:wrap;margin-bottom:10px}
button{font-family:'Barlow Condensed',sans-serif;font-size:16px;background:var(--panel);
color:var(--ink);border:1px solid var(--rule2);padding:6px 15px;border-radius:2px;cursor:pointer}
button:hover:not(:disabled){border-color:var(--spo2);color:var(--spo2)}
button:focus-visible{outline:2px solid var(--spo2);outline-offset:2px}
button:disabled{opacity:.5;cursor:default}
.clock{font-family:'Barlow Condensed',sans-serif;font-variant-numeric:tabular-nums;
font-size:28px;min-width:78px}
input[type=range]{accent-color:var(--spo2)}
#scrub{flex:1;min-width:150px}

.steps{position:relative;height:62px;margin-bottom:14px}
.step{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;
gap:10px;color:var(--dim);opacity:0;transition:opacity .35s;pointer-events:none}
.step.on{opacity:1}
.step svg{width:28px;height:28px;flex:none;color:var(--ink)}
.step span{font-family:'Barlow Condensed',sans-serif;font-size:17px;color:var(--ink)}
.step b{font-family:'Barlow Condensed',sans-serif;font-size:17px;font-weight:500;
font-variant-numeric:tabular-nums;color:var(--spo2)}
.caption{border-left:2px solid var(--spo2);padding:6px 0 6px 11px;margin-bottom:14px;
font-size:15px;min-height:40px;line-height:1.35}

.dials{display:grid;grid-template-columns:repeat(auto-fit,minmax(184px,1fr));gap:10px 20px;
background:var(--panel);border:1px solid var(--rule);padding:11px 14px;margin-bottom:14px}
.dial label{display:flex;justify-content:space-between;font-size:12px;color:var(--dim);
margin-bottom:2px}
.dial b{font-family:'Barlow Condensed',sans-serif;font-size:15px;color:var(--ink);
font-variant-numeric:tabular-nums;font-weight:500}
.dial input{width:100%}
.reset{grid-column:1/-1;justify-self:start}

.side{transition:opacity .18s ease}
/* Below the two-column breakpoint the panel simply goes away; there is no
   column for it to fold into. */
@media(max-width:1049px){body.sidehid .side{display:none}}
.arms{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.arm{background:var(--panel);border:1px solid var(--rule);padding:12px}
.armhead{display:flex;justify-content:space-between;align-items:baseline;gap:8px;
border-bottom:1px solid var(--rule);padding-bottom:7px;margin-bottom:10px}
.armname{font-family:'Barlow Condensed',sans-serif;font-size:18px;font-weight:500;
white-space:nowrap}
.armnote{font-size:11.5px;color:var(--dim);text-align:right;line-height:1.2}
.chan{display:flex;align-items:stretch;gap:10px;margin-top:6px}
.chan canvas{flex:1;min-width:0;margin-top:0}
.num{flex:none;width:98px;display:flex;flex-direction:column;justify-content:center;
align-items:flex-end;line-height:1;border-left:1px solid var(--rule);padding-left:9px}
.numlab{font-size:10.5px;color:var(--dim);letter-spacing:.04em;text-transform:uppercase}
.num .big{font-size:clamp(26px,3.2vw,46px)}
.numunit{font-size:10px;color:var(--dim);margin-top:2px}
.big{font-family:'Barlow Condensed',sans-serif;font-variant-numeric:tabular-nums;
font-size:clamp(34px,6vw,62px);line-height:.85;color:var(--sat)}
.biglab{font-size:11px;color:var(--dim);margin-bottom:-2px}
.ecg{width:100%;height:44px;display:block;margin-top:6px;background:#050a0d}
.plethw{width:100%;height:30px;display:block;margin-top:2px;background:#050a0d}
.stage{display:grid;grid-template-columns:126px minmax(0,1fr);gap:12px;align-items:start;
margin-top:10px}
@media(max-width:620px){.stage{grid-template-columns:82px minmax(0,1fr);gap:8px}
 /* two arms share a phone screen, so the numeric gives width back to the
    trace, which needs it more than the digits do */
 .chan{gap:6px} .num{width:58px;padding-left:6px} .num .big{font-size:25px}
 .numlab,.numunit{font-size:9px}}
canvas{width:100%;height:auto;display:block}
.row{display:flex;justify-content:space-between;gap:8px;border-bottom:1px solid var(--rule);
padding:3px 0;font-size:12.5px}
.row b{font-family:'Barlow Condensed',sans-serif;font-weight:500;font-size:15px;
font-variant-numeric:tabular-nums}
.k{color:var(--dim)}
.flat{color:var(--dim);font-size:11.5px;padding:4px 0}
.dead{color:var(--alarm)}
.stopped{opacity:.55}
.stoplab{font-family:'Barlow Condensed',sans-serif;font-size:12px;color:var(--alarm);
margin-top:-4px}
.legend{display:flex;gap:15px;font-size:12px;color:var(--dim);margin-top:14px;flex-wrap:wrap}
.sw{display:inline-block;width:10px;height:10px;margin-right:5px;vertical-align:-1px}
.credit{color:var(--dim);font-size:11px;line-height:1.45;margin-top:10px;max-width:78ch;
 opacity:.85}
.foot{color:var(--dim);font-size:12px;line-height:1.5;margin-top:16px;max-width:78ch;
border-top:1px solid var(--rule);padding-top:12px}
.busy{color:var(--co2);font-size:12px}
/* Expand cannot make the frame bigger - nothing inside a page can, and iOS
   blocks the Fullscreen API. So it does the useful thing instead: strips the
   chrome and FITS the two patients to whatever box is available, with no
   scrolling and nothing cut off. Everything is sized in viewport units so it
   adapts to a small embed and a projector alike. */
body.zen{overflow:hidden}
body.zen h1,body.zen .sub,body.zen .dials,body.zen .legend,body.zen .foot,
body.zen .steps{display:none}
body.zen .side{display:none}
body.zen #sidebtn{display:none}
body.zen .wrap{grid-template-columns:1fr}
body.zen .main{display:flex;flex-direction:column;min-height:0;height:100%}
body.zen .wrap{max-width:100%;height:100vh;height:100dvh;padding:6px 8px;
 display:flex;flex-direction:column;gap:6px}
body.zen .caption{margin:0;min-height:0;padding:2px 0 2px 10px;
 font-size:clamp(12px,2.1vh,17px)}
body.zen .transport{margin:0;gap:8px}
body.zen .transport button{padding:4px 11px;font-size:clamp(12px,1.9vh,16px)}
body.zen .clock{font-size:clamp(17px,3vh,28px);min-width:62px}
body.zen .arms{flex:1 1 auto;min-height:0;gap:8px}
body.zen .arm{padding:8px;min-height:0;overflow:hidden}
body.zen .armhead{padding-bottom:4px;margin-bottom:5px}
body.zen .armname{font-size:clamp(13px,2.2vh,19px)}
body.zen .armnote{font-size:clamp(9px,1.4vh,12px)}
body.zen .credit{margin:0;font-size:clamp(8px,1.15vh,11px);opacity:.75;
 white-space:nowrap;overflow:hidden;text-overflow:ellipsis;flex:none}
body.zen .big{font-size:clamp(26px,7.5vh,76px)}
body.zen .biglab{font-size:clamp(8px,1.3vh,11px)}
body.zen .ecg{height:clamp(26px,7vh,74px);margin-top:4px}
body.zen .plethw{height:clamp(17px,4.5vh,50px)}
/* Same fix as .main .stage: size the track by the canvas's own height
   expression times its aspect ratio, never by grid `auto`. body.zen is
   (0,2,0) so it already outranks the base rule -- the bug here was only the
   `auto`, not the specificity. */
body.zen .stage{grid-template-columns:calc(clamp(110px,32vh,330px)*252/404)
  minmax(0,1fr);gap:9px;margin-top:6px}
body.zen .stage canvas:not(.ecg){height:clamp(110px,32vh,330px);width:auto}
body.zen .row{font-size:clamp(10px,1.65vh,15px);padding:clamp(1px,0.35vh,5px) 0}
body.zen .row b{font-size:clamp(12px,2vh,19px)}
body.zen .flat{font-size:clamp(9px,1.3vh,12px);padding:2px 0}
</style></head><body><div class="wrap">
<div class="side" id="side">
<h1>An apnoea simulator</h1>
<p class="sub"><b>What this is.</b> A computational model of gas exchange during apnoea, run
forward in real time on two patients side by side. Everything on screen is computed from
the physiology &mdash; the oxygen stores, the dissociation curves, the shunt, the cardiac
output and the mechanics of a sealed lung &mdash; not replayed from a recording. Nothing is
animated for effect.</p>
<p class="sub"><b>What you are looking at.</b> Two identical patients, both obstructed from
induction. The only difference between them is what sits in the pharynx. In the lungs,
bright is oxygen and dull is nitrogen and CO&#8322;; the dark gap above is the vacuum the
obstruction creates as gas is absorbed and none replaces it, and the bases go violet as
they collapse. The head turns blue on <i>deoxygenated haemoglobin</i>, not on saturation
&mdash; which is why an anaemic patient never looks as bad as they are.</p>
<p class="sub"><b>How to use it.</b> Press Play. Move any slider and the whole simulation
re-computes from the new patient; nothing is interpolated. Collapsibility starts at the
calibrated median &mdash; the patients who desaturate despite good tracheal oxygen sit near
the top of its range, and that is worth seeing.</p>
<p class="sub"><b>What it is not.</b> Not a medical device and not validated for patient
care. It disagrees with the one human measurement of arterial oxygen under complete
obstruction by a wide margin, and that disagreement is recorded rather than hidden. Treat
it as a way to reason about mechanism, not as a predictor for an individual.</p>

<div class="dials" id="dials"></div>

<details class="sb" id="sb">
<summary>Scenario builder &mdash; edit the airway timeline</summary>
<p class="sbnote">Each row sets the airway <em>from</em> that moment until the next row.
The two arms differ only after the re-obstruction time: the control arm loses the
airway there, the device arm keeps it. Times are seconds from induction.</p>
<div class="sbrow"><label for="sbpre">Preset</label>
<select id="sbpre"></select>
<label for="sbend">Run length</label><input type="number" id="sbend" min="120" max="1800" step="30">
<label for="sbre">Control arm re-obstructs at</label>
<input type="number" id="sbre" min="0" max="1800" step="10" placeholder="never">
<button type="button" id="sbclear">never</button></div>
<table class="sbt" id="sbt"><thead><tr><th>Time (s)</th><th>Label</th>
<th>Airway</th><th>Icon</th><th></th></tr></thead><tbody></tbody></table>
<div class="sbrow"><button type="button" id="sbadd">Add segment</button>
<button type="button" id="sbapply">Apply</button>
<span class="sberr" id="sberr"></span></div>
</details>
<p class="foot">Modelled, not measured. Saturation carries a pulse oximeter delay. There is no
end-tidal CO&#8322; because there is no ventilation; the CO&#8322; and pH shown are arterial model
values you would not have at the bedside. Each arm stops where the model's fixed cardiac
output stops being defensible. The FRC relation's height and age basis is
Quanjer 1993's ECSC reference equation, read at source; its BMI term is
parameterised and agrees with, but was not fitted to, Pelosi 1998's measured
helium regression. Closing capacity's values are placeholders that disagree
with their own source (Buist &amp; Ross 1973). <strong>The model uses Quanjer's
MALE equations for every patient</strong>, by ruling: a woman of the same
height has about 14% less FRC and 16% less total lung capacity.</p>
</div>

<div class="main">
<div class="transport">
<button id="sidebtn" aria-controls="side" aria-expanded="true">Hide sliders</button>
<button id="runbtn">Run simulation</button>
<button id="play">Play</button><button id="rew">Restart</button>
<button id="fs">Expand</button>
<button id="snd">Sound off</button><button id="spd">4&times;</button>
<span class="clock" id="clock">0:00</span>
<input type="range" id="scrub" min="0" max="900" value="0" step="1" aria-label="Time">
<span class="busy" id="busy"></span>
</div>
<div class="steps" id="steps"></div>
<div class="caption" id="cap"></div>
<div class="arms">
<div class="arm"><div class="armhead"><span class="armname">No buccal oxygen</span>
<span class="armnote">pharynx holds room air</span></div>
<div class="chan"><canvas class="ecg" id="eA" width="600" height="88"></canvas>
<div class="num"><div class="numlab">ECG</div><div class="big" id="hA">--</div>
<div class="numunit">bpm</div></div></div>
<div class="chan"><canvas class="plethw" id="wA" width="600" height="60"></canvas>
<div class="num"><div class="numlab">SpO&#8322;</div><div class="big" id="sA">--</div>
<div class="numunit">%<span class="stoplab" id="tA"></span></div></div></div>
<div class="stage"><canvas id="bA" width="252" height="404"></canvas><div class="rows" id="mA"></div></div></div>
<div class="arm"><div class="armhead"><span class="armname">Buccal oxygen</span>
<span class="armnote" id="noteB">pharynx at 100% O&#8322;</span></div>
<div class="chan"><canvas class="ecg" id="eB" width="600" height="88"></canvas>
<div class="num"><div class="numlab">ECG</div><div class="big" id="hB">--</div>
<div class="numunit">bpm</div></div></div>
<div class="chan"><canvas class="plethw" id="wB" width="600" height="60"></canvas>
<div class="num"><div class="numlab">SpO&#8322;</div><div class="big" id="sB">--</div>
<div class="numunit">%<span class="stoplab" id="tB"></span></div></div></div>
<div class="stage"><canvas id="bB" width="252" height="404"></canvas><div class="rows" id="mB"></div></div></div>
</div>

<div class="legend"><span><i class="sw" style="background:var(--o2)"></i>oxygen in the lung</span>
<span><i class="sw" style="background:var(--inert)"></i>nitrogen and CO&#8322;</span>
<span><i class="sw" style="background:#0a1218;border:1px solid var(--rule2)"></i>vacuum</span></div>

<p class="credit">&copy; 2026 A. M. B. Heard. All rights reserved. Unpublished research model
&mdash; not a medical device, not for patient care. Reproduction or use in any publication
requires the author's written permission.</p>

</div>
</div>
<script>
__MODEL__
</script>
<script>

const ICONS={
syringe:'<svg viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"><path d="M4 28l5-5"/><path d="M8 24l-2 4 4-2"/><rect x="10.5" y="9" width="13" height="8" rx="1" transform="rotate(45 17 13)"/><path d="M13.5 19.5l-2.5-2.5M17 16l-2.5-2.5M20.5 12.5L18 10"/><path d="M22 10l5-5M24 4l4 4"/></svg>',
mask:'<svg viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M16 27c-6 0-9-4.5-9-10 0-4.5 3.5-8 9-8s9 3.5 9 8c0 5.5-3 10-9 10z"/><rect x="13" y="3" width="6" height="6" rx="1"/><path d="M11 17h10"/></svg>',
lma:'<svg viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="1.6"><ellipse cx="16" cy="22" rx="7" ry="8"/><ellipse cx="16" cy="22" rx="3.5" ry="4.5"/><path d="M16 14V6"/><rect x="13" y="2" width="6" height="4" rx="1"/></svg>',
blade:'<svg viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M6.4 5.4 C5.2 6.8 5.8 8.8 6.6 10.3 C5.8 15 6.0 19.6 7.8 23.4 C10.0 28.0 14.8 30.0 19.6 28.5 L28.2 22.7 L26.6 20.4 L19.4 25.3 C16.6 26.1 14.0 24.5 12.8 21.9 C11.4 18.7 11.6 14.3 12.5 10.3 C13.5 9.5 14.7 8.7 15.1 7.5 C15.5 6.1 14.7 4.9 13.3 4.5 L8.3 2.9 C7.0 2.5 6.7 4.1 6.4 5.4 Z"/></svg>'};

// ---- THE SCENARIO, AS DATA ---------------------------------------------
// Until 2026-09-25 the timeline was hardcoded in three places that had to be
// kept in step by hand: a resistance function R(t), a STEPS array for the
// icon strip and an EVENTS array for the caption. Editing one and not the
// others was a standing trap. They are now all DERIVED from one editable
// scenario, and the page can build its own.
//
// airway is the state of the airway FROM this moment until the next segment:
//   patent      R = 2      an open airway, a blade in place, an LMA that works
//   partial     R = 8      a narrowed but not closed airway
//   obstructed  R = OBS    nothing moves
// reobstructAt, if set, is the moment the CONTROL arm loses the airway again
// while the device arm keeps it -- the A/B comparison this page exists for.
//
// VERIFIED IDENTICAL to the hardcoded version it replaced, over 40
// combinations of LMA state, oxygen start time, arm and FiO2: 0 mismatches.
// Resistances are read LAZILY: OBS is declared further down this script
// and a direct reference here hits its temporal dead zone -- caught by
// loading the page in Chromium, which is now part of building it.
const AIRWAY_R={patent:()=>2,partial:()=>8,obstructed:()=>OBS};
const AIRWAY_LABEL={patent:'Patent',partial:'Partial',obstructed:'Obstructed'};
const PRESETS={
 'cico':{name:'Cannot intubate, cannot oxygenate',end:900,reobstructAt:430,segs:[
   {t:0,icon:'syringe',label:'Induction',airway:'obstructed',
    note:'Induction. Airway obstructs immediately.'},
   {t:120,icon:'mask',label:'Facemask ventilation fails',airway:'partial',
    note:'Facemask off, LMA going in'},
   {t:130,icon:'lma',label:'LMA inserted',airway:'obstructed',
    note:'LMA in place but no patent airway'},
   {t:160,icon:'lma',label:'LMA out, laryngospasm',airway:'obstructed',
    note:'LMA out. Laryngospasm. Drawing up rocuronium.'},
   {t:220,icon:'syringe',label:'Rocuronium given',airway:'obstructed',
    note:'Rocuronium given. 60 s to work.'},
   {t:280,icon:'blade',label:'Laryngoscopy',airway:'patent',
    note:'Laryngoscopy \\u2014 airway open, view obtained'},
   {t:430,icon:'blade',label:'Blade out (control) / left in (device)',
    airway:'patent',note:'Blade out (control) / blade left in (buccal)'}]},
 'patent':{name:'Patent airway throughout (Toner / Heard shape)',end:900,
   reobstructAt:null,segs:[
   {t:0,icon:'syringe',label:'Induction, airway held open',airway:'patent',
    note:'Induction. Airway kept patent throughout \\u2014 apnoeic oxygenation only.'}]},
 'obstructed':{name:'Obstructed throughout (Stock shape)',end:900,
   reobstructAt:null,segs:[
   {t:0,icon:'syringe',label:'Induction, airway obstructs',airway:'obstructed',
    note:'Induction. Complete obstruction from the first second.'}]},
 'lategain':{name:'Airway regained late',end:900,reobstructAt:null,segs:[
   {t:0,icon:'syringe',label:'Induction',airway:'obstructed',
    note:'Induction. Airway obstructs immediately.'},
   {t:300,icon:'lma',label:'LMA finally seats',airway:'partial',
    note:'LMA seats at last \\u2014 a narrowed airway, not a patent one'},
   {t:420,icon:'blade',label:'Laryngoscopy',airway:'patent',
    note:'Laryngoscopy \\u2014 airway open'}]}};
let SCENARIO=JSON.parse(JSON.stringify(PRESETS['cico']));
const STEPS=()=>SCENARIO.segs.map(s=>[s.t,s.icon,s.label]);
const EVENTS=()=>SCENARIO.segs.map(s=>[s.t,s.note]);

const DIALS=[
 ['weight','Body weight',45,180,1,107,null],
 ['height','Height',1.45,2.05,0.01,1.75,null],
 ['frcScale','FRC',0.55,1.5,0.01,1.0,null],
 ['bmrScale','Metabolic rate',0.6,1.7,0.01,1.0,null],
 ['hb','Haemoglobin',4.0,18.0,0.5,14.0,null],
 ['ccScale','Closing capacity',0.6,1.6,0.01,1.0,null],
 ['maxClosed','Lung collapsibility',0.10,0.65,0.01,0.25,null],
 ['tauMix','Cardiogenic mixing',10,300,5,45,null],
 ['fgBuccal','Pharyngeal O\u2082 (device arm)',0.21,1.00,0.01,1.00,null],
 ['inflowMechFrac','Absorption atelectasis',0.0,0.55,0.01,0.18,null],
 ['tiltDeg','Bed tilt (head up)',-20,45,1,25,null],
 ['buccalIdx','Buccal switched on',0,4,1,0,null]];
// The decision points an anaesthetist actually has, not arbitrary seconds.
const STARTS=[[0,'From induction'],[120,'After mask ventilation fails'],
 [160,'After the LMA fails'],[280,'At laryngoscopy'],
 [370,'After failed intubation attempts']];

const BASE={age:45,lmaOpens:true,frcRef:2500,frcDrop:400,tiltDeg:25,
 ccAt20:1800,ccPerYear:20,ccPerBmi:45,ccK:1.5,vo2Ref:250,coRef:5,crs:75,
 vArt:1.0,vVen:2.0,vTisO2:1.5,feo2:0.87,rv:1100,kRvBmi:0.0198,pCollapse:-149.5461,nVq:80};
const P=Object.assign({},BASE);
DIALS.forEach(d=>P[d[0]]=d[5]);

const stepsEl=document.getElementById('steps');
// Re-rendered whenever the scenario changes, rather than built once: the
// icon strip is a VIEW of SCENARIO now, not a second copy of it.
function renderSteps(){
 stepsEl.innerHTML='';
 STEPS().forEach(([t,ic,lab])=>{const d=document.createElement('div');d.className='step';
  d.dataset.t=t;
  const mmss=Math.floor(t/60)+':'+String(t%60).padStart(2,'0');
  d.innerHTML=ICONS[ic||'syringe']+'<b>'+mmss+'</b><span>'+lab+'</span>';
  stepsEl.appendChild(d);});
}
renderSteps();

// ---- the scenario builder -------------------------------------------------
// The page's own timeline, editable. Everything here is VIEW code: the single
// source of truth is SCENARIO, and tl(), renderSteps() and the caption all
// derive from it. Nothing in this block touches the physics.
const sbT=document.querySelector('#sbt tbody'), sbErr=document.getElementById('sberr');
function sbRow(seg){
 const tr=document.createElement('tr');
 const opts=Object.keys(AIRWAY_LABEL).map(k=>
   '<option value="'+k+'"'+(seg.airway===k?' selected':'')+'>'+AIRWAY_LABEL[k]+'</option>').join('');
 const icons=Object.keys(ICONS).map(k=>
   '<option value="'+k+'"'+(seg.icon===k?' selected':'')+'>'+k+'</option>').join('');
 tr.innerHTML='<td><input type="number" min="0" step="10" value="'+seg.t+'"></td>'+
  '<td><input type="text" value="'+(seg.label||'').replace(/"/g,'&quot;')+'"></td>'+
  '<td><select>'+opts+'</select></td>'+
  '<td><select>'+icons+'</select></td>'+
  '<td><button type="button" title="Remove">&times;</button></td>';
 tr.querySelector('button').onclick=()=>{
   if(sbT.children.length<2){sbErr.textContent='A scenario needs at least one segment.';return;}
   tr.remove();};
 return tr;
}
function sbRender(){
 sbT.innerHTML=''; SCENARIO.segs.forEach(sg=>sbT.appendChild(sbRow(sg)));
 document.getElementById('sbend').value=SCENARIO.end;
 document.getElementById('sbre').value=(SCENARIO.reobstructAt==null?'':SCENARIO.reobstructAt);
}
function sbApply(){
 sbErr.textContent='';
 const segs=[...sbT.children].map(tr=>{
  const f=tr.querySelectorAll('input,select');
  return {t:Math.max(0,Math.round(+f[0].value||0)),label:f[1].value.trim()||'(unlabelled)',
          airway:f[2].value,icon:f[3].value,note:f[1].value.trim()||''};
 }).sort((a,b)=>a.t-b.t);
 const end=Math.round(+document.getElementById('sbend').value||900);
 const reRaw=document.getElementById('sbre').value.trim();
 const re=(reRaw===''?null:Math.round(+reRaw));
 if(segs[0].t!==0){sbErr.textContent='The first segment must start at 0 s.';return;}
 for(let i=1;i<segs.length;i++) if(segs[i].t===segs[i-1].t){
   sbErr.textContent='Two segments share a start time ('+segs[i].t+' s).';return;}
 if(end<=segs[segs.length-1].t){
   sbErr.textContent='The run must be longer than the last segment.';return;}
 if(re!=null&&(re<0||re>end)){sbErr.textContent='Re-obstruction must fall inside the run.';return;}
 SCENARIO={name:'Custom',end:end,reobstructAt:re,segs:segs};
 const sc=document.getElementById('scrub'); sc.max=end; if(+sc.value>end) sc.value=end;
 renderSteps(); D={}; labels(); run();
}
const sbPre=document.getElementById('sbpre');
Object.keys(PRESETS).forEach(k=>{const o=document.createElement('option');
 o.value=k;o.textContent=PRESETS[k].name;sbPre.appendChild(o);});
sbPre.onchange=()=>{SCENARIO=JSON.parse(JSON.stringify(PRESETS[sbPre.value]));
 sbRender(); sbApply();};
document.getElementById('sbadd').onclick=()=>{
 const last=SCENARIO.segs[SCENARIO.segs.length-1];
 sbT.appendChild(sbRow({t:Math.min(SCENARIO.end-10,(last?last.t:0)+60),
   label:'New step',airway:'obstructed',icon:'syringe'}));};
document.getElementById('sbapply').onclick=sbApply;
document.getElementById('sbclear').onclick=()=>{
 document.getElementById('sbre').value='';};
sbRender();

const dialsEl=document.getElementById('dials');
DIALS.forEach(([key,lab,lo,hi,st,def,fmt])=>{
 const w=document.createElement('div');w.className='dial';
 w.innerHTML='<label><span>'+lab+'</span><b id="v_'+key+'"></b></label>'+
  '<input type="range" id="d_'+key+'" min="'+lo+'" max="'+hi+'" step="'+st+'" value="'+def+'">';
 dialsEl.appendChild(w);
 w.querySelector('input').addEventListener('input',e=>{P[key]=+e.target.value;dirty();});});
const rb=document.createElement('button');rb.className='reset';rb.textContent='Reset patient';
rb.onclick=()=>{DIALS.forEach(d=>{P[d[0]]=d[5];document.getElementById('d_'+d[0]).value=d[5];});
 P.lmaOpens=true; lmaBtn.textContent='LMA briefly opens airway'; dirty();};
const lmaBtn=document.createElement('button');
lmaBtn.className='reset';lmaBtn.textContent='LMA briefly opens airway';
lmaBtn.onclick=()=>{P.lmaOpens=!P.lmaOpens;
 lmaBtn.textContent=P.lmaOpens?'LMA briefly opens airway':'LMA never opens airway';
 dirty();};
dialsEl.appendChild(lmaBtn);dialsEl.appendChild(rb);

const cvs={A:bA,B:bB},mon={A:mA,B:mB},sN={A:sA,B:sB},hN={A:hA,B:hB},tL={A:tA,B:tB};
const css=k=>getComputedStyle(document.documentElement).getPropertyValue(k).trim();
const OBS=Infinity;
// Airway resistance by time, and the pharyngeal oxygen fraction switched on
// at an arbitrary moment. Splitting on both boundary sets lets the device be
// started before, during or long after the airway first opens.
function segAirwayAt(t){let a=SCENARIO.segs[0].airway;
 for(const s of SCENARIO.segs) if(t>=s.t) a=s.airway; return a;}
function tl(fg,startAt,keep){
 const cuts=[...new Set([0,...SCENARIO.segs.map(s=>s.t),
   ...(SCENARIO.reobstructAt!=null?[SCENARIO.reobstructAt]:[]),startAt,SCENARIO.end])]
   .filter(v=>v>=0&&v<=SCENARIO.end).sort((a,b)=>a-b);
 const ep=[];
 for(let i=0;i<cuts.length-1;i++){
  const a=cuts[i],b=cuts[i+1];
  let st=segAirwayAt(a);
  // The LMA dial overrides a PARTIAL segment: an LMA that does not open the
  // airway leaves it obstructed. Kept from the hardcoded version.
  if(st==='partial'&&P.lmaOpens===false) st='obstructed';
  let R=AIRWAY_R[st]();
  if(SCENARIO.reobstructAt!=null&&a>=SCENARIO.reobstructAt&&!keep) R=OBS;
  ep.push({d:b-a,R:R,fg:(a>=startAt?fg:0.21)});
 }
 return ep;
}
let D={},T=0,playing=false,last=0,pend=null,SPEED=4;

// ---- ECG -------------------------------------------------------------------
// Synthetic P-QRS-T from Gaussians. Only the RATE carries information;
// the morphology is decorative and should not be read as anything.
const ecgCv={A:document.getElementById('eA'),B:document.getElementById('eB')};
const trace={A:new Float32Array(600),B:new Float32Array(600)};
const phase={A:0,B:0};
const plethCv={A:document.getElementById('wA'),B:document.getElementById('wB')};
const plethTrace={A:new Float32Array(600),B:new Float32Array(600)};
const SR=220;   // trace sample rate, samples per second of wall clock
const acc={A:0,B:0};   // fractional sample carried between frames
function ecgWave(p){
  const g=(c,w,a)=>a*Math.exp(-((p-c)*(p-c))/(2*w*w));
  return g(0.15,0.022,0.12)+g(0.29,0.007,-0.14)+g(0.315,0.009,1.0)
       +g(0.345,0.011,-0.28)+g(0.52,0.042,0.26);
}
// ---- plethysmograph --------------------------------------------------------
// The pulse oximeter's own trace, the waveform an anaesthetist reads the SpO2
// number off. It is driven from the SAME cardiac phase as the ECG, delayed by
// a pulse transit time, so every upstroke follows its own QRS and the two can
// never drift apart however the rate changes.
//
// As with the ECG, only the RATE carries information. The morphology is
// decorative: a real pleth's amplitude tracks peripheral pulse volume, and
// this model has no peripheral vascular bed to predict that from. Do not read
// the shape as anything. What IS honest is the rhythm, and the flatline - it
// stops when the modelled heart stops, at the same instant as the ECG.
const R_WAVE=0.315;   // phase of the R peak in ecgWave()
const PTT=0.22;       // s, pulse transit time to a finger probe: the delay
                      // from the R wave to the FOOT of the pulse. Held in
                      // absolute time rather than as a fraction of the cycle,
                      // because that is what it is - a fraction would stretch
                      // to most of a second at the terminal escape rates and
                      // put the pulse nowhere near its own QRS.
const PLETH_NORM=1.243;   // peak of the unnormalised sum, so this returns 0-1
function plethWave(p,hr){
  const q=(p-R_WAVE-PTT*hr/60+2)%1;
  // fast systolic upstroke into a rounded peak, the dicrotic wave after the
  // notch, then a diastolic runoff that carries through to the next upstroke
  // so the trace never sits dead flat between beats
  const s=q<0.11?0.048:0.095;
  const peak=Math.exp(-((q-0.11)*(q-0.11))/(2*s*s));
  const dicrotic=0.28*Math.exp(-((q-0.35)*(q-0.35))/(2*0.058*0.058));
  const runoff=0.34*Math.exp(-q/0.50)*(1-Math.exp(-q/0.05));
  return (peak+dicrotic+runoff)/PLETH_NORM;
}
function ecgStep(k,hr,wall){
  const tr=trace[k],pw=plethTrace[k],N=tr.length;
  // One sample is 1/SR of a second, so the phase advance PER SAMPLE follows
  // the heart rate alone. It used to be beats/steps, which spread the whole
  // interval's beats across however many samples the loop actually ran -- so
  // whenever the cap below engaged the waveform came out time-compressed
  // rather than merely truncated. Capping is allowed to drop trace off the
  // left-hand end; it is not allowed to change the shape of what it draws.
  const dph=hr>1?hr/60/SR:0;
  // Carry the fractional sample between frames so the sweep advances at
  // exactly SR samples per wall second. Rounding it away per frame made the
  // sweep speed depend on the frame duration -- 250 samples/s at a 16 ms
  // frame against 212 at 33 ms, a 13.6% error either side of the truth -- and
  // since the beats are spaced in SAMPLES, the rate you saw inherited it.
  acc[k]+=wall*SR;
  let steps=Math.floor(acc[k]);
  acc[k]-=steps;
  // Writing more than N samples would only overwrite work already done, so N
  // is the natural bound. It stops a long stall (a backgrounded tab) from
  // spinning; the backlog is dropped rather than banked.
  if(steps>N){ steps=N; acc[k]=0; }
  for(let s=0;s<steps;s++){
    phase[k]=(phase[k]+dph)%1;
    tr.copyWithin(0,1); tr[N-1]=hr>1?ecgWave(phase[k]):0;
    pw.copyWithin(0,1); pw[N-1]=hr>1?plethWave(phase[k],hr):0;
  }
}
function ecgDraw(k){
  const cv=ecgCv[k],g=cv.getContext('2d'),W=cv.width,H=cv.height,tr=trace[k];
  g.clearRect(0,0,W,H);
  g.strokeStyle=css('--ecg-line'); g.lineWidth=1.8; g.beginPath();
  for(let i=0;i<tr.length;i++){
    const x=i*W/tr.length, y=H*0.62-tr[i]*H*0.46;
    i?g.lineTo(x,y):g.moveTo(x,y);
  }
  g.stroke();
}
function plethDraw(k){
  const cv=plethCv[k],g=cv.getContext('2d'),W=cv.width,H=cv.height,tr=plethTrace[k];
  const N=tr.length, base=H*0.93, amp=H*0.78;
  g.clearRect(0,0,W,H);
  const path=close=>{
    g.beginPath();
    for(let i=0;i<N;i++){
      const x=i*W/N, y=base-tr[i]*amp;
      i?g.lineTo(x,y):g.moveTo(x,y);
    }
    if(close){ g.lineTo(W,base); g.lineTo(0,base); g.closePath(); }
  };
  // trace and numeric carry the same colour, which is what lets you pair them
  // at a glance -- the SR6000's pleth and its SpO2 are both yellow for exactly
  // this reason
  path(true); g.globalAlpha=0.20; g.fillStyle=css('--sat'); g.fill(); g.globalAlpha=1;
  path(false); g.strokeStyle=css('--sat'); g.lineWidth=1.6; g.stroke();
}

// ---- pulse oximeter tone ---------------------------------------------------
// Pitch falls with saturation, about an octave per 20% - the mapping every
// anaesthetist's ear is trained on. Beat rate follows the modelled heart rate.
let actx=null, soundArm=null;
function beep(spo2){
  if(!actx) return;
  const o=actx.createOscillator(), g=actx.createGain();
  o.type='sine';
  o.frequency.value=Math.max(90,880*Math.pow(2,(spo2-100)*0.6/12));
  g.gain.setValueAtTime(0.0001,actx.currentTime);
  g.gain.exponentialRampToValueAtTime(0.22,actx.currentTime+0.008);
  g.gain.exponentialRampToValueAtTime(0.0001,actx.currentTime+0.13);
  o.connect(g).connect(actx.destination);
  o.start(); o.stop(actx.currentTime+0.15);
}

// The lung is 80 parallel compartments, so a full run takes a few seconds.
// Compute once on demand, then play back. This runs on the main thread on
// purpose: a Worker built from a blob URL is blocked in sandboxed embeds,
// which left the page stuck on "computing" with no way to recover.
let stale=true;
const busy=document.getElementById('busy');
const runBtn=document.getElementById('runbtn');

function labels(){
 document.getElementById('v_weight').textContent=P.weight+' kg';
 document.getElementById('v_tiltDeg').textContent=
   (P.tiltDeg>0?'+':'')+P.tiltDeg.toFixed(0)+'\u00b0'+
   (D.B?' \u00b7 FRC '+D.B.frc.toFixed(0)+' mL':'');
 document.getElementById('v_height').textContent=
   P.height.toFixed(2)+' m \u00b7 BMI '+(P.weight/(P.height*P.height)).toFixed(1);
  document.getElementById('v_tauMix').textContent=P.tauMix.toFixed(0)+' s';
 // Below 7 g/dL the resting cardiac output rises to defend delivery, so say
 // so on the dial: the number on its own does not tell you the circulation
 // has changed underneath it.
 {const hb=P.hb, thr=7.0;
  const f=hb>=thr?1:Math.min(3,Math.pow(thr/Math.max(hb,0.5),1.535));
  document.getElementById('v_hb').textContent=
    hb.toFixed(1)+' g/dL'+(f>1.005?' \u00b7 CO \u00d7'+f.toFixed(1):'');}
 document.getElementById('v_fgBuccal').textContent=(P.fgBuccal*100).toFixed(0)+'%';
 if(D.B) document.getElementById('v_inflowMechFrac').textContent=
   'atelectasis '+(D.B.atel[D.B.atel.length-1]*100).toFixed(0)+'%';
 const st=STARTS[P.buccalIdx], mm=Math.floor(st[0]/60)+':'+
   String(st[0]%60).padStart(2,'0');
 document.getElementById('v_buccalIdx').textContent=mm;
 document.querySelector('#d_buccalIdx').previousElementSibling
   .firstElementChild.textContent=st[1];
 document.getElementById('noteB').textContent=
   (P.buccalIdx>0?'on at '+mm+' \u00b7 ':'')+
   (P.fgBuccal*100).toFixed(0)+'% O\u2082';
 if(D.B){
  document.getElementById('v_frcScale').textContent=D.B.frc.toFixed(0)+' mL';
  document.getElementById('v_bmrScale').textContent=D.B.vo2.toFixed(0)+' mL/min';
  document.getElementById('v_ccScale').textContent=D.B.cc.toFixed(0)+' mL';
  document.getElementById('v_maxClosed').textContent=
    'shunt '+(D.B.shunt[D.B.shunt.length-1]*100).toFixed(0)+'%';
 }
}
function dirty(){stale=true;busy.textContent='parameters changed';
 runBtn.textContent='Run simulation';labels();}

function run(){
 playing=false;document.getElementById('play').textContent='Play';
 runBtn.disabled=true;busy.textContent='computing...';
 // yield once so the status text paints before we block
 setTimeout(()=>{
  try{
   const t0=performance.now();
   D.A=simulate(P,tl(0.21,0,false));
   D.B=simulate(P,tl(P.fgBuccal,STARTS[P.buccalIdx][0],true));
   stale=false; T=0;
   busy.textContent=((performance.now()-t0)/1000).toFixed(1)+' s';
   // prime both traces with resting beats so they read as a rhythm at rest
   for(const k of ['A','B']){ phase[k]=0; acc[k]=0;
     trace[k].fill(0); plethTrace[k].fill(0);
     ecgStep(k, D[k].hr[0], trace[k].length/SR); }
   runBtn.textContent='Re-run';
  }catch(err){
   busy.textContent='error: '+err.message;
  }
  runBtn.disabled=false; labels(); render();
 },30);
}

const at=(a,k,t)=>t>=a.t[a.t.length-1]?a[k][a[k].length-1]:a[k][Math.min(Math.round(t),a.t.length-1)];
const alive=(a,t)=>t<=a.t[a.t.length-1];
const isOpen=(k,t)=>(t>=120&&t<130)||(k==='B'?t>=280:(t>=280&&t<430));

// The patient, as the anaesthetist sees them from the head of the table: two
// lungs beyond, the head in profile nearest, the trachea between. Fill height
// is gas volume, bright is oxygen, dull is nitrogen and CO2, the dark gap above
// is the vacuum obstruction creates.
//
// Two things here are physiology rather than decoration. The bases go violet as
// compartments collapse, because collapse starts dependent and the tilt slider
// moves it. And the head turns blue on DEOXYGENATED HAEMOGLOBIN, not on
// saturation: cyanosis needs roughly 5 g/dL of it, so at Hb 15 the head starts
// turning near SpO2 67% while at Hb 4 it can never turn at all, however dead
// the patient is. That trap falls straight out of the Hb slider.
const SKIN=[198,158,136], CYAN=[86,100,158], ATEL=[122,74,140];
// Hair does NOT track saturation -- it is the one part of the head that
// holds its colour while the skin goes blue, which is what makes the
// cyanosis read as a change rather than as a different drawing.
const HAIR='#4a3a32';
function mixc(a,b,f){f=Math.max(0,Math.min(1,f));
 // parenthesised: without them these are string concatenations, not sums,
 // and the head renders white at every saturation.
 const m=i=>Math.round(a[i]+(b[i]-a[i])*f);
 return 'rgb('+m(0)+','+m(1)+','+m(2)+')';}

// One lung in a normalised box; mirrored for the other side so the concave
// medial border faces the trachea on both.
function lungPath(g,x,y,w,h,flip){
 g.save(); g.translate(x+(flip?w:0),y); g.scale(flip?-1:1,1);
 g.beginPath();
 g.moveTo(w*0.66,h*0.02);
 g.bezierCurveTo(w*0.40,h*0.00, w*0.04,h*0.24, w*0.07,h*0.64);
 g.bezierCurveTo(w*0.09,h*0.89, w*0.22,h*0.99, w*0.44,h*0.99);
 g.lineTo(w*0.82,h*0.99);
 g.bezierCurveTo(w*0.95,h*0.72, w*0.92,h*0.34, w*0.80,h*0.16);
 g.bezierCurveTo(w*0.75,h*0.06, w*0.71,h*0.02, w*0.66,h*0.02);
 g.closePath(); g.restore();
}

// Profile, neck uppermost so the trachea meets it, face to the viewer's left.
// The facial detail is drawn with straight segments and the cranium with
// curves; smoothing the nose and lips rounds them away at this size.
function headPath(g,cx,yN,h){
 // Profile, NECK UPPERMOST so the trachea meets it, face to the viewer's
 // left. u runs 0 at the neck to ~1.0 at the vertex, so LARGER u IS FURTHER
 // DOWN THE CANVAS -- get that backwards and the eyebrow lands on the chin.
 // Redrawn 2026-09-22. The old version was all straight segments, which gave
 // a spiked nose, a zigzag mouth and a visible corner at the jaw. Curves now
 // carry the jaw, the lips and the whole skull; only the nose keeps a hard
 // tip, because rounding it at this size erases it. The neck is also wider,
 // which stops the silhouette reading as a teardrop.
 const X=v=>cx+v, Y=u=>yN+u*h;
 g.beginPath();
 g.moveTo(X(-22),Y(0.000));                                          // throat
 g.bezierCurveTo(X(-28),Y(0.07), X(-36),Y(0.14), X(-46),Y(0.195));   // jaw
 g.bezierCurveTo(X(-51),Y(0.225), X(-53),Y(0.255), X(-52),Y(0.285)); // chin
 g.bezierCurveTo(X(-51),Y(0.305), X(-50),Y(0.315), X(-49),Y(0.325)); // lower lip
 g.bezierCurveTo(X(-51),Y(0.345), X(-53),Y(0.360), X(-53),Y(0.378)); // upper lip
 g.bezierCurveTo(X(-52),Y(0.395), X(-51),Y(0.408), X(-50),Y(0.420)); // subnasale
 g.lineTo(X(-65),Y(0.462));                                          // nose tip
 g.bezierCurveTo(X(-57),Y(0.492), X(-50),Y(0.505), X(-47),Y(0.522)); // bridge
 g.bezierCurveTo(X(-51),Y(0.552), X(-54),Y(0.578), X(-54),Y(0.605)); // brow ridge
 g.bezierCurveTo(X(-57),Y(0.78), X(-44),Y(0.95), X(-16),Y(1.00));    // forehead
 g.bezierCurveTo(X(14),Y(1.05), X(44),Y(0.97), X(54),Y(0.78));       // vertex
 g.bezierCurveTo(X(63),Y(0.56), X(58),Y(0.30), X(42),Y(0.16));       // occiput
 g.lineTo(X(30),Y(0.000));                                           // nape
 g.closePath();
}

// The hair, as an explicit CRESCENT rather than a filled half-plane. Two
// earlier attempts filled "everything beyond the hairline" inside a large
// bounding box; both left the patient bald across the forehead, because the
// box closed back across its own hairline and the nonzero winding rule
// cancelled the wedge between them. A ring has no such ambiguity.
//
// The OUTER edge reuses headPath's own forehead, vertex and occiput control
// points, so the hair and the skull cannot drift apart when either is
// adjusted. The INNER edge is the hairline, shaped to pass BEHIND and ABOVE
// the ear so the ear stays on the skin side and remains visible.
function hairPath(g,cx,yN,h){
 const X=v=>cx+v, Y=u=>yN+u*h;
 g.beginPath();
 g.moveTo(X(-55),Y(0.690));                                          // temple
 g.bezierCurveTo(X(-57),Y(0.78), X(-44),Y(0.95), X(-16),Y(1.00));    // forehead
 g.bezierCurveTo(X(14),Y(1.05), X(44),Y(0.97), X(54),Y(0.78));       // vertex
 g.bezierCurveTo(X(63),Y(0.56), X(58),Y(0.30), X(42),Y(0.16));       // occiput
 g.lineTo(X(32),Y(0.055));                                           // nape
 g.bezierCurveTo(X(36),Y(0.34), X(32),Y(0.56), X(20),Y(0.68));       // behind the ear
 g.bezierCurveTo(X(-4),Y(0.84), X(-34),Y(0.78), X(-55),Y(0.690));    // hairline
 g.closePath();
}

// Eye, brow and ear. Kept as one function so the three cannot be adjusted out
// of register with each other; all three take their positions from the same
// u scale as the profile above.
function facePath(g,cx,yN,h,hair,ink){
 const X=v=>cx+v, Y=u=>yN+u*h;
 // closed lid -- a shallow arc, not a straight scratch
 g.strokeStyle=ink; g.lineWidth=2.0; g.lineCap='round';
 g.beginPath();
 g.moveTo(X(-44),Y(0.556));
 g.quadraticCurveTo(X(-36),Y(0.588), X(-25),Y(0.578));
 g.stroke();
 // brow, forehead-ward of the lid (HIGHER u) and arched the same way
 g.strokeStyle=hair; g.lineWidth=3.4;
 g.beginPath();
 g.moveTo(X(-47),Y(0.612));
 g.quadraticCurveTo(X(-37),Y(0.648), X(-24),Y(0.632));
 g.stroke();
 // ear: helix plus a short antihelix, in front of the hairline
 g.strokeStyle=ink; g.lineWidth=1.8; g.lineCap='butt';
 g.beginPath();
 g.moveTo(X(2),Y(0.408));
 g.bezierCurveTo(X(16),Y(0.410), X(20),Y(0.470), X(14),Y(0.520));
 g.bezierCurveTo(X(10),Y(0.552), X(4),Y(0.556), X(1),Y(0.548));
 g.stroke();
 g.lineWidth=1.3;
 g.beginPath();
 g.moveTo(X(5),Y(0.438));
 g.quadraticCurveTo(X(12),Y(0.462), X(8),Y(0.508));
 g.stroke();
}

function patient(k,t){
 const cv=cvs[k],a=D[k],g=cv.getContext('2d'),W=cv.width,H=cv.height;
 g.clearRect(0,0,W,H);
 const cx=W/2;
 const lT=14, lB=190, lw=W*0.375, gap=W*0.055;
 const carina=lB+12, neck=250, headH=H-neck-6;

 const vol=at(a,'vol',t), fao2=at(a,'fao2',t), atel=at(a,'atel',t);
 const fill=Math.max(0,Math.min(1,vol/a.frc));
 const liqTop=lT+(lB-lT)*(1-fill);

 // ---- lungs -------------------------------------------------------------
 for(const flip of [false,true]){
  const x = flip ? cx+gap : cx-gap-lw;
  lungPath(g,x,lT,lw,lB-lT,flip);
  g.save(); g.clip();
  g.fillStyle='#0a1218'; g.fillRect(x-2,lT-2,lw+4,lB-lT+4);
  g.fillStyle=css('--inert'); g.fillRect(x-2,liqTop,lw+4,lB-liqTop+2);
  const o2h=(lB-liqTop)*Math.max(0,Math.min(1,fao2));
  g.fillStyle=css('--o2'); g.fillRect(x-2,lB-o2h,lw+4,o2h+2);
  // collapse is dependent: shade upward from the base by the collapsed share
  if(atel>0.001){
   const ah=(lB-lT)*Math.min(1,atel*3.2);
   const grd=g.createLinearGradient(0,lB-ah,0,lB);
   grd.addColorStop(0,'rgba(122,74,140,0)');
   grd.addColorStop(1,'rgba(122,74,140,.82)');
   g.fillStyle=grd; g.fillRect(x-2,lB-ah,lw+4,ah+2);
  }
  g.strokeStyle='rgba(255,255,255,.40)'; g.lineWidth=1;
  g.beginPath(); g.moveTo(x-2,liqTop+.5); g.lineTo(x+lw+2,liqTop+.5); g.stroke();
  g.restore();
  lungPath(g,x,lT,lw,lB-lT,flip);
  g.strokeStyle=css('--rule2'); g.lineWidth=2; g.stroke();
 }

 // ---- trachea and bronchi ----------------------------------------------
 const op=isOpen(k,t), tw=15;
 g.strokeStyle=css('--rule2'); g.lineWidth=2; g.fillStyle=css('--panel');
 g.beginPath(); g.moveTo(cx-tw,neck); g.lineTo(cx-tw,carina);
 g.lineTo(cx+tw,carina); g.lineTo(cx+tw,neck); g.closePath();
 g.fill(); g.stroke();
 g.beginPath();
 g.moveTo(cx-tw,carina); g.lineTo(cx-gap-lw*0.30,lB-6);
 g.moveTo(cx+tw,carina); g.lineTo(cx+gap+lw*0.30,lB-6);
 g.stroke();

 // the obstruction sits on the trachea, where it does in life
 g.fillStyle=op?css('--o2'):css('--alarm');
 g.fillRect(cx-tw-5, carina+16, (tw+5)*2, op?5:12);
 g.fillStyle=op?css('--dim'):css('--alarm');
 g.textAlign='left'; g.font="13px 'Barlow Condensed',sans-serif";
 g.fillText(op?'airway open':'obstructed', cx+tw+12, carina+26);

 // ---- head --------------------------------------------------------------
 const spo2=at(a,'spo2',t), hb=(P.hb||14);
 const deoxy=hb*(1-Math.max(0,Math.min(1,spo2/100)));
 const blue=(deoxy-3.2)/(6.0-3.2);
 headPath(g,cx,neck-4,headH);
 g.fillStyle=mixc(SKIN,CYAN,blue); g.fill();
 g.strokeStyle=css('--rule2'); g.lineWidth=2; g.stroke();
 // HAIR, BROW, EAR AND EYE -- the features that make it read as a person.
 // The head is drawn in profile with the neck UPPERMOST, so in this path's
 // coordinates u runs from the neck (u=0) over the face and forehead to the
 // vertex near u=1.0: LARGER u IS FURTHER DOWN THE CANVAS. Getting that
 // backwards puts the eyebrow on the chin, so the landmarks are named.
 const HX = v => cx + v, HY = u => (neck - 4) + u * headH;
 // Hair is clipped to the silhouette, so it can never spill outside the head
 // however the hairline is drawn. Inside the clip we simply fill everything
 // BEYOND the hairline -- across the forehead, over the vertex and down the
 // occiput to the nape -- with a polygon whose far edges sit well outside the
 // head. That is why the corners below are at +-90 and u 1.2: they are not
 // features, they are there to be clipped away.
 g.save();
 headPath(g, cx, neck - 4, headH);
 g.clip();
 hairPath(g, cx, neck - 4, headH);
 g.fillStyle = HAIR;
 g.fill();
 g.restore();
 facePath(g, cx, neck - 4, headH, HAIR, 'rgba(0,0,0,.40)');

 // ---- the vacuum, labelled where it lives -------------------------------
 const p=at(a,'palv',t);
 if(p<-0.5&&fill<0.97){g.fillStyle=css('--dim'); g.textAlign='center';
  g.fillText(p.toFixed(1)+' cmH₂O', cx, lT+(lB-lT)*(1-fill)/2+5);}
}
function panel(k,t){
 const a=D[k],live=alive(a,t),s=at(a,'spo2',t);
 // When the model stops we freeze the last state rather than blanking it —
 // the comparison is the whole point and it matters most at the end.
 const end=a.t[a.t.length-1];
 sN[k].textContent=s.toFixed(0);
 sN[k].style.color=(!live||s<90)?css('--alarm'):css('--sat');
 // heart rate sits beside its own trace, coloured to match it
 const hr=at(a,'hr',t);
 hN[k].textContent=hr<1?'--':hr.toFixed(0);
 hN[k].style.color=(!live||hr<45)?css('--alarm'):css('--ecg-line');
 tL[k].textContent=live?'':' asystole '+Math.floor(end/60)+':'+
   String(Math.round(end%60)).padStart(2,'0');
 mon[k].className='rows'+(live?'':' stopped');
 const r=(l,v,c)=>'<div class="row"><span class="k">'+l+'</span><b'+
  (c?' style="color:'+c+'"':'')+'>'+v+'</b></div>';
 mon[k].innerHTML=r('PaO&#8322;',at(a,'pao2',t).toFixed(0))+
  r('PaCO&#8322;',at(a,'paco2',t).toFixed(0),'var(--co2)')+
  r('pH',at(a,'ph',t).toFixed(2),'var(--co2)')+
  r('alveolar N&#8322;',at(a,'pan2',t).toFixed(0))+
  r('lung volume',at(a,'vol',t).toFixed(0)+' mL')+
  r('shunt',(at(a,'shunt',t)*100).toFixed(0)+'%')+
  r('atelectasis',(at(a,'atel',t)*100).toFixed(0)+'%')+
  r('MAP',at(a,'map',t).toFixed(0)+' mmHg',at(a,'map',t)<55?'var(--alarm)':null)+
  r('cardiac output',at(a,'co',t).toFixed(1)+' L/min')+
  r('stroke volume',at(a,'sv',t).toFixed(0)+' mL')+
  r('mean PA pressure',at(a,'pap',t).toFixed(0)+' mmHg')+
  r('HPV response',(at(a,'hpv',t)*100).toFixed(0)+'%')+
  '<div class="flat">EtCO&#8322; &mdash; no trace, no ventilation</div>';
}
function render(){
 if(!D.A||!D.B) return;
 patient('A',T);patient('B',T);panel('A',T);panel('B',T);
 ecgDraw('A');ecgDraw('B');plethDraw('A');plethDraw('B');
 cvs.A.style.opacity=alive(D.A,T)?1:0.55; cvs.B.style.opacity=alive(D.B,T)?1:0.55;
 document.getElementById('clock').textContent=
  Math.floor(T/60)+':'+String(Math.floor(T%60)).padStart(2,'0');
 document.getElementById('scrub').value=T;
 const _ev=EVENTS(); let c=_ev[0];for(const e of _ev)if(T>=e[0])c=e;
 let txt=c[1];
 // The 120 s caption is the ONLY place the LMA toggle shows in words, so
 // the base text above must not state an outcome of its own -- it used to
 // end '-- airway briefly open', which this then appended to, giving
 // '...briefly open -- airway stays shut' with the toggle off. The button
 // was working; the sentence said it was not.
 if(c[0]===120) txt+=P.lmaOpens?' \u2014 airway briefly open':' \u2014 airway stays shut';
 document.getElementById('cap').textContent=txt;
 const _st=STEPS(); let cur=_st[0];for(const s of _st)if(T>=s[0])cur=s;
 [...stepsEl.children].forEach(el=>
  el.classList.toggle('on',+el.dataset.t===cur[0]));
}
function loop(ts){if(!playing)return;if(!last)last=ts;
 const wall=Math.min(0.1,(ts-last)/1000); last=ts;
 T=Math.min(900,T+wall*SPEED);
 for(const k of ['A','B']){
   if(!D[k]) continue;
   const live = T<=D[k].t[D[k].t.length-1];
   const hr = live?at(D[k],'hr',T):0;
   const before=phase[k];
   ecgStep(k,hr,wall*Math.min(SPEED,2));
   if(soundArm===k && hr>1 && phase[k]<before) beep(at(D[k],'spo2',T));
 }
 render();
 if(T>=900){playing=false;document.getElementById('play').textContent='Play';return;}
 requestAnimationFrame(loop);}
runBtn.onclick=run;
document.getElementById('play').onclick=e=>{
 if(stale||!D.A){run();return;}
 playing=!playing;
 e.target.textContent=playing?'Pause':'Play';last=0;if(playing)requestAnimationFrame(loop);};
document.getElementById('rew').onclick=()=>{T=0;render();};
document.getElementById('scrub').oninput=e=>{T=+e.target.value;render();};
// ---- sliders panel ---------------------------------------------------------
// Folds itself away after ten seconds so the patients get the whole width,
// which is the point of the page. Any use of the panel cancels the countdown
// and leaving it starts it again, so it cannot close under your hand while you
// are dragging a slider.
const SIDE_HIDE_MS=10000;
const sideEl=document.getElementById('side'),sideBtn=document.getElementById('sidebtn');
let sideTimer=null;
function setSide(hidden){
 document.body.classList.toggle('sidehid',hidden);
 sideBtn.textContent=hidden?'Sliders':'Hide sliders';
 sideBtn.setAttribute('aria-expanded',String(!hidden));
}
function armSide(){
 clearTimeout(sideTimer);
 if(document.body.classList.contains('sidehid')) return;   // already away
 sideTimer=setTimeout(()=>setSide(true),SIDE_HIDE_MS);
}
sideBtn.onclick=()=>{setSide(!document.body.classList.contains('sidehid'));armSide();};
['pointerenter','pointermove','input','focusin','wheel'].forEach(ev=>
 sideEl.addEventListener(ev,()=>clearTimeout(sideTimer),{passive:true}));
['pointerleave','focusout'].forEach(ev=>
 sideEl.addEventListener(ev,armSide,{passive:true}));
armSide();

const sndBtn=document.getElementById('snd');
sndBtn.onclick=()=>{
 if(!actx){ try{actx=new (window.AudioContext||window.webkitAudioContext)();}
            catch(err){sndBtn.textContent='no audio';sndBtn.disabled=true;return;} }
 actx.resume();
 soundArm = soundArm===null?'A':(soundArm==='A'?'B':null);
 sndBtn.textContent = soundArm===null?'Sound off'
   :(soundArm==='A'?'Sound: no buccal':'Sound: buccal');
};
const spdBtn=document.getElementById('spd');
spdBtn.onclick=()=>{SPEED=SPEED===8?1:(SPEED===1?2:(SPEED===2?4:8));
 spdBtn.innerHTML=SPEED+'&times;';};
// Expand always works: it is a CSS class, not a browser API. Real fullscreen
// is attempted as well where it exists, but never depended on - iOS allows it
// for video elements only, which used to leave this button dead.
const fs=document.getElementById('fs');
fs.onclick=()=>{
 const on=document.body.classList.toggle('zen');
 fs.textContent=on?'Exit expand':'Expand';
 const el=document.documentElement;
 try{
  if(on && el.requestFullscreen) el.requestFullscreen().catch(()=>{});
  else if(!on && document.fullscreenElement) document.exitFullscreen();
 }catch(e){}
 render();
};
document.addEventListener('fullscreenchange',()=>{
 if(!document.fullscreenElement && document.body.classList.contains('zen')
    && fs.dataset.viaApi){ document.body.classList.remove('zen');
    fs.textContent='Expand'; render(); }});
labels(); run();
</script></body></html>"""

page = HTML.replace('__MODEL__', model)

# --check compares without writing, so the pre-commit hook can refuse a commit
# that changes model.js and leaves the embedded copy in the HTML behind. The
# page is a single self-contained file with the model inlined; nothing else
# notices when the two fall out of step.
if '--check' in sys.argv:
    current = open(OUT_HTML).read() if os.path.exists(OUT_HTML) else None
    if current == page:
        print(f"up to date: {os.path.basename(OUT_HTML)} matches model.js")
        sys.exit(0)
    if current is None:
        print(f"{OUT_HTML} does not exist; run: python3 build_page.py")
    else:
        print(f"STALE: {os.path.basename(OUT_HTML)} does not match model.js.")
        print("       The page embeds its own copy of the model, so it is now")
        print("       running different physics from the file next to it.")
        print("       Rebuild with: python3 build_page.py")
    sys.exit(1)

open(OUT_HTML, 'w').write(page)
print(f"built {OUT_HTML}")
