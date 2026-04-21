/*
 * admin.js — dashboard de administración.
 *
 *   - Toggles PATCH (publicado / destacado) con token CSRF en header.
 *   - Confirmación de eliminación mediante modal Bootstrap + form POST
 *     con token CSRF (server-side valida con DeleteForm).
 */
(function () {
  "use strict";

  const csrfToken = document
    .querySelector('meta[name="csrf-token"]')
    ?.getAttribute("content");

  async function patchToggle(url) {
    const res = await fetch(url, {
      method: "PATCH",
      headers: {
        "X-CSRFToken": csrfToken || "",
        Accept: "application/json",
      },
      credentials: "same-origin",
    });
    if (!res.ok) {
      throw new Error("HTTP " + res.status);
    }
    return res.json();
  }

  function wireToggle(selector, field, activeClass, inactiveClass, activeText, inactiveText) {
    document.querySelectorAll(selector).forEach((btn) => {
      btn.addEventListener("click", async () => {
        btn.disabled = true;
        try {
          const data = await patchToggle(btn.dataset.url);
          const on = Boolean(data[field]);
          btn.textContent = on ? activeText : inactiveText;
          btn.classList.toggle(activeClass, on);
          btn.classList.toggle(inactiveClass, !on);
        } catch (err) {
          console.error(err);
          alert("No se pudo actualizar. Recarga la página e intenta de nuevo.");
        } finally {
          btn.disabled = false;
        }
      });
    });
  }

  wireToggle(
    ".js-toggle-published",
    "is_published",
    "btn-success",
    "btn-secondary",
    "Publicado",
    "Oculto"
  );
  wireToggle(
    ".js-toggle-featured",
    "is_featured",
    "btn-warning",
    "btn-outline-warning",
    "★ Destacado",
    "☆ Normal"
  );

  // ---------- Modal de eliminación ----------
  const modalEl = document.getElementById("confirmDelete");
  const form = document.getElementById("deleteForm");
  const titleEl = document.getElementById("deleteProjectTitle");

  if (modalEl && form) {
    modalEl.addEventListener("show.bs.modal", (event) => {
      const trigger = event.relatedTarget;
      if (!trigger) return;
      const id = trigger.dataset.projectId;
      const title = trigger.dataset.projectTitle || "";
      // Construimos la URL server-side valida la ruta; el id es un entero
      // que Flask coaccionará vía <int:project_id>, no hay inyección posible.
      form.action = "/admin/project/" + encodeURIComponent(id) + "/delete";
      if (titleEl) titleEl.textContent = title;
    });
  }
})();
