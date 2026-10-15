/**
 * app/static/js/assessment.js
 *
 * Handles all interactivity on the assessment page:
 *   1. Skill checkboxes → show/hide proficiency slider
 *   2. Proficiency slider → update the label badge in real time
 *   3. Interest cards → toggle selected state on click
 *   4. Technology tags → toggle selected state on click
 *   5. Work-style cards → toggle selected state on click
 *   6. Progress bar → update as each section is filled
 *   7. Client-side validation before form submit
 *
 * Beginner note:
 *   - document.querySelectorAll() finds ALL elements matching a CSS selector.
 *   - element.addEventListener('event', fn) runs fn when the event fires.
 *   - element.classList.add/remove/toggle() adds, removes, or flips a CSS class.
 *   - element.closest('.parent-class') walks up the DOM to find a matching ancestor.
 */

"use strict";

// ── Proficiency level labels (match the Python dict in assessment.py) ──────────
const PROF_LABELS = {
  1: "Beginner",
  2: "Basic",
  3: "Intermediate",
  4: "Advanced",
  5: "Expert",
};

// ── Run everything after the page has fully loaded ────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  initSkillSliders();
  initInterestCards();
  initTechTags();
  initWorkStyleCards();
  initProgressBar();
  initFormValidation();
});


// ── 1. Skill checkboxes & proficiency sliders ─────────────────────────────────
function initSkillSliders() {
  document.querySelectorAll(".skill-checkbox").forEach((checkbox) => {
    const targetId = checkbox.dataset.target;          // e.g. "slider-python"
    const sliderWrap = document.getElementById(targetId);

    // Show/hide slider when checkbox is toggled
    checkbox.addEventListener("change", () => {
      if (checkbox.checked) {
        sliderWrap.classList.remove("d-none");
      } else {
        sliderWrap.classList.add("d-none");
      }
      updateProgress();
    });

    // If checkbox is already checked on page load (re-render after validation),
    // make sure the slider is visible
    if (checkbox.checked && sliderWrap) {
      sliderWrap.classList.remove("d-none");
    }
  });

  // Update proficiency label badge when slider moves
  document.querySelectorAll(".cgn-prof-slider").forEach((slider) => {
    const labelId = slider.dataset.label;              // e.g. "label-python"
    const labelEl = document.getElementById(labelId);

    const updateLabel = () => {
      const val = parseInt(slider.value, 10);
      if (labelEl) {
        labelEl.textContent = PROF_LABELS[val] || val;
        // Change badge colour based on level
        labelEl.className = "cgn-prof-label badge";
        if (val <= 2) labelEl.classList.add("cgn-prof-low");
        else if (val === 3) labelEl.classList.add("cgn-prof-mid");
        else labelEl.classList.add("cgn-prof-high");
      }
    };

    slider.addEventListener("input", updateLabel);
    updateLabel(); // Set initial colour on page load
  });
}


// ── 2. Interest cards ─────────────────────────────────────────────────────────
function initInterestCards() {
  document.querySelectorAll(".cgn-interest-card").forEach((card) => {
    const checkbox = card.querySelector(".interest-checkbox");

    card.addEventListener("click", () => {
      checkbox.checked = !checkbox.checked;
      card.classList.toggle("cgn-interest-card--selected", checkbox.checked);
      updateProgress();
    });

    // Sync visual state on load (after validation re-render)
    card.classList.toggle("cgn-interest-card--selected", checkbox.checked);
  });
}


// ── 3. Technology tags ────────────────────────────────────────────────────────
function initTechTags() {
  document.querySelectorAll(".cgn-tech-tag").forEach((tag) => {
    const checkbox = tag.querySelector(".tech-checkbox");

    tag.addEventListener("click", () => {
      checkbox.checked = !checkbox.checked;
      tag.classList.toggle("cgn-tech-tag--selected", checkbox.checked);
    });

    // Sync on load
    tag.classList.toggle("cgn-tech-tag--selected", checkbox.checked);
  });
}


// ── 4. Work-style cards ───────────────────────────────────────────────────────
function initWorkStyleCards() {
  document.querySelectorAll(".cgn-work-style-card").forEach((card) => {
    const radio = card.querySelector(".work-style-radio");

    card.addEventListener("click", () => {
      // Deselect all others first
      document.querySelectorAll(".cgn-work-style-card").forEach((c) => {
        c.classList.remove("cgn-work-style-card--selected");
      });
      radio.checked = true;
      card.classList.add("cgn-work-style-card--selected");
      updateProgress();
    });

    // Sync on load
    if (radio.checked) {
      card.classList.add("cgn-work-style-card--selected");
    }
  });
}


// ── 5. Progress bar ───────────────────────────────────────────────────────────
/**
 * A section is considered "started/filled" when:
 *   Skills    → at least 3 checkboxes are ticked
 *   Interests → at least 2 cards are selected
 *   Tech      → at least 1 tag is selected  (optional section — always counts)
 *   Goals     → short_term_role has a value AND a work_style is selected
 */
function initProgressBar() {
  // Listen on all inputs that affect section completion
  document.querySelectorAll(
    ".skill-checkbox, .interest-checkbox, .tech-checkbox, .work-style-radio, #short_term_role"
  ).forEach((el) => el.addEventListener("change", updateProgress));

  updateProgress(); // Set initial state
}

function updateProgress() {
  const sections = {
    skills:    countChecked(".skill-checkbox") >= 3,
    interests: countChecked(".interest-checkbox") >= 2,
    tech:      true,   // optional — always mark as done
    goals:     (
      document.querySelector("#short_term_role")?.value !== "" &&
      document.querySelector(".work-style-radio:checked") !== null
    ),
  };

  const completed = Object.values(sections).filter(Boolean).length;
  const total = Object.keys(sections).length;
  const pct = Math.round((completed / total) * 100);

  const bar   = document.getElementById("progress-bar");
  const label = document.getElementById("progress-label");
  const pctEl = document.getElementById("progress-pct");

  if (bar)   { bar.style.width = pct + "%"; bar.setAttribute("aria-valuenow", pct); }
  if (label) { label.textContent = `${completed} of ${total} sections completed`; }
  if (pctEl) { pctEl.textContent = pct + "%"; }

  // Colour the bar green once all done
  if (bar) {
    bar.classList.toggle("bg-success", pct === 100);
    bar.classList.toggle("bg-accent",  pct < 100);
  }
}

function countChecked(selector) {
  return document.querySelectorAll(selector + ":checked").length;
}


// ── 6. Client-side validation ─────────────────────────────────────────────────
/**
 * Runs before form submit. Shows inline error messages and stops submission
 * if requirements are not met.
 * Server-side validation in assessment.py is the authoritative check —
 * this just gives instant feedback to the user.
 */
function initFormValidation() {
  const form = document.getElementById("assessment-form");
  if (!form) return;

  form.addEventListener("submit", (e) => {
    let isValid = true;

    // Section A: at least 3 skills
    const skillsOk = countChecked(".skill-checkbox") >= 3;
    const skillsErr = document.getElementById("skills-error");
    if (skillsErr) {
      skillsErr.classList.toggle("d-none", skillsOk);
    }
    if (!skillsOk) {
      isValid = false;
      document.getElementById("section-skills")?.scrollIntoView({ behavior: "smooth", block: "center" });
    }

    // Section B: at least 2 interests
    const interestsOk = countChecked(".interest-checkbox") >= 2;
    const interestsErr = document.getElementById("interests-error");
    if (interestsErr) {
      interestsErr.classList.toggle("d-none", interestsOk);
    }
    if (!interestsOk && isValid) {
      isValid = false;
      document.getElementById("section-interests")?.scrollIntoView({ behavior: "smooth", block: "center" });
    }

    // Section D: short_term_role required
    const roleOk = document.querySelector("#short_term_role")?.value !== "";
    // Section D: work_style required
    const workOk = document.querySelector(".work-style-radio:checked") !== null;
    const workErr = document.getElementById("workstyle-error");
    if (workErr) {
      workErr.classList.toggle("d-none", workOk);
    }
    if ((!roleOk || !workOk) && isValid) {
      isValid = false;
      document.getElementById("section-goals")?.scrollIntoView({ behavior: "smooth", block: "center" });
    }

    if (!isValid) {
      e.preventDefault(); // Stop form from submitting
    } else {
      // Disable submit button to prevent double-click
      const btn = document.getElementById("submit-btn");
      if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Saving…';
      }
    }
  });
}
