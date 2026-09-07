"""
Car Dodge Game - Desktop 2P + Mobile Portrait Cross-Device Multiplayer
=========================================================================
Runs entirely in the browser via HTML5 Canvas + JavaScript, embedded into a
Streamlit page with components.html. No pygame, so it works on Streamlit
Community Cloud's headless servers.

Layouts:
  - DESKTOP / wide screens: the original same-keyboard 2-player split
    screen (Player 1: A/D/W/S, Player 2: arrow keys), landscape-style
    side-by-side canvases.
  - MOBILE / narrow screens (phones): a single, full-width PORTRAIT
    canvas. One player per phone. To play against someone else, a
    second player opens the same app on their own phone and joins your
    "room" using a short room code — the two phones connect directly
    to each other over WebRTC (peer-to-peer) using PeerJS's free public
    broker, so no backend server needs to be hosted for this project.
    Swipe left/right to steer, swipe up/down to speed up/slow down.

Notes on the cross-device multiplayer:
  - Uses the free public PeerJS broker only to help two browsers find
    each other; actual gameplay data travels directly device-to-device.
  - Both phones need an internet connection. Very restrictive networks
    (some corporate/school Wi-Fi) can block the peer-to-peer connection.
  - Each phone keeps its own local leaderboard (browser localStorage),
    same as before — this project has no shared server-side database.

Run locally:
    pip install streamlit
    streamlit run car_game.py
"""

import streamlit as st
import streamlit.components.v1 as components
import html as html_lib

st.set_page_config(page_title="Car Dodge Game", page_icon="🚗", layout="wide")

st.title("🚗🚙 Car Dodge Game")
st.caption("Desktop: 2 players, one keyboard. Mobile: swipe to play, and race a friend on another phone!")

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
        safe_url = html_lib.escape(app_url.strip())
        qr_html = f"""
        <div style="text-align:center; font-family:sans-serif;">
          <div id="qr" style="display:inline-block; padding:10px; background:white; border-radius:8px;"></div>
          <br>
          <button id="dl" style="margin-top:10px; padding:6px 14px; border-radius:6px; border:none;
                   background:#3c82dc; color:white; cursor:pointer; font-size:13px;">
            ⬇️ Download QR code
          </button>
        </div>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/qrcodejs/1.0.0/qrcode.min.js"></script>
        <script>
          const qrDiv = document.getElementById("qr");
          new QRCode(qrDiv, {{
            text: "{safe_url}",
            width: 200,
            height: 200,
            colorDark: "#000000",
            colorLight: "#ffffff"
          }});
          document.getElementById("dl").addEventListener("click", () => {{
            const canvas = qrDiv.querySelector("canvas");
            if (!canvas) return;
            const link = document.createElement("a");
            link.download = "car_game_qr.png";
            link.href = canvas.toDataURL("image/png");
            link.click();
          }});
        </script>
        """
        components.html(qr_html, height=300)
        st.caption("Scan with your phone's camera app to open the game.")
    else:
        st.caption("Enter a URL above to generate the QR code.")

    st.divider()
    st.caption(
        "On a phone, two players race by BOTH opening this app and using the "
        "'Room code' box in the mobile view — one taps Create, the other taps "
        "Join with that code."
    )

GAME_HTML = r"""
<div id="wrap" style="font-family: sans-serif; color: #eee;">

  <!-- =================================================================
       DESKTOP LAYOUT (wide screens): same-keyboard 2-player split screen
  ================================================================== -->
  <div id="desktopUI">
    <div style="display:flex; gap:20px; justify-content:center; align-items:flex-end; flex-wrap:wrap; margin-bottom:14px;">
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

    <div style="display:flex; gap:16px; justify-content:center; flex-wrap:wrap;">
      <div style="text-align:center;">
        <div id="p1label" style="color:#7CFC9A; font-weight:bold; margin-bottom:4px;">Player 1</div>
        <canvas id="canvas1" width="340" height="600"
                style="background:#3c3c3c; border:3px solid #7CFC9A; border-radius:8px; touch-action:none;"></canvas>
      </div>
      <div style="text-align:center;">
        <div id="p2label" style="color:#FFB347; font-weight:bold; margin-bottom:4px;">Player 2</div>
        <canvas id="canvas2" width="340" height="600"
                style="background:#3c3c3c; border:3px solid #FFB347; border-radius:8px; touch-action:none;"></canvas>
      </div>
    </div>

    <p style="text-align:center; color:#aaa; font-size:13px; margin-top:10px;">
      Player 1: A / D to steer, W / S for gas / brake &nbsp;&nbsp;|&nbsp;&nbsp;
      Player 2: ◀ / ▶ to steer, ▲ / ▼ for gas / brake &nbsp;&nbsp;|&nbsp;&nbsp;
      Space: pause &nbsp;&nbsp;|&nbsp;&nbsp; Enter: restart after race ends
    </p>
  </div>

  <!-- =================================================================
       MOBILE LAYOUT (narrow screens): single portrait canvas,
       optional cross-device opponent over PeerJS
  ================================================================== -->
  <div id="mobileUI" style="display:none;">
    <div id="mobileSetup" style="max-width:380px; margin:0 auto 14px auto;">
      <label style="color:#eee; font-weight:bold; font-size:14px;">Your name</label>
      <input id="mName" type="text" placeholder="Your name"
             style="display:block; width:100%; box-sizing:border-box; margin-top:4px; margin-bottom:10px;
                    padding:8px 10px; border-radius:6px; border:1px solid #555; font-size:15px;">

      <label style="color:#eee; font-weight:bold; font-size:14px;">Score to win (if you host)</label>
      <input id="mWinScore" type="number" min="10" step="10" value="300"
             style="display:block; width:100%; box-sizing:border-box; margin-top:4px; margin-bottom:10px;
                    padding:8px 10px; border-radius:6px; border:1px solid #555; font-size:15px;">

      <div style="display:flex; gap:8px; margin-bottom:8px;">
        <button id="mBtnCreate" style="flex:1; padding:10px; font-size:14px; font-weight:bold; border-radius:8px; border:none; background:#3c82dc; color:white; cursor:pointer;">
          🆕 Create Room
        </button>
        <button id="mBtnSolo" style="flex:1; padding:10px; font-size:14px; border-radius:8px; border:none; background:#555; color:white; cursor:pointer;">
          🙋 Play Solo
        </button>
      </div>
      <div style="display:flex; gap:8px; margin-bottom:10px;">
        <input id="mRoomCode" type="text" placeholder="Room code" maxlength="6"
               style="flex:1; padding:10px; border-radius:8px; border:1px solid #555; font-size:15px; text-transform:uppercase;">
        <button id="mBtnJoin" style="padding:10px 16px; font-size:14px; border-radius:8px; border:none; background:#3cc864; color:white; cursor:pointer;">
          🔗 Join
        </button>
      </div>

      <div id="mStatus" style="text-align:center; color:#ccc; font-size:13px; min-height:18px; margin-bottom:6px;"></div>

      <div style="display:flex; gap:8px; justify-content:center;">
        <button id="mBtnStart" style="display:none; padding:10px 20px; font-size:15px; font-weight:bold; border-radius:8px; border:none; background:#3c82dc; color:white; cursor:pointer;">
          ▶ Start Race
        </button>
        <button id="mBtnPause" style="padding:8px 16px; font-size:14px; border-radius:8px; border:none; background:#555; color:white; cursor:pointer;">
          ⏸ Pause
        </button>
        <button id="mBtnMute" style="padding:8px 16px; font-size:14px; border-radius:8px; border:none; background:#555; color:white; cursor:pointer;">
          🔊
        </button>
      </div>
    </div>

    <div id="mOpponentBar" style="display:none; max-width:340px; margin:0 auto 8px auto; background:#2a2a2a; border-radius:8px;
                padding:8px 12px; text-align:center; font-size:13px; color:#ffb347;">
      <span id="mOppText">Opponent: —</span>
    </div>

    <div style="text-align:center;">
      <div id="mLabel" style="color:#7CFC9A; font-weight:bold; margin-bottom:4px;">You</div>
      <canvas id="canvasM" width="340" height="600"
              style="background:#3c3c3c; border:3px solid #7CFC9A; border-radius:8px; max-width:96vw; height:auto; touch-action:none;"></canvas>
    </div>

    <p style="text-align:center; color:#aaa; font-size:13px; margin-top:10px;">
      Swipe ⬅️➡️ on your car's track to steer &nbsp;&nbsp;|&nbsp;&nbsp; Swipe ⬆️⬇️ to speed up / slow down
    </p>
  </div>

  <div id="leaderboardBox" style="max-width:520px; margin:20px auto 0 auto; background:#2a2a2a; border-radius:10px; padding:14px 18px;">
    <div style="display:flex; justify-content:space-between; align-items:center;">
      <h3 style="margin:0; color:#fff;">🏆 Leaderboard (this device)</h3>
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

<script src="https://cdnjs.cloudflare.com/ajax/libs/peerjs/1.5.2/peerjs.min.js"></script>
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
  constructor() { this.osc = null; this.gain = null; this.filter = null; }
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
  for (let i = 0; i < bufferSize; i++) data[i] = (Math.random() * 2 - 1) * (1 - i / bufferSize);
  const noise = audioCtx.createBufferSource();
  noise.buffer = buffer;
  const filter = audioCtx.createBiquadFilter();
  filter.type = "lowpass";
  filter.frequency.value = 900;
  const gain = audioCtx.createGain();
  gain.gain.value = 0.35;
  noise.connect(filter); filter.connect(gain); gain.connect(audioCtx.destination);
  noise.start();

  const thud = audioCtx.createOscillator();
  const thudGain = audioCtx.createGain();
  thud.type = "square";
  thud.frequency.value = 90;
  thudGain.gain.value = 0.25;
  thud.connect(thudGain); thudGain.connect(audioCtx.destination);
  thud.start();
  thudGain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.3);
  thud.stop(audioCtx.currentTime + 0.32);
}

function playWin() {
  if (!audioCtx || !soundOn) return;
  const notes = [523.25, 659.25, 783.99, 1046.5];
  notes.forEach((freq, i) => {
    const o = audioCtx.createOscillator();
    const g = audioCtx.createGain();
    o.type = "triangle";
    o.frequency.value = freq;
    g.gain.value = 0.0001;
    o.connect(g); g.connect(audioCtx.destination);
    const startTime = audioCtx.currentTime + i * 0.14;
    o.start(startTime);
    g.gain.setValueAtTime(0.0001, startTime);
    g.gain.exponentialRampToValueAtTime(0.12, startTime + 0.03);
    g.gain.exponentialRampToValueAtTime(0.0001, startTime + 0.35);
    o.stop(startTime + 0.4);
  });
}

// ---------------------------------------------------------------------
// Game entities (shared by desktop and mobile)
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
// Per-player game session (used by BOTH desktop players and the mobile player)
// ---------------------------------------------------------------------
class PlayerGame {
  constructor(canvasId, playerName, colorMain, controls, winTarget) {
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
    this.controls = controls;
    this.winTarget = winTarget || 300;
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

  update(keysDown, running, paused, halted) {
    if (!running || paused) return;
    if (this.gameOver || halted) return;

    if (keysDown && keysDown[this.controls.left]) this.car.moveLeft();
    if (keysDown && keysDown[this.controls.right]) this.car.moveRight();
    if (keysDown && keysDown[this.controls.up]) this.baseSpeed = Math.min(this.baseSpeed + 0.04, 14);
    if (keysDown && keysDown[this.controls.down]) this.baseSpeed = Math.max(this.baseSpeed - 0.04, 3);

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
      if (rectsCollide(carRect, o.rect())) this.gameOver = true;
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
      while (y < this.height) { ctx.fillRect(x - 3, y, 6, 22); y += 40; }
    }
    ctx.fillStyle = COLORS.white;
    ctx.fillRect(this.roadX - 5, 0, 5, this.height);
    ctx.fillRect(this.roadX + this.roadWidth, 0, 5, this.height);
  }

  drawHUD(resultOverlay) {
    const ctx = this.ctx;
    ctx.fillStyle = COLORS.white;
    ctx.font = "bold 15px sans-serif";
    ctx.textAlign = "left";
    ctx.fillText("Score: " + Math.floor(this.score) + " / " + this.winTarget, 8, 20);
    ctx.fillText("Speed: " + this.baseSpeed.toFixed(1), 8, 40);

    if (resultOverlay) {
      const won = resultOverlay.won;
      ctx.fillStyle = won ? "rgba(30,90,30,0.75)" : "rgba(0,0,0,0.65)";
      ctx.fillRect(0, 0, this.width, this.height);
      ctx.fillStyle = COLORS.white;
      ctx.textAlign = "center";
      ctx.font = "bold 24px sans-serif";
      ctx.fillText(won ? "🏆 YOU WIN! 🏆" : "You lose", this.width / 2, this.height / 2 - 20);
      ctx.font = "bold 16px sans-serif";
      ctx.fillText(resultOverlay.line, this.width / 2, this.height / 2 + 6);
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

  draw(resultOverlay) {
    this.drawRoad();
    this.car.draw(this.ctx);
    this.obstacles.forEach(o => o.draw(this.ctx));
    this.drawHUD(resultOverlay);
  }
}

// ---------------------------------------------------------------------
// Leaderboard (localStorage - per device)
// ---------------------------------------------------------------------
function loadLeaderboard() {
  try { const raw = localStorage.getItem(LB_KEY); return raw ? JSON.parse(raw) : []; }
  catch (e) { return []; }
}
function saveLeaderboard(list) {
  try { localStorage.setItem(LB_KEY, JSON.stringify(list)); } catch (e) {}
}
function addScore(name, score) {
  const list = loadLeaderboard();
  list.push({ name: name || "Player", score: Math.floor(score), date: new Date().toLocaleDateString() });
  list.sort((a, b) => b.score - a.score);
  saveLeaderboard(list.slice(0, 10));
  renderLeaderboard();
}
function renderLeaderboard() {
  const list = loadLeaderboard();
  const body = document.getElementById("lbBody");
  const empty = document.getElementById("lbEmpty");
  body.innerHTML = "";
  if (list.length === 0) { empty.style.display = "block"; return; }
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
function escapeHtml(s) { const div = document.createElement("div"); div.innerText = s; return div.innerHTML; }

// ---------------------------------------------------------------------
// Layout detection: desktop split-screen vs mobile portrait
// ---------------------------------------------------------------------
let isMobile = window.matchMedia("(max-width: 700px)").matches;
let anyRaceRunning = false; // set true once either mode starts a race

function applyLayout() {
  document.getElementById("desktopUI").style.display = isMobile ? "none" : "block";
  document.getElementById("mobileUI").style.display = isMobile ? "block" : "none";
}
applyLayout();

window.addEventListener("resize", () => {
  if (anyRaceRunning) return; // don't yank the layout out from under an active race
  const nowMobile = window.matchMedia("(max-width: 700px)").matches;
  if (nowMobile !== isMobile) { isMobile = nowMobile; applyLayout(); }
});

// ---------------------------------------------------------------------
// Touch / swipe controls
// ---------------------------------------------------------------------
function addSwipeControls(canvas, getPlayer, getHalted) {
  const SWIPE_THRESHOLD = 28;
  let startX = null, startY = null;

  canvas.addEventListener("touchstart", (e) => {
    ensureAudio();
    const t = e.changedTouches[0];
    startX = t.clientX; startY = t.clientY;
    e.preventDefault();
  }, { passive: false });

  canvas.addEventListener("touchend", (e) => {
    if (startX === null) return;
    const player = getPlayer();
    if (player && !player.gameOver && !(getHalted && getHalted())) {
      const t = e.changedTouches[0];
      const dx = t.clientX - startX;
      const dy = t.clientY - startY;
      const absDx = Math.abs(dx), absDy = Math.abs(dy);
      if (absDx > absDy && absDx > SWIPE_THRESHOLD) {
        for (let i = 0; i < 5; i++) { if (dx > 0) player.car.moveRight(); else player.car.moveLeft(); }
      } else if (absDy > SWIPE_THRESHOLD) {
        if (dy < 0) player.baseSpeed = Math.min(player.baseSpeed + 1.2, 14);
        else player.baseSpeed = Math.max(player.baseSpeed - 1.2, 3);
      }
    }
    startX = null; startY = null;
    e.preventDefault();
  }, { passive: false });

  canvas.addEventListener("touchmove", (e) => { e.preventDefault(); }, { passive: false });
}

// =======================================================================
// DESKTOP CONTROLLER (2 players, same keyboard)
// =======================================================================
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
  p1 = new PlayerGame("canvas1", p1Name, "#3cc864", { left: "a", right: "d", up: "w", down: "s" }, winScore);
  p2 = new PlayerGame("canvas2", p2Name, "#ffa93c", { left: "ArrowLeft", right: "ArrowRight", up: "ArrowUp", down: "ArrowDown" }, winScore);
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
  anyRaceRunning = true;
}

function checkWinCondition() {
  if (raceOver || !p1 || !p2) return;
  const p1Wins = p1.score >= winScore && !p1.gameOver;
  const p2Wins = p2.score >= winScore && !p2.gameOver;
  if (p1Wins || p2Wins) {
    winnerName = (p1Wins && p2Wins) ? (p1.score >= p2.score ? p1.name : p2.name)
                 : (p1Wins ? p1.name : p2.name);
    raceOver = true;
    p1.engineSound.update(0, false);
    p2.engineSound.update(0, false);
    playWin();
  }
}

function isRaceDecided() { return raceOver || (p1 && p2 && p1.gameOver && p2.gameOver); }

function maybeRecordScores() {
  if (!p1 || !p2) return;
  if (isRaceDecided() && !scoresRecorded) {
    addScore(p1.name, p1.score);
    addScore(p2.name, p2.score);
    scoresRecorded = true;
    anyRaceRunning = false;
  }
}

function desktopLoop() {
  if (!isMobile && running) {
    p1.update(keysDown, running, paused, false);
    p2.update(keysDown, running, paused, false);
    if (!paused) checkWinCondition();
    maybeRecordScores();
  }
  if (!isMobile && p1 && p2) {
    const decided = isRaceDecided();
    p1.draw(decided ? { won: p1.name === winnerName, line: winnerName + " reached " + winScore + "!" } : null);
    p2.draw(decided ? { won: p2.name === winnerName, line: winnerName + " reached " + winScore + "!" } : null);
  }
}

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
drawPlaceholder("canvasM", "Create or join a room, or play solo");

function isTypingInField(e) {
  const tag = e.target.tagName;
  return tag === "INPUT" || tag === "TEXTAREA";
}

window.addEventListener("keydown", (e) => {
  if (isTypingInField(e)) return;
  keysDown[e.key] = true;
  if (e.key === " ") { paused = !paused; mPaused = !mPaused; e.preventDefault(); }
  if (e.key === "Enter" && !isMobile && p1 && p2 && isRaceDecided()) {
    initPlayers();
    p1.engineSound.start();
    p2.engineSound.start();
    running = true;
    paused = false;
    anyRaceRunning = true;
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
document.getElementById("btnPause").addEventListener("click", () => { if (running) paused = !paused; });
document.getElementById("btnMute").addEventListener("click", (e) => {
  soundOn = !soundOn;
  e.target.innerText = soundOn ? "🔊 Sound On" : "🔇 Sound Off";
  document.getElementById("mBtnMute").innerText = soundOn ? "🔊" : "🔇";
});
document.getElementById("btnClearBoard").addEventListener("click", () => { saveLeaderboard([]); renderLeaderboard(); });

addSwipeControls(document.getElementById("canvas1"), () => p1, () => raceOver);
addSwipeControls(document.getElementById("canvas2"), () => p2, () => raceOver);

// =======================================================================
// MOBILE CONTROLLER (1 phone = 1 player, optional remote opponent via PeerJS)
// =======================================================================
let pm = null;               // my PlayerGame instance
let mRunning = false;
let mPaused = false;
let mScoresRecorded = false;
let mRaceOver = false;
let mResult = null;          // { won: bool, line: string }
let myName = "Player";
let isHost = false;
let peer = null;
let conn = null;
let opponentConnected = false;
let opponent = { name: null, score: 0, baseSpeed: 0, gameOver: false, finished: false };
let pendingOpponentName = null;

function setStatus(text) { document.getElementById("mStatus").innerText = text; }

function roomIdFor(code) { return "cardodge-room-" + code; }

function randomRoomCode() {
  const chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"; // no ambiguous chars
  let code = "";
  for (let i = 0; i < 5; i++) code += chars[Math.floor(Math.random() * chars.length)];
  return code;
}

function wireConnection(c) {
  conn = c;
  conn.on("open", () => {
    opponentConnected = true;
    document.getElementById("mOpponentBar").style.display = "block";
    updateOpponentBar();
    conn.send({ type: "hello", name: myName, winScore: isHost ? currentMWinScore() : undefined });
    if (isHost) {
      setStatus("✅ Opponent connected! Tap Start Race when ready.");
      document.getElementById("mBtnStart").style.display = "inline-block";
    } else {
      setStatus("✅ Connected to host. Waiting for them to start...");
    }
  });
  conn.on("data", (data) => handlePeerData(data));
  conn.on("close", () => {
    opponentConnected = false;
    setStatus("⚠️ Opponent disconnected.");
  });
  conn.on("error", (err) => { setStatus("⚠️ Connection error."); });
}

function currentMWinScore() {
  const v = parseInt(document.getElementById("mWinScore").value, 10);
  return (!isNaN(v) && v > 0) ? v : 300;
}

function handlePeerData(data) {
  if (!data || !data.type) return;
  if (data.type === "hello") {
    opponent.name = data.name || "Opponent";
    if (!isHost && typeof data.winScore === "number") {
      document.getElementById("mWinScore").value = data.winScore;
    }
    updateOpponentBar();
  } else if (data.type === "start") {
    beginMobileRace(data.winScore, false);
  } else if (data.type === "state") {
    opponent.score = data.score;
    opponent.baseSpeed = data.baseSpeed;
    opponent.gameOver = data.gameOver;
    updateOpponentBar();
  } else if (data.type === "over") {
    finishMobileRace(data.winnerName === myName, data.winnerName, false);
  } else if (data.type === "restart") {
    beginMobileRace(data.winScore, false);
  }
}

function updateOpponentBar() {
  const el = document.getElementById("mOppText");
  if (!opponent.name) { el.innerText = "Opponent: connected"; return; }
  const state = opponent.gameOver ? "crashed" : "racing";
  el.innerText = "Opponent: " + opponent.name + " — score " + Math.floor(opponent.score) + " (" + state + ")";
}

function createRoom() {
  ensureAudio();
  myName = document.getElementById("mName").value.trim() || "Player 1";
  isHost = true;
  const code = randomRoomCode();
  document.getElementById("mRoomCode").value = code;
  setStatus("Setting up room...");
  peer = new Peer(roomIdFor(code));
  peer.on("open", () => {
    setStatus("🏠 Room code: " + code + " — share it with your friend. Waiting for them to join...");
  });
  peer.on("connection", (c) => wireConnection(c));
  peer.on("error", (err) => {
    setStatus("⚠️ Could not create room (try again, or Play Solo).");
  });
}

function joinRoom() {
  ensureAudio();
  myName = document.getElementById("mName").value.trim() || "Player 2";
  const code = document.getElementById("mRoomCode").value.trim().toUpperCase();
  if (!code) { setStatus("Enter a room code first."); return; }
  isHost = false;
  setStatus("Connecting to room " + code + "...");
  peer = new Peer();
  peer.on("open", () => {
    const c = peer.connect(roomIdFor(code));
    wireConnection(c);
  });
  peer.on("error", (err) => {
    setStatus("⚠️ Couldn't find that room. Check the code and try again.");
  });
}

function playSolo() {
  ensureAudio();
  myName = document.getElementById("mName").value.trim() || "Player";
  isHost = true;
  opponentConnected = false;
  document.getElementById("mOpponentBar").style.display = "none";
  beginMobileRace(currentMWinScore(), true);
}

function beginMobileRace(winTarget, isLocalStart) {
  const target = winTarget || currentMWinScore();
  pm = new PlayerGame("canvasM", myName, "#3cc864", { left: "ArrowLeft", right: "ArrowRight", up: "ArrowUp", down: "ArrowDown" }, target);
  document.getElementById("mLabel").innerText = myName;
  pm.engineSound.start();
  mRunning = true;
  mPaused = false;
  mRaceOver = false;
  mResult = null;
  mScoresRecorded = false;
  opponent.gameOver = false;
  opponent.finished = false;
  anyRaceRunning = true;
  document.getElementById("mBtnStart").style.display = "none";
  setStatus(opponentConnected ? "🏁 Racing against " + (opponent.name || "opponent") + "!" : "🏁 Solo run — beat your target score!");

  if (isLocalStart && isHost && conn && opponentConnected) {
    conn.send({ type: "start", winScore: target });
  }
}

let mLastSentAt = 0;
function mobileLoop() {
  if (isMobile && mRunning) {
    pm.update(null, mRunning, mPaused, mRaceOver);

    // periodically broadcast my state to the opponent
    const now = performance.now();
    if (conn && opponentConnected && now - mLastSentAt > 150) {
      mLastSentAt = now;
      conn.send({ type: "state", score: pm.score, baseSpeed: pm.baseSpeed, gameOver: pm.gameOver });
    }

    if (!mPaused && !mRaceOver) {
      // win-by-score
      if (pm.score >= pm.winTarget) {
        finishMobileRace(true, myName, true);
      }
      // both crashed (only meaningful with an opponent)
      else if (pm.gameOver && opponentConnected && opponent.gameOver) {
        const iWon = pm.score >= opponent.score;
        finishMobileRace(iWon, iWon ? myName : opponent.name, true);
      }
      // solo crash with no opponent = just end the run
      else if (pm.gameOver && !opponentConnected) {
        finishMobileRace(false, null, true, true);
      }
    }

    if (mRaceOver && !mScoresRecorded) {
      addScore(myName, pm.score);
      if (opponentConnected && opponent.name) addScore(opponent.name, opponent.score);
      mScoresRecorded = true;
      anyRaceRunning = false;
    }
  }
  if (isMobile && pm) {
    pm.draw(mResult);
  }
}

function finishMobileRace(iWon, winner, announce, soloEnd) {
  if (mRaceOver) return;
  mRaceOver = true;
  pm.engineSound.update(0, false);
  if (soloEnd) {
    // solo practice run ended by crashing alone - no win/lose framing
    mResult = { won: false, line: "Run complete!" };
  } else {
    mResult = { won: iWon, line: (winner || "Someone") + " reached the target!" };
    playWin();
    if (announce && conn && opponentConnected) {
      conn.send({ type: "over", winnerName: winner });
    }
  }
}

document.getElementById("mBtnCreate").addEventListener("click", createRoom);
document.getElementById("mBtnJoin").addEventListener("click", joinRoom);
document.getElementById("mBtnSolo").addEventListener("click", playSolo);
document.getElementById("mBtnStart").addEventListener("click", () => beginMobileRace(currentMWinScore(), true));
document.getElementById("mBtnPause").addEventListener("click", () => { if (mRunning) mPaused = !mPaused; });
document.getElementById("mBtnMute").addEventListener("click", (e) => {
  soundOn = !soundOn;
  e.target.innerText = soundOn ? "🔊" : "🔇";
  document.getElementById("btnMute").innerText = soundOn ? "🔊 Sound On" : "🔇 Sound Off";
});

addSwipeControls(document.getElementById("canvasM"), () => pm, () => mRaceOver);

// =======================================================================
// Main render/update loop (runs both controllers; only the active one draws)
// =======================================================================
function loop() {
  desktopLoop();
  mobileLoop();
  requestAnimationFrame(loop);
}

renderLeaderboard();
loop();
</script>
"""

components.html(GAME_HTML, height=1450, scrolling=True)

st.info(
    "💡 **Desktop:** set a win score and click Start Race — both players use "
    "one keyboard. **Mobile:** enter your name, then either tap **Create Room** "
    "and share the code with a friend on another phone, tap **Join** with a "
    "code you were given, or tap **Play Solo** to practice alone. Swipe to "
    "steer and change speed."
)

with st.expander("About cross-device multiplayer & the leaderboard"):
    st.write(
        "Two phones connect **directly to each other** using a free, no-signup "
        "WebRTC connection service (PeerJS) — no extra backend was added to "
        "this project. Both phones need internet access, and very locked-down "
        "networks (some school/office Wi-Fi) can occasionally block the "
        "connection. The leaderboard is stored in each device's own browser "
        "storage, so it isn't shared between devices — see `game.txt` for "
        "notes on adding a real shared/global leaderboard with a small "
        "database backend."
    )
