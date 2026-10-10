/* =========================================================
   PULSE — Global JS
   - Sidebar toggle (mobile)
   - CSRF-aware fetch
   - Lucide icon refresh
   - Modal open/close
   - Transaction modal (shared across pages)
   - Category dropdown sync with transaction type
   ========================================================= */

(function () {
  "use strict";

  // ------------------------------------------------------ CSRF
  const csrfMeta = document.querySelector('meta[name="csrf-token"]');
  const CSRF_TOKEN = csrfMeta ? csrfMeta.getAttribute("content") : "";

  async function apiFetch(url, options = {}) {
    const opts = Object.assign({ method: "GET", headers: {} }, options);
    opts.headers = Object.assign(
      {
        "X-CSRFToken": CSRF_TOKEN,
        "X-Requested-With": "XMLHttpRequest",
      },
      opts.headers || {}
    );
    const res = await fetch(url, opts);
    let data = null;
    try {
      data = await res.json();
    } catch (_) {
      /* non-JSON response */
    }
    return { ok: res.ok, status: res.status, data };
  }

  // ------------------------------------------------------ Icons
  function refreshIcons() {
    if (window.lucide && typeof window.lucide.createIcons === "function") {
      window.lucide.createIcons();
    }
  }

  // ------------------------------------------------------ Sidebar
  function initSidebar() {
    const sidebar = document.getElementById("appSidebar");
    const toggle = document.getElementById("menuToggle");
    const closeBtn = document.getElementById("sidebarClose");
    const backdrop = document.getElementById("sidebarBackdrop");
    if (!sidebar) return;

    function open() {
      sidebar.classList.add("is-open");
      if (backdrop) backdrop.classList.add("is-open");
    }
    function close() {
      sidebar.classList.remove("is-open");
      if (backdrop) backdrop.classList.remove("is-open");
    }

    if (toggle) toggle.addEventListener("click", open);
    if (closeBtn) closeBtn.addEventListener("click", close);
    if (backdrop) backdrop.addEventListener("click", close);

    // Close sidebar on nav-item click (mobile)
    sidebar.querySelectorAll(".nav-item").forEach((el) =>
      el.addEventListener("click", () => {
        if (window.innerWidth <= 768) close();
      })
    );
  }

  // ------------------------------------------------------ Modals
  function openModal(el) {
    if (!el) return;
    el.classList.add("is-open");
    el.setAttribute("aria-hidden", "false");
    document.body.style.overflow = "hidden";
  }
  function closeModal(el) {
    if (!el) return;
    el.classList.remove("is-open");
    el.setAttribute("aria-hidden", "true");
    document.body.style.overflow = "";
  }

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      document
        .querySelectorAll(".modal-backdrop.is-open")
        .forEach(closeModal);
    }
  });

  // Click outside modal closes it
  document.querySelectorAll(".modal-backdrop").forEach((backdrop) => {
    backdrop.addEventListener("click", (e) => {
      if (e.target === backdrop) closeModal(backdrop);
    });
  });

  // ------------------------------------------------------ Flash auto-dismiss
  function initFlash() {
    document.querySelectorAll(".flash").forEach((el) => {
      setTimeout(() => {
        el.style.transition = "opacity 0.4s ease";
        el.style.opacity = "0";
        setTimeout(() => el.remove(), 450);
      }, 3800);
    });
  }

  // ------------------------------------------------------ Transaction modal
  function initTransactionModal() {
    const modal = document.getElementById("txModal");
    if (!modal) return;

    const form = document.getElementById("txForm");
    const title = document.getElementById("txModalTitle");
    const idField = document.getElementById("txId");
    const typeField = document.getElementById("txType");
    const categorySelect = document.getElementById("txCategory");
    const amountField = document.getElementById("txAmount");
    const descField = document.getElementById("txDescription");
    const dateField = document.getElementById("txDate");
    const paymentField = document.getElementById("txPayment");
    const notesField = document.getElementById("txNotes");
    const errorsBox = document.getElementById("txErrors");
    const submitBtn = document.getElementById("txSubmit");
    const cancelBtn = document.getElementById("txCancel");
    const closeBtn = document.getElementById("txModalClose");
    const segButtons = modal.querySelectorAll(".seg-btn");

    // Category data injected by transaction_modal.html
    const catDataEl = document.getElementById("categoriesData");
    const catData = catDataEl ? JSON.parse(catDataEl.textContent) : { expense: [], income: [] };

    function fillCategories(type) {
      const list = catData[type] || [];
      categorySelect.innerHTML = "";
      list.forEach((c) => {
        const opt = document.createElement("option");
        opt.value = c;
        opt.textContent = c;
        categorySelect.appendChild(opt);
      });
    }

    function setType(type) {
      typeField.value = type;
      segButtons.forEach((b) =>
        b.classList.toggle("is-active", b.dataset.type === type)
      );
      fillCategories(type);
    }

    // Type toggle
    segButtons.forEach((b) =>
      b.addEventListener("click", () => setType(b.dataset.type))
    );

    function resetForm() {
      form.reset();
      idField.value = "";
      setType("expense");
      title.textContent = "Add Transaction";
      submitBtn.textContent = "Save";
      errorsBox.hidden = true;
      errorsBox.innerHTML = "";
      // Default date = today
      const today = new Date().toISOString().slice(0, 10);
      dateField.value = today;
    }

    function showErrors(errors) {
      const parts = Object.values(errors || {});
      if (!parts.length) {
        errorsBox.hidden = true;
        return;
      }
      errorsBox.hidden = false;
      errorsBox.innerHTML =
        "<ul>" + parts.map((p) => `<li>${p}</li>`).join("") + "</ul>";
    }

    function openForCreate() {
      resetForm();
      openModal(modal);
      refreshIcons();
      setTimeout(() => descField.focus(), 60);
    }

    function openForEdit(tx) {
      form.reset();
      errorsBox.hidden = true;
      idField.value = tx.id;
      setType(tx.transaction_type);
      descField.value = tx.description || "";
      amountField.value = tx.amount_rupees;
      dateField.value = tx.transaction_date;
      paymentField.value = tx.payment_method;
      categorySelect.value = tx.category;
      notesField.value = tx.notes || "";
      title.textContent = "Edit Transaction";
      submitBtn.textContent = "Update";
      openModal(modal);
      refreshIcons();
    }

    async function submitForm(e) {
      e.preventDefault();
      const id = idField.value;
      const isEdit = !!id;
      const url = isEdit
        ? `/transactions/api/${id}`
        : `/transactions/api`;
      const method = isEdit ? "PUT" : "POST";

      const formData = new FormData(form);

      submitBtn.disabled = true;
      submitBtn.textContent = isEdit ? "Updating..." : "Saving...";

      const { ok, data } = await apiFetch(url, {
        method,
        body: formData,
      });

      submitBtn.disabled = false;
      submitBtn.textContent = isEdit ? "Update" : "Save";

      if (!ok) {
        showErrors((data && data.errors) || { general: (data && data.error) || "Something went wrong." });
        return;
      }

      closeModal(modal);
      // Reload so the page reflects the new totals/charts.
      window.location.reload();
    }

    // Wire up
    form.addEventListener("submit", submitForm);
    if (cancelBtn) cancelBtn.addEventListener("click", () => closeModal(modal));
    if (closeBtn) closeBtn.addEventListener("click", () => closeModal(modal));

    // Any element with id="openAddTransaction" opens the modal
    document
      .querySelectorAll("#openAddTransaction")
      .forEach((el) => el.addEventListener("click", openForCreate));

    // Expose for other scripts (transactions.js uses openForEdit)
    window.PULSE = window.PULSE || {};
    window.PULSE.openTxCreate = openForCreate;
    window.PULSE.openTxEdit = openForEdit;
    window.PULSE.closeModal = closeModal;
    window.PULSE.openModal = openModal;

    // Default state
    resetForm();
  }

  // ------------------------------------------------------ Boot
  document.addEventListener("DOMContentLoaded", () => {
    refreshIcons();
    initSidebar();
    initFlash();
    initTransactionModal();
  });

  // Re-run Lucide if content changes dynamically
  window.addEventListener("load", refreshIcons);

  // Expose helpers
  window.PULSE = window.PULSE || {};
  window.PULSE.apiFetch = apiFetch;
  window.PULSE.refreshIcons = refreshIcons;
  window.PULSE.CSRF_TOKEN = CSRF_TOKEN;
})();