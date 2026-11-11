document.addEventListener("DOMContentLoaded", () => {
  const ball = document.querySelector(".cricket-ball");
  const label = document.querySelector(".impact-label");
  if (!ball || !label || window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  ball.animate([
    { transform: "translate(0, 0) rotate(0deg)" },
    { transform: "translate(38vw, 4vh) rotate(720deg)", offset: .62 },
    { transform: "translate(70vw, -24vh) rotate(1400deg)" }
  ], { duration: 5200, iterations: Infinity, easing: "cubic-bezier(.2,.8,.2,1)" });
  label.animate([{ opacity: 0, transform: "scale(.6) rotate(-12deg)" }, { opacity: 1, transform: "scale(1) rotate(-12deg)", offset: .5 }, { opacity: 0 }], { duration: 5200, iterations: Infinity, delay: 2500 });
});
