(() => {
  "use strict";

  const chart = document.querySelector("#score-chart");
  const source = document.querySelector("#trend-data");
  if (!chart || !source || typeof Chart === "undefined") return;
  const values = JSON.parse(source.textContent);
  new Chart(chart, {
    type: "line",
    data: {
      labels: values.map((item) => item.label),
      datasets: [{
        label: "Score (%)",
        data: values.map((item) => item.score),
        borderColor: "#4f6bed",
        backgroundColor: "rgba(79, 107, 237, .11)",
        fill: true,
        tension: .32,
        pointRadius: 3,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: { y: { min: 0, max: 100, ticks: { stepSize: 20 } } },
      plugins: { legend: { display: false } },
    },
  });
})();
