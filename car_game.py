"""
Car Dodge Game - 2 Player + Leaderboard + Sound (Streamlit Cloud compatible)
=============================================================================
Runs entirely in the browser via HTML5 Canvas + JavaScript, embedded into a
Streamlit page with components.html. No pygame, so it works on Streamlit
Community Cloud's headless servers.

Features:
  - 2-player local split-screen (same keyboard, two control sets)
  - Synthesized car engine hum + crash sound via the Web Audio API
    (no external audio files needed)
  - Leaderboard stored in the browser's localStorage (per-browser/device).
    NOTE: this is a *local* leaderboard, not shared across different users'
    browsers. See game.txt for how a shared/global leaderboard could be
    added later (would need a small backend/database).

Run locally:
    pip install streamlit
    streamlit run car_game.py
"""

import streamlit as st
import streamlit.components.v1 as components
import qrcode
from io import BytesIO

st.set_page_config(page_title="Car Dodge Game - 2 Player", page_icon="🚗", layout="wide")

st.title("🚗🚙 Car Dodge Game — 2 Player")
st.caption("Race side by side, dodge traffic, and climb the leaderboard!")

# ---------------------------------------------------------------------------
# QR code: lets a player scan and open this game on their phone
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("📱 Play on your phone")
    st.write("Paste this app's live URL below to get a scannable QR code.")
    app_url = st.text_input(
        "App URL",
        placeholder="https://your-app-name.streamlit.app",
        help="Copy this from your browser's address bar once the app is deployed "
             "(or use your local network address, e.g. http://192.168.1.23:8501, "
             "to test on a phone on the same Wi-Fi).",
    )
    if app_url.strip():
        qr = qrcode.QRCode(border=2, box_size=8)
        qr.add_data(app_url.strip())
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buf = BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        st.image(buf, caption="Scan with your phone's camera", use_container_width=True)
        st.download_button(
            "⬇️ Download QR code",
            data=buf.getvalue(),
            file_name="car_game_qr.png",
            mime="image/png",
        )
    else:
        st.caption("Enter a URL above to generate the QR code.")

GAME_HTML = r"""
<div id="wrap" style="font-family: sans-serif; color: #eee;">

  <div id="setup" style="display:flex; gap:20px; justify-content:center; align-items:flex-end; flex-wrap:wrap; margin-bottom:14px;">
    <div>
      <label style="color:#7CFC9A; font-weight:bold;">Player 1 name (WASD)</label><br>
      <input id="p1name" type="text" placeholder="Player 1"
             style="padding:6px 10px; border-radius:6px; border:1px solid #555; width:220px;">
    </div>
    <div>
      <label style="color:#FFB347; font-weight:bold;">Player 2 name (Arrow keys)</label><br>
      <input id="p2name" type="text" placeholder="Player 2"
             style="padding:6px 10px; border-radius:6px; border:1px solid #555; width:220px;">
    </div>
    <div>
      <label style="color:#eee; font-weight:bold;">Score to win</label><br>
      <input id="winScoreInput" type="number" min="10" step="10" value="300"
             style="padding:6px 10px; border-radius:6px; border:1px solid #555; width:100px;">
    </div>
    <button id="btnStart" style="padding:9px 22px; font-size:16px; font-weight:bold; border-radius:8px; border:none; background:#3c82dc; color:white; cursor:pointer;">
      ▶ Start Race
    </button>
    <button id="btnPause" style="padding:9px 22px; font-size:16px; border-radius:8px; border:none; background:#555; color:white; cursor:pointer;">
      ⏸ Pause
    </button>
    <button id="btnMute" style="padding:9px 22px; font-size:16px; border-radius:8px; border:none; background:#555; color:white; cursor:pointer;">
      🔊 Sound On
    </button>
  </div>

  <div id="canvases" style="display:flex; gap:16px; justify-content:center; flex-wrap:wrap;">
    <div style="text-align:center;">
      <div id="p1label" style="color:#7CFC9A; font-weight:bold; margin-bottom:4px;">Player 1</div>
      <canvas id="canvas1" width="340" height="600"
              style="background:#3c3c3c; border:3px solid #7CFC9A; border-radius:8px;"></canvas>
    </div>
    <div style="text-align:center;">
      <div id="p2label" style="color:#FFB347; font-weight:bold; margin-bottom:4px;">Player 2</div>
      <canvas id="canvas2" width="340" height="600"
              style="background:#3c3c3c; border:3px solid #FFB347; border-radius:8px;"></canvas>
    </div>
  </div>

  <p style="text-align:center; color:#aaa; font-size:13px; margin-top:10px;">
    Player 1: A / D to steer, W / S for gas / brake &nbsp;&nbsp;|&nbsp;&nbsp;
    Player 2: ◀ / ▶ to steer, ▲ / ▼ for gas / brake &nbsp;&nbsp;|&nbsp;&nbsp;
    Space: pause &nbsp;&nbsp;|&nbsp;&nbsp; Enter: restart after race ends
  </p>

  <div id="leaderboardBox" style="max-width:520px; margin:20px auto 0 auto; background:#2a2a2a; border-radius:10px; padding:14px 18px;">
    <div style="display:flex; justify-content:space-between; align-items:center;">
      <h3 style="margin:0; color:#fff;">🏆 Leaderboard (this browser)</h3>
      <button id="btnClearBoard" style="padding:4px 10px; font-size:12px; border-radius:6px; border:none; background:#772222; color:white; cursor:pointer;">
        Clear
      </button>
    </div>
    <table id="lbTable" style="width:100%; margin-top:10px; border-collapse:collapse; color:#eee; font-size:14px;">
      <thead>
        <tr style="border-bottom:1px solid #555; text-align:left;">
          <th style="padding:4px;">#</th>
          <th style="padding:4px;">Name</th>
          <th style="padding:4px;">Score</th>
          <th style="padding:4px;">Date</th>
        </tr>
      </thead>
      <tbody id="lbBody"></tbody>
    </table>
    <p id="lbEmpty" style="color:#888; font-size:13px; display:none;">No scores yet — finish a race to set one!</p>
  </div>
</div>

<script>
// ---------------------------------------------------------------------
// Shared constants / helpers
// ---------------------------------------------------------------------
const COLORS = {
  white: "#f5f5f5", black: "#141414", gray: "#3c3c3c",
  lightGray: "#6e6e6e", yellow: "#f0c828"
};
const OBSTACLE_COLORS = ["#dc3c3c", "#3cc864", "#f0c828", "#c864dc", "#3cb0dc"];
const LB_KEY = "car_dodge_leaderboard_v1";

function roundRectPath(ctx, x, y, w, h, r) {
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.arcTo(x + w, y, x + w, y + h, r);
  ctx.arcTo(x + w, y + h, x, y + h, r);
  ctx.arcTo(x, y + h, x, y, r);
  ctx.arcTo(x, y, x + w, y, r);
  ctx.closePath();
}

function rectsCollide(a, b) {
  return a.x < b.x + b.w && a.x + a.w > b.x && a.y < b.y + b.h && a.y + a.h > b.y;
}

// ---------------------------------------------------------------------
// Audio engine (synthesized - no files needed)
// ---------------------------------------------------------------------
let audioCtx = null;
let soundOn = true;

function ensureAudio() {
  if (!audioCtx) {
    audioCtx = new (window.AudioContext || window.webkitAudioContext)();
  }
  if (audioCtx.state === "suspended") audioCtx.resume();
}

class EngineSound {
  constructor() {
    this.osc = null;
    this.gain = null;
    this.filter = null;
  }
  start() {
    if (!audioCtx || this.osc) return;
    this.osc = audioCtx.createOscillator();
    this.osc.type = "sawtooth";
    this.gain = audioCtx.createGain();
    this.filter = audioCtx.createBiquadFilter();
    this.filter.type = "lowpass";
    this.filter.frequency.value = 400;
    this.gain.gain.value = soundOn ? 0.05 : 0.0;
    this.osc.frequency.value = 60;
    this.osc.connect(this.filter);
    this.filter.connect(this.gain);
    this.gain.connect(audioCtx.destination);
    this.osc.start();
  }
  update(speed, running) {
    if (!this.osc) return;
    const targetFreq = 45 + speed * 9;
    this.osc.frequency.setTargetAtTime(targetFreq, audioCtx.currentTime, 0.05);
    const targetGain = (running && soundOn) ? (0.035 + speed * 0.004) : 0.0;
    this.gain.gain.setTargetAtTime(Math.min(targetGain, 0.09), audioCtx.currentTime, 0.08);
  }
  stop() {
    if (!this.osc) return;
    try { this.osc.stop(); } catch (e) {}
    this.osc.disconnect();
    this.osc = null;
  }
}

function playCrash() {
  if (!audioCtx || !soundOn) return;
  const bufferSize = audioCtx.sampleRate * 0.35;
  const buffer = audioCtx.createBuffer(1, bufferSize, audioCtx.sampleRate);
  const data = buffer.getChannelData(0);
  for (let i = 0; i < bufferSize; i++) {
    data[i] = (Math.random() * 2 - 1) * (1 - i / bufferSize);
  }
  const noise = audioCtx.createBufferSource();
  noise.buffer = buffer;
  const filter = audioCtx.createBiquadFilter();
  filter.type = "lowpass";
  filter.frequency.value = 900;
  const gain = audioCtx.createGain();
  gain.gain.value = 0.35;
  noise.connect(filter);
  filter.connect(gain);
  gain.connect(audioCtx.destination);
  noise.start();

  const thud = audioCtx.createOscillator();
  const thudGain = audioCtx.createGain();
  thud.type = "square";
  thud.frequency.value = 90;
  thudGain.gain.value = 0.25;
  thud.connect(thudGain);
  thudGain.connect(audioCtx.destination);
  thud.start();
  thudGain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.3);
  thud.stop(audioCtx.currentTime + 0.32);
}

function playWin() {
  if (!audioCtx || !soundOn) return;
  const notes = [523.25, 659.25, 783.99, 1046.5]; // C5 E5 G5 C6
  notes.forEach((freq, i) => {
    const o = audioCtx.createOscillator();
    const g = audioCtx.createGain();
    o.type = "triangle";
    o.frequency.value = freq;
    g.gain.value = 0.0001;
    o.connect(g);
    g.connect(audioCtx.destination);
    const startTime = audioCtx.currentTime + i * 0.14;
    o.start(startTime);
    g.gain.setValueAtTime(0.0001, startTime);
    g.gain.exponentialRampToValueAtTime(0.12, startTime + 0.03);
    g.gain.exponentialRampToValueAtTime(0.0001, startTime + 0.35);
    o.stop(startTime + 0.4);
  });
}

function playHonk() {
  if (!audioCtx || !soundOn) return;
  const o = audioCtx.createOscillator();
  const g = audioCtx.createGain();
  o.type = "square";
  o.frequency.value = 320;
  g.gain.value = 0.06;
  o.connect(g);
  g.connect(audioCtx.destination);
  o.start();
  g.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.15);
  o.stop(audioCtx.currentTime + 0.16);
}

// ---------------------------------------------------------------------
// Game entities
// ---------------------------------------------------------------------
class Car {
  constructor(field, color) {
    this.field = field;
    this.width = 40;
    this.height = 72;
    this.lane = Math.floor(field.laneCount / 2);
    this.x = this.laneX(this.lane);
    this.y = field.height - this.height - 26;
    this.speedX = 6;
    this.color = color;
  }
  laneX(lane) {
    const f = this.field;
    const center = f.roadX + lane * f.laneWidth + f.laneWidth / 2;
    return center - this.width / 2;
  }
  moveLeft() { this.x = Math.max(this.field.roadX + 4, this.x - this.speedX); }
  moveRight() { this.x = Math.min(this.field.roadX + this.field.roadWidth - this.width - 4, this.x + this.speedX); }
  rect() { return { x: this.x, y: this.y, w: this.width, h: this.height }; }
  draw(ctx) { drawCarBody(ctx, this.rect(), this.color); }
}

class Obstacle {
  constructor(field, speed) {
    this.field = field;
    this.width = 40;
    this.height = 72;
    const lane = Math.floor(Math.random() * field.laneCount);
    const center = field.roadX + lane * field.laneWidth + field.laneWidth / 2;
    this.x = center - this.width / 2;
    this.y = -this.height;
    this.speed = speed;
    this.color = OBSTACLE_COLORS[Math.floor(Math.random() * OBSTACLE_COLORS.length)];
  }
  update() { this.y += this.speed; }
  rect() { return { x: this.x, y: this.y, w: this.width, h: this.height }; }
  offScreen() { return this.y > this.field.height; }
  draw(ctx) { drawCarBody(ctx, this.rect(), this.color); }
}

function drawCarBody(ctx, r, color) {
  ctx.fillStyle = color;
  roundRectPath(ctx, r.x, r.y, r.w, r.h, 9);
  ctx.fill();
  ctx.fillStyle = COLORS.white;
  roundRectPath(ctx, r.x + 5, r.y + 9, r.w - 10, 16, 4); ctx.fill();
  roundRectPath(ctx, r.x + 5, r.y + r.h - 25, r.w - 10, 16, 4); ctx.fill();
  ctx.fillStyle = COLORS.black;
  ctx.fillRect(r.x - 4, r.y + 7, 6, 16);
  ctx.fillRect(r.x + r.w - 2, r.y + 7, 6, 16);
  ctx.fillRect(r.x - 4, r.y + r.h - 23, 6, 16);
  ctx.fillRect(r.x + r.w - 2, r.y + r.h - 23, 6, 16);
}

// ---------------------------------------------------------------------
// Per-player game session
// ---------------------------------------------------------------------
class PlayerGame {
  constructor(canvasId, playerName, colorMain, controls) {
    this.canvas = document.getElementById(canvasId);
    this.ctx = this.canvas.getContext("2d");
    this.width = this.canvas.width;
    this.height = this.canvas.height;
    this.roadWidth = Math.floor(this.width * 0.78);
    this.roadX = (this.width - this.roadWidth) / 2;
    this.laneCount = 3;
    this.laneWidth = this.roadWidth / this.laneCount;
    this.colorMain = colorMain;
    this.name = playerName;
    this.controls = controls; // {left, right, up, down}
    this.engineSound = new EngineSound();
    this.reset();
  }

  reset() {
    this.car = new Car(this, this.colorMain);
    this.obstacles = [];
    this.score = 0;
    this.baseSpeed = 5;
    this.spawnTimer = 0;
    this.spawnInterval = 55;
    this.gameOver = false;
    this.roadScroll = 0;
    this.crashSoundPlayed = false;
  }

  update(keysDown, running, paused) {
    if (!running || paused) return;
    if (this.gameOver || raceOver) return;

    if (keysDown[this.controls.left]) this.car.moveLeft();
    if (keysDown[this.controls.right]) this.car.moveRight();
    if (keysDown[this.controls.up]) this.baseSpeed = Math.min(this.baseSpeed + 0.04, 14);
    if (keysDown[this.controls.down]) this.baseSpeed = Math.max(this.baseSpeed - 0.04, 3);

    this.spawnTimer++;
    if (this.spawnTimer >= this.spawnInterval) {
      this.spawnTimer = 0;
      this.obstacles.push(new Obstacle(this, this.baseSpeed + Math.random() * 2));
      this.spawnInterval = Math.max(20, this.spawnInterval - 0.5);
    }

    this.obstacles.forEach(o => o.update());
    this.obstacles = this.obstacles.filter(o => !o.offScreen());

    const carRect = this.car.rect();
    for (const o of this.obstacles) {
      if (rectsCollide(carRect, o.rect())) {
        this.gameOver = true;
      }
    }

    this.score += this.baseSpeed * 0.05;
    this.roadScroll = (this.roadScroll + this.baseSpeed) % 40;

    this.engineSound.update(this.baseSpeed, !this.gameOver);
    if (this.gameOver && !this.crashSoundPlayed) {
      playCrash();
      this.crashSoundPlayed = true;
      this.engineSound.update(0, false);
    }
  }

  drawRoad() {
    const ctx = this.ctx;
    ctx.fillStyle = COLORS.gray;
    ctx.fillRect(0, 0, this.width, this.height);
    ctx.fillStyle = COLORS.lightGray;
    ctx.fillRect(this.roadX, 0, this.roadWidth, this.height);

    ctx.fillStyle = COLORS.yellow;
    for (let lane = 1; lane < this.laneCount; lane++) {
      const x = this.roadX + lane * this.laneWidth;
      let y = -40 + this.roadScroll;
      while (y < this.height) {
        ctx.fillRect(x - 3, y, 6, 22);
        y += 40;
      }
    }
    ctx.fillStyle = COLORS.white;
    ctx.fillRect(this.roadX - 5, 0, 5, this.height);
    ctx.fillRect(this.roadX + this.roadWidth, 0, 5, this.height);
  }

  drawHUD() {
    const ctx = this.ctx;
    ctx.fillStyle = COLORS.white;
    ctx.font = "bold 15px sans-serif";
    ctx.textAlign = "left";
    ctx.fillText("Score: " + Math.floor(this.score) + " / " + winScore, 8, 20);
    ctx.fillText("Speed: " + this.baseSpeed.toFixed(1), 8, 40);

    if (raceOver) {
      const won = this.name === winnerName;
      ctx.fillStyle = won ? "rgba(30,90,30,0.75)" : "rgba(0,0,0,0.65)";
      ctx.fillRect(0, 0, this.width, this.height);
      ctx.fillStyle = COLORS.white;
      ctx.textAlign = "center";
      ctx.font = "bold 24px sans-serif";
      ctx.fillText(won ? "🏆 YOU WIN! 🏆" : "You lose", this.width / 2, this.height / 2 - 20);
      ctx.font = "bold 16px sans-serif";
      ctx.fillText(winnerName + " reached " + winScore + "!", this.width / 2, this.height / 2 + 6);
      ctx.font = "bold 18px sans-serif";
      ctx.fillText("Score: " + Math.floor(this.score), this.width / 2, this.height / 2 + 34);
    } else if (this.gameOver) {
      ctx.fillStyle = "rgba(0,0,0,0.65)";
      ctx.fillRect(0, 0, this.width, this.height);
      ctx.fillStyle = COLORS.white;
      ctx.textAlign = "center";
      ctx.font = "bold 26px sans-serif";
      ctx.fillText("CRASHED!", this.width / 2, this.height / 2 - 20);
      ctx.font = "bold 18px sans-serif";
      ctx.fillText("Score: " + Math.floor(this.score), this.width / 2, this.height / 2 + 14);
    }
  }

  draw() {
    this.drawRoad();
    this.car.draw(this.ctx);
    this.obstacles.forEach(o => o.draw(this.ctx));
    this.drawHUD();
  }
}

// ---------------------------------------------------------------------
// Leaderboard (localStorage - per browser)
// ---------------------------------------------------------------------
function loadLeaderboard() {
  try {
    const raw = localStorage.getItem(LB_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch (e) { return []; }
}

function saveLeaderboard(list) {
  try { localStorage.setItem(LB_KEY, JSON.stringify(list)); } catch (e) {}
}

function addScore(name, score) {
  const list = loadLeaderboard();
  list.push({
    name: name || "Player",
    score: Math.floor(score),
    date: new Date().toLocaleDateString()
  });
  list.sort((a, b) => b.score - a.score);
  saveLeaderboard(list.slice(0, 10));
  renderLeaderboard();
}

function renderLeaderboard() {
  const list = loadLeaderboard();
  const body = document.getElementById("lbBody");
  const empty = document.getElementById("lbEmpty");
  body.innerHTML = "";
  if (list.length === 0) {
    empty.style.display = "block";
    return;
  }
  empty.style.display = "none";
  list.forEach((entry, i) => {
    const tr = document.createElement("tr");
    tr.style.borderBottom = "1px solid #3a3a3a";
    tr.innerHTML =
      "<td style='padding:4px;'>" + (i + 1) + "</td>" +
      "<td style='padding:4px;'>" + escapeHtml(entry.name) + "</td>" +
      "<td style='padding:4px;'>" + entry.score + "</td>" +
      "<td style='padding:4px; color:#999;'>" + entry.date + "</td>";
    body.appendChild(tr);
  });
}

function escapeHtml(s) {
  const div = document.createElement("div");
  div.innerText = s;
  return div.innerHTML;
}

// ---------------------------------------------------------------------
// Main controller
// ---------------------------------------------------------------------
let p1, p2;
let running = false;
let paused = false;
let keysDown = {};
let scoresRecorded = false;
let winScore = 300;
let raceOver = false;
let winnerName = null;

function initPlayers() {
  const p1Name = document.getElementById("p1name").value.trim() || "Player 1";
  const p2Name = document.getElementById("p2name").value.trim() || "Player 2";
  p1 = new PlayerGame("canvas1", p1Name, "#3cc864", { left: "a", right: "d", up: "w", down: "s" });
  p2 = new PlayerGame("canvas2", p2Name, "#ffa93c", { left: "ArrowLeft", right: "ArrowRight", up: "ArrowUp", down: "ArrowDown" });
  document.getElementById("p1label").innerText = p1Name;
  document.getElementById("p2label").innerText = p2Name;
  scoresRecorded = false;
  raceOver = false;
  winnerName = null;
}

function startRace() {
  ensureAudio();
  const inputVal = parseInt(document.getElementById("winScoreInput").value, 10);
  winScore = (!isNaN(inputVal) && inputVal > 0) ? inputVal : 300;
  initPlayers();
  p1.engineSound.start();
  p2.engineSound.start();
  running = true;
  paused = false;
}

function checkWinCondition() {
  if (raceOver || !p1 || !p2) return;
  const p1Wins = p1.score >= winScore && !p1.gameOver;
  const p2Wins = p2.score >= winScore && !p2.gameOver;
  if (p1Wins || p2Wins) {
    // if both cross the line the same frame, higher score wins
    winnerName = (p1Wins && p2Wins) ? (p1.score >= p2.score ? p1.name : p2.name)
                 : (p1Wins ? p1.name : p2.name);
    raceOver = true;
    p1.engineSound.update(0, false);
    p2.engineSound.update(0, false);
    playWin();
  }
}

function isRaceDecided() {
  return raceOver || (p1 && p2 && p1.gameOver && p2.gameOver);
}

function maybeRecordScores() {
  if (!p1 || !p2) return;
  if (isRaceDecided() && !scoresRecorded) {
    addScore(p1.name, p1.score);
    addScore(p2.name, p2.score);
    scoresRecorded = true;
  }
}

function loop() {
  if (running) {
    p1.update(keysDown, running, paused);
    p2.update(keysDown, running, paused);
    if (!paused) checkWinCondition();
    maybeRecordScores();
  }
  if (p1) p1.draw();
  if (p2) p2.draw();
  requestAnimationFrame(loop);
}

// draw placeholder state before first start
function drawPlaceholder(canvasId, text) {
  const c = document.getElementById(canvasId);
  const ctx = c.getContext("2d");
  ctx.fillStyle = COLORS.gray;
  ctx.fillRect(0, 0, c.width, c.height);
  ctx.fillStyle = "#aaa";
  ctx.font = "bold 16px sans-serif";
  ctx.textAlign = "center";
  ctx.fillText(text, c.width / 2, c.height / 2);
}
drawPlaceholder("canvas1", "Press Start Race to begin");
drawPlaceholder("canvas2", "Press Start Race to begin");

// ---------------------------------------------------------------------
// Input
// ---------------------------------------------------------------------
function isTypingInField(e) {
  const tag = e.target.tagName;
  return tag === "INPUT" || tag === "TEXTAREA";
}

window.addEventListener("keydown", (e) => {
  if (isTypingInField(e)) return; // let the name boxes accept every key normally

  keysDown[e.key] = true;
  if (e.key === " ") { paused = !paused; e.preventDefault(); }
  if (e.key === "Enter" && p1 && p2 && isRaceDecided()) {
    initPlayers();
    p1.engineSound.start();
    p2.engineSound.start();
    running = true;
    paused = false;
  }
  if (["ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown", "w", "a", "s", "d"].includes(e.key)) {
    e.preventDefault();
  }
});
window.addEventListener("keyup", (e) => {
  if (isTypingInField(e)) return;
  keysDown[e.key] = false;
});

document.getElementById("btnStart").addEventListener("click", startRace);
document.getElementById("btnPause").addEventListener("click", () => {
  if (running) paused = !paused;
});
document.getElementById("btnMute").addEventListener("click", (e) => {
  soundOn = !soundOn;
  e.target.innerText = soundOn ? "🔊 Sound On" : "🔇 Sound Off";
});
document.getElementById("btnClearBoard").addEventListener("click", () => {
  saveLeaderboard([]);
  renderLeaderboard();
});

renderLeaderboard();
loop();
</script>
"""

components.html(GAME_HTML, height=1150, scrolling=True)

st.info(
    "💡 Tip: set **Score to win** before clicking **Start Race** (this also "
    "enables sound — browsers require a click before audio can play). "
    "First player to reach that score wins instantly; if both crash before "
    "anyone reaches it, whoever had the higher score is recorded as the "
    "winner. Scores for both players are saved to the leaderboard "
    "automatically once the race ends."
)

with st.expander("About the leaderboard"):
    st.write(
        "The leaderboard is stored in your browser's local storage, so it's "
        "specific to this browser/device and won't be shared with other "
        "visitors to your deployed app. See `game.txt` for notes on adding "
        "a real shared/global leaderboard with a small database backend."
    )
