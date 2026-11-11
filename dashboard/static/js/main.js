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
});
function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, character => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;"
  }[character]));
}
