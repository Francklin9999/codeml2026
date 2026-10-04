// DayOne midwife app: WhatsApp-style conversational agent, offline-first (strategies 8, 9, 10, 13, 15, 17).
// Records live encrypted in IndexedDB (AES-GCM, key derived from the device PIN). Every state change is an
// event. AI processing, booklet checks, patient matching and sync go to the facility edge box when online.
"use strict";
const PARAMS = new URLSearchParams(location.search);
const DB_NAME = PARAMS.get("db") || "dayone", API = "";        // ?db=e2e keeps test runs apart from real data
let key = null, db = null, LANG = localStorage.getItem("lang") || "fr", SCHEMA = null;
const T = (k, vars = {}) => (I18N[LANG][k] || k).replace(/\{(\w+)\}/g, (_, v) => vars[v] ?? "");
const app = { forceOffline: false };
window.app = app;

// ------------------------------------------------------------------ storage (IndexedDB + WebCrypto)
function idb() {
  return new Promise((res, rej) => {
    const r = indexedDB.open(DB_NAME, 2);
    r.onupgradeneeded = () => {
      const d = r.result;
      for (const s of ["records", "meta"]) if (!d.objectStoreNames.contains(s)) d.createObjectStore(s, s === "records" ? { keyPath: "id" } : undefined);
      if (!d.objectStoreNames.contains("events")) d.createObjectStore("events", { autoIncrement: true });
    };
    r.onsuccess = () => res(r.result); r.onerror = () => rej(r.error);
  });
}
const tx = (store, mode, fn) => new Promise((res, rej) => {
  const t = db.transaction(store, mode); const out = fn(t.objectStore(store));
  t.oncomplete = () => res(out instanceof IDBRequest ? out.result : out); t.onerror = () => rej(t.error);
});
async function deriveKey(pin) {
  let salt = await tx("meta", "readonly", s => s.get("salt"));
  if (!salt) { salt = crypto.getRandomValues(new Uint8Array(16)); await tx("meta", "readwrite", s => s.put(salt, "salt")); }
  const base = await crypto.subtle.importKey("raw", new TextEncoder().encode(pin), "PBKDF2", false, ["deriveKey"]);
  return crypto.subtle.deriveKey({ name: "PBKDF2", salt, iterations: 200000, hash: "SHA-256" }, base,
    { name: "AES-GCM", length: 256 }, false, ["encrypt", "decrypt"]);
}
async function enc(bytes, aad) {
  const iv = crypto.getRandomValues(new Uint8Array(12));
  const c = await crypto.subtle.encrypt({ name: "AES-GCM", iv, additionalData: new TextEncoder().encode(aad) }, key, bytes);
  return { iv, c: new Uint8Array(c) };
}
async function dec(blob, aad) {
  return new Uint8Array(await crypto.subtle.decrypt({ name: "AES-GCM", iv: blob.iv, additionalData: new TextEncoder().encode(aad) }, key, blob.c));
}
const encJSON = (o, aad) => enc(new TextEncoder().encode(JSON.stringify(o)), aad);
const decJSON = async (b, aad) => JSON.parse(new TextDecoder().decode(await dec(b, aad)));
const getRec = id => tx("records", "readonly", s => s.get(id));
const putRec = r => tx("records", "readwrite", s => s.put(r));
const allRecs = () => tx("records", "readonly", s => s.getAll());

// lifecycle (same states as strategy 8; the server-side store implements the same machine)
const TRANSITIONS = {
  "CAPTURÉ": ["EN_ATTENTE_IA", "DOUBLON_SUSPECTÉ"], "DOUBLON_SUSPECTÉ": ["EN_ATTENTE_IA"],
  "EN_ATTENTE_IA": ["TRAITÉ_IA", "ÉCHEC_TRAITEMENT", "RÉVISION_MANUELLE_REQUISE"],
  "ÉCHEC_TRAITEMENT": ["EN_ATTENTE_IA", "RÉVISION_MANUELLE_REQUISE"],
  "TRAITÉ_IA": ["À_RÉVISER", "VALIDÉ"], "À_RÉVISER": ["VALIDÉ", "CAPTURÉ"], "RÉVISION_MANUELLE_REQUISE": ["VALIDÉ"],
  "VALIDÉ": ["PATIENTE_LIÉE", "RÉVISION_MANUELLE_REQUISE"], "PATIENTE_LIÉE": ["ENREGISTRÉ"],
  "ENREGISTRÉ": ["SYNCHRONISÉ", "ÉCHEC_SYNCHRO"], "ÉCHEC_SYNCHRO": ["ENREGISTRÉ"], "SYNCHRONISÉ": []
};
async function setState(rec, to, reason) {
  if (rec.state === to) return;
  if (!(TRANSITIONS[rec.state] || []).includes(to)) throw new Error(`illegal ${rec.state} -> ${to}`);
  const from = rec.state; rec.state = to; rec.updatedAt = Date.now();
  await putRec(rec);
  await tx("events", "readwrite", s => s.add({ id: rec.id, from, to, reason, at: Date.now() }));
  renderQueue();
}
app.events = () => tx("events", "readonly", s => s.getAll());

// ------------------------------------------------------------------ connectivity
const online = () => navigator.onLine && !app.forceOffline;
async function api(path, opts) {
  if (!online()) throw new Error("offline");
  const r = await fetch(API + path, opts);
  if (!r.ok) { const e = new Error("HTTP " + r.status); e.status = r.status; throw e; }
  return r.json();
}

// ------------------------------------------------------------------ chat UI
const chat = () => document.getElementById("chat");
const now = () => new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
function bubble(who, text, img) {
  const row = document.createElement("div"); row.className = "row " + who;
  const b = document.createElement("div"); b.className = "bubble";
  if (img) { const i = document.createElement("img"); i.src = img; i.alt = "extrait de la page"; b.appendChild(i); }
  if (text) b.appendChild(document.createTextNode(text));
  const m = document.createElement("span"); m.className = "meta"; m.textContent = now() + (who === "me" ? " ✓✓" : ""); b.appendChild(m);
  row.appendChild(b); chat().appendChild(row); chat().scrollTop = 1e9; return b;
}
function sys(text) { const d = document.createElement("div"); d.className = "sys"; d.innerHTML = "<span></span>"; d.firstChild.textContent = text; chat().appendChild(d); chat().scrollTop = 1e9; }
const say = (text, img) => bubble("bot", text, img);
app.transcript = () => [...chat().querySelectorAll(".bubble, .sys span, .replies button")].map(e => e.textContent);

// non-blocking quick replies with direct actions (e.g. "finish the registry")
function offer(text, buttons) {
  say(text);
  const box = document.createElement("div"); box.className = "replies";
  for (const [lab, fn] of buttons) {
    const btn = document.createElement("button"); btn.textContent = lab;
    btn.onclick = () => { box.querySelectorAll("button").forEach(b => b.disabled = true); bubble("me", lab); fn(); };
    box.appendChild(btn);
  }
  chat().appendChild(box); chat().scrollTop = 1e9;
}

// one pending question at a time: resolved by a quick-reply button or by typed text
let pending = null;
function ask(text, buttons = [], { img = null, text: expectText = true } = {}) {
  say(text, img);
  const box = document.createElement("div"); box.className = "replies";
  return new Promise(resolve => {
    const q = { resolve, expectText, box };
    pending = q;
    for (const b of buttons) {
      const btn = document.createElement("button"); btn.textContent = b;
      btn.onclick = () => { if (pending === q) answer(b, true); }; box.appendChild(btn);
    }
    if (buttons.length) { chat().appendChild(box); chat().scrollTop = 1e9; }
  });
}
function answer(text, fromButton) {
  if (!pending || (!fromButton && !pending.expectText)) return false;
  const p = pending; pending = null;
  p.box.querySelectorAll("button").forEach(b => b.disabled = true);
  bubble("me", text);
  p.resolve(text);
  return true;
}
app.reply = text => answer(text, true);          // used by tests / demo script
app.pendingButtons = () => pending ? [...pending.box.querySelectorAll("button")].map(b => b.textContent) : null;
app.pendingText = () => pending ? pending.box.previousSibling?.textContent || "" : null;

// ------------------------------------------------------------------ on-device quality gate (strategy 4)
app.quality = async function (blob) {
  const bmp = await createImageBitmap(blob);
  const sc = 600 / Math.max(bmp.width, bmp.height);
  const w = Math.round(bmp.width * sc), h = Math.round(bmp.height * sc);
  const cv = new OffscreenCanvas(w, h); const cx = cv.getContext("2d"); cx.drawImage(bmp, 0, 0, w, h);
  const d = cx.getImageData(0, 0, w, h).data; const g = new Float32Array(w * h);
  let sum = 0, glare = 0;
  for (let i = 0; i < w * h; i++) {
    const r = d[4 * i], gg = d[4 * i + 1], b = d[4 * i + 2]; const y = 0.299 * r + 0.587 * gg + 0.114 * b;
    g[i] = y; sum += y; if (Math.min(r, gg, b) > 245) glare++;
  }
  let lap = 0, lap2 = 0, n = 0;
  for (let y = 1; y < h - 1; y++) for (let x = 1; x < w - 1; x++) {
    const i = y * w + x; const v = 4 * g[i] - g[i - 1] - g[i + 1] - g[i - w] - g[i + w]; lap += v; lap2 += v * v; n++;
  }
  const varLap = lap2 / n - (lap / n) ** 2, mean = sum / (w * h), glareFrac = glare / (w * h);
  const issues = [];
  // blur threshold measured in strat4/quality_gate.py: catches 90% of badly-extracted captures at 12% false rejects
  if (varLap < 340) issues.push("blurry");
  if (mean < 60) issues.push("dark");
  if (glareFrac > 0.08) issues.push("glare");
  return { ok: issues.length === 0, varLap, mean, glareFrac, issues };
};

// ------------------------------------------------------------------ capture
let session = null, retakeOf = null;
const newSession = () => ({ id: crypto.randomUUID(), started: Date.now() });

app.captureBlob = async function (blob, { force = false } = {}) {
  const url = URL.createObjectURL(blob);
  bubble("me", "", url);
  const q = await app.quality(blob);
  if (!q.ok && !force) {
    const a = await ask(q.issues.map(i => T(i)).join(" "), [T("retakeNow"), T("keepAnyway")], { text: false });
    if (ACTIONS[a] !== "keepAnyway") return { rejected: true, q };
  }
  const bytes = new Uint8Array(await blob.arrayBuffer());
  const sha = Array.from(new Uint8Array(await crypto.subtle.digest("SHA-256", bytes))).map(b => b.toString(16).padStart(2, "0")).join("");
  if (!session) session = newSession();
  let rec;
  if (retakeOf) {                                         // "Reprendre la photo": new version of the same record
    rec = await getRec(retakeOf); retakeOf = null;
    rec.version += 1; rec.image = await enc(bytes, rec.id + ":" + rec.version); rec.sha256 = sha; rec.result = null; rec.attempts = 0;
    await setState(rec, "CAPTURÉ", "retake");
  } else {
    rec = { id: crypto.randomUUID(), sid: session.id, state: "CAPTURÉ", version: 0, midwife: "sf-01", capturedAt: Date.now(),
            sha256: sha, attempts: 0 };
    rec.image = await enc(bytes, rec.id + ":0");
    await putRec(rec);
    await tx("events", "readwrite", s => s.add({ id: rec.id, from: null, to: "CAPTURÉ", reason: "capture", at: Date.now() }));
    const dup = (await allRecs()).find(r => r.id !== rec.id && r.sid === rec.sid && r.sha256 === sha && r.state !== "DOUBLON_SUSPECTÉ");
    if (dup) {                                            // strategy 17: same bytes already captured in this session
      await setState(rec, "DOUBLON_SUSPECTÉ", "same sha256 as " + dup.id.slice(0, 8));
      const a = await ask(T("dup"), [T("dupDrop"), T("dupKeep")], { text: false });
      if (ACTIONS[a] !== "dupKeep") { renderQueue(); return { duplicate: true, id: rec.id }; }
    }
  }
  await setState(rec, "EN_ATTENTE_IA", "queued");
  say(online() ? T("processing") : T("queuedOffline"));
  kick();
  return { id: rec.id, q };
};

// ------------------------------------------------------------------ agent loops
// netLoop: AI processing + sync (no user interaction, runs whenever the network allows)
// uiLoop : review, cross-checks and patient matching (one conversation at a time)
let netRunning = false, uiRunning = false;
function kick() { if (!netRunning) netLoop(); if (!uiRunning) uiLoop(); }
async function netLoop() {
  netRunning = true;
  try {
    for (;;) {
      if (!online()) break;
      const recs = await allRecs();
      const todo = recs.filter(r => r.state === "EN_ATTENTE_IA" && (r.nextTry || 0) <= Date.now()).sort((a, b) => a.capturedAt - b.capturedAt);
      if (todo.length) { await processRec(todo[0]); if (!uiRunning) uiLoop(); continue; }
      const reg = recs.filter(r => r.state === "ENREGISTRÉ" || (r.state === "ÉCHEC_SYNCHRO" && (r.nextTry || 0) <= Date.now()));
      if (reg.length) { await syncRecords(reg); continue; }
      break;
    }
  } catch (e) { console.error(e); }
  netRunning = false; renderQueue();
}
async function uiLoop() {
  uiRunning = true;
  try {
    for (;;) {
      const recs = await allRecs();
      const rev = recs.filter(r => r.state === "TRAITÉ_IA" || r.state === "À_RÉVISER").sort((a, b) => a.capturedAt - b.capturedAt);
      if (rev.length) { await review(rev[0]); continue; }
      if (finishRequested && online()) { finishRequested = false; await finishSession(); if (!netRunning) netLoop(); continue; }
      break;
    }
  } catch (e) { console.error(e); say("⚠️ " + e.message); }
  uiRunning = false; renderQueue();
}

async function processRec(rec) {
  try {
    const bytes = await dec(rec.image, rec.id + ":" + rec.version);
    const fd = new FormData();
    fd.append("image", new Blob([bytes], { type: "image/jpeg" }), "page.jpg");
    fd.append("idempotency_key", rec.id + ":" + rec.version);
    fd.append("midwife_id", rec.midwife);
    fd.append("session_id", rec.sid);
    const res = await api("/process", { method: "POST", body: fd });
    rec.result = await encJSON(res.page, rec.id + ":res");
    if (res.masked_image) {            // keep the original photo with identifier zones masked; drop the raw one
      const mb = new Uint8Array(await (await fetch(res.masked_image)).arrayBuffer());
      rec.image = await enc(mb, rec.id + ":" + rec.version); rec.imageMasked = true;
    }
    rec.pageType = res.page.page_type; rec.pageName = res.page.page_name;
    rec.toReview = res.page.fields.filter(f => ["À_RÉVISER", "ILLISIBLE"].includes(f.status)).length;
    await setState(rec, "TRAITÉ_IA", "edge box");
  } catch (e) {
    if (e.message === "offline") return;
    rec.attempts = (rec.attempts || 0) + 1; rec.nextTry = Date.now() + Math.min(60000, 2000 * 2 ** rec.attempts);
    await setState(rec, "ÉCHEC_TRAITEMENT", e.message || String(e));
    await setState(rec, "EN_ATTENTE_IA", "retry in " + Math.round((rec.nextTry - Date.now()) / 1000) + " s");
    if (rec.attempts === 3) say(T("procFail") + " → « manuel »");
  }
}

const label = (pt, key) => ((SCHEMA[pt] || {}).fields || []).find(f => f.key === key)?.label || key;
const PRIORITY = /\.(ta|t|pouls|poids|ddr|date_prevue|hemoglobine|serologie_vih|syphilis|bcf)\b|inline\.(ta|t|ddr)/;

async function review(rec) {
  const page = await decJSON(rec.result, rec.id + ":res");
  const pt = String(page.page_type);
  if (rec.state === "TRAITÉ_IA" && page.page_status && page.page_status !== "OK" && !page.verdictAsked) {
    const bad = page.page_status === "PAGE_NON_RECONNUE";
    const a = await ask(T(bad ? "notRecognised" : "lowQuality"), [T("retake"), bad ? T("manual") : T("checkAnyway")], { text: false });
    if (ACTIONS[a] === "retake") { await setState(rec, "À_RÉVISER", page.page_status); return retake(rec); }
    if (ACTIONS[a] === "manual") { await setState(rec, "À_RÉVISER", page.page_status); await setState(rec, "CAPTURÉ", "manual instead");
      await setState(rec, "EN_ATTENTE_IA", "manual"); await setState(rec, "RÉVISION_MANUELLE_REQUISE", "page not recognised"); return manualEntry(rec, true); }
    page.verdictAsked = true; rec.result = await encJSON(page, rec.id + ":res"); await putRec(rec);
  }
  if (rec.state === "TRAITÉ_IA") {
    const textF = page.fields.filter(f => f.type === "text");
    const unsure = page.fields.filter(f => ["À_RÉVISER", "ILLISIBLE"].includes(f.status) && !f.reviewed);
    say(T("summary", { page: LANG === "fr" ? SCHEMA[pt].name_fr : SCHEMA[pt].name_en,
      ok: page.fields.length - unsure.length - textF.filter(f => f.value == null).length,
      q: unsure.length, blank: textF.filter(f => f.value == null).length }));
    if (!unsure.length) { say(T("allSure")); await setState(rec, "VALIDÉ", "all confident"); return afterPage(rec); }
    await setState(rec, "À_RÉVISER", unsure.length + " uncertain fields");
  }
  const queue = page.fields.filter(f => ["À_RÉVISER", "ILLISIBLE"].includes(f.status) && !f.reviewed)
    .sort((a, b) => (!PRIORITY.test(a.key)) - (!PRIORITY.test(b.key)) || (a.confidence || 0) - (b.confidence || 0));
  let n = 0;
  const BATCH = 8;
  for (const [i, f] of queue.entries()) {
    if (i > 0 && i % BATCH === 0) {                   // never more than 8 questions in a row
      const a = await ask(T("moreLeft", { n: queue.length - i }), [T("continue"), T("validateAsIs")], { text: false });
      if (ACTIONS[a] === "validateAsIs") {            // remaining doubts stay visible as À_RÉVISER in the record
        for (const g of queue.slice(i)) { g.status = "À_RÉVISER"; g.deferred = true; g.reviewed = true; }
        rec.result = await encJSON(page, rec.id + ":res"); await putRec(rec);
        break;
      }
    }
    const lab = label(pt, f.key), conf = Math.round(100 * (f.confidence || 0));
    let a;
    if (f.type === "checkbox") {
      a = await ask(T("askBox", { label: lab, guess: f.value ? T("checked") : T("unchecked"), conf }),
        [T("yesChecked"), T("noBox"), T("retake")], { img: f.evidence, text: false });
      if (ACTIONS[a] === "retake") return retake(rec);
      f.value = ACTIONS[a] === "yesChecked"; f.status = "CONNU";
    } else if (f.value == null) {
      a = await ask(T("askIllegible", { label: lab }), [T("type"), T("empty"), T("unknown"), T("retake"), ...(f.suggestions || [])], { img: f.evidence });
      if (ACTIONS[a] === "retake") return retake(rec);
      if (ACTIONS[a] === "type") a = await ask(T("typeValue", { label: lab }), []);
      setValue(f, a);
    } else {
      a = await ask(T("ask", { label: lab, value: f.value, conf }), [T("confirm"), T("correct"), T("retake"), ...(f.suggestions || []).filter(s => s !== f.value)], { img: f.evidence });
      if (ACTIONS[a] === "retake") return retake(rec);
      if (ACTIONS[a] === "correct") a = await ask(T("typeValue", { label: lab }), []);
      if (ACTIONS[a] === "confirm") { f.status = "CONNU"; f.confidence = 1; } else setValue(f, a);
    }
    f.reviewed = true; n++;
    rec.result = await encJSON(page, rec.id + ":res"); await putRec(rec);   // nothing lost if the app closes mid-review
  }
  say(T("pageDone", { n }));
  await setState(rec, "VALIDÉ", "midwife review");
  return afterPage(rec);
}
function setValue(f, a) {
  const k = ACTIONS[a], low = (a || "").trim().toLowerCase();
  if (k === "empty" || ["vide", "empty", "-", "–"].includes(low)) { f.value = null; f.status = "NON_FOURNI"; }
  else if (k === "unknown" || ["inconnu", "unknown", "?"].includes(low)) { f.value = a; f.status = "INCONNU"; }
  else { f.value = a.trim(); f.status = "CONNU"; }
  f.confidence = 1; f.reviewed = true;
}
async function retake(rec) {
  retakeOf = rec.id;
  await setState(rec, "CAPTURÉ", "retake requested");
  say(T("retakeAsk"));
}
let finishRequested = false;
async function afterPage(rec) {
  const others = (await allRecs()).filter(r => r.sid === rec.sid && ["EN_ATTENTE_IA", "TRAITÉ_IA", "À_RÉVISER", "CAPTURÉ"].includes(r.state));
  if (others.length) return;
  offer(T("next"), [[T("finish"), () => { finishRequested = true; if (!online()) say(T("waitNet")); kick(); }]]);
}

// ------------------------------------------------------------------ manual entry when AI is unavailable
async function manualEntry(rec, askType = false) {
  let pt = askType ? null : rec.pageType;
  if (!pt) {
    const names = Object.entries(SCHEMA).map(([k, v]) => `${k}. ${LANG === "fr" ? v.name_fr : v.name_en}`);
    const a = await ask(T("whichPage"), names, { text: false });
    pt = parseInt(a, 10);
  }
  say(T("manualStart", { page: LANG === "fr" ? SCHEMA[pt].name_fr : SCHEMA[pt].name_en }));
  const fields = [];
  for (const f of SCHEMA[pt].fields.filter(f => f.manual && f.type === "text")) {
    const a = await ask(T("typeValue", { label: f.label }), [T("empty")]);
    const g = { key: f.key, type: "text" }; setValue(g, a); fields.push(g);
  }
  rec.pageType = pt; rec.pageName = SCHEMA[pt].name_fr;
  rec.result = await encJSON({ page_type: pt, fields, manual: true }, rec.id + ":res");
  await setState(rec, "VALIDÉ", "manual entry");
  return afterPage(rec);
}
app.manualEntry = async () => {
  if (!session) session = newSession();
  const rec = { id: crypto.randomUUID(), sid: session.id, state: "EN_ATTENTE_IA", version: 0, midwife: "sf-01", capturedAt: Date.now(), attempts: 0 };
  await putRec(rec); await setState(rec, "RÉVISION_MANUELLE_REQUISE", "AI unavailable");
  return manualEntry(rec);
};

// ------------------------------------------------------------------ end of booklet: checks, matching, registration
async function finishSession() {
  const valid = (await allRecs()).filter(r => r.state === "VALIDÉ").sort((a, b) => b.capturedAt - a.capturedAt);
  if (!valid.length) return;
  const recs = valid.filter(r => r.sid === valid[0].sid);
  const pages = {};
  for (const r of recs) pages[r.id + ":" + r.version] = await decJSON(r.result, r.id + ":res");
  // 1. booklet-level consistency (strategy 7/13), on the reviewed values
  say(T("checks"));
  const fin = await api(`/session/${recs[0].sid}/finalize`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ pages }) });
  const auto = fin.issues.filter(i => i.repaired);
  if (auto.length) say(T("repaired", { n: auto.length, key: auto[0].key, old: auto[0].old, new: auto[0].new }));
  for (const iss of fin.issues.filter(i => !i.repaired && i.suggestion)) {
    const a = await ask(T("rule", { msg: I18N[LANG].rules[iss.rule] || iss.rule, old: iss.old, new: iss.suggestion }),
      [T("takeNew", { new: iss.suggestion }), T("keepOld", { old: iss.old })], { text: false });
    if (a === T("takeNew", { new: iss.suggestion })) for (const p of Object.values(fin.pages)) for (const f of p.fields) if (f.key === iss.key && f.value === iss.old) { f.value = iss.suggestion; f.status = "CONNU"; }
  }
  for (const r of recs) { const p = fin.pages[r.id + ":" + r.version]; if (p) { r.result = await encJSON(p, r.id + ":res"); await putRec(r); } }
  // 2. patient matching by the registry code (strategy 10): the midwife decides
  const all = Object.values(fin.pages);
  const get = (t, k) => (all.find(p => p.page_type === t)?.fields.find(f => f.key === k) || {}).value;
  let code = get(1, "inline.n_de_la_fiche");
  if (code) say(T("codeRead", { code })); else code = await ask(T("codeAsk"), []);
  const facts = { ddr: get(3, "inline.ddr"), date_prevue: get(3, "inline.date_prevue_d_accouchement") };
  const prop = await api("/match/propose", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ code, facts }) });
  if (prop.candidates.length) {
    say(T("matchAsk") + "\n" + prop.candidates.map(c => T("cand", { i: c.rank, code: c.code,
      facts: c.facts.ddr ? ` · DDR ${c.facts.ddr}` + (c.clash ? " ⚠️" : c.agree ? " ✓" : "") : "" })).join("\n"));
  } else say(T("noMatch"));
  const choice = await ask("👇", prop.buttons, { text: false });
  const dcs = await api("/match/decide", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ proposal_id: prop.proposal_id, choice }) });
  if (!dcs.patient_id) {
    say(T("unsure"));
    for (const r of recs) await setState(r, "RÉVISION_MANUELLE_REQUISE", "match undecided");
    session = null; return;
  }
  say(choice.startsWith("Patiente") || choice.startsWith("Patient") ? T("linked", { pid: dcs.patient_id.slice(0, 8) }) : T("created", { pid: dcs.patient_id.slice(0, 8) }));
  for (const r of recs) {
    r.patientId = dcs.patient_id; await setState(r, "PATIENTE_LIÉE", "midwife: " + choice);
    // strategy 13 / brief task 7: this page was digitised before for this patient -> show the diff, she decides
    const page = await decJSON(r.result, r.id + ":res");
    const prev = await api(`/records/previous?patient_id=${dcs.patient_id}&page_type=${page.page_type}&exclude=${r.id}`);
    if (prev.found) {
      const old = Object.fromEntries(prev.page.fields.map(f => [f.key, f.value]));
      const fresh = page.fields.filter(f => f.type === "text" && f.value != null && old[f.key] == null);
      const changed = page.fields.filter(f => f.value != null && old[f.key] != null && String(old[f.key]) !== String(f.value));
      if (fresh.length || changed.length) {
        const ex = changed[0] ? `
${label(String(page.page_type), changed[0].key)} : ${old[changed[0].key]} → ${changed[0].value}` : "";
        const a = await ask(T("rescan", { page: SCHEMA[page.page_type][LANG === "fr" ? "name_fr" : "name_en"], n: fresh.length, m: changed.length }) + ex,
          [T("update"), T("keepPrev")], { text: false });
        if (ACTIONS[a] === "keepPrev") for (const f of changed) { f.value = old[f.key]; f.status = "CONNU"; f.provenance = "previous record"; }
        r.result = await encJSON(page, r.id + ":res"); await putRec(r);
      } else say(T("rescanSame"));
    }
    await setState(r, "ENREGISTRÉ", "session closed");
  }
  say(online() ? T("saved") : T("syncWait"));
  session = null;
}

async function syncRecords(recs) {
  let n = 0;
  for (const r of recs) {
    try {
      if (r.state === "ÉCHEC_SYNCHRO") await setState(r, "ENREGISTRÉ", "retry");
      const p = await decJSON(r.result, r.id + ":res");
      const pages = [{ page_type: p.page_type, fields: p.fields.map(({ key, type, value, status, confidence }) => ({ key, type, value, status, confidence })) }];
      await api("/records", { method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ record_id: r.id, version: r.version, patient_id: r.patientId, pages }) });
      await setState(r, "SYNCHRONISÉ", "central ack"); n++;
    } catch (e) {
      if (e.message !== "offline") { r.nextTry = Date.now() + 5000; await setState(r, "ÉCHEC_SYNCHRO", e.message || "network"); }
      break;
    }
  }
  if (n) say(T("synced", { n }));
}

// ------------------------------------------------------------------ misc UI
async function renderQueue() {
  const n = document.getElementById("net");
  if (!db) return;
  const recs = await allRecs();
  const waiting = recs.filter(r => ["EN_ATTENTE_IA", "ENREGISTRÉ", "ÉCHEC_SYNCHRO", "ÉCHEC_TRAITEMENT"].includes(r.state)).length;
  n.textContent = (online() ? T("online") : T("offline")) + (waiting ? ` · ${waiting} ${T("pending")}` : "");
  document.getElementById("offline").textContent = online() ? "📶" : "📴";
  const ul = document.getElementById("queue"); ul.innerHTML = "";
  for (const r of recs.sort((a, b) => b.capturedAt - a.capturedAt)) {
    const li = document.createElement("li");
    li.innerHTML = `<span>${r.id.slice(0, 6)} · ${r.pageName || "page"} v${r.version}</span><span class="pill ${r.state}">${r.state}</span>`;
    ul.appendChild(li);
  }
  document.getElementById("qTitle").textContent = T("queue");
}
app.records = async () => (await allRecs()).map(r => ({ id: r.id, state: r.state, pageType: r.pageType, version: r.version, patientId: r.patientId }));
app.decryptResult = async id => decJSON((await getRec(id)).result, id + ":res");
app.setOffline = v => { const was = online(); app.forceOffline = v; renderQueue(); if (!was && online()) { say(T("back")); kick(); } else if (was && !online()) sys(T("lost")); };
app.finish = () => { finishRequested = true; kick(); };

app.unlock = async function (pin) {
  const prev = key;
  key = await deriveKey(pin);
  const check = await tx("meta", "readonly", s => s.get("check"));
  if (check) {
    try { await dec(check, "check"); }                     // throws on a wrong PIN
    catch (e) { key = prev; throw e; }                     // a wrong PIN must never replace the working key
  }
  if (!check) { const c = await enc(new Uint8Array([1]), "check"); await tx("meta", "readwrite", s => s.put(c, "check")); }
  document.getElementById("lock").hidden = true;
  say(T("hello"));
  const recs = await allRecs();
  const open = recs.filter(r => r.state !== "SYNCHRONISÉ" && r.state !== "DOUBLON_SUSPECTÉ");
  if (open.length) { session = { id: open[0].sid }; sys(`${open.length} dossier(s) en cours repris`); }
  renderQueue(); kick();
  return true;
};

(async () => {
  db = await idb();
  SCHEMA = await (await fetch("schema.json")).json();
  if ("serviceWorker" in navigator) navigator.serviceWorker.register("sw.js").catch(() => {});
  const $ = id => document.getElementById(id);
  $("unlock").onclick = () => app.unlock($("pin").value).catch(() => { $("lockMsg").textContent = T("pinBad"); });
  $("pin").onkeydown = e => { if (e.key === "Enter") $("unlock").click(); };
  $("cam").onclick = () => $("file").click();
  $("file").onchange = e => { const f = e.target.files[0]; e.target.value = ""; if (f) app.captureBlob(f); };
  const send = () => { const v = $("text").value.trim(); if (!v) return; $("text").value = "";
    if (!answer(v, false)) { if (/^(manuel|manual)/i.test(v)) app.manualEntry(); else if (/^(fin|terminer|finish|end)/i.test(v)) app.finish(); else bubble("me", v); } };
  $("send").onclick = send; $("text").onkeydown = e => { if (e.key === "Enter") send(); };
  $("queueBtn").onclick = () => { $("drawer").hidden = !$("drawer").hidden; renderQueue(); };
  $("offline").onclick = () => app.setOffline(online());
  $("lang").onclick = () => { LANG = LANG === "fr" ? "en" : "fr"; localStorage.setItem("lang", LANG); $("lang").textContent = LANG === "fr" ? "EN" : "FR"; document.documentElement.lang = LANG; renderQueue(); };
  $("lang").textContent = LANG === "fr" ? "EN" : "FR";
  window.addEventListener("online", () => { say(T("back")); kick(); renderQueue(); });
  window.addEventListener("offline", () => { sys(T("lost")); renderQueue(); });
  setInterval(() => { if (key && online()) kick(); }, 5000);            // retries with back-off
  if (PARAMS.get("e2e")) { const sc = document.createElement("script"); sc.src = "testdata/e2e.js"; document.body.appendChild(sc); }
})();
