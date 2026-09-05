// parity_driver.js — run model.js from the command line so the Python test
// suite can drive it.
//
// Exists only so test_parity.py can put the two implementations on identical
// inputs. It is deliberately dumb: it holds no parameters and no defaults of
// its own, because any value it invented here would be a value the comparison
// silently stopped testing. Everything comes in from Python.
//
//   echo '<job json>' | node parity_driver.js
//
// Job:
//   { "params": {...},                     // the P object model.js reads
//     "epochs": [{"d":600,"R":2,"fg":1.0}] // R null means a sealed airway
//     "dt": 0.05 }
//
// Out: {"ok":true,"out":{...}} or {"ok":false,"error":"..."}
//
// JSON has no Infinity, so a sealed airway arrives as R:null and is converted
// here. model.js tests it with isFinite(), and isFinite(null) is TRUE — null
// coerces to 0 — so passing it through untouched would silently model a
// zero-resistance wide-open airway instead of a sealed one. That is exactly
// the kind of quiet mistranslation this harness exists to catch, so it is
// asserted rather than assumed.

'use strict';

const path = require('path');
const model = require(path.join(__dirname, 'model.js'));

function readStdin() {
  return new Promise((resolve, reject) => {
    let buf = '';
    process.stdin.setEncoding('utf8');
    process.stdin.on('data', (d) => { buf += d; });
    process.stdin.on('end', () => resolve(buf));
    process.stdin.on('error', reject);
  });
}

function main(job) {
  if (!job || typeof job !== 'object') throw new Error('job must be an object');
  const params = job.params;
  const dt = job.dt;
  if (!params || typeof params !== 'object') throw new Error('job.params missing');
  if (typeof dt !== 'number' || !(dt > 0)) throw new Error('job.dt must be > 0');
  if (!Array.isArray(job.epochs) || job.epochs.length === 0) {
    throw new Error('job.epochs must be a non-empty array');
  }

  // Guard against a param that model.js reads but Python forgot to send.
  // Such a key is `undefined`, arithmetic on it yields NaN, and NaN silently
  // poisons the whole run -- a comparison that then "passes" on both sides
  // being garbage. Fail loudly instead.
  for (const [k, v] of Object.entries(params)) {
    if (typeof v === 'number' && !Number.isFinite(v)) {
      throw new Error(`param ${k} is not finite: ${v}`);
    }
  }

  const epochs = job.epochs.map((e, i) => {
    if (typeof e.d !== 'number' || !(e.d > 0)) {
      throw new Error(`epoch ${i}: d must be > 0`);
    }
    if (typeof e.fg !== 'number') throw new Error(`epoch ${i}: fg must be a number`);
    // null is the wire form of an occluded airway (JSON cannot carry Infinity)
    const R = (e.R === null) ? Infinity : e.R;
    if (typeof R !== 'number') throw new Error(`epoch ${i}: R must be a number or null`);
    if (R !== Infinity && !(R > 0)) throw new Error(`epoch ${i}: R must be > 0 or null`);
    return { d: e.d, R: R, fg: e.fg };
  });

  const out = model.simulate(params, epochs, dt);

  // Every series must be finite. A NaN here means the port diverged into
  // nonsense, which is a louder failure than a 1% mismatch and should be
  // reported as such rather than compared.
  for (const [k, v] of Object.entries(out)) {
    if (Array.isArray(v)) {
      for (let i = 0; i < v.length; i++) {
        if (!Number.isFinite(v[i])) {
          throw new Error(`output series ${k}[${i}] is not finite: ${v[i]}`);
        }
      }
    } else if (typeof v === 'number' && !Number.isFinite(v)) {
      throw new Error(`output scalar ${k} is not finite: ${v}`);
    }
  }
  return out;
}

// process.exit() is deliberately not used. When stdout is a pipe its writes
// are asynchronous, and exit() drops whatever has not flushed -- which for a
// long run truncates the JSON at the 64 KB pipe buffer and hands Python a
// parse error instead of results. Setting exitCode lets node drain and leave
// of its own accord.
function finish(result) {
  process.exitCode = result.ok ? 0 : 1;
  process.stdout.write(JSON.stringify(result));
}

readStdin().then((raw) => {
  try {
    finish({ ok: true, out: main(JSON.parse(raw)) });
  } catch (err) {
    finish({ ok: false, error: err && err.message ? err.message : String(err) });
  }
}).catch((err) => {
  finish({ ok: false, error: String(err) });
});
