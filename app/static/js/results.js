/**
 * app/static/js/results.js
 *
 * Animates the score progress bars on the results page when they
 * scroll into view.  Uses IntersectionObserver so the animation only
 * runs when the bars are visible — not immediately on page load.
 */
"use strict";

document.addEventListener("DOMContentLoaded", () => {
  const bars = document.querySelectorAll(".cgn-score-bar");

  if (!bars.length) return;

  // IntersectionObserver fires our callback when an element enters the viewport.
  // threshold: 0.3 means "fire when 30% of the element is visible".
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          const bar = entry.target;
          const score = parseInt(bar.dataset.score, 10) || 0;
          // Set the actual width — the CSS transition handles the animation
          bar.style.width = score + "%";
          // Stop observing once animated
          observer.unobserve(bar);
        }
      });
    },
    { threshold: 0.3 }
  );

  bars.forEach((bar) => observer.observe(bar));
});
