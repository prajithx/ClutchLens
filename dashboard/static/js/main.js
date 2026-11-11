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
      const response = await fetch(`/api/players?q=${encodeURIComponent(search.value)}`);
      if (!response.ok) return;
      const players = await response.json();
      results.innerHTML = players.length
        ? players.map(player => `<a role="option" href="/players?player_id=${player.id}">${escapeHtml(player.name)} <small>${player.id}</small></a>`).join("")
        : "<p class='micro-note'>No supplied player matches that search.</p>";
    });
  }

  const candidateCards = [...document.querySelectorAll("[data-candidate-card]")];
  const emptyCandidates = document.querySelector("#recruitment-empty");
  const roleFilter = document.querySelector("#recruitment-role-filter");
  const recruitmentSearch = document.querySelector("#recruitment-search");
  const filterTabs = [...document.querySelectorAll("[data-recruitment-filter]")];
  if (candidateCards.length && roleFilter && recruitmentSearch) {
    let classification = "all";
    const renderCandidates = () => {
      const query = recruitmentSearch.value.trim().toLowerCase();
      let visible = 0;
      candidateCards.forEach(card => {
        const matchesClassification = classification === "all" || card.dataset.classification === classification;
        const matchesRole = roleFilter.value === "all" || card.dataset.role === roleFilter.value;
        const matchesName = !query || card.dataset.name.includes(query);
        const show = matchesClassification && matchesRole && matchesName;
        card.hidden = !show;
        if (show) visible += 1;
      });
      if (emptyCandidates) emptyCandidates.hidden = visible !== 0;
    };
    filterTabs.forEach(tab => tab.addEventListener("click", () => {
      classification = tab.dataset.recruitmentFilter;
      filterTabs.forEach(item => item.classList.toggle("active", item === tab));
      renderCandidates();
    }));
    roleFilter.addEventListener("change", renderCandidates);
    recruitmentSearch.addEventListener("input", renderCandidates);
    renderCandidates();
  }
});
function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, character => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;"
  }[character]));
}
