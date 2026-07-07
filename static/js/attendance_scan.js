/**
 * Smart Attendance System — Live Attendance Scanner Controller
 * Manages webcam feed, continuous frame posting to /attendance/scan, and live UI updates.
 */

let scanStream = null;
let scanInterval = null;
let isScanning = false;

async function startCamera() {
  const video = document.getElementById('videoFeed');
  const startBtn = document.getElementById('startCameraBtn');
  const stopBtn = document.getElementById('stopCameraBtn');
  const statusEl = document.getElementById('scanStatus');

  try {
    scanStream = await navigator.mediaDevices.getUserMedia({
      video: { width: 640, height: 480, facingMode: 'user' }
    });
    video.srcObject = scanStream;
    await video.play();

    startBtn.classList.add('d-none');
    stopBtn.classList.remove('d-none');
    statusEl.innerHTML = '<span style="width:6px;height:6px;background:#34d399;border-radius:50%;display:inline-block;animation:livePulse 1.5s infinite;margin-right:4px;"></span> Scanning...';

    isScanning = true;
    // Send a frame every 800ms
    scanInterval = setInterval(scanFrame, 800);
  } catch (err) {
    console.error('Camera error:', err);
    statusEl.textContent = 'Camera denied';
    statusEl.className = 'risk-indicator critical';
  }
}

function stopCamera() {
  isScanning = false;
  clearInterval(scanInterval);
  scanInterval = null;

  document.getElementById('startCameraBtn').classList.remove('d-none');
  document.getElementById('stopCameraBtn').classList.add('d-none');
  document.getElementById('scanStatus').textContent = 'Paused';

  // Don't kill the stream, just stop scanning
}

async function scanFrame() {
  if (!isScanning) return;

  const video = document.getElementById('videoFeed');
  const canvas = document.getElementById('captureCanvas');
  const ctx = canvas.getContext('2d');

  canvas.width = video.videoWidth || 640;
  canvas.height = video.videoHeight || 480;
  ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

  const frameData = canvas.toDataURL('image/jpeg', 0.7);

  try {
    const resp = await fetch(`/attendance/scan/${SESSION_ID}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ frame: frameData })
    });

    const data = await resp.json();
    if (data.success && data.results) {
      drawOverlay(data.results);
      updateAttendanceLog(data.results);
    }
  } catch (err) {
    console.error('Scan request failed:', err);
  }
}

function drawOverlay(results) {
  const overlayCanvas = document.getElementById('overlayCanvas');
  const video = document.getElementById('videoFeed');
  const ctx = overlayCanvas.getContext('2d');

  overlayCanvas.width = video.videoWidth || 640;
  overlayCanvas.height = video.videoHeight || 480;
  ctx.clearRect(0, 0, overlayCanvas.width, overlayCanvas.height);

  results.forEach(r => {
    const [x, y, w, h] = r.box;
    const color = r.status === 'recognized' ? '#34d399' : '#fb7185';

    // Draw bounding box
    ctx.strokeStyle = color;
    ctx.lineWidth = 2;
    ctx.strokeRect(x, y, w, h);

    // Draw label background
    ctx.fillStyle = 'rgba(0,0,0,0.7)';
    const labelH = 20;
    ctx.fillRect(x, y + h, w, labelH);

    // Draw label text
    ctx.fillStyle = color;
    ctx.font = '12px Inter, sans-serif';
    ctx.fillText(
      r.status === 'recognized' ? `${r.name}` : 'Unknown',
      x + 4, y + h + 14
    );
  });
}

function updateAttendanceLog(results) {
  const logContainer = document.getElementById('attendanceLog');
  const presentCountEl = document.getElementById('presentCount');
  const remainingCountEl = document.getElementById('remainingCount');

  results.forEach(r => {
    if (r.status === 'recognized' && r.action === 'marked') {
      markedIds.add(r.student_id);
      markedCount++;

      // Add to log
      const entry = document.createElement('div');
      entry.className = 'd-flex align-items-center gap-3 mb-2 p-2 rounded-3 marked-row';
      entry.style.cssText = 'background:rgba(52,211,153,0.06);border:1px solid rgba(52,211,153,0.15);';
      entry.innerHTML = `
        <div style="width:36px;height:36px;border-radius:50%;background:var(--success-gradient);display:flex;align-items:center;justify-content:center;flex-shrink:0;">
          <i class="fa-solid fa-check text-white small"></i>
        </div>
        <div class="flex-grow-1">
          <div class="fw-semibold text-white small">${r.name}</div>
          <div class="text-muted" style="font-size:0.7rem;">${r.matric} · ${r.time_marked}</div>
        </div>
        <span class="risk-indicator good small">Present</span>
      `;

      // Prepend to log
      logContainer.insertBefore(entry, logContainer.firstChild);

      // Remove from pending list
      const pendingEl = document.getElementById(`pending-${r.student_id}`);
      if (pendingEl) pendingEl.remove();

      // Update counters
      presentCountEl.textContent = `${markedCount} Present`;
      remainingCountEl.textContent = TOTAL_ENROLLED - markedCount;
    }
  });
}
