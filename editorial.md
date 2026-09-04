# Cannot intubate, *can* oxygenate: reframing apnoeic oxygenation as a strategy for avoiding the emergency rather than surviving it

## The wrong endpoint

Apnoeic oxygenation is almost always justified by the wrong number. "Prolongs safe apnoea time" is the standard claim, and it sounds incremental — a few more minutes of the same emergency. It invites the reasonable objection that a difficult airway is difficult whether you have nine minutes or nineteen, and it puts the technique in competition with better laryngoscopy, better positioning and better preoxygenation, all of which also buy time.

That framing understates what is actually happening. Continuous oxygen delivery to a patent pharynx does not extend a trajectory. It replaces one trajectory with a qualitatively different one. Without it, arterial saturation falls without limit, because the alveolar oxygen store is finite and is being consumed at roughly 250 ml.min⁻¹. With it, saturation falls to a **plateau** and stops.

The algebra is elementary and, as far as we can find, has not been stated explicitly in this context. Substituting the Fick relation, CvO₂ = CaO₂ − V̇O₂/(10Q̇), into the shunt equation, CaO₂ = (1−f)Cc′O₂ + f·CvO₂, and solving for arterial content gives

> CaO₂ = Cc′O₂ − [f/(1−f)] · V̇O₂/(10Q̇)

This is a fixed point. Because the iteration has gain *f* < 1 it is always stable, and it is approached geometrically over roughly 1/(1−f) circulation times — a matter of a few minutes. It exists *only* because a maintained supply of alveolar oxygen holds Cc′O₂ constant. Remove the oxygen supply and Cc′O₂ itself decays; there is then no fixed point, and desaturation continues to levels incompatible with life.

The clinical consequence follows directly. Apnoeic oxygenation does not buy time in a losing situation. It converts *cannot intubate, cannot oxygenate* into *cannot intubate, can oxygenate* — two emergencies with entirely different mortality, and one of which permits the anaesthetist to stop, think, and call for help.

## How much shunt can be tolerated

Computational modelling of the plateau across patient phenotypes produces a result that we did not anticipate: the plateau saturation is governed almost entirely by shunt fraction, and barely at all by body habitus. The critical shunt at which the plateau falls to 90% is 0.36–0.37 in a lean adult, an obese adult and a morbidly obese adult alike. The reason is that oxygen consumption and cardiac output scale together, so the arteriovenous content difference — the other term in the equation — is nearly invariant. Phenotype determines what shunt fraction a patient arrives at, not what a given shunt fraction costs.

This explains an otherwise puzzling observation in our own randomised data. Toner and colleagues reported that some patients desaturated early despite reliably maintained tracheal oxygen concentrations, and concluded that mechanisms other than device failure must be operating [1]. The plateau model identifies the mechanism: these are patients whose shunt fraction exceeded roughly 0.35, most plausibly through airway closure and absorption atelectasis in lungs whose closing capacity already exceeded their functional residual capacity.

## The conduit is smaller than anyone assumes

The second finding is more surprising and more useful. The aventilatory mass flow required is only about 200 ml.min⁻¹ — 3.3 ml.s⁻¹. The pressure cost of driving that flow through a narrowed airway is trivial. For a 3 mm aperture it is 0.016 cmH₂O; for a 2 mm aperture, 0.05; for a 1 mm aperture, about 0.6–1.7 cmH₂O depending on the length of the narrowed segment. Against this, the relaxed lung generates several cmH₂O of subatmospheric recoil within the first minute of apnoea, and the flow is laminar throughout (Reynolds number ≈ 265 at 1 mm), so the analysis is straightforward.

Airway resistance is linear in the length of the constriction and inversely proportional to the fourth power of its radius, so radius dominates overwhelmingly. Across the full anatomical range of obstruction lengths — 1 cm for a glottic narrowing, 5 cm for an apposed pharynx — the aperture at which the pressure cost reaches 10 cmH₂O varies only between 0.49 and 0.64 mm. At apertures below about 1 mm the inertial entrance and exit losses become comparable to the viscous term, so Poiseuille alone underestimates a short constriction; both terms should be included.

**Patency is therefore effectively binary.** A continuous channel of a millimetre or so sustains oxygenation indefinitely. Only a true seal — soft palate apposition, laryngospasm, an inhaled mass, an occluding plug — defeats the technique. Modelling bears this out: with the pharynx at 100% oxygen, an airway of 0.8 mm effective aperture maintains saturation above 90% for 30 minutes in both a lean and an obese virtual patient, while complete occlusion fails at 402 and 264 seconds respectively.

A related point deserves emphasis because it is a real advantage over pressure-dependent techniques. During spontaneous inspiration at 30 l.min⁻¹, intraluminal pharyngeal pressure falls to around −11 cmH₂O, which actively collapses a compliant airway. During aventilatory mass flow it falls by 0.07 cmH₂O at a 2 mm aperture. Measured pharyngeal critical closing pressures run from −15 cmH₂O in normal subjects to positive values in the anaesthetised obese. Mass flow therefore sits three orders of magnitude below the pressures at which collapse is determined. **The airway closes on anatomy and muscle tone, not on the flow.** Apnoeic oxygenation is uniquely undemanding of a collapsible pharynx.

## Where it fails, and where it cannot

Intellectual honesty requires stating the failure modes precisely.

**True occlusion.** No pharyngeal oxygen fraction helps when there is no conduit. In modelling a can't-intubate-can't-oxygenate progression, buccal oxygen bought approximately 50–70 seconds, all of it banked before the airway was lost. The technique must not be sold as a CICO intervention.

**Occluding plugs — and blood is far more forgiving than mucus.** Both face a capillary threshold of 2σ/r, and mucus's is actually the lower of the two because its surface tension is lower. The difference is rheological. Blood is Newtonian at ~3.5 mPa.s and, once past the capillary threshold, clears in milliseconds. Mucus has a yield stress of 1–10 Pa normally and up to ~100 Pa when purulent; below yield it does not flow at any pressure, for any duration. Wall shear at 5 cmH₂O across a 5 mm plug is 24.5 Pa at a 1 mm aperture but only 4.9 Pa at 0.2 mm. Blood is a transient obstruction; mucus is an absorbing one.

**Nitrogen.** In prolonged apnoea there is no expiration, so nitrogen returning from tissue accumulates in the alveolus permanently and displaces oxygen. Modelled with three perfusion-limited compartments (vessel-rich, τ ≈ 3 min; muscle, τ ≈ 40 min; fat, τ ≈ 4 h), alveolar PN₂ reaches 179 mmHg at 30 minutes in a lean adult but 395 mmHg in the morbidly obese, whose fat mass holds a larger nitrogen store. In that patient PAO₂ falls to 107 mmHg and the plateau begins to erode. This is a genuine ceiling on very long apnoeic oxygenation, and it is worse in obesity.

**Carbon dioxide.** This, not hypoxia, is the binding constraint on duration. Frumin's subjects reached pH below 7.0 within 30 minutes, with a nadir of 6.72 and a PaCO₂ of 250 mmHg at 53 minutes, while saturation was maintained at 98–100% throughout [2]. Our model reproduces this: 2.86 mmHg.min⁻¹ and pH 7.05 at 30 minutes in a lean adult, but pH 6.95 at 30 minutes in an obese one, because CO₂ production scales with mass and buffering does not.

O'Loughlin and colleagues should be read carefully here. Their mean apnoea was 18.7 minutes and they conclude for *short duration* laryngeal surgery, excluding BMI >45 and any condition exacerbated by hypercapnia [3]. Their measured rate of 0.15 kPa.min⁻¹ was venous, and they state explicitly that venous and end-tidal measurements significantly underestimate accumulation; their own tabulation shows arterial studies clustering at 0.40–0.45 kPa.min⁻¹. **A 30-minute ceiling is defensible in a lean patient; obesity brings it forward, and transcutaneous CO₂ monitoring beyond 15 minutes is the better recommendation than a fixed number.**

## The algorithmic consequence

If the only thing that defeats apnoeic oxygenation is a seal, then a difficult-airway algorithm built around it should not optimise for the technique most likely to place a tube. It should optimise for **the technique most likely to guarantee a non-zero conduit, whether or not intubation succeeds.**

That selects hyperangulated video laryngoscopy, for reasons that have nothing to do with intubation success rates. A hyperangulated blade follows the tongue contour and lifts the entire 2–4 cm velopharyngeal and tongue-base segment off the posterior wall — precisely the long, narrow obstruction that our resistance analysis identifies as worst. A Macintosh blade instead displaces the tongue into the submandibular space, which is the space unavailable in exactly the patients who need the conduit most. Once seated, a rigid blade stents the pharynx irrespective of muscle tone, without a mask seal and without a sustained jaw thrust. And its characteristic failure mode — an excellent view with difficult tube delivery — is a weakness in a conventional algorithm but is the *desired state* in one aimed at avoiding CICO. It decouples opening the airway from delivering the tube, and apnoeic oxygenation needs only the first.

The corollary is that the blade should be inserted early, as an oxygenation manoeuvre, before saturation falls — not as a rescue after mask ventilation has failed — and should remain in place while help is called and equipment prepared.

## The evidence gap that matters

The clinical rationale rests on a chain: falling saturation raises operator stress; stress degrades decision-making; degraded decision-making produces fixation, repeated attempts and trauma. Each individual link has support. Repeated laryngoscopic attempts are associated with sharply increased hypoxaemia, aspiration and cardiac arrest [4], and with adverse events in prospective multicentre data [5]. Human factors contributed to *all* twelve NAP4 cases examined in detail, at a median of 4.5 factors per case, most commonly loss of situation awareness and person factors including stress [6]. Acute stress specifically impairs divided attention, working memory, retrieval and decision-making [7] — the exact cognitive functions needed to abandon a failing plan. Traumatic complications during unanticipated difficult intubation run at 0.5–7%, and guidelines already advise against blind bougie insertion at poor laryngoscopic views because of the trauma it causes.

What is missing is the causal link itself. **No study has shown that maintaining saturation improves operator performance, reduces attempt count, or reduces airway injury.** That inference is biologically obvious and entirely unevidenced.

It is also cheap to test, and requires no patients. A simulated difficult airway, randomised to a monitor displaying stable versus falling saturation with all else identical, measuring attempt count, applied force, time to escalation, time to call for help, and operator physiological stress markers, would convert the central argument of this editorial from plausible to demonstrated. Until someone does it, the case for apnoeic oxygenation as a CICO-avoidance strategy rests on physiology and inference rather than on evidence — which is a reasonable place to stand, provided we say so.

---

## References

1. Toner AJ, Douglas SG, Bailey MA, et al. Effect of apneic oxygenation on tracheal oxygen levels, tracheal pressure, and carbon dioxide accumulation: a randomized, controlled trial of buccal oxygen administration. *Anesth Analg* 2019;128:1154–9.
2. Frumin MJ, Epstein RM, Cohen G. Apneic oxygenation in man. *Anesthesiology* 1959;20:789–98.
3. O'Loughlin CJ, Phyland DJ, Vallance NA, et al. Low-flow apnoeic oxygenation for laryngeal surgery: a prospective observational study. *Anaesthesia* 2020;75:1070–5.
4. Mort TC. Emergency tracheal intubation: complications associated with repeated laryngoscopic attempts. *Anesth Analg* 2004;99:607–13.
5. Hasegawa K, Shigemitsu K, Hagiwara Y, et al. Association between repeated intubation attempts and adverse events in emergency departments: an analysis of a multicenter prospective observational study. *Ann Emerg Med* 2012;60:749–754.e2.
6. Flin R, Fioratou E, Frerk C, Trotter C, Cook TM. Human factors in the development of complications of airway management: preliminary evaluation of an interview tool. *Anaesthesia* 2013;68:817–25.
7. LeBlanc VR. The effects of acute stress on performance: implications for health professions education. *Acad Med* 2009;84(10 Suppl):S25–33.
8. Heard A, Toner AJ, Evans JR, Aranda Palacios AM, Lauer S. Apneic oxygenation during prolonged laryngoscopy in obese patients: a randomized, controlled trial of buccal RAE tube oxygen administration. *Anesth Analg* 2017;124:1162–7.
9. Peterson GN, Domino KB, Caplan RA, Posner KL, Lee LA, Cheney FW. Management of the difficult airway: a closed claims analysis. *Anesthesiology* 2005;103:33–9.
10. Cook TM, Woodall N, Frerk C. Major complications of airway management in the UK: results of the Fourth National Audit Project of the Royal College of Anaesthetists and the Difficult Airway Society. *Br J Anaesth* 2011;106:617–31.
