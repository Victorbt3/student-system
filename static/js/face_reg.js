/**
 * Smart Attendance System — Face Registration Controller
 * Handles webcam access, frame capture loop, progress updates, and training trigger.
 */

let faceStream = null;
let captureInterval = null;
let sampleCount = 0;
const TOTAL_SAMPLES = 50; // Reduced from 100 for faster registration
let frameBuffer = [];
const FRAMES_PER_BATCH = 5; // Send 5 frames at once

async function startFaceCapture() {
  const video = document.getElementById('faceVideo');
  const startBtn = document.getElementById('startCaptureBtn');
  const pauseBtn = document.getElementById('pauseCaptureBtn');
  const statusEl = document.getElementById('captureStatus');

  try {
    faceStream = await navigator.mediaDevices.getUserMedia({
      video: { width: 320, height: 240, facingMode: 'user' } // Reduced resolution for speed
    });
    video.srcObject = faceStream;
    await video.play();

    startBtn.classList.add('d-none');
    pauseBtn.classList.remove('d-none');
    statusEl.textContent = 'Capturing... Keep your face centered.';

    // Start auto-capture every 150ms (faster capture)
    captureInterval = setInterval(() => captureOneSample(), 150);
  } catch (err) {
    console.error('Camera access denied:', err);
    statusEl.textContent = 'Camera access denied. Please grant permission and refresh.';
    statusEl.style.color = '#fb7185';
  }
}

function pauseCapture() {
  clearInterval(captureInterval);
  captureInterval = null;
  document.getElementById('startCaptureBtn').classList.remove('d-none');
  document.getElementById('pauseCaptureBtn').classList.add('d-none');
  document.getElementById('captureStatus').textContent = `Paused at ${sampleCount}/${TOTAL_SAMPLES}. Press Start to resume.`;
}

async function captureOneSample() {
  if (sampleCount >= TOTAL_SAMPLES) {
    clearInterval(captureInterval);
    captureInterval = null;
    // Send any remaining frames in buffer
    if (frameBuffer.length > 0) {
      await sendFrameBatch();
    }
    onCaptureComplete();
    return;
  }

  const video = document.getElementById('faceVideo');
  const canvas = document.getElementById('faceCapCanvas');
  const ctx = canvas.getContext('2d');

  canvas.width = video.videoWidth || 320;
  canvas.height = video.videoHeight || 240;
  ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

  const frameData = canvas.toDataURL('image/jpeg', 0.6); // Lower quality for speed

  frameBuffer.push({
    frame: frameData,
    sample_num: sampleCount + 1
  });

  // Flash effect on webcam container
  const container = document.getElementById('faceWebcamContainer');
  container.classList.add('capture-flash');
  setTimeout(() => container.classList.remove('capture-flash'), 150);

  sampleCount++;
  updateProgress(sampleCount);

  // Send batch when buffer is full
  if (frameBuffer.length >= FRAMES_PER_BATCH) {
    await sendFrameBatch();
  }
}

async function sendFrameBatch() {
  if (frameBuffer.length === 0) return;

  const batch = frameBuffer.splice(0, FRAMES_PER_BATCH);

  try {
    const resp = await fetch('/student/register-face/batch-capture', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ frames: batch })
    });

    const data = await resp.json();
    if (!data.success) {
      console.error('Batch capture failed:', data);
    } else if (data.saved_count !== undefined) {
      // optionally log per-batch failures
      if (data.results && data.results.some(r => !r.success)) {
        console.warn('Some samples failed:', data.results.filter(r => !r.success).slice(0, 5));
      }
    }
  } catch (err) {
    console.error('Batch capture request failed:', err);
  }
}


function updateProgress(count) {
  const countEl = document.getElementById('captureCount');
  const circle = document.getElementById('progressCircle');
  const statusEl = document.getElementById('captureStatus');
  const circumference = 326.73;

  countEl.textContent = count;
  const offset = circumference - (count / TOTAL_SAMPLES) * circumference;
  circle.style.strokeDashoffset = offset;
  statusEl.textContent = `Captured ${count}/${TOTAL_SAMPLES} samples...`;

  // Update step indicators
  if (count > 0) document.getElementById('step1').classList.add('done');
}

function onCaptureComplete() {
  // Stop camera
  if (faceStream) {
    faceStream.getTracks().forEach(t => t.stop());
    faceStream = null;
  }

  // Move to training phase
  document.getElementById('step1').classList.add('done');
  document.getElementById('step2').classList.add('active');
  document.getElementById('phaseCapture').classList.add('d-none');
  document.getElementById('phaseTraining').classList.remove('d-none');

  startTraining();
}

async function startTraining() {
  const progressBar = document.getElementById('trainProgress');
  const statusEl = document.getElementById('trainStatus');

  // Simulate visual progress
  progressBar.style.width = '30%';
  statusEl.textContent = 'Loading samples...';

  await new Promise(r => setTimeout(r, 800));
  progressBar.style.width = '60%';
  statusEl.textContent = 'Training LBPH model...';

  try {
    const resp = await fetch('/student/register-face/train', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    });
    const data = await resp.json();

    progressBar.style.width = '100%';

    if (data.success) {
      statusEl.textContent = 'Training complete!';
      await new Promise(r => setTimeout(r, 600));
      onTrainingComplete();
    } else {
      statusEl.textContent = `Error: ${data.message}`;
      statusEl.style.color = '#fb7185';
    }
  } catch (err) {
    statusEl.textContent = 'Training request failed. Please try again.';
    statusEl.style.color = '#fb7185';
    console.error('Training error:', err);
  }
}

function onTrainingComplete() {
  document.getElementById('step2').classList.add('done');
  document.getElementById('step3').classList.add('active');
  document.getElementById('phaseTraining').classList.add('d-none');
  document.getElementById('phaseSuccess').classList.remove('d-none');
}
