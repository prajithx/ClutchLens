document.addEventListener("DOMContentLoaded", () => {
  const journey = document.querySelector("[data-stadium-journey]");
  const camera = document.querySelector("[data-stadium-camera]");
  if (!journey || !camera) return;

  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
  let frame = 0;
  const update = () => {
    frame = 0;
    const bounds = journey.getBoundingClientRect();
    const travel = Math.max(1, journey.offsetHeight - window.innerHeight);
    const progress = reducedMotion.matches
      ? 0.42
      : Math.min(1, Math.max(0, -bounds.top / travel));
    journey.style.setProperty("--journey-progress", progress.toFixed(4));
    camera.setAttribute("aria-label", `Stadium camera journey ${Math.round(progress * 100)} percent complete`);
  };
  const schedule = () => {
    if (!frame) frame = window.requestAnimationFrame(update);
  };
  if (!reducedMotion.matches) {
    window.addEventListener("scroll", schedule, { passive: true });
    window.addEventListener("resize", schedule, { passive: true });
  }
  reducedMotion.addEventListener?.("change", schedule);
  update();
});
