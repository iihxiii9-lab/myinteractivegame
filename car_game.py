"""
Car Dodge Game - Streamlit Cloud compatible version
=====================================================
This version does NOT use pygame (pygame needs a real display/window and
cannot run on Streamlit Cloud's headless servers). Instead, the game is
built with HTML5 Canvas + JavaScript and embedded directly into the
Streamlit app using components.html. It runs entirely in the visitor's
browser, so it works great on Streamlit Community Cloud.

Run locally:
    pip install streamlit
    streamlit run car_game.py
"""

import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Car Dodge Game", page_icon="🚗", layout="centered")

st.title("🚗 Car Dodge Game")
st.caption("Dodge the oncoming traffic and survive as long as you can!")

GAME_HTML = r"""
<div style="display:flex; justify-content:center;">
  <canvas id="gameCanvas" width="480" height="700"
          style="background:#3c3c3c; border:2px solid #fff; border-radius:8px; outline:none;"
          tabindex="0"></canvas>
</div>
<div style="display:flex; justify-content:center; gap:10px; margin-top:10px;">
  <button id="btnLeft" style="padding:10px 20px; font-size:18px;">⬅️ Left</button>
  <button id="btnPause" style="padding:10px 20px; font-size:18px;">⏸ Pause</button>
  <button id="btnRestart" style="padding:10px 20px; font-size:18px;">🔄 Restart</button>
  <button id="btnRight" style="padding:10px 20px; font-size:18px;">Right ➡️</button>
</div>
<p style="text-align:center; color:#ccc; font-family:sans-serif; font-size:14px;">
  Controls: Arrow keys / A / D to move, P to pause, R to restart.<br>
  On mobile, use the on-screen buttons.
</p>

<script>
const canvas = document.getElementById("gameCanvas");
const ctx = canvas.getContext("2d");

const WIDTH = canvas.width;
const HEIGHT = canvas.height;
const ROAD_WIDTH = 360;
const ROAD_X = (WIDTH - ROAD_WIDTH) / 2;
const LANE_COUNT = 3;
const LANE_WIDTH = ROAD_WIDTH / LANE_COUNT;

const COLORS = {
  white: "#f5f5f5",
  black: "#141414",
  gray: "#3c3c3c",
  lightGray: "#6e6e6e",
  yellow: "#f0c828",
  blue: "#3c82dc"
};
const OBSTACLE_COLORS = ["#dc3c3c", "#3cc864", "#f0c828", "#c864dc"];

class Car {
  constructor() {
    this.width = 46;
    this.height = 80;
    this.lane = Math.floor(LANE_COUNT / 2);
    this.x = this.laneX(this.lane);
    this.y = HEIGHT - this.height - 30;
    this.speedX = 6;
  }
  laneX(lane) {
    const center = ROAD_X + lane * LANE_WIDTH + LANE_WIDTH / 2;
    return center - this.width / 2;
  }
  moveLeft() { this.x = Math.max(ROAD_X + 4, this.x - this.speedX); }
  moveRight() { this.x = Math.min(ROAD_X + ROAD_WIDTH - this.width - 4, this.x + this.speedX); }
  rect() { return { x: this.x, y: this.y, w: this.width, h: this.height }; }
  draw() {
    const r = this.rect();
    drawCarBody(r, COLORS.blue);
  }
}

class Obstacle {
  constructor(speed) {
    this.width = 46;
    this.height = 80;
    const lane = Math.floor(Math.random() * LANE_COUNT);
    const center = ROAD_X + lane * LANE_WIDTH + LANE_WIDTH / 2;
    this.x = center - this.width / 2;
    this.y = -this.height;
    this.speed = speed;
    this.color = OBSTACLE_COLORS[Math.floor(Math.random() * OBSTACLE_COLORS.length)];
  }
  update() { this.y += this.speed; }
  rect() { return { x: this.x, y: this.y, w: this.width, h: this.height }; }
  offScreen() { return this.y > HEIGHT; }
  draw() { drawCarBody(this.rect(), this.color); }
}

function drawCarBody(r, color) {
  ctx.fillStyle = color;
  roundRect(r.x, r.y, r.w, r.h, 10);
  ctx.fill();
  ctx.fillStyle = COLORS.white;
  roundRect(r.x + 6, r.y + 10, r.w - 12, 18, 4); ctx.fill();
  roundRect(r.x + 6, r.y + r.h - 28, r.w - 12, 18, 4); ctx.fill();
  ctx.fillStyle = COLORS.black;
  ctx.fillRect(r.x - 4, r.y + 8, 6, 18);
  ctx.fillRect(r.x + r.w - 2, r.y + 8, 6, 18);
  ctx.fillRect(r.x - 4, r.y + r.h - 26, 6, 18);
  ctx.fillRect(r.x + r.w - 2, r.y + r.h - 26, 6, 18);
}

function roundRect(x, y, w, h, r) {
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

let game;

function newGame() {
  return {
    car: new Car(),
    obstacles: [],
    score: 0,
    baseSpeed: 5,
    spawnTimer: 0,
    spawnInterval: 55,
    gameOver: false,
    paused: false,
    roadScroll: 0,
    keys: {}
  };
}

function spawnObstacle() {
  const speed = game.baseSpeed + Math.random() * 2;
  game.obstacles.push(new Obstacle(speed));
}

function update() {
  if (game.gameOver || game.paused) return;

  if (game.keys["ArrowLeft"] || game.keys["a"]) game.car.moveLeft();
  if (game.keys["ArrowRight"] || game.keys["d"]) game.car.moveRight();
  if (game.keys["ArrowUp"] || game.keys["w"]) game.baseSpeed = Math.min(game.baseSpeed + 0.04, 14);
  if (game.keys["ArrowDown"] || game.keys["s"]) game.baseSpeed = Math.max(game.baseSpeed - 0.04, 3);

  game.spawnTimer++;
  if (game.spawnTimer >= game.spawnInterval) {
    game.spawnTimer = 0;
    spawnObstacle();
    game.spawnInterval = Math.max(20, game.spawnInterval - 0.5);
  }

  game.obstacles.forEach(o => o.update());
  game.obstacles = game.obstacles.filter(o => !o.offScreen());

  const carRect = game.car.rect();
  for (const o of game.obstacles) {
    if (rectsCollide(carRect, o.rect())) {
      game.gameOver = true;
    }
  }

  game.score += game.baseSpeed * 0.05;
  game.roadScroll = (game.roadScroll + game.baseSpeed) % 40;
}

function drawRoad() {
  ctx.fillStyle = COLORS.gray;
  ctx.fillRect(0, 0, WIDTH, HEIGHT);
  ctx.fillStyle = COLORS.lightGray;
  ctx.fillRect(ROAD_X, 0, ROAD_WIDTH, HEIGHT);

  ctx.fillStyle = COLORS.yellow;
  for (let lane = 1; lane < LANE_COUNT; lane++) {
    const x = ROAD_X + lane * LANE_WIDTH;
    let y = -40 + game.roadScroll;
    while (y < HEIGHT) {
      ctx.fillRect(x - 3, y, 6, 24);
      y += 40;
    }
  }
  ctx.fillStyle = COLORS.white;
  ctx.fillRect(ROAD_X - 6, 0, 6, HEIGHT);
  ctx.fillRect(ROAD_X + ROAD_WIDTH, 0, 6, HEIGHT);
}

function drawHUD() {
  ctx.fillStyle = COLORS.white;
  ctx.font = "bold 16px sans-serif";
  ctx.textAlign = "left";
  ctx.fillText("Score: " + Math.floor(game.score), 10, 24);
  ctx.fillText("Speed: " + game.baseSpeed.toFixed(1), 10, 46);

  if (game.paused) centerMessage("PAUSED", "Press P or tap Pause to resume");
  if (game.gameOver) centerMessage("GAME OVER", "Press R or tap Restart");
}

function centerMessage(title, subtitle) {
  ctx.fillStyle = "rgba(0,0,0,0.6)";
  ctx.fillRect(0, 0, WIDTH, HEIGHT);
  ctx.fillStyle = COLORS.white;
  ctx.textAlign = "center";
  ctx.font = "bold 42px sans-serif";
  ctx.fillText(title, WIDTH / 2, HEIGHT / 2 - 10);
  ctx.font = "bold 20px sans-serif";
  ctx.fillText(subtitle, WIDTH / 2, HEIGHT / 2 + 30);
}

function draw() {
  drawRoad();
  game.car.draw();
  game.obstacles.forEach(o => o.draw());
  drawHUD();
}

function loop() {
  update();
  draw();
  requestAnimationFrame(loop);
}

// input handling
window.addEventListener("keydown", (e) => {
  game.keys[e.key] = true;
  if (e.key === "p" || e.key === "P") game.paused = !game.paused;
  if ((e.key === "r" || e.key === "R") && game.gameOver) game = newGame();
  if (["ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown"].includes(e.key)) e.preventDefault();
});
window.addEventListener("keyup", (e) => { game.keys[e.key] = false; });

document.getElementById("btnLeft").addEventListener("click", () => game.car.moveLeft());
document.getElementById("btnRight").addEventListener("click", () => game.car.moveRight());
document.getElementById("btnPause").addEventListener("click", () => { if (!game.gameOver) game.paused = !game.paused; });
document.getElementById("btnRestart").addEventListener("click", () => { game = newGame(); });

canvas.addEventListener("click", () => canvas.focus());

game = newGame();
canvas.focus();
loop();
</script>
"""

components.html(GAME_HTML, height=850, scrolling=False)

st.info(
    "Tip: click on the game canvas first so it captures your keyboard input, "
    "then use the arrow keys (or the on-screen buttons on mobile)."
)
