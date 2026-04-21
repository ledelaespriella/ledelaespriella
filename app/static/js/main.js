/*
 * main.js — vista pública.
 *
 * Responsabilidades:
 *   1. Animaciones de entrada con IntersectionObserver (respeta prefers-reduced-motion).
 *   2. Cargar /api/projects y renderizar la galería filtrable por categoría.
 *   3. Todo el DOM se construye con document.createElement + textContent
 *      para NUNCA inyectar HTML arbitrario desde la API → mitiga XSS
 *      almacenado (admin malicioso o DB comprometida).
 */
(function () {
  "use strict";

  // ---------- Reveal on scroll ----------
  const reveals = document.querySelectorAll(".reveal");
  if ("IntersectionObserver" in window && reveals.length) {
    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-visible");
            io.unobserve(entry.target);
          }
        });
      },
      { rootMargin: "0px 0px -80px 0px", threshold: 0.08 }
    );
    reveals.forEach((el) => io.observe(el));
  } else {
    // Fallback: si no hay IntersectionObserver, mostramos todo sin animación.
    reveals.forEach((el) => el.classList.add("is-visible"));
  }

  // ---------- Galería de proyectos ----------
  const grid = document.getElementById("projects-grid");
  const filters = document.getElementById("project-filters");
  if (!grid || !filters) return;

  const state = { projects: [], activeCategory: "" };

  function cardForProject(p) {
    const col = document.createElement("div");
    col.className = "col-md-6 col-lg-4";

    const card = document.createElement("article");
    card.className = "card card-project h-100";

    if (p.image_filename) {
      const img = document.createElement("img");
      // La URL se construye con el filename ya validado server-side contra
      // un regex estricto. Aun así, encodeURIComponent por defensa.
      img.src = "/uploads/" + encodeURIComponent(p.image_filename);
      img.alt = p.title || "Proyecto";
      img.loading = "lazy";
      img.className = "card-img-top";
      card.appendChild(img);
    }

    const body = document.createElement("div");
    body.className = "card-body";

    const title = document.createElement("h3");
    title.className = "h5";
    title.textContent = p.title || ""; // textContent = seguro ante XSS
    body.appendChild(title);

    if (p.category) {
      const badge = document.createElement("span");
      badge.className = "badge bg-primary me-2";
      badge.textContent = p.category;
      body.appendChild(badge);
    }
    if (p.is_featured) {
      const star = document.createElement("span");
      star.className = "badge bg-warning text-dark";
      star.textContent = "★ Destacado";
      body.appendChild(star);
    }

    if (p.description) {
      const desc = document.createElement("p");
      desc.className = "mt-2";
      desc.textContent = p.description;
      body.appendChild(desc);
    }

    if (Array.isArray(p.tags) && p.tags.length) {
      const tags = document.createElement("p");
      tags.className = "small text-secondary mb-2";
      tags.textContent = p.tags.map((t) => "#" + t).join(" ");
      body.appendChild(tags);
    }

    if (p.project_url) {
      const link = document.createElement("a");
      link.href = p.project_url;
      link.target = "_blank";
      link.rel = "noopener noreferrer"; // mitiga reverse tabnabbing
      link.className = "btn btn-sm btn-outline-primary mt-2";
      link.textContent = "Ver más →";
      body.appendChild(link);
    }

    card.appendChild(body);
    col.appendChild(card);
    return col;
  }

  function render() {
    grid.replaceChildren();
    const visible = state.activeCategory
      ? state.projects.filter((p) => p.category === state.activeCategory)
      : state.projects;

    if (!visible.length) {
      const empty = document.createElement("p");
      empty.className = "text-center text-secondary py-4";
      empty.textContent = "No hay proyectos para mostrar todavía.";
      grid.appendChild(empty);
      return;
    }
    visible.forEach((p) => grid.appendChild(cardForProject(p)));
  }

  function renderFilters(categories) {
    // Conservamos el botón "Todos" ya presente en el HTML; añadimos el resto.
    const all = filters.querySelector('[data-category=""]');
    filters.replaceChildren(all);
    categories.forEach((cat) => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "btn btn-outline-primary";
      btn.dataset.category = cat;
      btn.textContent = cat;
      filters.appendChild(btn);
    });
  }

  filters.addEventListener("click", (ev) => {
    const btn = ev.target.closest("button[data-category]");
    if (!btn) return;
    state.activeCategory = btn.dataset.category || "";
    filters
      .querySelectorAll("button")
      .forEach((b) => b.classList.toggle("active", b === btn));
    render();
  });

  fetch("/api/projects", { headers: { Accept: "application/json" } })
    .then((r) => {
      if (!r.ok) throw new Error("HTTP " + r.status);
      return r.json();
    })
    .then((data) => {
      state.projects = Array.isArray(data.projects) ? data.projects : [];
      renderFilters(Array.isArray(data.categories) ? data.categories : []);
      render();
    })
    .catch((err) => {
      console.error("No pude cargar proyectos:", err);
      grid.replaceChildren();
      const p = document.createElement("p");
      p.className = "text-center text-danger py-4";
      p.textContent = "No se pudieron cargar los proyectos. Intenta recargar la página.";
      grid.appendChild(p);
    });
})();
