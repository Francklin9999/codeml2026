export const meta = {
  name: 'optiframe-finish',
  description: 'OptiFrame: finish waves 2 and 3 with model routing (cheap model first, escalate only on failure), then an app-performance pass',
  whenToUse: 'Pass args {stage: "interfaces" | "wave2" | "perf" | "wave3" | "all"}. Stages are resumable one by one; "all" runs them in order.',
  phases: [
    { title: 'Interfaces', detail: 'one Sonnet agent writes agents/WAVE1_INTERFACES.md from the real code', model: 'sonnet' },
    { title: 'Build', detail: 'one Sonnet builder per brief, in parallel', model: 'sonnet' },
    { title: 'Verify', detail: 'Sonnet verifier; Sonnet fix; Opus only if the second check still fails' },
    { title: 'Integrate', detail: 'Haiku runs the whole-project commands; Sonnet fixes attributed failures', model: 'haiku' },
    { title: 'Performance', detail: 'Haiku measures, Sonnet applies a fixed list of optimisations, Haiku re-measures' },
    { title: 'Audit', detail: 'single Opus read-only audit of rubric coverage and cross-module contracts', model: 'opus' },
  ],
}

// Token policy (why this script is cheap):
//  - prompts carry paths, not content: every agent reads its brief and its probe list from disk;
//  - mechanical work (run commands, count, measure sizes) goes to Haiku at low effort;
//  - building and fixing go to Sonnet at medium effort (high only for brief 10, the integration-heavy one);
//  - Opus is called in two places only: a blocker that survived one Sonnet fix, and the final audit;
//  - one verify round by default, a second only after a fix; no agent re-reads what a cheaper one already measured.

const ROOT = 'C:/Users/raybo/Documents/projets/CodeML_2026/codeml2026/optiframe-participants'
const OLD = ROOT + '/agents/orchestration/optiframe-wave.js'
const stage = (args && args.stage) || 'all'
const run = (s) => stage === 'all' || stage === s

const BRIEFS = {
  '10': { file: '10_ui-flow.md', effort: 'high', venv: 'none' },
  '14': { file: '14_eval-tools.md', effort: 'medium', venv: 'tools/.venv' },
  '17': { file: '17_data-collection.md', effort: 'medium', venv: 'none' },
  '15': { file: '15_docs-jury.md', effort: 'medium', venv: 'none' },
  '16': { file: '16_docs-internal.md', effort: 'medium', venv: 'none' },
}

const RULES = [
  'Project root: ' + ROOT + '. Windows machine, Git Bash and PowerShell available, Python 3.13.',
  'Write only the files listed under "You own" in your brief. A needed change elsewhere goes in your report.',
  'Never change git state (add, commit, checkout, stash, reset, clean, restore). Never run npm install/ci/update: every dependency is already in app/node_modules.',
  'While other builders run, test only your own files: from app/, `npx vitest run <your folder>` and `npx tsc --noEmit -p .` (ignore errors in files you do not own). Give every long command a timeout; the full JS suite loads OpenCV.js and can take several minutes.',
  'Python: a virtual environment inside your own directory only. Scratch files go in the OS temp directory. No process may outlive you. Do not use the Browser pane.',
  'Never invent a real-world measurement: write TO MEASURE (English) or À COMPLÉTER (French). Numbers printed by a run you made are fine.',
  'Keep your final report short: strings of one line, no prose.',
].map((x) => '- ' + x).join('\n')

const BUILD = { type: 'object', properties: {
  status: { type: 'string', enum: ['done', 'partial', 'blocked'] },
  files: { type: 'array', items: { type: 'string' } },
  tests: { type: 'string' },
  unmet: { type: 'array', items: { type: 'string' } },
  needsElsewhere: { type: 'array', items: { type: 'string' } },
  toMeasure: { type: 'array', items: { type: 'string' } },
}, required: ['status', 'files', 'tests', 'unmet'] }

const VERIFY = { type: 'object', properties: {
  pass: { type: 'boolean' },
  tests: { type: 'string' },
  blockers: { type: 'array', items: { type: 'object', properties: { file: { type: 'string' }, problem: { type: 'string' }, fix: { type: 'string' } }, required: ['file', 'problem', 'fix'] } },
  minor: { type: 'array', items: { type: 'string' } },
}, required: ['pass', 'tests', 'blockers'] }

const FIX = { type: 'object', properties: { fixed: { type: 'array', items: { type: 'string' } }, remaining: { type: 'array', items: { type: 'string' } }, tests: { type: 'string' } }, required: ['fixed', 'remaining', 'tests'] }

const INTEG = { type: 'object', properties: {
  pass: { type: 'boolean' },
  commands: { type: 'array', items: { type: 'object', properties: { cmd: { type: 'string' }, ok: { type: 'boolean' }, summary: { type: 'string' } }, required: ['cmd', 'ok', 'summary'] } },
  failures: { type: 'array', items: { type: 'object', properties: { owner: { type: 'string' }, file: { type: 'string' }, message: { type: 'string' } }, required: ['owner', 'file', 'message'] } },
}, required: ['pass', 'commands', 'failures'] }

const PERF = { type: 'object', properties: {
  initialJsKb: { type: 'number' }, initialJsGzipKb: { type: 'number' },
  assetsMb: { type: 'array', items: { type: 'object', properties: { file: { type: 'string' }, mb: { type: 'number' }, loadedWhen: { type: 'string' } }, required: ['file', 'mb', 'loadedWhen'] } },
  stageMs: { type: 'array', items: { type: 'object', properties: { stage: { type: 'string' }, ms: { type: 'number' } }, required: ['stage', 'ms'] } },
  notes: { type: 'array', items: { type: 'string' } },
}, required: ['assetsMb', 'stageMs', 'notes'] }

const buildPrompt = (id) => [
  'You build OptiFrame brief ' + id + '. Read it completely first: ' + ROOT + '/agents/' + BRIEFS[id].file + ' (Shared context, Rules, Strategy inputs and Done when are binding).',
  'Also read ' + ROOT + '/agents/WAVE1_INTERFACES.md (what the existing modules really export) and, for extra notes on this brief, the `extra` string of entry ' + id + ' in ' + OLD + '.',
  'Python venv for you: ' + BRIEFS[id].venv + '.',
  RULES,
  'Report: status, files written, test result with counts, Done-when boxes you could not meet (unmet), changes needed in files you do not own, what is left TO MEASURE.',
].join('\n')

const verifyPrompt = (id, report) => [
  'You verify OptiFrame brief ' + id + ' independently. You did not build it; look for what is wrong.',
  'Brief: ' + ROOT + '/agents/' + BRIEFS[id].file + '. Probe list: the `hints` array of entry ' + id + ' in ' + OLD + ' (read only that entry). Venv: ' + BRIEFS[id].venv + '.',
  'Builder report: ' + JSON.stringify(report),
  'Do: (1) re-run the brief tests and quote the counts; (2) for each Done-when box find the test or file that proves it and read that test (a box is met only if you saw non-tautological evidence); (3) run the probes with throwaway files in the OS temp directory or app/tests/_verify' + id + '.test.ts, deleted afterwards; (4) check scope (git status --short), contract signatures, and that no invented real-world figure appears.',
  'You may not edit owned files, install packages or change git state. A blocker makes a Done-when box false, breaks a contract, violates scope or honesty, or crashes on a probe; each needs file, problem and a concrete fix. Everything else is minor. pass = zero blockers.',
  RULES,
].join('\n')

const fixPrompt = (id, blockers, who) => [
  'You fix OptiFrame brief ' + id + ' (' + who + '). Brief: ' + ROOT + '/agents/' + BRIEFS[id].file + ' (read "You own" and Shared context). Venv: ' + BRIEFS[id].venv + '.',
  'Fix exactly these blockers at their root cause, only in files this brief owns, then re-run the brief tests:',
  JSON.stringify(blockers),
  RULES,
].join('\n')

async function buildAndVerify(ids) {
  return pipeline(
    ids,
    (id) => agent(buildPrompt(id), { label: 'build:' + id, phase: 'Build', schema: BUILD, model: 'sonnet', effort: BRIEFS[id].effort }),
    async (report, id) => {
      if (!report) return { id, status: 'no build result', blockers: [] }
      let v = await agent(verifyPrompt(id, report), { label: 'verify:' + id, phase: 'Verify', schema: VERIFY, model: 'sonnet', effort: 'medium' })
      if (v && !v.pass && v.blockers.length) {
        await agent(fixPrompt(id, v.blockers, 'first fix'), { label: 'fix:' + id, phase: 'Verify', schema: FIX, model: 'sonnet', effort: 'medium' })
        v = await agent(verifyPrompt(id, report), { label: 'reverify:' + id, phase: 'Verify', schema: VERIFY, model: 'sonnet', effort: 'medium' })
        if (v && !v.pass && v.blockers.length) {
          log('brief ' + id + ': ' + v.blockers.length + ' blocker(s) survived a Sonnet fix, escalating to Opus')
          const f = await agent(fixPrompt(id, v.blockers, 'escalation: a first fix did not resolve these'), { label: 'fix-opus:' + id, phase: 'Verify', schema: FIX, model: 'opus', effort: 'high' })
          return { id, status: report.status, unmet: report.unmet, escalated: true, remaining: f ? f.remaining : v.blockers.map((b) => b.problem), toMeasure: report.toMeasure || [], needsElsewhere: report.needsElsewhere || [] }
        }
      }
      return { id, status: report.status, unmet: report.unmet, pass: v ? v.pass : null, blockers: v ? v.blockers : [], minor: v ? (v.minor || []) : [], toMeasure: report.toMeasure || [], needsElsewhere: report.needsElsewhere || [] }
    },
  )
}

const integPrompt = (extra) => [
  'Mechanical integration check of OptiFrame. Nothing else is running. Do not fix anything, do not analyse: run, read the output, report.',
  'From ' + ROOT + '/app run, each with a 15-minute timeout: `npm run typecheck`, `npm run test`, `npm run build`. Then each Python suite that exists, from its own venv without creating one: rig/.venv, training/data/.venv, training/model/.venv, tools/.venv (`python -m pytest -q`).',
  extra,
  'For each failing test or error give the file, the first error line, and the owner brief number from the OWNERSHIP table in ' + OLD + ' (read only that table).',
].join('\n')

async function integrate(tag, extra) {
  let r = await agent(integPrompt(extra), { label: 'integrate:' + tag, phase: 'Integrate', schema: INTEG, model: 'haiku', effort: 'low' })
  if (r && !r.pass && r.failures.length) {
    const by = {}
    for (const f of r.failures) { const o = String(f.owner).padStart(2, '0'); (by[o] = by[o] || []).push(f) }
    await parallel(Object.keys(by).map((o) => () => agent([
      'Integration fixer for OptiFrame brief ' + o + '. Nothing else is running. Edit only the files that brief owns (OWNERSHIP table in ' + OLD + '; brief text in ' + ROOT + '/agents/). Fix the root cause, do not weaken a test unless the test is wrong (say why), re-run the affected tests.',
      JSON.stringify(by[o]), RULES,
    ].join('\n'), { label: 'integfix:' + o, phase: 'Integrate', schema: FIX, model: 'sonnet', effort: 'medium' })))
    r = await agent(integPrompt(extra), { label: 'integrate:' + tag + '#2', phase: 'Integrate', schema: INTEG, model: 'haiku', effort: 'low' })
  }
  return r
}

const out = { stage }

// ------------------------------------------------------------------ interfaces
if (run('interfaces')) {
  phase('Interfaces')
  out.interfaces = await agent([
    'Write ' + ROOT + '/agents/WAVE1_INTERFACES.md (the only file you may create). It is read by the builders of briefs 10, 14, 15, 16 and 17 instead of the source, so it must be exact and short (under 150 lines).',
    'Source of truth: app/src/contracts.ts and the code under app/src/capture, vision, measure, quality, frame, export, plus app/src/worker.ts, app/public/sw.js, app/src/swRegister.ts, app/public/board_spec.json, app/public/bias.json. Read the code, not the briefs.',
    'For each module: import path; every exported function with its exact TypeScript signature; what it throws (OptiError codes); named constants a caller may need; asset files it loads and how the URL is resolved; whether it is worker-safe. Then a "Conventions and traps" section taken from docs/HANDOFF_AUDIT.md section 6 only where the code confirms it (polygon orientation sign, frame mesh axes, lip overhang, sharpness measure). No opinion, no figure that is not in the code.',
    RULES,
  ].join('\n'), { label: 'interfaces', phase: 'Interfaces', model: 'sonnet', effort: 'medium' })
}

// ------------------------------------------------------------------ wave 2
if (run('wave2')) {
  out.wave2 = await buildAndVerify(['10', '14', '17'])
  out.integration2 = await integrate('wave2', 'Also check that app/dist contains index.html, eval.html, collect.html, lightbox.html, sw.js, board_spec.json, bias.json and vendor/opencv, vendor/manifold, vendor/ort; that index.html links to collect.html; and run tools/validate_stl.py from tools/.venv on an STL produced by any existing test or demo path if one writes it to the OS temp directory.')
}

// ------------------------------------------------------------------ performance
if (run('perf')) {
  phase('Performance')
  const measure = (tag) => agent([
    'Measure, do not change anything. OptiFrame web app at ' + ROOT + '/app. Run `npm run build` (15-minute timeout).',
    'Report: (1) size of the JS that index.html loads before any user action, raw and gzip, in kB (follow the script tags and static imports in dist/assets; dynamic imports do not count); (2) every file in dist larger than 0.3 MB with its size in MB and when it is fetched (at start, on first photo, on frame screen, only if a model exists, precached by sw.js: read app/public/sw.js and the loaders to answer); (3) per-stage time in ms of rectify, segmentClassic, measureLens, fuseShots (3 shots), generateFrame, meshToStl on one fixture of rig/out/fixtures, measured with a throwaway test app/tests/_perf_' + tag + '.test.ts that you delete afterwards (median of 3 runs after one warm-up; OpenCV load time reported separately as stage "opencv-load"). These are Node timings on this machine, label them so in notes.',
    RULES,
  ].join('\n'), { label: 'perf-measure:' + tag, phase: 'Performance', schema: PERF, model: 'haiku', effort: 'low' })

  const before = await measure('before')
  const applied = await agent([
    'You improve the load time and run time of the OptiFrame web app (' + ROOT + '/app) for a mid-range phone on a venue network. Nothing else is running, so you may edit across modules, but only for the items below, without changing any contract, any measured result, or any user-visible text. Baseline measured just now: ' + JSON.stringify(before),
    'Apply each item, or say why it is already true or not worth it:',
    '1. The ONNX runtime (about 14 MB) must never be downloaded unless app/public/models/lens_seg.onnx exists: probe with a HEAD request once, import onnxruntime-web dynamically only after that, and keep it out of the service-worker precache list.',
    '2. OpenCV.js (about 13 MB) loads only inside the worker, starts warming up in the background as soon as the home screen is shown, and the capture screen shows a French progress line while it is not ready. It stays cache-first in sw.js so the second visit works offline.',
    '3. three.js and the frame generator (manifold WASM) are dynamic imports reached only from the frame screen; check the build output proves they are separate chunks.',
    '4. Photos and rectified images cross the worker boundary as transferables (buffers moved, not copied); no ImageData is cloned twice.',
    '5. Marker detection runs on a downscaled copy and only corner refinement touches full resolution; the window warp is done once at PX_PER_MM. Confirm in rectify.ts, fix if not.',
    '6. Every pipeline stage records its duration (performance.now) and the result carries a `timings` record shown on the "Pas à pas" screen, so the team can read phone timings without a debugger. Add it without changing contracts.ts: return it beside the measurement.',
    '7. Add app/scripts/size-report.mjs and an npm script `size`: prints the initial JS size (raw and gzip) and each asset over 0.3 MB, exits non-zero when the initial JS exceeds 250 kB gzip. Add app/tests/perf/budget.test.ts: on one fixture, the stages after OpenCV load take under 3000 ms in total in Node (a regression guard, not a phone figure).',
    '8. deploy.yml: typecheck and tests must block the deployment (remove continue-on-error), and the size script runs after the build.',
    'Then run typecheck, the tests of every folder you touched, the new budget test, and the build. Phone timings stay TO MEASURE.',
    RULES.replace('Write only the files listed under "You own" in your brief. A needed change elsewhere goes in your report.', 'You may edit files under app/ and the deploy workflow for the eight items only.'),
  ].join('\n'), { label: 'perf-apply', phase: 'Performance', schema: FIX, model: 'sonnet', effort: 'high' })
  const after = await measure('after')
  out.perf = { before, applied, after }
  out.integrationPerf = await integrate('perf', 'Also run `npm run size` from app/.')
}

// ------------------------------------------------------------------ wave 3 + audit
if (run('wave3')) {
  out.wave3 = await buildAndVerify(['15', '16'])
  phase('Audit')
  out.audit = await agent([
    'Final read-only audit of OptiFrame (' + ROOT + '). Change nothing. Be strict and brief.',
    'A. Rubric: for each line of CHALLENGE.md sections 4, 5 and 6, name the file, test or screen that proves it and rate it implemented / partial / missing / needs-hardware.',
    'B. Contracts across modules: polygon orientation from measure and quality into frame and export; eye and nasal side from measureLens through layout to SVG; units and PX_PER_MM; worker message shapes; every ErrorCode reaches messageFor; every asset URL is relative (sub-path hosting); file names and CSV columns written by the collect page equal what tools/ and training/data read.',
    'C. Honesty: any real-world accuracy or phone timing stated anywhere without TO MEASURE or À COMPLÉTER.',
    'Return a Markdown report of at most 80 lines: a table for A, a list of issues for B and C with severity, owner brief and a one-line fix, then the five actions with the most rubric points at stake.',
  ].join('\n'), { label: 'audit', phase: 'Audit', model: 'opus', effort: 'high' })
  out.integration3 = await integrate('wave3', 'Also write a throwaway link checker in the OS temp directory and list every broken relative link in the .md files of the project tree (skip node_modules and agents/orchestration/docs_backup).')
}

return out
