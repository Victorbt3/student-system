/**
 * Smart Attendance System — Chart.js Dashboard Builder
 * Generates analytics charts for Admin and Lecturer dashboards.
 */

const chartColors = {
  cyan: '#38bdf8',
  cyanBg: 'rgba(56,189,248,0.15)',
  green: '#34d399',
  greenBg: 'rgba(52,211,153,0.15)',
  purple: '#a78bfa',
  purpleBg: 'rgba(167,139,250,0.15)',
  red: '#fb7185',
  redBg: 'rgba(251,113,133,0.15)',
  amber: '#fbbf24',
  amberBg: 'rgba(251,191,36,0.15)',
  gridColor: 'rgba(255,255,255,0.05)',
  tickColor: '#64748b'
};

Chart.defaults.color = '#94a3b8';
Chart.defaults.borderColor = chartColors.gridColor;
Chart.defaults.font.family = "'Inter', sans-serif";

function initAdminCharts(attendanceRate) {
  // 1. Gauge Doughnut Chart
  const gaugeCtx = document.getElementById('gaugeChart');
  if (gaugeCtx) {
    new Chart(gaugeCtx, {
      type: 'doughnut',
      data: {
        datasets: [{
          data: [attendanceRate, 100 - attendanceRate],
          backgroundColor: [chartColors.cyan, 'rgba(255,255,255,0.03)'],
          borderWidth: 0,
          borderRadius: 10,
          cutout: '82%'
        }]
      },
      options: {
        responsive: false,
        plugins: { legend: { display: false }, tooltip: { enabled: false } },
        rotation: -90,
        circumference: 180
      }
    });
  }

  // 2. Weekly Attendance Bar Chart (Sample Data)
  const weeklyCtx = document.getElementById('weeklyChart');
  if (weeklyCtx) {
    new Chart(weeklyCtx, {
      type: 'bar',
      data: {
        labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'],
        datasets: [
          {
            label: 'Present',
            data: [42, 38, 45, 40, 35],
            backgroundColor: chartColors.greenBg,
            borderColor: chartColors.green,
            borderWidth: 1.5,
            borderRadius: 6,
            barPercentage: 0.6
          },
          {
            label: 'Absent',
            data: [8, 12, 5, 10, 15],
            backgroundColor: chartColors.redBg,
            borderColor: chartColors.red,
            borderWidth: 1.5,
            borderRadius: 6,
            barPercentage: 0.6
          }
        ]
      },
      options: {
        responsive: true,
        plugins: {
          legend: { position: 'top', labels: { usePointStyle: true, pointStyle: 'circle', padding: 20 } }
        },
        scales: {
          x: { grid: { display: false }, ticks: { color: chartColors.tickColor } },
          y: { grid: { color: chartColors.gridColor }, ticks: { color: chartColors.tickColor } }
        }
      }
    });
  }

  // 3. Department Doughnut Chart (Sample Data)
  const deptCtx = document.getElementById('deptChart');
  if (deptCtx) {
    new Chart(deptCtx, {
      type: 'doughnut',
      data: {
        labels: ['Computer Science', 'Mathematics', 'Physics', 'Engineering'],
        datasets: [{
          data: [85, 78, 92, 70],
          backgroundColor: [chartColors.cyanBg, chartColors.purpleBg, chartColors.greenBg, chartColors.amberBg],
          borderColor: [chartColors.cyan, chartColors.purple, chartColors.green, chartColors.amber],
          borderWidth: 1.5,
          cutout: '60%',
          borderRadius: 4
        }]
      },
      options: {
        responsive: true,
        plugins: {
          legend: { position: 'bottom', labels: { usePointStyle: true, pointStyle: 'circle', padding: 16, font: { size: 11 } } }
        }
      }
    });
  }
}

function initLecturerCharts() {
  // Course Attendance Trend (Line)
  const courseCtx = document.getElementById('courseAttendanceChart');
  if (courseCtx) {
    new Chart(courseCtx, {
      type: 'line',
      data: {
        labels: ['Week 1', 'Week 2', 'Week 3', 'Week 4', 'Week 5', 'Week 6', 'Week 7', 'Week 8'],
        datasets: [
          {
            label: 'CSC 401',
            data: [90, 88, 85, 82, 80, 78, 75, 72],
            borderColor: chartColors.cyan,
            backgroundColor: chartColors.cyanBg,
            fill: true,
            tension: 0.4,
            pointRadius: 4,
            pointBackgroundColor: chartColors.cyan
          },
          {
            label: 'CSC 403',
            data: [95, 93, 90, 88, 85, 83, 80, 78],
            borderColor: chartColors.purple,
            backgroundColor: chartColors.purpleBg,
            fill: true,
            tension: 0.4,
            pointRadius: 4,
            pointBackgroundColor: chartColors.purple
          }
        ]
      },
      options: {
        responsive: true,
        plugins: {
          legend: { position: 'top', labels: { usePointStyle: true, pointStyle: 'circle', padding: 20 } }
        },
        scales: {
          x: { grid: { display: false } },
          y: { grid: { color: chartColors.gridColor }, min: 50, max: 100,
               ticks: { callback: v => v + '%' } }
        }
      }
    });
  }

  // Status Pie
  const statusCtx = document.getElementById('statusPieChart');
  if (statusCtx) {
    new Chart(statusCtx, {
      type: 'pie',
      data: {
        labels: ['Present', 'Late', 'Absent'],
        datasets: [{
          data: [72, 8, 20],
          backgroundColor: [chartColors.greenBg, chartColors.amberBg, chartColors.redBg],
          borderColor: [chartColors.green, chartColors.amber, chartColors.red],
          borderWidth: 1.5
        }]
      },
      options: {
        responsive: true,
        plugins: {
          legend: { position: 'bottom', labels: { usePointStyle: true, pointStyle: 'circle', padding: 12, font: { size: 11 } } }
        }
      }
    });
  }
}
