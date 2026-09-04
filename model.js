// model.js — browser port of bloodgas.py + apnoea_core.py.
// Bisection replaces brentq; otherwise the equations are identical.
// Verified against the Python reference in verify_port.py.

const PB=760, PH2O=47, PDRY=713, GASK=863, HUFNER=1.34, O2SOL=0.003, MLCO2=22.26;

const bisect=(f,lo,hi,n)=>{let a=lo,b=hi,fa=f(a);for(let i=0;i<n;i++){
  const m=(a+b)/2,fm=f(m); if((fa<0)===(fm<0)){a=m;fa=fm;}else{b=m;} } return (a+b)/2;};

const satStd=p=>{p=Math.max(p,1e-9);return 1/(23400/(p*p*p+150*p)+1);};
const bohr=(pH,pco2,T)=>Math.pow(10,
  0.024*(37-T)+0.40*(pH-7.40)+0.06*(Math.log10(40)-Math.log10(Math.max(pco2,1e-9))));
const so2FromPo2=(po2,pH,pco2,T)=>satStd(po2*bohr(pH,pco2,T));
const po2FromSo2=(so2,pH,pco2,T)=>{
  const s=Math.min(Math.max(so2,1e-9),0.999999);
  return bisect(p=>satStd(p)-s,1e-6,2000,44)/bohr(pH,pco2,T);};
const o2Content=(po2,hb,pH,pco2,T)=>HUFNER*hb*so2FromPo2(po2,pH,pco2,T)+O2SOL*po2;
const po2FromO2Content=(c,hb,pH,pco2,T)=>{
  if(o2Content(1e-6,hb,pH,pco2,T)>c) return 1e-6;
  if(o2Content(2000,hb,pH,pco2,T)<c) return 2000;
  return bisect(p=>o2Content(p,hb,pH,pco2,T)-c,1e-6,2000,44);};

const co2Sol=T=>{const d=37-T;return 0.0307+0.00057*d+0.00002*d*d;};
const pkPrime=(pH,T)=>6.086+0.042*(7.4-pH)+(38-T)*(0.00472+0.00139*(7.4-pH));
const phFromPco2Be=(pco2,be,hb,so2,T)=>{
  const hbm=hb*0.6206;
  return bisect(pH=>{
    const hco3=co2Sol(T)*pco2*Math.pow(10,pH-pkPrime(pH,T));
    return (1-0.0143*hbm)*((hco3-24.8)+(9.5+1.63*hbm)*(pH-7.4))
           -0.2*hbm*(1-so2)-be;},4.5,10.5,34);};
const co2Content=(pco2,pH,so2,hb,T)=>{
  const hbm=hb*0.6206;
  const pl=co2Sol(T)*pco2*(1+Math.pow(10,pH-pkPrime(pH,T)));
  return pl*(1-(0.0289*hbm)/((3.352-0.456*so2)*(8.142-pH)))*MLCO2/10;};
const arterialState=(cco2,be,hb,o2c,T)=>{
  const st=pco2=>{let so2=0.9,pH=0,po2=0;
    for(let i=0;i<8;i++){pH=phFromPco2Be(pco2,be,hb,so2,T);
      po2=po2FromO2Content(o2c,hb,pH,pco2,T);
      const s=so2FromPo2(po2,pH,pco2,T); if(Math.abs(s-so2)<1e-6){so2=s;break;} so2=s;}
    return [pH,po2,so2];};
  const res=pco2=>{const[p,,s]=st(pco2);return co2Content(pco2,p,s,hb,T)-cco2;};
  let pco2; if(res(3)>0)pco2=3; else if(res(400)<0)pco2=400; else pco2=bisect(res,3,400,34);
  const[pH,po2,so2]=st(pco2); return {pco2,pH,po2,so2};};

function vqDist(n, sd){
  const z=[], w=[], vol=[];
  for(let i=0;i<n;i++) z.push(-2.2 + 4.4*i/(n-1));
  let ws=0; for(const zz of z){ const v=Math.exp(-0.5*zz*zz); w.push(v); ws+=v; }
  for(let i=0;i<n;i++) w[i]/=ws;
  let vs=0; for(let i=0;i<n;i++){ const v=w[i]*Math.exp(sd*z[i]); vol.push(v); vs+=v; }
  for(let i=0;i<n;i++) vol[i]/=vs;
  return {q:w, v:vol};
}

function derive(P){
  const bmi=P.weight/(P.height*P.height);
  const ibw=50+2.3*(P.height/0.0254-60);
  const abw=ibw+0.4*Math.max(0,P.weight-ibw);
  // lung volumes scale with height; adiposity only modifies them
  const hf=(2.34*P.height-1.09)/(2.34*1.75-1.09);
  // bed tilt: head-up lifts the abdomen off the diaphragm and raises FRC
  const tg=(P.tiltGainLean===undefined?0.0130:P.tiltGainLean)
          +(P.tiltGainBmi===undefined?0.00015:P.tiltGainBmi)*Math.max(0,bmi-25);
  const tiltF=Math.max(0.45,1+(P.tiltDeg||0)*tg);
  const frcAwake=P.frcRef*hf*Math.exp(-0.0417*(bmi-22))*tiltF;
  const frc=Math.max(300,(frcAwake-Math.min(P.frcDrop,0.25*frcAwake))*(P.frcScale||1));
  const cc=(P.ccAt20+P.ccPerYear*(P.age-20)+P.ccPerBmi*Math.max(0,bmi-25))*hf*(P.ccScale||1);
  const vo2=P.vo2Ref*Math.pow(abw/70,0.75)*(P.bmrScale||1)-0.27*P.weight;
  const co=P.coRef*Math.pow(P.weight/70,0.75)*0.75;   // baseline at induction
  const fatKg=Math.max(5,P.weight*(0.10+0.011*Math.max(0,bmi-20)));
  const leanKg=P.weight-fatKg, lam=1.895e-5;
  const n2cap=[(5+0.10*leanKg)*1000*lam,(0.50*leanKg)*1000*lam,(fatKg/0.92)*1000*lam*5];
  return {bmi,frc,cc,vo2:Math.max(60,vo2),co,n2cap,lam,hf,tiltF};
}

function simulate(P, epochs, dt=0.1){
  const d=derive(P), {frc,cc,vo2,co,n2cap,lam,hf}=d;
  const hb=P.hb,T=37,be=0,crs=P.crs/1.35951, vco2m=vo2*0.8;
  let vA=frc-150;
  const fo2=P.feo2, fco2=40/PDRY, fn2=Math.max(0,1-fo2-fco2);
  const ntot=vA*PDRY/GASK;
  const NC=P.nVq||16, SD=P.vqLogSd===undefined?0.70:P.vqLogSd;
  const TAUMIX=P.tauMix===undefined?45:P.tauMix;
  const dist=vqDist(NC,SD), qw=dist.q, vw=dist.v;
  // n[3i]=O2, n[3i+1]=CO2, n[3i+2]=N2 for compartment i, mL STPD
  const MECH=P.inflowMechFrac===undefined?0.18:P.inflowMechFrac;
  const CVF=P.cvFrac||0.55;
  const n=new Float64Array(NC*3);
  for(let i=0;i<NC;i++){ n[3*i]=vw[i]*ntot*fo2; n[3*i+1]=vw[i]*ntot*fco2;
                         n[3*i+2]=vw[i]*ntot*fn2; }
  const nc=new Float64Array(NC), pO2=new Float64Array(NC), pCO2=new Float64Array(NC),
        pN2=new Float64Array(NC), ccO2=new Float64Array(NC), ccC=new Float64Array(NC),
        vo2c=new Float64Array(NC), vco2c=new Float64Array(NC);
  const NS=10, vseg=15;
  let ds=[]; for(let i=0;i<NS;i++) ds.push([fo2,fco2,fn2]);

  const pha0=phFromPco2Be(40,be,hb,0.99,T), pao2_0=fo2*PDRY;
  const cao2=o2Content(pao2_0,hb,pha0,40,T), caco2=co2Content(40,pha0,0.99,hb,T);
  // arterial blood starts shunt-mixed (the plateau fixed point), not at the
  // alveolar value - see the Python for why this matters
  const _f=Math.min(P.shuntBase===undefined?0.05:P.shuntBase,0.9);
  const cao2s=cao2-(_f/(1-_f))*vo2/(co*10);
  let cvo2=cao2s-vo2/(co*10), cvco2=caco2+vco2m/(co*10);
  const NP=3;
  let aO2=Array(NP).fill(cao2s), aC=Array(NP).fill(caco2);
  let vO2=Array(NP).fill(cvo2), vC=Array(NP).fill(cvco2);
  let tO2=cvo2,tC=cvco2,sC=cvco2, collapsed=0, hpv=0, pvo2=40;
  const nc0=new Float64Array(NC), collC=new Float64Array(NC);
  for(let c=0;c<NC;c++) nc0[c]=n[3*c]+n[3*c+1]+n[3*c+2];
  let nc0Sum=0; for(let c=0;c<NC;c++) nc0Sum+=nc0[c];
  let n2p=[573,573,573];
  const coBase=co; let coNow=co, paco2Prev=40, hrNow=70, sao2Prev=0.99, tLow=0,
      svNow=0, svrNow=18, mapNow=80, papNow=15;
  const qf=[0.75,0.18,0.07];
  const vas=P.vArt/NP, vvs=P.vVen/NP, dtm=dt/60;

  const total=epochs.reduce((s,e)=>s+e.d,0), N=Math.round(total/dt);
  const st=[]; epochs.forEach(e=>{for(let i=0;i<Math.round(e.d/dt);i++) st.push(e);});
  while(st.length<=N) st.push(epochs[epochs.length-1]);

  const out={t:[],spo2:[],vol:[],fao2:[],pan2:[],paco2:[],ph:[],pao2:[],
             shunt:[],palv:[],lungO2:[],hpv:[],pvo2:[],co:[],hr:[],map:[],pap:[],sv:[],atel:[]};
  let spo2=0.99, hist=[], last=null, stride=Math.round(1/dt);

  for(let i=0;i<=N;i++){
    const ep=st[i];
    let nd=0;
    for(let c=0;c<NC;c++){ nc[c]=n[3*c]+n[3*c+1]+n[3*c+2]; nd+=nc[c]; }
    let vv,pabs;
    { // recoil: linear, stiffening below RV, floored where units collapse
      const rv=Math.max(200,(P.rv||1100)*hf-150), stiff=0.15, fl=(P.pCollapse||-50)/1.35951;
      const rec=v=>{let p=(v-(frc-150))/crs; if(v<rv) p+=(v-rv)/(crs*stiff);
                    return Math.max(p,fl);};
      let lo=1,hi=frc+4000;
      for(let q=0;q<60;q++){const m=(lo+hi)/2;
        if((PB+rec(m)-PH2O)*m < nd*GASK) lo=m; else hi=m;}
      vv=(lo+hi)/2; pabs=PB+rec(vv);
      if(pabs>PB){vv=nd*GASK/PDRY;pabs=PB;} }
    vA=vv; const pdry=pabs-PH2O;
    let tO=0,tC2=0,tN=0;
    for(let c=0;c<NC;c++){
      const q=Math.max(nc[c],1e-12);
      pO2[c]=n[3*c]/q*pdry; pCO2[c]=n[3*c+1]/q*pdry; pN2[c]=n[3*c+2]/q*pdry;
      tO+=n[3*c]; tC2+=n[3*c+1]; tN+=n[3*c+2];
    }
    const pAO2=tO/nd*pdry, pACO2=tC2/nd*pdry, pAN2=tN/nd*pdry, vLung=vA+150;

    const x=Math.max(0,cc-vLung)/Math.max(vLung,100);
    const tgt=P.maxClosed*x/(x+P.ccK);
    const fO2mean=tO/nd;
    const tauC=60*fO2mean+900*(1-fO2mean);
    if(tgt>collapsed) collapsed+=(tgt-collapsed)*(dt/tauC);
    // HPV, Marshall 1994. A collapsed unit holds no gas, so its stimulus
    // oxygen tension is simply the mixed venous PO2.
    // per-compartment absorption collapse: a unit whose uptake outruns its
    // refill shrinks, and once below its own closing volume it is lost.
    let absorbed=0;
    for(let c=0;c<NC;c++){
      const vf=nc[c]/Math.max(nc0[c],1e-9);
      const exp_=Math.min(1,Math.max(0,(CVF-vf)/CVF));
      const tc=60*(n[3*c]/Math.max(nc[c],1e-12))+900*(1-n[3*c]/Math.max(nc[c],1e-12));
      // collapse ratchets up quickly, recruits back only partially
      if(exp_>collC[c]) collC[c]+=(exp_-collC[c])*(dt/tc);
      else collC[c]+=(exp_-collC[c])*(dt/(P.tauRecruit||25))*(P.recruitFrac===undefined?0.65:P.recruitFrac);
      if(collC[c]<0) collC[c]=0; if(collC[c]>1) collC[c]=1;
      absorbed+=qw[c]*collC[c];
    }
    const f0=1.2*Math.min(0.95,collapsed+absorbed);
    let fEff=f0;
    if((P.hpvEnabled!==false)&&f0>1e-6){
      const ps=Math.max(pvo2,1);
      const resp=Math.pow(ps,-2.616)/(6.683e-5+Math.pow(ps,-2.616));
      hpv+=(resp-hpv)*(dt/250);
      const k=1+((P.hpvPvrMax||3.15)-1)*hpv;
      fEff=f0/(f0+k*(1-f0));
    }
    const shunt=Math.min(0.95,Math.max(0,(P.shuntBase===undefined?0.05:P.shuntBase)+fEff));

    // cardiac output rises with hypercapnia: +0.97% of baseline per mmHg
    // PaCO2 above 40 (Sci Rep 2023, n=91 apnoeic oxygenation, measured)
    // Stroke volume is constant, so cardiac output is DERIVED from rate, not
    // the other way round. Hypercapnia raises the rate, hypoxaemia lowers it,
    // and the terminal rhythm takes flow down with it - an agonal escape rate
    // cannot deliver a normal cardiac output.
    const cap=P.co2ResponseCap||150;
    const co2arg=Math.max(0,Math.min(paco2Prev,cap)-40);
    const co2f=Math.min(P.coMaxFactor||2.0,
          1+(P.coCo2Gain===undefined?0.0045:P.coCo2Gain)*co2arg);
    const sHr=Math.max(sao2Prev,1e-3), bn=P.hrBradyN||4, b50=P.hrBradySao250||0.45;
    const sig=x=>Math.pow(x,bn)/(Math.pow(x,bn)+Math.pow(b50,bn));
    const brady=Math.min(1,sig(sHr)/sig(0.99));
    hrNow=(P.hrBase||70)*co2f*brady;
    // terminal rhythm: below the trigger saturation for the trigger delay,
    // the rhythm degenerates to three beats in ten seconds, then two, then
    // one, then asystole. Timings are for teaching, not measured.
    const TS=P.hrTermSao2||0.40, TD=P.hrTermDelay||20, RATES=[18,12,6];
    if(sao2Prev<TS) tLow+=dt;
    else if(tLow < TD+10*RATES.length) tLow=0;
    if(tLow>=TD){ const k=Math.floor((tLow-TD)/10);
      hrNow = k<RATES.length ? RATES[k] : 0; }
    // stroke volume: hypercapnic inotropy up, Muller effect down
    const itp=Math.min(0,(pabs-PB)*1.35951)*(P.itpFraction||0.60);
    const svf=(1+(P.svCo2Gain===undefined?0.0045:P.svCo2Gain)*co2arg)
              *Math.max(0.15,1+(P.svItpGain===undefined?0.0025:P.svItpGain)*itp);
    coNow=Math.max(0.02, coBase*(hrNow/(P.hrBase||70))*svf);
    svNow=coNow*1000/Math.max(hrNow,1e-6);
    svrNow=(P.svrBase||18)*Math.max(P.svrFloor||0.40,
            1+(P.svrCo2Gain===undefined?-0.0045:P.svrCo2Gain)*co2arg);
    mapNow=coNow*svrNow;
    papNow=coNow*(P.pvrBase||1.40)*(1+((P.hpvPvrMax||3.15)-1)*hpv)+(P.pcwp||8);
    const n2cond=qf.map(q=>q*coNow*1000*lam);
    const cvO2=vO2[NP-1], cvC=vC[NP-1];
    // one pH for the lung; every compartment then costs only analytic terms
    const phc=phFromPco2Be(pACO2,be,hb,0.99,T);
    const qeff=coNow*(1-shunt)*10;
    let vo2L=0, vco2L=0, mixO=0, mixC=0;
    for(let c=0;c<NC;c++){
      const s2=so2FromPo2(pO2[c],phc,pCO2[c],T);
      ccO2[c]=HUFNER*hb*s2+O2SOL*pO2[c];
      ccC[c]=co2Content(pCO2[c],phc,s2,hb,T);
      const qc=qeff*qw[c];
      vo2c[c]=qc*(ccO2[c]-cvO2); vco2c[c]=qc*(cvC-ccC[c]);
      vo2L+=vo2c[c]; vco2L+=vco2c[c];
      mixO+=qw[c]*ccO2[c]; mixC+=qw[c]*ccC[c];
    }
    const caN=(1-shunt)*mixO+shunt*cvO2, ccN=(1-shunt)*mixC+shunt*cvC;

    const flux=n2p.map((p,j)=>n2cond[j]*(p-pAN2));
    const vn2=flux[0]+flux[1]+flux[2];
    const deficit=vo2L-vco2L-vn2;
    let inflow=0;
    if(isFinite(ep.R)){
      const drive=Math.max(0,(PB-pabs)*1.35951);
      let qm=drive/Math.max(ep.R,1e-6)*1000*60*PDRY/GASK;
      const refill=Math.max(0,(frc-150-vA))*PDRY/GASK/dtm;
      inflow=Math.min(qm,Math.max(deficit,0)+refill);
      // Sub-step the dead-space advection so no more than one segment is
      // displaced per pass (CFL <= 1). Without this a large inrush delivers a
      // whole timestep of stale dead-space gas to the alveolus in one go.
      const nIn=Math.max(0,inflow)*dtm, volIn=nIn*GASK/PDRY;
      let add=[0,0,0];
      if(nIn>0){
        const sub=Math.min(400,Math.max(1,Math.ceil(volIn/vseg)));
        const dn=nIn/sub, kk=(volIn/sub)/vseg;
        for(let q=0;q<sub;q++){
          const ex=ds[NS-1];
          add[0]+=ex[0]*dn; add[1]+=ex[1]*dn; add[2]+=ex[2]*dn;
          const src=[[ep.fg,0,1-ep.fg]].concat(ds.slice(0,NS-1));
          ds=ds.map((seg,j)=>seg.map((v,w)=>v+kk*(src[j][w]-v)));
        }
      }
      // inflow follows absorption, not volume: compartments share one airway
      let dtot=0; const dfc=new Float64Array(NC);
      for(let c=0;c<NC;c++){ dfc[c]=Math.max(vo2c[c]-vco2c[c]-vn2*qw[c],0); dtot+=dfc[c]; }
      for(let c=0;c<NC;c++){
        const byAbs = dtot>1e-9 ? dfc[c]/dtot : nc[c]/Math.max(nd,1e-9);
        let sh2 = (1-MECH)*byAbs + MECH*(nc[c]/Math.max(nd,1e-9));
        // refill above the metabolic deficit restores the resting
        // distribution, which is what lets a collapsed unit see gas again
        const exc=Math.max(0,inflow-Math.max(deficit,0));
        if(exc>1e-9 && inflow>1e-9){ const w=exc/inflow;
          sh2=(1-w)*sh2 + w*(nc0[c]/nc0Sum); }
        n[3*c]   += (-vo2c[c])*dtm + sh2*add[0];
        n[3*c+1] += ( vco2c[c])*dtm + sh2*add[1];
        n[3*c+2] += ( vn2*qw[c])*dtm + sh2*add[2];
      }
    } else {
      for(let c=0;c<NC;c++){
        n[3*c]   += (-vo2c[c])*dtm;
        n[3*c+1] += ( vco2c[c])*dtm;
        n[3*c+2] += ( vn2*qw[c])*dtm;
      }
    }
    // cardiogenic stirring toward the lung-mean composition
    if(TAUMIX>0){
      let so=0,sc2=0,sn2=0,st2=0;
      for(let c=0;c<NC;c++){ so+=n[3*c]; sc2+=n[3*c+1]; sn2+=n[3*c+2]; }
      st2=so+sc2+sn2; const k=Math.min(1,dt/TAUMIX);
      if(st2>1e-12){ const fo=so/st2, fc=sc2/st2, fn=sn2/st2;
        for(let c=0;c<NC;c++){ const q=n[3*c]+n[3*c+1]+n[3*c+2];
          n[3*c]+=(q*fo-n[3*c])*k; n[3*c+1]+=(q*fc-n[3*c+1])*k;
          n[3*c+2]+=(q*fn-n[3*c+2])*k; } }
    }
    for(let c=0;c<NC*3;c++) if(n[c]<1e-12) n[c]=1e-12;
    n2p=n2p.map((p,j)=>Math.max(0,p-flux[j]*dtm/n2cap[j]));

    let p1=caN,p2=ccN;
    for(let j=0;j<NP;j++){ aO2[j]+=(coNow/vas)*(p1-aO2[j])*dtm; aC[j]+=(coNow/vas)*(p2-aC[j])*dtm;
      p1=aO2[j];p2=aC[j]; }
    tO2+=((coNow*(aO2[NP-1]-tO2)*10-vo2)/(P.vTisO2*10))*dtm;
    const fs=0.8*(tC-sC)*10;
    tC+=((coNow*(aC[NP-1]-tC)*10+vco2m-fs)/(22*10))*dtm;
    sC+=(fs/(140*10))*dtm;
    p1=tO2;p2=tC;
    for(let j=0;j<NP;j++){ vO2[j]+=(coNow/vvs)*(p1-vO2[j])*dtm; vC[j]+=(coNow/vvs)*(p2-vC[j])*dtm;
      p1=vO2[j];p2=vC[j]; }

    if(i%stride===0||!last){ last=arterialState(aC[NP-1],be,hb,aO2[NP-1],T);
      pvo2=po2FromO2Content(vO2[NP-1],hb,last.pH,last.pco2,T);
      paco2Prev=last.pco2; sao2Prev=last.so2; }
    hist.push(last.so2);
    const lag=Math.round(25/dt);
    spo2+=(hist[Math.max(0,hist.length-1-lag)]-spo2)*(dt/8);

    if(i%stride===0){
      out.t.push(i*dt); out.spo2.push(spo2*100); out.vol.push(vLung);
      out.fao2.push(pAO2/713); out.pan2.push(pAN2); out.paco2.push(last.pco2);
      out.ph.push(last.pH); out.pao2.push(last.po2); out.shunt.push(shunt);
      out.palv.push((pabs-PB)*1.35951); out.lungO2.push(tO);
      out.hpv.push(hpv); out.pvo2.push(pvo2); out.co.push(coNow); out.hr.push(hrNow);
      out.map.push(mapNow); out.pap.push(papNow); out.sv.push(svNow);
      out.atel.push(absorbed);
    }
    if(hrNow<=0 && tLow > (P.hrTermDelay||20)+30+45) break;
  }
  out.frc=frc; out.cc=cc; out.vo2=vo2; out.coBase=co; out.bmi=d.bmi;
  return out;
}

if(typeof module!=='undefined') module.exports={simulate,derive,
  so2FromPo2,o2Content,co2Content,phFromPco2Be,arterialState};
