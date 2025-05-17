const chartTitles = [
    "図書館の混雑予想",
    "鳩カフェの混雑予想",
    "komorebiの混雑予想",
    "第一食堂の混雑予想",
    "9号館ラウンジの混雑予想",
    "12号館ラウンジの混雑予想"
  ];
  
  const chartIds = [
    "libraryChart",
    "hatocafeChart",
    "komorebiChart",
    "diningChart",
    "lounge9Chart",
    "lounge12Chart"
  ];
  
  let currentIndex = 0;
  
  function showGraph(index) {
    chartIds.forEach((id, i) => {
      document.getElementById(id).style.display = i === index ? "block" : "none";
    });
    document.getElementById("graph-title").textContent = chartTitles[index];
  }
  
  function nextGraph() {
    currentIndex = (currentIndex + 1) % chartIds.length;
    showGraph(currentIndex);
  }
  
  function prevGraph() {
    currentIndex = (currentIndex - 1 + chartIds.length) % chartIds.length;
    showGraph(currentIndex);
  }
  
  window.onload = function () {
    const labels = ["8時", "10時", "12時", "14時", "16時", "18時"];
    const datasets = chartIds.map((id, idx) => ({
      label: chartTitles[idx],
      data: Array.from({ length: 6 }, () => Math.floor(Math.random() * 100)),
      backgroundColor: "#0aab0a"
    }));
  
    chartIds.forEach((id, index) => {
      new Chart(document.getElementById(id), {
        type: "bar",
        data: {
          labels: labels,
          datasets: [datasets[index]]
        },
        options: {
          responsive: true,
          plugins: {
            legend: { display: false }
          },
          scales: {
            y: {
              beginAtZero: true,
              max: 100
            }
          }
        }
      });
    });
  
    showGraph(0);
  };
  