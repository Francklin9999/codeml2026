(function () {
  "use strict";

  var data = window.NOVA_DATA || {};
  var routes = ["brief", "questions", "timeline", "decisions", "contradictions", "actions", "risks", "sources", "limits", "versions"];
  var view = document.getElementById("view");
  var status = document.getElementById("app-status");
  var searchForm = document.getElementById("search-form");
  var searchInput = document.getElementById("search-input");

  function arr(value) {
    if (Array.isArray(value)) return value;
    if (value && typeof value === "object") return Object.keys(value).sort().map(function (key) {
      var item = value[key];
      return item && typeof item === "object" ? Object.assign({ id: key }, item) : { id: key, text: item };
    });
    return [];
  }

  function esc(value) {
    return String(value == null ? "" : value)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;").replace(/'/g, "&#39;");
  }

  function text(item, keys, fallback) {
    for (var i = 0; i < keys.length; i += 1) {
      if (item && item[keys[i]] != null && item[keys[i]] !== "") return String(item[keys[i]]);
    }
    return fallback || "";
  }

  function normalize(value) {
    return String(value || "").toLocaleLowerCase("fr-CA").normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "").replace(/[^a-z0-9]+/g, " ").trim();
  }

  function safeHref(value) {
    var href = String(value || "").trim();
    if (!href || /^\s*(?:[a-z][a-z0-9+.-]*:|\/\/)/i.test(href) || href.indexOf("\\") >= 0) return "";
    return href;
  }

  function badge(value) {
    if (!value) return "";
    var clean = normalize(value).replace(/\s+/g, "-");
    return '<span class="badge badge-' + esc(clean) + '">' + esc(value) + "</span>";
  }

  function evidence(items) {
    var entries = Array.isArray(items) ? items : (items == null || items === "" ? [] : [items]);
    var links = entries.map(function (entry) {
      if (typeof entry === "string") return { label: entry, evidenceHref: "" };
      return entry || {};
    }).map(function (entry) {
      var href = safeHref(entry.evidenceHref || entry.href || entry.url);
      var label = text(entry, ["label", "locator", "file", "id"], "Preuve");
      if (!href) return '<li><span class="meta">' + esc(label) + " (lien indisponible)</span></li>";
      return '<li><a href="' + esc(href) + '">' + esc(label) + "</a></li>";
    }).join("");
    return links ? '<ul class="evidence-list" aria-label="Preuves">' + links + "</ul>" : "";
  }

  function empty(title, detail) {
    return '<div class="empty"><strong>' + esc(title) + "</strong>" + esc(detail) + "</div>";
  }

  function page(title, lede, content, extra) {
    return '<div class="view-root"><header class="page-head"><div><h1 tabindex="-1">' + esc(title) +
      '</h1><p class="lede">' + esc(lede) + "</p></div>" + (extra || "") + "</header>" + content + "</div>";
  }

  function recordEvidence(item) {
    var linked = item.evidence || item.sources || item.proofs;
    if (linked) return linked;
    if (item.evidenceHref) return [{ label: text(item, ["locator", "source_file", "id"], "Preuve"), evidenceHref: item.evidenceHref }];
    return [];
  }

  function briefSection(title, value) {
    if (value == null || value === "") return "";
    var item = typeof value === "object" && !Array.isArray(value) ? value : { text: value };
    var body = Array.isArray(value) ? "<ul>" + value.map(function (x) { return "<li>" + esc(typeof x === "object" ? text(x, ["text", "label", "title"]) : x) + "</li>"; }).join("") + "</ul>" : '<p class="body-text">' + esc(text(item, ["text", "value", "summary", "answer"])) + "</p>";
    return '<article class="card"><h2>' + esc(title) + "</h2>" + body + evidence(recordEvidence(item)) + "</article>";
  }

  function renderBrief() {
    var brief = data.brief || {};
    var briefStatus = brief.status ? '<div class="brief-status" role="note"><strong>État de reprise</strong><span>' + esc(brief.status) + "</span></div>" : "";
    var conditionRows = arr(brief.go_live_conditions || brief.goLiveConditions).map(function (condition) {
      var actions = arr(condition.action_ids || condition.actionIds).map(function (item) {
        return typeof item === "object" ? text(item, ["id", "label", "text"]) : String(item);
      }).filter(Boolean).join(", ");
      return "<tr><td><strong>" + esc(text(condition, ["number", "id"], "—")) + "</strong></td><td>" + esc(text(condition, ["condition", "title"], "Condition")) + '<br><span class="meta">' + esc(text(condition, ["current_state", "currentState", "status"], "État non documenté")) + "</span></td><td>" + esc(text(condition, ["owner", "responsible"], "À confirmer")) + "</td><td>" + esc(actions || "À confirmer") + "</td></tr>";
    }).join("");
    var conditions = conditionRows ? '<section class="brief-conditions" aria-labelledby="brief-conditions-title"><h2 id="brief-conditions-title">Conditions de mise en production</h2><div class="table-wrap"><table><thead><tr><th>No</th><th>Condition et état</th><th>Responsable</th><th>Actions</th></tr></thead><tbody>' + conditionRows + "</tbody></table></div></section>" : "";
    var sections = [
      ["Responsable", brief.owner || brief.responsable],
      ["Date approuvée et conditions", brief.dateConditions || brief.date_and_conditions || brief.conditions],
      ["Portée", brief.scope || brief.portee],
      ["Budget et factures", brief.budget || brief.invoices],
      ["Priorités", brief.priorities || brief.priorites],
      ["Incertitudes", brief.uncertainties || brief.incertitudes]
    ].map(function (entry) { return briefSection(entry[0], entry[1]); }).filter(Boolean).join("");
    var content = sections ? briefStatus + conditions + '<div class="grid grid-2 brief-grid">' + sections + "</div>" : empty("Brief non généré", "Les données vérifiées seront affichées ici après la construction de la livraison.");
    return page("Brief de reprise", "L’essentiel pour reprendre NOVA, à la date de référence indiquée.", content, '<button class="print-button" type="button" data-print>Imprimer le brief</button>');
  }

  function renderEventUpdates(updates) {
    var items = arr(updates);
    if (!items.length) return "";
    var cards = items.map(function (item) {
      var context = [text(item, ["actor"]), text(item, ["source"])].filter(Boolean).join(" · ");
      return '<article class="event-update"><div class="badge-row">' + badge(text(item, ["kind", "type"], "mise à jour")) + '<span class="meta">' + esc(text(item, ["event_id", "id"])) + '</span></div><p class="body-text">' + esc(text(item, ["statement", "description"], "Mise à jour sans description")) + "</p>" + (context ? '<p class="meta">' + esc(context) + "</p>" : "") + evidence(recordEvidence(item)) + "</article>";
    }).join("");
    return '<section class="event-updates" aria-label="Mises à jour live"><h3>Mise à jour live</h3><p class="meta"><strong>La réponse de baseline ci-dessus est conservée.</strong> Les éléments ci-dessous ont été appris après la date de référence.</p>' + cards + "</section>";
  }

  function renderQuestions() {
    var answers = arr(data.answers).sort(function (a, b) { return text(a, ["id"]).localeCompare(text(b, ["id"]), "fr", { numeric: true }); });
    var byId = {};
    answers.forEach(function (a) { byId[String(a.id || a.question_id || "").toUpperCase()] = a; });
    var cards = [];
    for (var i = 1; i <= 10; i += 1) {
      var id = "Q" + String(i).padStart(2, "0");
      var item = byId[id];
      if (!item) {
        cards.push('<article class="card"><span class="question-id">' + id + '</span><h2>Question non chargée</h2><p class="meta">Aucune réponse vérifiée n’a été injectée.</p></article>');
        continue;
      }
      var nuances = arr(item.nuance || item.nuances).map(function (n) { return "<li>" + esc(typeof n === "object" ? text(n, ["text", "statement"]) : n) + "</li>"; }).join("");
      cards.push('<article class="card"><span class="question-id">' + esc(id) + '</span><h2>' + esc(text(item, ["question", "title"], "Question")) + '</h2><p class="answer"><span class="label">Réponse de baseline</span><br>' + esc(text(item, ["answer", "response"], "Non documenté dans le corpus.")) + "</p>" + (nuances ? '<ul class="nuances">' + nuances + "</ul>" : "") + evidence(recordEvidence(item)) + renderEventUpdates(item.eventUpdates || item.event_updates) + "</article>");
    }
    return page("Questions Q01–Q10", "Réponses nuancées avec accès direct aux preuves locales.", '<div class="stack">' + cards.join("") + "</div>");
  }

  function renderTimeline() {
    var items = arr(data.timeline || data.events || data.facts).slice().sort(function (a, b) {
      return text(a, ["date", "date_effective", "timestamp"]).localeCompare(text(b, ["date", "date_effective", "timestamp"])) || text(a, ["id"]).localeCompare(text(b, ["id"]));
    });
    if (!items.length) return page("Chronologie", "Événements classés par date d’effet.", empty("Chronologie vide", "Aucun événement vérifié n’est disponible."));
    var rows = items.map(function (item) {
      return '<li><article class="card"><div class="meta">' + esc(text(item, ["date", "date_effective", "timestamp"], "Date non documentée")) + " · " + badge(text(item, ["type", "status"])) + '</div><h2>' + esc(text(item, ["title", "statement", "label"], "Événement")) + '</h2><p class="body-text">' + esc(text(item, ["description", "notes", "detail"])) + "</p>" + evidence(recordEvidence(item)) + "</article></li>";
    }).join("");
    return page("Chronologie", "Événements classés par date d’effet.", '<ol class="timeline">' + rows + "</ol>");
  }

  function renderCards(route, title, lede, primaryKeys) {
    var items = arr(data[route]);
    if (!items.length && route === "decisions") {
      items = arr(data.facts).filter(function (item) { return ["proposal", "decision", "delivery", "validation"].indexOf(normalize(item.type)) >= 0; });
    }
    if (!items.length && route === "contradictions") {
      items = arr(data.facts).filter(function (item) { return normalize(item.type) === "contradiction"; });
    }
    if (!items.length && route === "risks") {
      items = arr(data.facts).filter(function (item) { return normalize(item.type) === "risk"; });
    }
    if (!items.length) return page(title, lede, empty("Aucun élément", "Le registre vérifié ne contient actuellement aucun élément à afficher."));
    var html = items.map(function (item) {
      var heading = text(item, primaryKeys.concat(["title", "statement", "action", "id"]), "Élément");
      var detail = text(item, ["resolution", "description", "notes", "detail", "mitigation", "answer"]);
      var state = text(item, ["status", "origin", "severity", "authority"]);
      var metadata = [text(item, ["date", "due", "deadline"]), text(item, ["owner", "actor", "responsible"])].filter(Boolean).join(" · ");
      return '<article class="card"><div>' + badge(state) + '</div><h2>' + esc(heading) + '</h2>' + (detail ? '<p class="body-text">' + esc(detail) + "</p>" : "") + (metadata ? '<p class="meta">' + esc(metadata) + "</p>" : "") + evidence(recordEvidence(item)) + "</article>";
    }).join("");
    return page(title, lede, '<div class="stack">' + html + "</div>");
  }

  function renderDecisions() {
    var items = arr(data.decisions);
    if (!items.length) items = arr(data.facts).filter(function (item) { return ["proposal", "decision", "delivery", "validation"].indexOf(normalize(item.type)) >= 0; });
    if (!items.length) return page("Décisions", "Cycle proposition, décision, livraison et validation.", empty("Aucune décision", "Aucun élément de gouvernance vérifié n’est disponible."));
    var cards = items.slice().sort(function (a, b) {
      return text(a, ["date", "date_effective"]).localeCompare(text(b, ["date", "date_effective"])) || text(a, ["id"]).localeCompare(text(b, ["id"]));
    }).map(function (item) {
      var metadata = [text(item, ["date", "date_effective"]), text(item, ["actor", "owner"]), text(item, ["authority"])].filter(Boolean).join(" · ");
      return '<article class="card"><div class="badge-row">' + badge(text(item, ["type"], "étape")) + badge(text(item, ["status"], "statut non précisé")) + '</div><h2>' + esc(text(item, ["statement", "decision", "title", "id"], "Décision")) + "</h2>" + (metadata ? '<p class="meta">' + esc(metadata) + "</p>" : "") + evidence(recordEvidence(item)) + "</article>";
    }).join("");
    return page("Décisions", "Cycle proposition, décision, livraison et validation.", '<div class="stack">' + cards + "</div>");
  }

  function renderActions() {
    var items = arr(data.actions);
    if (!items.length) return page("Actions", "Engagements documentés et recommandations de l’équipe sont distingués.", empty("Registre d’actions vide", "Aucune action vérifiée n’est disponible."));
    var rows = items.map(function (item) {
      var ownerStatus = text(item, ["owner_status", "ownerStatus"]);
      var dueStatus = text(item, ["due_status", "dueStatus"]);
      return "<tr><td><strong>" + esc(text(item, ["id"])) + "</strong><br>" + esc(text(item, ["action", "title", "statement"])) + "</td><td>" + esc(text(item, ["linked_condition", "condition"], "—")) + "</td><td>" + esc(text(item, ["owner", "responsible"], "À confirmer")) + " " + badge(ownerStatus) + "</td><td>" + esc(text(item, ["due", "deadline"], "À confirmer")) + " " + badge(dueStatus) + "</td><td>" + badge(text(item, ["origin"], "non précisée")) + evidence(recordEvidence(item)) + "</td></tr>";
    }).join("");
    return page("Actions", "Chaque action indique son responsable, son échéance, son origine et sa preuve.", '<div class="table-wrap"><table><thead><tr><th>Action</th><th>Condition</th><th>Responsable</th><th>Échéance</th><th>Origine et preuve</th></tr></thead><tbody>' + rows + "</tbody></table></div>");
  }

  function renderRisks() {
    var items = arr(data.risks);
    if (!items.length) items = arr(data.facts).filter(function (item) { return normalize(item.type) === "risk"; });
    if (!items.length) return page("Risques", "Probabilité, impact, responsable, mitigation et provenance.", empty("Aucun risque", "Le registre vérifié ne contient actuellement aucun risque."));
    var cards = items.map(function (item) {
      var owner = text(item, ["owner", "responsible"], "À confirmer");
      var ownerState = text(item, ["owner_status", "ownerStatus"]);
      return '<article class="card risk-card"><div class="badge-row">' + badge(text(item, ["status"], "statut non précisé")) + badge(text(item, ["probability"], "probabilité non précisée")) + badge(text(item, ["impact"], "impact non précisé")) + '</div><h2>' + esc(text(item, ["title", "risk", "statement", "id"], "Risque")) + '</h2><p class="body-text">' + esc(text(item, ["description", "notes"])) + '</p><dl class="definition-list compact-definitions"><dt>Responsable</dt><dd>' + esc(owner) + " " + badge(ownerState) + '</dd><dt>Mitigation</dt><dd>' + esc(text(item, ["mitigation"], "À définir")) + '</dd><dt>Provenance</dt><dd>' + esc(text(item, ["origin", "provenance"], "Non précisée")) + "</dd></dl>" + evidence(recordEvidence(item)) + "</article>";
    }).join("");
    return page("Risques", "Probabilité, impact, responsable, mitigation et provenance.", '<div class="stack">' + cards + "</div>");
  }

  function claimText(value) {
    if (value && typeof value === "object") return text(value, ["statement", "text", "claim", "label"]);
    return String(value || "Non documentée");
  }

  function renderContradictions() {
    var items = arr(data.contradictions);
    if (!items.length) items = arr(data.facts).filter(function (item) { return normalize(item.type) === "contradiction"; });
    if (!items.length) return page("Contradictions", "Écarts résolus selon l’autorité, la date et la nature de chaque source.", empty("Aucune contradiction", "Le registre vérifié ne contient actuellement aucune contradiction."));
    var cards = items.map(function (item) {
      var left = item.claim_a || item.claimA || item.left;
      var right = item.claim_b || item.claimB || item.right;
      var resolution = item.resolution;
      var resolutionText = resolution && typeof resolution === "object" ? text(resolution, ["text", "statement", "reason"]) : String(resolution || text(item, ["description", "notes"]));
      return '<article class="card"><div>' + badge(text(item, ["status"], "résolue")) + '</div><h2>' + esc(text(item, ["subject", "title", "id"], "Contradiction")) + '</h2><div class="grid grid-2"><div><h3>Affirmation A</h3><p>' + esc(claimText(left)) + '</p></div><div><h3>Affirmation B</h3><p>' + esc(claimText(right)) + '</p></div></div><h3>Résolution</h3><p class="body-text">' + esc(resolutionText || "À documenter") + "</p>" + evidence(recordEvidence(item)) + "</article>";
    }).join("");
    return page("Contradictions", "Écarts résolus selon l’autorité, la date et la nature de chaque source.", '<div class="stack">' + cards + "</div>");
  }

  function renderSources() {
    var items = arr(data.sources);
    if (!items.length) return page("Sources", "Inventaire du corpus et accès aux rendus de preuve.", empty("Inventaire non chargé", "Aucune source n’est disponible dans cette copie."));
    var rows = items.map(function (item) {
      var href = safeHref(item.evidenceHref || item.href || item.evidence_path);
      var name = text(item, ["label", "file", "path", "id"], "Source");
      var link = href ? '<a href="' + esc(href) + '">' + esc(name) + "</a>" : esc(name);
      return "<tr><td class=" + '"source-path"' + ">" + link + "</td><td>" + esc(text(item, ["type", "class", "category", "classification"], "—")) + "</td><td>" + esc(text(item, ["info_as_of", "information_date", "date", "updated"], "—")) + "</td><td>" + esc(text(item, ["notes", "status", "classification_reason"], "")) + "</td></tr>";
    }).join("");
    return page("Sources", "Inventaire du corpus et accès aux rendus de preuve.", '<div class="table-wrap"><table><thead><tr><th>Fichier</th><th>Classe</th><th>Date d’information</th><th>Note</th></tr></thead><tbody>' + rows + "</tbody></table></div>");
  }

  function renderLimits() {
    var limits = arr(data.limits || data.unknowns);
    var declared = data.meta || {};
    var intro = '<article class="card"><h2>Mode d’emploi</h2><ol><li>Ouvrir <strong>index.html</strong> dans un navigateur récent.</li><li>Utiliser la navigation ou la recherche locale.</li><li>Suivre un lien de preuve pour vérifier un passage précis.</li></ol><p class="meta">Aucun serveur, compte ou accès réseau n’est requis.</p></article>';
    var manualSteps = arr(declared.manualSteps || declared.manual_steps).map(function (step) { return "<li>" + esc(typeof step === "object" ? text(step, ["text", "label"]) : step) + "</li>"; }).join("");
    var disclosure = '<article class="card"><h2>Traçabilité</h2><dl class="definition-list"><dt>Date de référence</dt><dd>' + esc(text(declared, ["asOf", "as_of", "info_as_of"], "Non fournie")) + '</dd><dt>Version</dt><dd>' + esc(text(declared, ["version", "baselineSha256"], "Non fournie")) + '</dd><dt>Outils et IA</dt><dd>' + esc(text(declared, ["toolDisclosure", "tools", "aiDisclosure"], "À documenter dans les données de livraison")) + "</dd></dl>" + (manualSteps ? '<h3>Étapes manuelles</h3><ul>' + manualSteps + "</ul>" : "") + "</article>";
    var limitCards = limits.length ? limits.map(function (item) {
      var expected = item.expected_location || item.expectedLocation;
      var expectedText = expected && typeof expected === "object" ? [text(expected, ["file", "path"]), text(expected, ["locator", "location"])].filter(Boolean).join(" · ") : String(expected || "Non précisé");
      return '<article class="card limit-card"><div class="badge-row">' + badge(text(item, ["severity"], "sévérité non précisée")) + '</div><h2>' + esc(text(item, ["title", "unknown", "gap", "question"], "Limite")) + '</h2><dl class="definition-list compact-definitions"><dt>Impact</dt><dd>' + esc(text(item, ["impact", "description", "notes"], "Non précisé")) + '</dd><dt>À demander à</dt><dd>' + esc(text(item, ["ask", "owner", "responsible"], "À confirmer")) + '</dd><dt>Question proposée</dt><dd>' + esc(text(item, ["proposed_question", "proposedQuestion"], "À formuler")) + '</dd><dt>Emplacement attendu</dt><dd class="source-path">' + esc(expectedText) + "</dd></dl>" + evidence(recordEvidence(item)) + "</article>";
    }).join("") : empty("Aucune limite injectée", "Cette absence ne signifie pas que le corpus est complet; le registre des inconnues n’a pas été chargé.");
    return page("Limites et utilisation", "Ce que la mémoire sait, ce qu’elle ne sait pas et comment la vérifier.", '<div class="grid grid-2">' + intro + disclosure + '</div><h2 style="margin-top:1.2rem">Inconnues déclarées</h2><div class="stack">' + limitCards + "</div>");
  }

  function renderVersions() {
    var versions = data.versions || {};
    var changes = arr(versions.changes || data.diff);
    var top = '<div class="grid grid-2"><article class="card"><span class="label">Référence</span><p class="metric">' + esc(text(versions.baseline || {}, ["label", "version", "id"], "Non fournie")) + '</p><p class="meta">' + esc(text(versions.baseline || {}, ["hash", "date", "asOf"], "")) + '</p></article><article class="card"><span class="label">État courant</span><p class="metric">' + esc(text(versions.current || {}, ["label", "version", "id"], "Non fourni")) + '</p><p class="meta">' + esc(text(versions.current || {}, ["hash", "date", "asOf"], "")) + "</p></article></div>";
    var diff = changes.length ? changes.map(function (item) {
      var kind = normalize(text(item, ["kind", "type", "status"], "changed"));
      var provenance = item.source && typeof item.source === "object" ? text(item.source, ["label", "file", "text", "id"]) : String(item.source || "");
      var affectedAnswers = arr(item.affected_answers || item.affectedAnswers).map(function (x) { return typeof x === "object" ? text(x, ["id", "label"]) : String(x); }).filter(Boolean).join(", ");
      var affectedActions = arr(item.affected_actions || item.affectedActions).map(function (x) { return typeof x === "object" ? text(x, ["id", "label"]) : String(x); }).filter(Boolean).join(", ");
      var details = [
        ["Acteur", text(item, ["actor"])], ["Autorité", text(item, ["authority"])],
        ["Source", provenance], ["Appris le", text(item, ["record_time", "recordTime"])],
        ["Valide depuis", text(item, ["valid_time", "validTime"])],
        ["Réponses touchées", affectedAnswers], ["Actions touchées", affectedActions]
      ].filter(function (entry) { return entry[1]; }).map(function (entry) { return "<dt>" + esc(entry[0]) + "</dt><dd>" + esc(entry[1]) + "</dd>"; }).join("");
      return '<article class="card diff-' + esc(kind) + '"><div>' + badge(kind) + '</div><h2>' + esc(text(item, ["title", "field", "id"], "Changement")) + '</h2><p class="body-text">' + esc(text(item, ["description", "statement"], "Changement sans description")) + "</p>" + (details ? '<dl class="definition-list compact-definitions diff-details">' + details + "</dl>" : "") + evidence(recordEvidence(item)) + "</article>";
    }).join("") : empty("Aucun diff disponible", "Aucune comparaison de versions n’a été injectée.");
    var unchanged = arr(versions.unchanged).map(function (x) { return "<li>" + esc(typeof x === "object" ? text(x, ["label", "text", "statement"]) : x) + "</li>"; }).join("");
    return page("Versions et diff", "Les changements sont séparés de ce qui demeure inchangé; la référence est conservée.", top + '<h2 style="margin-top:1.2rem">Changements</h2><div class="stack">' + diff + "</div>" + (unchanged ? '<article class="card" style="margin-top:1rem"><h2>Inchangé</h2><ul>' + unchanged + "</ul></article>" : ""));
  }

  function briefSearchItems() {
    var brief = data.brief || {};
    var definitions = [
      ["brief-owner", "Brief — Responsable", brief.owner || brief.responsable],
      ["brief-date", "Brief — Date et conditions", brief.dateConditions || brief.date_and_conditions || brief.conditions],
      ["brief-scope", "Brief — Portée", brief.scope || brief.portee],
      ["brief-budget", "Brief — Budget et factures", brief.budget || brief.invoices],
      ["brief-priorities", "Brief — Priorités", brief.priorities || brief.priorites],
      ["brief-uncertainties", "Brief — Incertitudes", brief.uncertainties || brief.incertitudes]
    ];
    var items = definitions.filter(function (entry) { return entry[2] != null; }).map(function (entry) {
      var value = entry[2];
      var body = Array.isArray(value) ? value.map(function (x) { return typeof x === "object" ? text(x, ["text", "summary", "label"]) : String(x); }).join(" ") : text(value && typeof value === "object" ? value : { text: value }, ["text", "summary", "value"]);
      return { id: entry[0], title: entry[1], description: body, evidence: value && typeof value === "object" && !Array.isArray(value) ? recordEvidence(value) : [] };
    });
    arr(brief.go_live_conditions || brief.goLiveConditions).forEach(function (condition, index) {
      items.push({ id: "brief-condition-" + text(condition, ["number", "id"], index), title: "Brief — " + text(condition, ["condition", "title"], "Condition"), description: [text(condition, ["current_state", "currentState"]), text(condition, ["owner"])].filter(Boolean).join(" ") });
    });
    return items;
  }

  function flattenForSearch() {
    var groups = [
      ["Fait", data.facts], ["Réponse", data.answers], ["Contradiction", data.contradictions],
      ["Action", data.actions], ["Risque", data.risks], ["Inconnue", data.unknowns || data.limits],
      ["Source", data.sources], ["Brief", briefSearchItems()], ["Chronologie", data.timeline || data.events],
      ["Décision", data.decisions]
    ];
    var result = [];
    var seen = new Set();
    groups.forEach(function (group) {
      arr(group[1]).forEach(function (item, index) {
        var title = text(item, ["question", "title", "action", "statement", "label", "file", "id"], group[0]);
        var body = ["answer", "description", "resolution", "notes", "quote", "mitigation", "detail", "unknown", "impact", "ask", "proposed_question", "current_state"].map(function (key) {
          return item[key] != null && typeof item[key] !== "object" ? String(item[key]) : "";
        }).filter(Boolean).join(" ");
        var keywords = arr(item.tags || item.keywords).join(" ");
        var id = text(item, ["id"], group[0] + "-" + index);
        var dedupeKey = item.id != null ? "id:" + String(item.id) : "content:" + normalize(title + " " + body);
        if (seen.has(dedupeKey)) return;
        seen.add(dedupeKey);
        result.push({ type: group[0], id: id, title: title, body: body, evidence: recordEvidence(item), haystack: normalize(title + " " + body + " " + keywords + " " + JSON.stringify(recordEvidence(item))) });
      });
    });
    return result;
  }

  var synonymGroups = [
    ["go live", "mise en production", "lancement", "deploiement"],
    ["facture", "facturation", "invoice", "paiement"],
    ["securite", "sec"], ["accessibilite", "acc"], ["responsable", "proprietaire", "owner"],
    ["echeance", "date", "deadline"], ["budget", "cout", "montant"]
  ];

  function queryTerms(query) {
    var clean = normalize(query);
    var stop = ["a", "au", "aux", "de", "des", "du", "en", "et", "est", "la", "le", "les", "ou", "pour", "que", "qui", "un", "une"];
    var base = clean.split(/\s+/).filter(function (term) { return term.length >= 2 && stop.indexOf(term) < 0; });
    var expanded = base.slice();
    synonymGroups.forEach(function (group) {
      var normalizedGroup = group.map(normalize);
      if (normalizedGroup.some(function (phrase) { return clean.indexOf(phrase) >= 0; })) {
        normalizedGroup.forEach(function (phrase) { expanded = expanded.concat(phrase.split(" ")); });
      }
    });
    return Array.from(new Set(expanded));
  }

  function search(query) {
    var clean = normalize(query);
    var terms = queryTerms(query);
    if (!clean || !terms.length) return [];
    return flattenForSearch().map(function (item) {
      var matched = 0;
      terms.forEach(function (term) { if (item.haystack.indexOf(term) >= 0) matched += 1; });
      var score = matched * 10 + (item.haystack.indexOf(clean) >= 0 ? 25 : 0) + (normalize(item.title).indexOf(clean) >= 0 ? 20 : 0);
      return Object.assign({}, item, { score: score, coverage: matched / terms.length });
    }).filter(function (item) { return item.score >= 10 && item.coverage >= Math.min(1, 1 / terms.length); })
      .sort(function (a, b) { return b.score - a.score || a.type.localeCompare(b.type, "fr") || a.id.localeCompare(b.id, "fr", { numeric: true }); })
      .slice(0, 8);
  }

  function renderSearch(query) {
    var results = search(query);
    var content;
    if (!results.length) {
      content = '<div class="empty"><strong>Non documenté dans le corpus</strong>La recherche locale n’a trouvé aucun passage vérifié correspondant. Reformulez la question ou consultez les limites; cette interface ne complète pas les faits manquants.</div>';
    } else {
      content = '<p class="status-banner">Passages correspondants seulement : vérifiez les preuves avant de conclure.</p><div class="stack">' + results.map(function (item) {
        return '<article class="card search-result"><div><span class="badge">' + esc(item.type) + '</span> <span class="search-score">correspondance déterministe</span></div><h2>' + esc(item.title) + '</h2><p class="body-text">' + esc(item.body || "Aucun résumé; ouvrir la preuve.") + "</p>" + evidence(item.evidence) + "</article>";
      }).join("") + "</div>";
    }
    return page('Recherche : « ' + query + ' »', "Résultats tirés exclusivement des données injectées dans cette copie.", content);
  }

  var renderers = {
    brief: renderBrief,
    questions: renderQuestions,
    timeline: renderTimeline,
    decisions: renderDecisions,
    contradictions: renderContradictions,
    actions: renderActions,
    risks: renderRisks,
    sources: renderSources,
    limits: renderLimits,
    versions: renderVersions
  };

  function currentRoute() {
    var route = window.location.hash.replace(/^#/, "").split("?")[0];
    return routes.indexOf(route) >= 0 ? route : "brief";
  }

  function renderRoute(moveFocus) {
    var route = currentRoute();
    document.body.dataset.view = route;
    document.querySelectorAll("[data-route]").forEach(function (link) {
      if (link.dataset.route === route) link.setAttribute("aria-current", "page");
      else link.removeAttribute("aria-current");
    });
    view.setAttribute("aria-busy", "true");
    view.innerHTML = renderers[route]();
    view.setAttribute("aria-busy", "false");
    status.textContent = Object.keys(data).length ? "" : "Coquille hors ligne prête. Aucune donnée vérifiée n’a encore été injectée.";
    var printButton = view.querySelector("[data-print]");
    if (printButton) printButton.addEventListener("click", function () { window.print(); });
    if (moveFocus) {
      var heading = view.querySelector("h1");
      if (heading) heading.focus();
    }
  }

  var asOf = text(data.meta || {}, ["asOf", "as_of", "info_as_of"]);
  function formatAsOf(value) {
    if (!value) return "";
    var parsed = new Date(value);
    if (Number.isNaN(parsed.getTime())) return value;
    return new Intl.DateTimeFormat("fr-CA", {
      dateStyle: "long", timeStyle: "short", timeZone: "America/Toronto"
    }).format(parsed) + " (Montréal)";
  }
  document.getElementById("as-of").textContent = asOf ? "État au " + formatAsOf(asOf) : "Date de référence non chargée";
  window.addEventListener("hashchange", function () { renderRoute(true); });
  searchForm.addEventListener("submit", function (event) {
    event.preventDefault();
    var query = searchInput.value.trim();
    if (!query) { searchInput.focus(); return; }
    status.textContent = "";
    document.body.dataset.view = "search";
    document.querySelectorAll("[data-route]").forEach(function (link) { link.removeAttribute("aria-current"); });
    view.innerHTML = renderSearch(query);
    var heading = view.querySelector("h1");
    if (heading) heading.focus();
  });
  renderRoute(false);
})();
