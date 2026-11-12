document.addEventListener("DOMContentLoaded", () => {
  const toggle = document.querySelector(".menu-toggle");
  const nav = document.querySelector(".primary-nav");
  if (toggle && nav) {
    toggle.addEventListener("click", () => {
      const open = nav.classList.toggle("open");
      toggle.setAttribute("aria-expanded", String(open));
    });
  }

  const search = document.querySelector("#player-search");
  const results = document.querySelector("#player-results");
  if (search && results) {
    search.addEventListener("input", async () => {
      search.setAttribute("aria-busy", "true");
      try {
        const response = await fetch(`/api/players?q=${encodeURIComponent(search.value)}`);
        if (!response.ok) {
          results.innerHTML = "<p class='micro-note'>Player search is temporarily unavailable.</p>";
          return;
        }
        const players = await response.json();
        results.innerHTML = players.length
          ? players.map(player => `<a role="option" href="/players?player_id=${player.id}">${escapeHtml(player.name)} <small>${player.id}</small></a>`).join("")
          : "<p class='micro-note'>No supplied player matches that search.</p>";
        const resultStatus = document.querySelector("#player-result-status");
        if (resultStatus) resultStatus.textContent = `${players.length} matching players`;
      } catch (error) {
        results.innerHTML = "<p class='micro-note'>Player search is temporarily unavailable.</p>";
      } finally {
        search.setAttribute("aria-busy", "false");
      }
    });
  }

  initializeRecruitmentWorkspace();
});

function initializeRecruitmentWorkspace() {
  const dataElement = document.querySelector("#recruitment-data");
  const definitionsElement = document.querySelector("#recruitment-comparison-definitions");
  if (!dataElement || !definitionsElement) return;

  let candidates;
  let definitions;
  try {
    candidates = JSON.parse(dataElement.textContent);
    definitions = JSON.parse(definitionsElement.textContent);
  } catch (error) {
    showWorkspaceError("Candidate evidence could not be loaded safely.");
    return;
  }
  const byKey = new Map(candidates.map(candidate => [candidate.candidate_key, candidate]));
  const cards = [...document.querySelectorAll("[data-candidate-card]")];
  const classification = document.querySelector("#recruitment-classification-filter");
  const role = document.querySelector("#recruitment-role-filter");
  const evidence = document.querySelector("#recruitment-evidence-filter");
  const search = document.querySelector("#recruitment-search");
  const season = document.querySelector("#recruitment-season-filter");
  const team = document.querySelector("#recruitment-team-filter");
  const resultCount = document.querySelector("#recruitment-result-count");
  const empty = document.querySelector("#recruitment-empty");
  const shortlistKey = "clutchlens:working-shortlist:v1";
  const selectedForComparison = new Set();
  let shortlist = loadShortlist(byKey, shortlistKey);
  const suggestedCards = [...document.querySelectorAll("[data-suggested-card]")];
  const suggestedRole = document.querySelector("#suggested-role-filter");
  const suggestedEvidence = document.querySelector("#suggested-evidence-filter");
  const suggestedSearch = document.querySelector("#suggested-search");
  const suggestedSeason = document.querySelector("#suggested-season-filter");
  const suggestedTeam = document.querySelector("#suggested-team-filter");
  const suggestedResultCount = document.querySelector("#suggested-result-count");
  const suggestedEmpty = document.querySelector("#suggested-empty");

  const renderCards = () => {
    const query = search.value.trim().toLowerCase();
    let visible = 0;
    cards.forEach(card => {
      const matches = (classification.value === "all" || card.dataset.classification === classification.value)
        && (role.value === "all" || card.dataset.role === role.value)
        && (evidence.value === "all" || card.dataset.evidence === evidence.value)
        && (season.value === "all" || card.dataset.season === season.value)
        && (team.value === "all" || card.dataset.team === team.value)
        && (!query || card.dataset.name.includes(query));
      card.hidden = !matches;
      if (matches) visible += 1;
    });
    resultCount.textContent = `${visible} contextual row${visible === 1 ? "" : "s"}`;
    empty.hidden = visible !== 0;
  };

  [classification, role, evidence, search, season, team].forEach(control => control.addEventListener("input", renderCards));
  const renderSuggestedCards = () => {
    const query = suggestedSearch.value.trim().toLowerCase();
    let visible = 0;
    suggestedCards.forEach(card => {
      const matches = (suggestedRole.value === "all" || card.dataset.role === suggestedRole.value)
        && (suggestedEvidence.value === "all" || card.dataset.evidence === suggestedEvidence.value)
        && (suggestedSeason.value === "all" || card.dataset.season === suggestedSeason.value)
        && (suggestedTeam.value === "all" || card.dataset.team === suggestedTeam.value)
        && (!query || card.dataset.name.includes(query));
      card.hidden = !matches;
      if (matches) visible += 1;
    });
    suggestedResultCount.textContent = `${visible} suggestion${visible === 1 ? "" : "s"}`;
    suggestedEmpty.hidden = visible !== 0;
  };
  [suggestedRole, suggestedEvidence, suggestedSearch, suggestedSeason, suggestedTeam].forEach(control => control.addEventListener("input", renderSuggestedCards));
  document.querySelector("#suggested-rerun").addEventListener("click", () => window.location.reload());
  document.querySelector("#recruitment-reset").addEventListener("click", () => {
    classification.value = "all";
    role.value = "all";
    evidence.value = "all";
    search.value = "";
    season.value = "all";
    team.value = "all";
    renderCards();
  });

  cards.forEach(card => {
    const key = card.dataset.candidateKey;
    const compareCheck = card.querySelector("[data-compare-check]");
    const detailButton = card.querySelector("[data-detail-button]");
    const shortlistButton = card.querySelector("[data-shortlist-button]");
    compareCheck.addEventListener("change", () => {
      if (compareCheck.checked) selectedForComparison.add(key);
      else selectedForComparison.delete(key);
      renderComparison();
    });
    detailButton.addEventListener("click", () => showDetail(byKey.get(key)));
    shortlistButton.addEventListener("click", () => {
      if (shortlist.has(key)) shortlist.delete(key);
      else shortlist.add(key);
      saveShortlist(shortlist, shortlistKey);
      renderShortlist();
      updateShortlistButtons();
      updateSuggestedButtons();
    });
  });
  document.querySelectorAll("[data-suggested-add]").forEach(button => {
    button.addEventListener("click", () => {
      const key = button.dataset.candidateKey;
      if (shortlist.has(key)) return;
      shortlist.add(key);
      saveShortlist(shortlist, shortlistKey);
      renderShortlist();
      updateShortlistButtons();
      updateSuggestedButtons();
    });
  });
  document.querySelectorAll("[data-suggested-detail]").forEach(button => {
    button.addEventListener("click", () => showDetail(byKey.get(button.dataset.candidateKey)));
  });

  document.querySelector("#close-detail").addEventListener("click", () => {
    document.querySelector("#candidate-detail-panel").hidden = true;
  });
  document.querySelector("#shortlist-jump").addEventListener("click", () => {
    document.querySelector("#shortlist-panel").scrollIntoView({ behavior: "smooth", block: "start" });
  });
  document.querySelector("#shortlist-clear").addEventListener("click", () => {
    if (!shortlist.size || !window.confirm("Clear the human-reviewed working shortlist?")) return;
    shortlist.clear();
    saveShortlist(shortlist, shortlistKey);
    renderShortlist();
    updateShortlistButtons();
    updateSuggestedButtons();
  });
  document.querySelector("#shortlist-export").addEventListener("click", () => exportShortlist(shortlist, byKey));
  document.querySelector("#shortlist-print").addEventListener("click", () => window.print());

  function showDetail(candidate) {
    if (!candidate) return;
    const panel = document.querySelector("#candidate-detail-panel");
    document.querySelector("#candidate-detail-title").textContent = `${candidate.player_name} · ${candidate.role} context`;
    const metrics = definitions[candidate.role] || [];
    const metricRows = metrics.map(metric => `
      <tr><th>${escapeHtml(metric.label)}</th><td>${formatValue(candidate[metric.key])}</td><td>${escapeHtml(metric.unit)}</td><td>${escapeHtml(metric.basis)}</td><td>${escapeHtml(metric.caveat)}</td></tr>
    `).join("");
    const contexts = candidates.filter(item => item.role === candidate.role && String(item.player_id) === String(candidate.player_id));
    const contextList = contexts.map(item => `<li>${escapeHtml(item.context_key)} · ${escapeHtml(item.team_name)} · ${escapeHtml(item.comp_name)} · ${escapeHtml(String(item.season))}</li>`).join("");
    document.querySelector("#candidate-detail-content").innerHTML = `
      <div class="detail-identity"><span class="candidate-avatar">${escapeHtml(candidate.player_name.slice(0, 1))}</span><div><h3>${escapeHtml(candidate.player_name)}</h3><p>${escapeHtml(candidate.context_identity)}</p><p>${escapeHtml(candidate.team_name)} · ${escapeHtml(candidate.comp_name)} · ${escapeHtml(String(candidate.season))} · ${escapeHtml(candidate.match_format)}</p></div><button class="button button-small ${shortlist.has(candidate.candidate_key) ? "button-danger" : "button-primary"}" id="detail-shortlist-button" type="button">${shortlist.has(candidate.candidate_key) ? "Remove from shortlist" : "Add to shortlist"}</button></div>
      <div class="detail-grid">
        <dl class="evidence-list"><div><dt>Role status</dt><dd>${escapeHtml(candidate.role_status)}</dd></div><div><dt>RR classification</dt><dd>${escapeHtml(candidate.classification)}</dd></div><div><dt>Evidence status</dt><dd>${escapeHtml(candidate.evidence_label)}</dd></div><div><dt>Evidence confidence</dt><dd>${escapeHtml(candidate.evidence_confidence)}</dd></div><div><dt>Contextual identity</dt><dd>${escapeHtml(candidate.context_key)}</dd></div><div><dt>RR reference matches</dt><dd>${formatValue(candidate.rr_reference_season_matches)}</dd></div><div><dt>Auction availability</dt><dd>NOT VERIFIED FROM SUPPLIED DATA</dd></div></dl>
        <div><h3>Evidence gates</h3><p>${escapeHtml(candidate.evidence_gate_summary)}</p><p class="micro-note">${escapeHtml(candidate.pressure_semantics)}</p><p class="micro-note">Source: ${escapeHtml(candidate.source_lineage)}</p></div>
      </div>
      <h3>Supported descriptive evidence</h3><div class="table-scroll"><table class="evidence-table"><thead><tr><th>Metric</th><th>Value</th><th>Unit</th><th>Source basis</th><th>Caveat</th></tr></thead><tbody>${metricRows}</tbody></table></div>
      <div class="unavailable-box"><strong>Not supported by supplied data:</strong> ${escapeHtml(candidate.unavailable_metric_summary)}.</div>
      <h3>Historical contexts for this supplied player ID</h3><p class="micro-note">Each context remains separately inspectable; no player-level total is calculated.</p><ul class="context-list">${contextList}</ul>
    `;
    panel.hidden = false;
    document.querySelector("#detail-shortlist-button").addEventListener("click", () => {
      if (shortlist.has(candidate.candidate_key)) shortlist.delete(candidate.candidate_key);
      else shortlist.add(candidate.candidate_key);
      saveShortlist(shortlist, shortlistKey);
      renderShortlist();
      updateShortlistButtons();
      updateSuggestedButtons();
      showDetail(candidate);
    });
    panel.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function renderComparison() {
    const selected = [...selectedForComparison].map(key => byKey.get(key)).filter(Boolean);
    const comparisonContent = document.querySelector("#comparison-content");
    document.querySelector("#comparison-count").textContent = `${selected.length} selected`;
    document.querySelector("#comparison-empty").hidden = selected.length !== 0;
    comparisonContent.hidden = selected.length < 2;
    if (selected.length < 2) {
      comparisonContent.innerHTML = "";
      return;
    }
    const roles = new Set(selected.map(candidate => candidate.role));
    if (roles.size > 1) {
      comparisonContent.innerHTML = "<div class='unavailable-box'>Not comparable: batter and bowler contexts use different metric definitions and populations. Select contexts from one role.</div>";
      return;
    }
    const roleName = selected[0].role;
    const rows = definitions[roleName].map(metric => `
      <tr><th>${escapeHtml(metric.label)}<small>${escapeHtml(metric.unit)}</small></th>${selected.map(candidate => `<td><strong>${formatValue(candidate[metric.key])}</strong><small>${escapeHtml(candidate.player_name)} · ${escapeHtml(candidate.context_key)}</small></td>`).join("")}<td>${escapeHtml(metric.caveat)}</td></tr>
    `).join("");
    const contexts = new Set(selected.map(candidate => `${candidate.comp_name} · ${candidate.match_format} · ${candidate.season}`));
    comparisonContent.innerHTML = `
      <p class="comparison-note">Descriptive side-by-side view only. ${contexts.size > 1 ? "These contexts differ by competition, format or season; direct comparison is limited." : "Contexts share the same displayed competition, format and season."}</p>
      <div class="table-scroll"><table class="evidence-table comparison-table"><thead><tr><th>Metric</th>${selected.map(candidate => `<th>${escapeHtml(candidate.player_name)}</th>`).join("")}<th>Limitation</th></tr></thead><tbody>${rows}</tbody></table></div>
      <p class="micro-note">No winner, score, rate, ranking or recommendation is calculated. Unavailable metrics remain excluded.</p>
    `;
  }

  function renderShortlist() {
    const selected = [...shortlist].map(key => byKey.get(key)).filter(Boolean);
    const content = document.querySelector("#shortlist-content");
    document.querySelector("#shortlist-count").textContent = `${selected.length} selected`;
    document.querySelector("#shortlist-dock-count").textContent = selected.length;
    document.querySelector("#shortlist-dock-batters").textContent = selected.filter(candidate => candidate.role === "batter").length;
    document.querySelector("#shortlist-dock-bowlers").textContent = selected.filter(candidate => candidate.role === "bowler").length;
    document.querySelector("#shortlist-empty").hidden = selected.length !== 0;
    content.hidden = selected.length === 0;
    const renderGroup = (group, label) => `<section class="shortlist-group"><h3>${label} <span>${group.length}</span></h3>${group.map(candidate => `
      <div class="shortlist-row"><div><strong>${escapeHtml(candidate.player_name)}</strong><span>${escapeHtml(candidate.team_name)} · ${escapeHtml(candidate.comp_name)} · ${escapeHtml(String(candidate.season))}</span><small>${escapeHtml(candidate.role)} · ${escapeHtml(candidate.context_key)} · ${escapeHtml(candidate.classification)}</small><small>${escapeHtml(candidate.evidence_gate_summary)}</small></div><div class="shortlist-row-actions"><button class="button button-small button-muted" type="button" data-open-shortlist="${escapeHtml(candidate.candidate_key)}">Open profile</button><button class="button button-small button-muted" type="button" data-remove-shortlist="${escapeHtml(candidate.candidate_key)}">Remove</button></div></div>
    `).join("")}</section>`;
    content.innerHTML = renderGroup(selected.filter(candidate => candidate.role === "batter"), "Batters") + renderGroup(selected.filter(candidate => candidate.role === "bowler"), "Bowlers") + renderGroup(selected.filter(candidate => !["batter", "bowler"].includes(candidate.role)), "Unknown / not inferred");
    content.querySelectorAll("[data-open-shortlist]").forEach(button => button.addEventListener("click", () => showDetail(byKey.get(button.dataset.openShortlist))));
    content.querySelectorAll("[data-remove-shortlist]").forEach(button => button.addEventListener("click", () => {
      shortlist.delete(button.dataset.removeShortlist);
      saveShortlist(shortlist, shortlistKey);
      renderShortlist();
      updateShortlistButtons();
      updateSuggestedButtons();
    }));
  }

  function updateShortlistButtons() {
    cards.forEach(card => {
      const button = card.querySelector("[data-shortlist-button]");
      const active = shortlist.has(card.dataset.candidateKey);
      button.textContent = active ? "Remove from working shortlist" : "Add to working shortlist";
      button.setAttribute("aria-pressed", String(active));
    });
  }

  function updateSuggestedButtons() {
    document.querySelectorAll("[data-suggested-add]").forEach(button => {
      const active = shortlist.has(button.dataset.candidateKey);
      button.disabled = active;
      button.textContent = active ? "Already in working shortlist" : "Review and add";
      button.setAttribute("aria-label", active
        ? "Already in human-reviewed working shortlist"
        : "Review and add to human-reviewed working shortlist");
    });
  }

  renderCards();
  renderSuggestedCards();
  renderComparison();
  renderShortlist();
  updateShortlistButtons();
  updateSuggestedButtons();
}

function loadShortlist(byKey, storageKey) {
  try {
    const saved = JSON.parse(window.localStorage.getItem(storageKey) || "[]");
    return new Set(Array.isArray(saved) ? saved.filter(key => byKey.has(key)) : []);
  } catch (error) {
    return new Set();
  }
}

function saveShortlist(shortlist, storageKey) {
  window.localStorage.setItem(storageKey, JSON.stringify([...shortlist]));
}

function exportShortlist(shortlist, byKey) {
  const rows = [...shortlist].map(key => byKey.get(key)).filter(Boolean);
  if (!rows.length) return;
  const fields = ["player_name", "candidate_key", "role", "context_key", "team_name", "comp_name", "season", "classification", "evidence_label", "evidence_gate_summary", "supported_metric_summary", "unavailable_metric_summary", "auction_availability_status"];
  const csv = [fields, ...rows.map(row => fields.map(field => csvCell(row[field])))]
    .map(row => row.join(",")).join("\r\n");
  const link = document.createElement("a");
  link.href = URL.createObjectURL(new Blob([csv], { type: "text/csv;charset=utf-8" }));
  link.download = "clutchlens-working-shortlist.csv";
  link.click();
  URL.revokeObjectURL(link.href);
}

function csvCell(value) {
  return `"${String(value ?? "").replaceAll('"', '""')}"`;
}

function formatValue(value) {
  if (value === null || value === undefined || value === "") return "Unavailable";
  if (typeof value === "number") return value.toLocaleString();
  return escapeHtml(String(value));
}

function showWorkspaceError(message) {
  const grid = document.querySelector("#candidate-grid");
  if (grid) grid.innerHTML = `<div class="unavailable-box">${escapeHtml(message)}</div>`;
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, character => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;"
  }[character]));
}
