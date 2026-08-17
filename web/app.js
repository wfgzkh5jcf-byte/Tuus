const canvas = document.getElementById('clock');
const ctx = canvas.getContext('2d');
const timeEl = document.getElementById('digitalTime');
const dateEl = document.getElementById('digitalDate');

const colors = {
  cream: '#f3ebdd',
  green: '#91a961',
  orange: '#f39a18',
  muted: '#7f8c88',
  edge: '#374247',
};

const days = ['zondag','maandag','dinsdag','woensdag','donderdag','vrijdag','zaterdag'];
const months = ['januari','februari','maart','april','mei','juni','juli','augustus','september','oktober','november','december'];

function resizeCanvas() {
  const rect = canvas.getBoundingClientRect();
  const dpr = window.devicePixelRatio || 1;
  const width = Math.round(rect.width * dpr);
  const height = Math.round(rect.height * dpr);
  if (canvas.width !== width || canvas.height !== height) {
    canvas.width = width;
    canvas.height = height;
  }
}

function polar(cx, cy, angle, radius) {
  return [
    cx + Math.cos(angle - Math.PI / 2) * radius,
    cy + Math.sin(angle - Math.PI / 2) * radius,
  ];
}

function drawClock(now) {
  resizeCanvas();
  const dpr = window.devicePixelRatio || 1;
  const w = canvas.width;
  const h = canvas.height;
  const cx = w / 2;
  const cy = h / 2;
  const r = Math.min(w, h) * 0.46;

  ctx.clearRect(0, 0, w, h);
  ctx.lineCap = 'round';

  ctx.strokeStyle = colors.edge;
  ctx.lineWidth = 2 * dpr;
  ctx.beginPath();
  ctx.arc(cx, cy, r, 0, Math.PI * 2);
  ctx.stroke();

  for (let i = 0; i < 60; i++) {
    const major = i % 5 === 0;
    const angle = i * Math.PI / 30;
    const [x1, y1] = polar(cx, cy, angle, r - (major ? 20 : 10) * dpr);
    const [x2, y2] = polar(cx, cy, angle, r - 3 * dpr);
    ctx.strokeStyle = major ? colors.cream : colors.muted;
    ctx.lineWidth = (major ? 3 : 1) * dpr;
    ctx.beginPath();
    ctx.moveTo(x1, y1);
    ctx.lineTo(x2, y2);
    ctx.stroke();
  }

  ctx.fillStyle = colors.cream;
  ctx.font = `700 ${Math.round(18 * dpr)}px system-ui, sans-serif`;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  for (let hour = 1; hour <= 12; hour++) {
    const angle = hour * Math.PI / 6;
    const [x, y] = polar(cx, cy, angle, r * 0.72);
    ctx.fillText(String(hour), x, y);
  }

  const sec = now.getSeconds() + now.getMilliseconds() / 1000;
  const min = now.getMinutes() + sec / 60;
  const hour = (now.getHours() % 12) + min / 60;

  function hand(angle, length, width, color, back = 0) {
    const [x2, y2] = polar(cx, cy, angle, r * length);
    const [x1, y1] = polar(cx, cy, angle + Math.PI, r * back);
    ctx.strokeStyle = color;
    ctx.lineWidth = width * dpr;
    ctx.beginPath();
    ctx.moveTo(x1, y1);
    ctx.lineTo(x2, y2);
    ctx.stroke();
  }

  hand(hour * Math.PI / 6, 0.48, 8, colors.cream);
  hand(min * Math.PI / 30, 0.69, 5, colors.green);
  hand(sec * Math.PI / 30, 0.80, 2, colors.orange, 0.15);

  ctx.fillStyle = colors.orange;
  ctx.beginPath();
  ctx.arc(cx, cy, 6 * dpr, 0, Math.PI * 2);
  ctx.fill();
}

function updateDigital(now) {
  const hh = String(now.getHours()).padStart(2, '0');
  const mm = String(now.getMinutes()).padStart(2, '0');
  timeEl.textContent = `${hh}:${mm}`;
  dateEl.textContent = `${days[now.getDay()]} ${now.getDate()} ${months[now.getMonth()]} ${now.getFullYear()}`;
}

let lastMinute = -1;
function frame() {
  const now = new Date();
  drawClock(now);
  if (now.getMinutes() !== lastMinute) {
    updateDigital(now);
    lastMinute = now.getMinutes();
  }
  requestAnimationFrame(frame);
}

window.addEventListener('resize', resizeCanvas);
requestAnimationFrame(frame);
