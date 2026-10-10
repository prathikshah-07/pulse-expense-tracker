/* =========================================================
   PULSE — Dashboard charts
   - Cash flow bar chart (income vs expenses over months)
   - Category doughnut chart
   ========================================================= */

(function () {
  "use strict";

  function readData() {
    const el = document.getElementById("dashboardData");
    if (!el) return null;
    try {
      return JSON.parse(el.textContent);
    } catch (e) {
      console.warn("Invalid dashboard data", e);
      return null;
    }
  }

  // Convert paise → rupees for chart axis readability
  function toRupees(paise) {
    return (paise || 0) / 100;
  }

  function baseOptions() {
    return {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          labels: {
            color: "#A59ABF",
            font: { family: "Inter", size: 11 },
            boxWidth: 10,
            boxHeight: 10,
          },
        },
        tooltip: {
          backgroundColor: "#19142A",
          borderColor: "#302446",
          borderWidth: 1,
          titleColor: "#F3EEFF",
          bodyColor: "#F3EEFF",
          padding: 10,
          callbacks: {
            label: (ctx) => {
              const val = ctx.parsed.y ?? ctx.parsed;
              const formatted = new Intl.NumberFormat("en-IN", {
                style: "currency",
                currency: "INR",
                maximumFractionDigits: 0,
              }).format(val);
              return `${ctx.dataset.label || ctx.label}: ${formatted}`;
            },
          },
        },
      },
      scales: {
        x: {
          grid: { color: "rgba(48, 36, 70, 0.35)", drawBorder: false },
          ticks: { color: "#A59ABF", font: { size: 11 } },
        },
        y: {
          grid: { color: "rgba(48, 36, 70, 0.35)", drawBorder: false },
          ticks: {
            color: "#A59ABF",
            font: { size: 11 },
            callback: (v) =>
              "₹" +
              new Intl.NumberFormat("en-IN", {
                maximumFractionDigits: 0,
                notation: v >= 100000 ? "compact" : "standard",
              }).format(v),
          },
        },
      },
    };
  }

  function initCashflow(data) {
    const canvas = document.getElementById("cashflowChart");
    if (!canvas) return;
    const cf = data.cashflow;

    new Chart(canvas, {
      type: "bar",
      data: {
        labels: cf.labels,
        datasets: [
          {
            label: "Income",
            data: cf.income_paise.map(toRupees),
            backgroundColor: "rgba(118, 229, 176, 0.75)",
            borderColor: "#76E5B0",
            borderWidth: 1,
            borderRadius: 3,
            maxBarThickness: 32,
          },
          {
            label: "Expenses",
            data: cf.expense_paise.map(toRupees),
            backgroundColor: "rgba(149, 96, 255, 0.75)",
            borderColor: "#9560FF",
            borderWidth: 1,
            borderRadius: 3,
            maxBarThickness: 32,
          },
        ],
      },
      options: baseOptions(),
    });
  }

  function initCategory(data) {
    const canvas = document.getElementById("categoryChart");
    if (!canvas) return;
    const c = data.category;
    if (!c.labels || !c.labels.length) return;

    new Chart(canvas, {
      type: "doughnut",
      data: {
        labels: c.labels,
        datasets: [
          {
            data: c.values_paise.map(toRupees),
            backgroundColor: c.colors,
            borderColor: "#131020",
            borderWidth: 2,
            hoverOffset: 4,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: "62%",
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: "#19142A",
            borderColor: "#302446",
            borderWidth: 1,
            titleColor: "#F3EEFF",
            bodyColor: "#F3EEFF",
            padding: 10,
            callbacks: {
              label: (ctx) => {
                const val = ctx.parsed;
                const total = ctx.dataset.data.reduce((a, b) => a + b, 0);
                const pct = total ? ((val / total) * 100).toFixed(1) : "0";
                const formatted = new Intl.NumberFormat("en-IN", {
                  style: "currency",
                  currency: "INR",
                  maximumFractionDigits: 0,
                }).format(val);
                return `${ctx.label}: ${formatted} (${pct}%)`;
              },
            },
          },
        },
      },
    });
  }

  document.addEventListener("DOMContentLoaded", () => {
    const data = readData();
    if (!data) return;
    initCashflow(data);
    initCategory(data);
  });
})();