/* =========================================================
   PULSE — Transactions page
   - Edit transaction (fetches data, opens shared modal)
   - Delete transaction (with confirm modal)
   ========================================================= */

(function () {
  "use strict";

  function initEditButtons() {
    document.querySelectorAll(".edit-tx").forEach((btn) => {
      btn.addEventListener("click", async () => {
        const id = btn.dataset.id;
        const { ok, data } = await window.PULSE.apiFetch(
          `/transactions/api/${id}`,
          { method: "GET" }
        );
        if (!ok || !data || !data.transaction) {
          alert("Could not load transaction.");
          return;
        }
        if (window.PULSE.openTxEdit) {
          window.PULSE.openTxEdit(data.transaction);
        }
      });
    });
  }

  function initDeleteButtons() {
    const confirmModal = document.getElementById("confirmModal");
    const confirmBtn = document.getElementById("confirmDeleteBtn");
    let pendingId = null;

    document.querySelectorAll(".delete-tx").forEach((btn) => {
      btn.addEventListener("click", () => {
        pendingId = btn.dataset.id;
        window.PULSE.openModal(confirmModal);
      });
    });

    document
      .querySelectorAll("[data-close-confirm]")
      .forEach((el) =>
        el.addEventListener("click", () =>
          window.PULSE.closeModal(confirmModal)
        )
      );

    if (confirmBtn) {
      confirmBtn.addEventListener("click", async () => {
        if (!pendingId) return;
        confirmBtn.disabled = true;
        confirmBtn.textContent = "Deleting...";

        const { ok } = await window.PULSE.apiFetch(
          `/transactions/api/${pendingId}`,
          { method: "DELETE" }
        );

        confirmBtn.disabled = false;
        confirmBtn.textContent = "Delete";

        if (ok) {
          window.PULSE.closeModal(confirmModal);
          window.location.reload();
        } else {
          alert("Failed to delete transaction.");
        }
      });
    }
  }

  document.addEventListener("DOMContentLoaded", () => {
    if (!window.PULSE) return;
    initEditButtons();
    initDeleteButtons();
  });
})();