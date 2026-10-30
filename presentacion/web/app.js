/* Presentación interactiva: navegación, animaciones en cascada, notas del orador, índice y pantalla completa. */
(() => {
  "use strict";

  const slides = [...document.querySelectorAll(".slide")];
  const total = slides.length;
  const stage = document.getElementById("stage");
  const counter = document.getElementById("counter");
  const bar = document.querySelector(".progress > i");
  const progress = document.querySelector(".progress");
  const notesPanel = document.getElementById("notes");
  const notesText = notesPanel.querySelector("p");
  const overview = document.getElementById("overview");
  const btnNotes = document.getElementById("btn-notes");
  const btnFs = document.getElementById("btn-fs");
  const btnIndex = document.getElementById("btn-index");
  const brand = document.getElementById("brand-title");
  let current = 0;

  // Cada elemento [data-a] aparece en cascada (equivalente a las animaciones del PPTX).
  slides.forEach((slide) => {
    slide.querySelectorAll("[data-a]").forEach((el, i) => el.style.setProperty("--i", i));
    if (slide.dataset.step) slide.style.setProperty("--step", slide.dataset.step + "s");
  });

  const clamp = (n) => Math.max(0, Math.min(total - 1, n));

  function render() {
    slides.forEach((s, i) => {
      const active = i === current;
      s.classList.toggle("active", active);
      s.setAttribute("aria-hidden", String(!active));
      if (active) s.scrollTop = 0;
    });
    const slide = slides[current];
    counter.textContent = `${current + 1} / ${total}`;
    bar.style.width = `${((current + 1) / total) * 100}%`;
    notesText.textContent = slide.querySelector(".notes-src")?.textContent.trim() || "Sin notas para esta diapositiva.";
    brand.textContent = slide.dataset.title || "";
    document.title = `${slide.dataset.title} · Orquestación con CrewAI`;
    overview.querySelectorAll("button").forEach((b, i) => b.classList.toggle("cur", i === current));
    if (location.hash !== `#${current + 1}`) history.replaceState(null, "", `#${current + 1}`);
  }

  function go(n) {
    const next = clamp(n);
    if (next === current) return;
    current = next;
    render();
  }

  // Índice (vista general)
  const grid = overview.querySelector(".grid");
  slides.forEach((s, i) => {
    const b = document.createElement("button");
    b.type = "button";
    b.innerHTML = `<b>${String(i + 1).padStart(2, "0")}</b><span></span>`;
    b.lastChild.textContent = s.dataset.title;
    b.addEventListener("click", () => { toggleOverview(false); go(i); });
    grid.appendChild(b);
  });

  function toggleNotes(force) {
    const open = force ?? !notesPanel.classList.contains("open");
    notesPanel.classList.toggle("open", open);
    btnNotes.setAttribute("aria-pressed", String(open));
  }
  function toggleOverview(force) {
    const open = force ?? !overview.classList.contains("open");
    overview.classList.toggle("open", open);
    btnIndex.setAttribute("aria-pressed", String(open));
    if (open) overview.querySelector("button.cur")?.focus();
  }
  function toggleFullscreen() {
    if (!document.fullscreenElement) document.documentElement.requestFullscreen?.().catch(() => {});
    else document.exitFullscreen?.();
  }
  document.addEventListener("fullscreenchange", () => {
    const fs = !!document.fullscreenElement;
    document.body.classList.toggle("fs", fs);
    btnFs.setAttribute("aria-pressed", String(fs));
  });

  document.getElementById("btn-prev").addEventListener("click", () => go(current - 1));
  document.getElementById("btn-next").addEventListener("click", () => go(current + 1));
  btnNotes.addEventListener("click", () => toggleNotes());
  btnIndex.addEventListener("click", () => toggleOverview());
  btnFs.addEventListener("click", toggleFullscreen);
  overview.addEventListener("click", (e) => { if (e.target === overview) toggleOverview(false); });
  progress.addEventListener("click", (e) => {
    const r = progress.getBoundingClientRect();
    go(Math.floor(((e.clientX - r.left) / r.width) * total));
  });

  // Teclado
  document.addEventListener("keydown", (e) => {
    if (e.ctrlKey || e.metaKey || e.altKey) return;
    const k = e.key;
    if (overview.classList.contains("open")) {
      if (k === "Escape" || k.toLowerCase() === "o") toggleOverview(false);
      return;
    }
    if (["ArrowRight", "PageDown", " ", "Enter"].includes(k) && !(e.target instanceof HTMLButtonElement && k === " ")) { e.preventDefault(); go(current + 1); }
    else if (["ArrowLeft", "PageUp", "Backspace"].includes(k)) { e.preventDefault(); go(current - 1); }
    else if (k === "Home") go(0);
    else if (k === "End") go(total - 1);
    else if (k.toLowerCase() === "f") toggleFullscreen();
    else if (k.toLowerCase() === "n") toggleNotes();
    else if (k.toLowerCase() === "o") toggleOverview();
    else if (k === "Escape") toggleNotes(false);
  });

  // Gestos táctiles: deslizar horizontalmente cambia de diapositiva; el scroll vertical se conserva.
  let sx = 0, sy = 0, tracking = false;
  stage.addEventListener("pointerdown", (e) => {
    if (e.pointerType === "mouse") return;
    tracking = true; sx = e.clientX; sy = e.clientY;
  });
  stage.addEventListener("pointerup", (e) => {
    if (!tracking) return;
    tracking = false;
    const dx = e.clientX - sx, dy = e.clientY - sy;
    if (Math.abs(dx) > 60 && Math.abs(dx) > Math.abs(dy) * 1.6) go(current + (dx < 0 ? 1 : -1));
  });
  stage.addEventListener("pointercancel", () => { tracking = false; });

  // Botón "copiar" en los bloques de código
  document.querySelectorAll(".code").forEach((code) => {
    const btn = document.createElement("button");
    btn.type = "button"; btn.className = "copy"; btn.textContent = "Copiar"; btn.setAttribute("aria-label", "Copiar código");
    btn.addEventListener("click", async (e) => {
      e.stopPropagation();
      const text = code.innerText.replace(/Copiar\s*$/, "").trimEnd();
      try { await navigator.clipboard.writeText(text); }
      catch {
        const ta = document.createElement("textarea"); ta.value = text; document.body.appendChild(ta); ta.select();
        try { document.execCommand("copy"); } catch { /* sin soporte */ } ta.remove();
      }
      btn.textContent = "¡Copiado!"; setTimeout(() => (btn.textContent = "Copiar"), 1400);
    });
    code.appendChild(btn);
  });

  window.addEventListener("hashchange", () => {
    const n = parseInt(location.hash.slice(1), 10);
    if (!Number.isNaN(n)) go(n - 1);
  });

  const start = parseInt(location.hash.slice(1), 10);
  current = Number.isNaN(start) ? 0 : clamp(start - 1);
  render();
})();
