/* =========================================================
   PULSE — Budgets page
   - Create / edit budget modal
   - Delete budget with confirmation
   ========================================================= */

(function () {
  "use strict";

  function initBudgetModal() {
    const modal = document.getElementById("budgetModal");
    if (!modal) return;

    const form = document.getElementById("budgetForm");
    const title = document.getElementById("budgetModalTitle");
    const idField = document.getElementById("budgetId");
    const categorySelect = document.getElementById("budgetCategory");
    const limitInput = document.getElementById("budgetLimit");
    const errorsBox = document.getElementById("budgetErrors");

    const meta = document.getElementById("budgetMeta");
    const { month, year } = meta
      ? JSON.parse(meta.textContent)
      : { month: null, year: null };

    function reset() {
      form.reset();
      idField.value = "";
      title.textContent = "Add Budget";
      errorsBox.hidden = true;
      errorsBox.innerHTML = "";
      categorySelect.disabled = false;
    }

    function openCreate() {
      reset();
      window.PULSE.openModal(modal);
      window.PULSE.refreshIcons();
    }

    function openEdit(row) {
      reset();
      idField.value = row.id;
      categorySelect.value = row.category;
      categorySelect.disabled = true; // category is immutable on edit
      limitInput.value = row.limit;
      title.textContent = "Edit Budget";
      window.PULSE.openModal(modal);
      window.PULSE.refreshIcons();
    }

    function showErrors(errors) {
      const parts = Object.values(errors || {});
      if (!parts.length) {
        errorsBox.hidden = true;
        return;
      }
      errorsBox.hidden = false;
      errorsBox.innerHTML = "<ul>" + parts.map((p) => `<li>${p}</li>`).join("") + "</ul>";
    }

    // Wire up "Add Budget" buttons
    document
      .querySelectorAll("#openAddBudget")
      .forEach((el) => el.addEventListener("click", openCreate));

    // Close buttons
    document
      .getElementById("budgetModalClose")
      ?.addEventListener("click", () => window.PULSE.closeModal(modal));
    document
      .getElementById("budgetCancel")
      ?.addEventListener("click", () => window.PULSE.closeModal(modal));

    // Edit buttons in the list
    document.querySelectorAll(".edit-budget").forEach((btn) => {
      btn.addEventListener("click", () => {
        openEdit({
          id: btn.dataset.id,
          category: btn.dataset.category,
          limit: btn.dataset.limit,
        });
      });
    });

    // Submit
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      const id = idField.value;
      const isEdit = !!id;
      const url = isEdit ? `/budgets/api/${id}` : "/budgets/api";
      const method = isEdit ? "PUT" : "POST";

      const fd = new FormData(form);
      if (isEdit) {
        // Only limit is updated
        fd.set("monthly_limit", limitInput.value);
      } else {
        fd.set("month", month);
        fd.set("year", year);
      }

      const { ok, data } = await window.PULSE.apiFetch(url, {
        method,
        body: fd,
      });

      if (!ok) {
        showErrors(
          (data && data.errors) ||
            { general: (data && data.error) || "Could not save budget." }
        );
        return;
      }

      window.PULSE.closeModal(modal);
      window.location.reload();
    });
  }

  function initDeleteBudgets() {
    const modal = document.getElementById("confirmBudgetModal");
    const confirmBtn = document.getElementById("confirmBudgetDeleteBtn");
    const text = document.getElementById("confirmBudgetText");
    let pendingId = null;

    document.querySelectorAll(".delete-budget").forEach((btn) => {
      btn.addEventListener("click", () => {
        pendingId = btn.dataset.id;
        if (text) {
          text.textContent = `Delete the "${btn.dataset.category}" budget? This cannot be undone.`;
        }
        window.PULSE.openModal(modal);
      });
    });

    document
      .querySelectorAll("[data-close-confirm-budget]")
      .forEach((el) =>
        el.addEventListener("click", () =>
          window.PULSE.closeModal(modal)
        )
      );

    if (confirmBtn) {
      confirmBtn.addEventListener("click", async () => {
        if (!pendingId) return;
        confirmBtn.disabled = true;
        confirmBtn.textContent = "Deleting...";

        const { ok } = await window.PULSE.apiFetch(
          `/budgets/api/${pendingId}`,
          { method: "DELETE" }
        );

        confirmBtn.disabled = false;
        confirmBtn.textContent = "Delete";

        if (ok) {
          window.PULSE.closeModal(modal);
          window.location.reload();
        } else {
          alert("Failed to delete budget.");
        }
      });
    }
  }

  document.addEventListener("DOMContentLoaded", () => {
    if (!window.PULSE) return;
    initBudgetModal();
    initDeleteBudgets();
  });
})();