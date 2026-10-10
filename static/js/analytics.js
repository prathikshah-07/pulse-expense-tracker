/* =========================================================
   PULSE — Analytics page charts
   - Income vs Expenses trend (line)
   - Expense distribution (doughnut)
   - Payment-method split (polar/pie)
   ========================================================= */

(function () {
  "use strict";

  function readData() {
    const el = document.getElementById("analyticsData");
    if (!el) return null;
    try {
      return JSON.parse(el.textContent);
    } catch (e) {
      console.warn("Invalid analytics data", e);
      return null;
    }
  }

  function toRupees(p) {
    return (p || 0) / 100;
  }

  function inrTooltipLabel(ctx) {
    const val = ctx.parsed.y ?? ctx.parsed;
    const formatted = new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 0,
    }).format(val);
    return `${ctx.dataset.label || ctx.label}: ${formatted}`;
  }

  function lineOptions() {
    return {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: "index", intersect: false },
      plugins: {
        legend: {
          labels: { color: "#A59ABF", boxWidth: 10, boxHeight: 10, font: { size: 11 } },
        },
        tooltip: {
          backgroundColor: "#19142A",
          borderColor: "#302446",
          borderWidth: 1,
          titleColor: "#F3EEFF",
          bodyColor: "#F3EEFF",
          padding: 10,
          callbacks: { label: inrTooltipLabel },
        },
      },
      scales: {
        x: {
          grid: { color: "rgba(48, 36, 70, 0.3)", drawBorder: false },
          ticks: { color: "#A59ABF", font: { size: 11 } },
        },
        y: {
          grid: { color: "rgba(48, 36, 70, 0.3)", drawBorder: false },
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

  function initTrend(data) {
    const canvas = document.getElementById("trendChart");
    if (!canvas) return;
    const t = data.trend;

    new Chart(canvas, {
      type: "line",
      data: {
        labels: t.labels,
        datasets: [
          {
            label: "Income",
            data: t.income.map(toRupees),
            borderColor: "#76E5B0",
            backgroundColor: "rgba(118, 229, 176, 0.15)",
            tension: 0.32,
            fill: true,
            pointRadius: 3,
            pointBackgroundColor: "#76E5B0",
            borderWidth: 2,
          },
          {
            label: "Expenses",
            data: t.expense.map(toRupees),
            borderColor: "#9560FF",
            backgroundColor: "rgba(149, 96, 255, 0.16)",
            tension: 0.32,
            fill: true,
            pointRadius: 3,
            pointBackgroundColor: "#9560FF",
            borderWidth: 2,
          },
        ],
      },
      options: lineOptions(),
    });
  }

  function initCategory(data) {
    const canvas = document.getElementById("analyticsCategoryChart");
    if (!canvas) return;
    const c = data.category;
    if (!c.labels || !c.labels.length) return;

    new Chart(canvas, {
      type: "doughnut",
      data: {
        labels: c.labels,
        datasets: [
          {
            data: c.values.map(toRupees),
            backgroundColor: c.colors,
            borderColor: "#131020",
            borderWidth: 2,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: "60%",
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: "#19142A",
            borderColor: "#302446",
            borderWidth: 1,
            callbacks: {
              label: (ctx) => {
                const val = ctx.parsed;
                const total = ctx.dataset.data.reduce((a, b) => a + b, 0);
                const pct = total ? ((val / total) * 100).toFixed(1) : "0";
                return `${ctx.label}: ₹${val.toLocaleString("en-IN")} (${pct}%)`;
              },
            },
          },
        },
      },
    });
  }

  function initPayment(data) {
    const canvas = document.getElementById("paymentChart");
    if (!canvas) return;
    const p = data.payment;
    if (!p.labels || !p.labels.length) return;

    const palette = ["#9560FF", "#62E7E0", "#FFCA72", "#76E5B0", "#FF718D"];

    new Chart(canvas, {
      type: "polarArea",
      data: {
        labels: p.labels,
        datasets: [
          {
            data: p.values.map(toRupees),
            backgroundColor: p.labels.map(
              (_, i) => palette[i % palette.length] + "cc"
            ),
            borderColor: "#131020",
            borderWidth: 2,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: "bottom",
            labels: {
              color: "#A59ABF",
              boxWidth: 10,
              boxHeight: 10,
              font: { size: 11 },
            },
          },
          tooltip: {
            backgroundColor: "#19142A",
            borderColor: "#302446",
            borderWidth: 1,
            callbacks: {
              label: (ctx) =>
                `${ctx.label}: ₹${ctx.parsed.r.toLocaleString("en-IN")}`,
            },
          },
        },
        scales: {
          r: {
            grid: { color: "rgba(48, 36, 70, 0.4)" },
            angleLines: { color: "rgba(48, 36, 70, 0.4)" },
            ticks: { color: "#A59ABF", backdropColor: "transparent", font: { size: 10 } },
            pointLabels: { display: false },
          },
        },
      },
    });
  }

  document.addEventListener("DOMContentLoaded", () => {
    const data = readData();
    if (!data) return;
    initTrend(data);
    initCategory(data);
    initPayment(data);
  });
})();