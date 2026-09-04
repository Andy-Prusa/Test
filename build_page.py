model = open('model.js').read().split("if(typeof module")[0]

HTML = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Airway obstruction: where the oxygen goes</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@400;500;600&family=Barlow:wght@400;500&display=swap" rel="stylesheet">
<style>
:root{--screen:#060a0d;--panel:#0d151b;--rule:#16242e;--rule2:#223743;
--spo2:#4fd8e8;--co2:#e8d54a;--ecg-line:#4ade5e;--alarm:#ff4d3d;--o2:#a8ecff;--inert:#41586a;
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
 .main{display:flex;flex-direction:column;min-height:0;gap:8px}
 .arms{flex:1 1 auto;min-height:0}
 .arm{min-height:0;overflow-y:auto}
 .dials{grid-template-columns:1fr;gap:9px 0}
 .transport{gap:8px}
 .transport button{padding:5px 12px;font-size:15px}
 #scrub{width:100%;flex:1 1 100%;min-width:0}
 .steps{height:52px}
 .stage{grid-template-columns:auto minmax(0,1fr);margin-top:8px}
 .stage canvas:not(.ecg){height:clamp(150px,30vh,400px);width:auto}
 .ecg{height:clamp(38px,7vh,80px)}
 .foot{margin-top:8px;padding-top:9px;font-size:11.5px;max-width:none}
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

.steps{position:relative;height:62px;margin-bottom:4px}
.step{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;
gap:10px;color:var(--dim);opacity:0;transition:opacity .35s;pointer-events:none}
.step.on{opacity:1}
.step svg{width:28px;height:28px;flex:none;color:var(--ink)}
.step span{font-family:'Barlow Condensed',sans-serif;font-size:17px;color:var(--ink)}
.step b{font-family:'Barlow Condensed',sans-serif;font-size:17px;font-weight:500;
font-variant-numeric:tabular-nums;color:var(--spo2)}
.track{position:relative;height:12px;border-top:1px solid var(--rule);margin-bottom:12px}
.mk{position:absolute;top:0;width:1px;height:7px;background:var(--rule2)}
.head{position:absolute;top:-1px;width:2px;height:12px;background:var(--spo2)}
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

.arms{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.arm{background:var(--panel);border:1px solid var(--rule);padding:12px}
.armhead{display:flex;justify-content:space-between;align-items:baseline;gap:8px;
border-bottom:1px solid var(--rule);padding-bottom:7px;margin-bottom:10px}
.armname{font-family:'Barlow Condensed',sans-serif;font-size:18px;font-weight:500;
white-space:nowrap}
.armnote{font-size:11.5px;color:var(--dim);text-align:right;line-height:1.2}
.vitals{display:flex;align-items:flex-end;gap:12px}
.big{font-family:'Barlow Condensed',sans-serif;font-variant-numeric:tabular-nums;
font-size:clamp(34px,6vw,62px);line-height:.85}
.biglab{font-size:11px;color:var(--dim);margin-bottom:-2px}
.ecg{width:100%;height:44px;display:block;margin-top:6px;background:#050a0d}
.pleth{flex:1;height:6px;background:var(--rule);overflow:hidden;margin-bottom:9px}
.pleth i{display:block;height:100%;background:var(--spo2);transition:width .2s linear}
.stage{display:grid;grid-template-columns:126px minmax(0,1fr);gap:12px;align-items:start;
margin-top:10px}
@media(max-width:620px){.stage{grid-template-columns:82px minmax(0,1fr);gap:8px}}
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
body.zen .steps,body.zen .track{display:none}
body.zen .side{display:none}
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
body.zen .big{font-size:clamp(26px,7.5vh,76px)}
body.zen .biglab{font-size:clamp(8px,1.3vh,11px)}
body.zen .ecg{height:clamp(26px,7vh,74px);margin-top:4px}
body.zen .stage{grid-template-columns:auto minmax(0,1fr);gap:9px;margin-top:6px}
body.zen .stage canvas:not(.ecg){height:clamp(110px,32vh,330px);width:auto}
body.zen .row{font-size:clamp(10px,1.65vh,15px);padding:clamp(1px,0.35vh,5px) 0}
body.zen .row b{font-size:clamp(12px,2vh,19px)}
body.zen .flat{font-size:clamp(9px,1.3vh,12px);padding:2px 0}
</style></head><body><div class="wrap">
<div class="side">
<h1>Every time the airway opens, something rushes in</h1>
<p class="sub">Obstructed from induction. Both arms are physically identical until 7:10 &mdash;
the only difference is what sits in the pharynx when each inrush happens. The bottle is the
lung: bright is oxygen, dull is nitrogen and CO&#8322;, the dark gap is the vacuum obstruction
creates. Move the sliders and the whole simulation re-runs. Collapsibility defaults to
the calibrated median; the patients who desaturate despite good tracheal oxygen sit near
the top of its range.</p>

<div class="steps" id="steps"></div>
<div class="track" id="track"></div>
<div class="caption" id="cap"></div>

<div class="transport">
<button id="runbtn">Run simulation</button>
<button id="play">Play</button><button id="rew">Restart</button>
<button id="fs">Expand</button>
<button id="snd">Sound off</button><button id="spd">4&times;</button>
<span class="clock" id="clock">0:00</span>
<input type="range" id="scrub" min="0" max="900" value="0" step="1" aria-label="Time">
<span class="busy" id="busy"></span>
</div>

<div class="dials" id="dials"></div>
</div>

<div class="main">
<div class="arms">
<div class="arm"><div class="armhead"><span class="armname">No buccal oxygen</span>
<span class="armnote">pharynx holds room air</span></div>
<div class="vitals"><div><div class="biglab">SpO&#8322; %</div><div class="big" id="sA">--</div>
<div class="stoplab" id="tA"></div></div>
<div class="pleth"><i id="pA"></i></div></div>
<canvas class="ecg" id="eA" width="600" height="88"></canvas>
<div class="stage"><canvas id="bA" width="252" height="404"></canvas><div class="rows" id="mA"></div></div></div>
<div class="arm"><div class="armhead"><span class="armname">Buccal oxygen</span>
<span class="armnote" id="noteB">pharynx at 100% O&#8322;</span></div>
<div class="vitals"><div><div class="biglab">SpO&#8322; %</div><div class="big" id="sB">--</div>
<div class="stoplab" id="tB"></div></div>
<div class="pleth"><i id="pB"></i></div></div>
<canvas class="ecg" id="eB" width="600" height="88"></canvas>
<div class="stage"><canvas id="bB" width="252" height="404"></canvas><div class="rows" id="mB"></div></div></div>
</div>

<div class="legend"><span><i class="sw" style="background:var(--o2)"></i>oxygen in the lung</span>
<span><i class="sw" style="background:var(--inert)"></i>nitrogen and CO&#8322;</span>
<span><i class="sw" style="background:#0a1218;border:1px solid var(--rule2)"></i>vacuum</span></div>
<p class="foot">Modelled, not measured. Saturation carries a pulse oximeter delay. There is no
end-tidal CO&#8322; because there is no ventilation; the CO&#8322; and pH shown are arterial model
values you would not have at the bedside. Each arm stops where the model's fixed cardiac
output stops being defensible. Closing capacity and the FRC&ndash;BMI relation are
parameterised, not fitted to source data.</p>
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
blade:'<svg viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"><rect x="19" y="3" width="7" height="13" rx="1.5"/><path d="M19 15H12C7 15 4 19 4 24c0 3 1.5 5 3 5"/><path d="M7 29c-1-2-1-4 0-6"/></svg>'};

const STEPS=[[0,'syringe','Induction'],[120,'mask','Facemask ventilation fails'],
[130,'lma','LMA inserted'],[220,'syringe','Rocuronium given'],
[280,'blade','Laryngoscopy']];
const EVENTS=[[0,'Induction. Airway obstructs immediately.'],
[120,'Facemask off, LMA going in \\u2014 airway briefly open'],
[130,'LMA in place but no patent airway'],
[160,'LMA out. Laryngospasm. Drawing up rocuronium.'],
[220,'Rocuronium given. 60 s to work.'],
[280,'Laryngoscopy \\u2014 airway open, view obtained'],
[430,'Blade out (control) / blade left in (buccal)']];

const DIALS=[
 ['weight','Body weight',45,180,1,107,null],
 ['height','Height',1.45,2.05,0.01,1.75,null],
 ['frcScale','FRC',0.55,1.5,0.01,1.0,null],
 ['bmrScale','Metabolic rate',0.6,1.7,0.01,1.0,null],
 ['ccScale','Closing capacity',0.6,1.6,0.01,1.0,null],
 ['maxClosed','Lung collapsibility',0.10,0.65,0.01,0.25,null],
 ['vqLogSd','V/Q spread',0.0,1.4,0.02,0.70,null],
 ['tauMix','Cardiogenic mixing',10,300,5,45,null],
 ['fgBuccal','Pharyngeal O\u2082 (device arm)',0.21,1.00,0.01,1.00,null],
 ['inflowMechFrac','Absorption atelectasis',0.0,0.55,0.01,0.18,null],
 ['tiltDeg','Bed tilt (head up)',-20,45,1,25,null],
 ['buccalIdx','Buccal switched on',0,4,1,0,null]];
// The decision points an anaesthetist actually has, not arbitrary seconds.
const STARTS=[[0,'From induction'],[120,'After mask ventilation fails'],
 [160,'After the LMA fails'],[280,'At laryngoscopy'],
 [370,'After failed intubation attempts']];

const BASE={age:45,hb:14,lmaOpens:true,frcRef:2500,frcDrop:400,tiltDeg:25,
 ccAt20:1800,ccPerYear:20,ccPerBmi:45,ccK:1.5,vo2Ref:250,coRef:5,crs:85,
 vArt:1.0,vVen:2.0,vTisO2:1.5,feo2:0.87,rv:1100,pCollapse:-50,nVq:20};
const P=Object.assign({},BASE);
DIALS.forEach(d=>P[d[0]]=d[5]);

const stepsEl=document.getElementById('steps');
STEPS.forEach(([t,ic,lab])=>{const d=document.createElement('div');d.className='step';
 d.dataset.t=t;
 const mmss=Math.floor(t/60)+':'+String(t%60).padStart(2,'0');
 d.innerHTML=ICONS[ic]+'<b>'+mmss+'</b><span>'+lab+'</span>';
 stepsEl.appendChild(d);});
const track=document.getElementById('track');
EVENTS.forEach(([t])=>{const d=document.createElement('div');d.className='mk';
 d.style.left=(100*t/900)+'%';track.appendChild(d);});
const head=document.createElement('div');head.className='head';track.appendChild(head);

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

const cvs={A:bA,B:bB},mon={A:mA,B:mB},sN={A:sA,B:sB},pl={A:pA,B:pB},tL={A:tA,B:tB};
const css=k=>getComputedStyle(document.documentElement).getPropertyValue(k).trim();
const OBS=Infinity;
// Airway resistance by time, and the pharyngeal oxygen fraction switched on
// at an arbitrary moment. Splitting on both boundary sets lets the device be
// started before, during or long after the airway first opens.
function tl(fg,startAt,keep){
 const R=t=> t>=280 ? (t>=430&&!keep?OBS:2)
          : ((t>=120&&t<130) ? (P.lmaOpens===false?OBS:8) : OBS);
 const cuts=[...new Set([0,120,130,160,280,430,startAt,900])]
   .filter(v=>v>=0&&v<=900).sort((a,b)=>a-b);
 const ep=[];
 for(let i=0;i<cuts.length-1;i++){
  const a=cuts[i],b=cuts[i+1];
  ep.push({d:b-a,R:R(a),fg:(a>=startAt?fg:0.21)});
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
function ecgWave(p){
  const g=(c,w,a)=>a*Math.exp(-((p-c)*(p-c))/(2*w*w));
  return g(0.15,0.022,0.12)+g(0.29,0.007,-0.14)+g(0.315,0.009,1.0)
       +g(0.345,0.011,-0.28)+g(0.52,0.042,0.26);
}
function ecgStep(k,hr,wall){
  const tr=trace[k],N=tr.length;
  const steps=Math.min(80,Math.max(1,Math.round(wall*220)));
  const beats=hr>1?hr/60*wall:0;
  for(let s=0;s<steps;s++){
    phase[k]=(phase[k]+beats/steps)%1;
    tr.copyWithin(0,1); tr[N-1]=hr>1?ecgWave(phase[k]):0;
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

// The lung is 20 parallel compartments, so a full run takes a second or two.
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
 document.getElementById('v_vqLogSd').textContent='log SD '+P.vqLogSd.toFixed(2);
 document.getElementById('v_tauMix').textContent=P.tauMix.toFixed(0)+' s';
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
   // prime the ECG with a few resting beats so it reads as a rhythm at rest
   for(const k of ['A','B']){ phase[k]=0; trace[k].fill(0);
     ecgStep(k, D[k].hr[0], trace[k].length/220); }
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

function bottle(k,t){
 const cv=cvs[k],a=D[k],g=cv.getContext('2d'),W=cv.width,H=cv.height;
 g.clearRect(0,0,W,H);
 const L=46,R=W-46,top=14,nT=H-96,nB=H-38,nL=W/2-19,nR=W/2+19;
 const path=()=>{g.beginPath();g.moveTo(L,top+14);g.quadraticCurveTo(L,top,L+14,top);
  g.lineTo(R-14,top);g.quadraticCurveTo(R,top,R,top+14);g.lineTo(R,nT-28);
  g.quadraticCurveTo(R,nT,nR,nT+6);g.lineTo(nR,nB);g.lineTo(nL,nB);g.lineTo(nL,nT+6);
  g.quadraticCurveTo(L,nT,L,nT-28);g.closePath();};
 path();g.save();g.clip();
 const vol=at(a,'vol',t),fao2=at(a,'fao2',t),body=nT-top;
 const fill=Math.max(0,Math.min(1,vol/a.frc)),liqTop=top+body*(1-fill);
 g.fillStyle='#0a1218';g.fillRect(0,0,W,H);
 g.fillStyle=css('--inert');g.fillRect(0,liqTop,W,H-liqTop);
 const o2h=(nT-liqTop)*Math.max(0,Math.min(1,fao2));
 g.fillStyle=css('--o2');g.fillRect(0,nT-o2h,W,H-(nT-o2h));
 g.strokeStyle='rgba(255,255,255,.45)';g.lineWidth=1;
 g.beginPath();g.moveTo(0,liqTop+.5);g.lineTo(W,liqTop+.5);g.stroke();
 g.restore();
 path();g.strokeStyle=css('--rule2');g.lineWidth=2;g.stroke();
 const op=isOpen(k,t);
 g.fillStyle=op?css('--o2'):css('--alarm');g.fillRect(nL-6,nB,50,op?7:11);
 g.fillStyle=css('--dim');g.textAlign='center';g.font="13px 'Barlow Condensed',sans-serif";
 g.fillText(op?'airway open':'obstructed',W/2,H-9);
 const p=at(a,'palv',t);
 if(p<-0.5&&fill<0.97){g.fillStyle=css('--dim');
  g.fillText(p.toFixed(1)+' cmH\\u2082O',W/2,top+body*(1-fill)/2+5);}
}
function panel(k,t){
 const a=D[k],live=alive(a,t),s=at(a,'spo2',t);
 // When the model stops we freeze the last state rather than blanking it —
 // the comparison is the whole point and it matters most at the end.
 const end=a.t[a.t.length-1];
 sN[k].textContent=s.toFixed(0);
 sN[k].style.color=(!live||s<90)?css('--alarm'):css('--spo2');
 tL[k].textContent=live?'':'asystole at '+Math.floor(end/60)+':'+
   String(Math.round(end%60)).padStart(2,'0');
 mon[k].className='rows'+(live?'':' stopped');
 pl[k].style.width=Math.max(0,(s-40)/60*100)+'%';
 pl[k].style.background=live?css('--spo2'):css('--alarm');
 const r=(l,v,c)=>'<div class="row"><span class="k">'+l+'</span><b'+
  (c?' style="color:'+c+'"':'')+'>'+v+'</b></div>';
 mon[k].innerHTML=r('PaO&#8322;',at(a,'pao2',t).toFixed(0))+
  r('PaCO&#8322;',at(a,'paco2',t).toFixed(0),'var(--co2)')+
  r('pH',at(a,'ph',t).toFixed(2),'var(--co2)')+
  r('alveolar N&#8322;',at(a,'pan2',t).toFixed(0))+
  r('lung volume',at(a,'vol',t).toFixed(0)+' mL')+
  r('shunt',(at(a,'shunt',t)*100).toFixed(0)+'%')+
  r('atelectasis',(at(a,'atel',t)*100).toFixed(0)+'%')+
  r('heart rate',at(a,'hr',t).toFixed(0)+' bpm',
    at(a,'hr',t)<45?'var(--alarm)':null)+
  r('MAP',at(a,'map',t).toFixed(0)+' mmHg',at(a,'map',t)<55?'var(--alarm)':null)+
  r('cardiac output',at(a,'co',t).toFixed(1)+' L/min')+
  r('stroke volume',at(a,'sv',t).toFixed(0)+' mL')+
  r('mean PA pressure',at(a,'pap',t).toFixed(0)+' mmHg')+
  r('HPV response',(at(a,'hpv',t)*100).toFixed(0)+'%')+
  '<div class="flat">EtCO&#8322; &mdash; no trace, no ventilation</div>';
}
function render(){
 if(!D.A||!D.B) return;
 bottle('A',T);bottle('B',T);panel('A',T);panel('B',T);
 ecgDraw('A');ecgDraw('B');
 cvs.A.style.opacity=alive(D.A,T)?1:0.55; cvs.B.style.opacity=alive(D.B,T)?1:0.55;
 document.getElementById('clock').textContent=
  Math.floor(T/60)+':'+String(Math.floor(T%60)).padStart(2,'0');
 document.getElementById('scrub').value=T;
 head.style.left=(100*T/900)+'%';
 let c=EVENTS[0];for(const e of EVENTS)if(T>=e[0])c=e;
 let txt=c[1];
 if(c[0]===120) txt+=P.lmaOpens?' \u2014 airway briefly open':' \u2014 airway stays shut';
 document.getElementById('cap').textContent=txt;
 let cur=STEPS[0];for(const s of STEPS)if(T>=s[0])cur=s;
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

open('/mnt/user-data/outputs/airway_scenario.html','w').write(HTML.replace('__MODEL__', model))
print("built")
