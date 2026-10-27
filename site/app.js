/* =========================================================================
   FOOTBALL PCA MAP — site de apresentação.
   Todos os números vêm de data.js (gerado por `uv run football-pca-map site`):
   nada aqui é ajustado no navegador, só reproduzimos as contas do pipeline.
   ========================================================================= */
"use strict";

const D = window.PCA_DATA;
const F = D.features;
const P = D.jogadores;
const N = P.nome.length;
const GROUPS = ["Goleiro", "Defensor", "Meio-campo", "Atacante"];
const GC = ["#8b7bff", "#2fd197", "#ffbf1f", "#ff5f5c"];
const REDUCE = matchMedia("(prefers-reduced-motion: reduce)").matches;

const $ = (s, el = document) => el.querySelector(s);
const $$ = (s, el = document) => [...el.querySelectorAll(s)];
const nf = (v, d = 0) => v.toLocaleString("pt-BR", { minimumFractionDigits: d, maximumFractionDigits: d });
const pct = (r, d = 1) => nf(r * 100, d) + "%";
const sgn = (v, d = 2) => (v >= 0 ? "+" : "−") + nf(Math.abs(v), d);
const clamp = (v, a, b) => (v < a ? a : v > b ? b : v);
const ease = (t) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);
const fi = (name) => F.indexOf(name);
const strip = (s) => s.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);

// gerador pseudoaleatório com semente (mesmo desenho a cada visita)
function rng(seed) {
  return () => {
    seed |= 0; seed = (seed + 0x6d2b79f5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
const rand = rng(42);
const gauss = () => Math.sqrt(-2 * Math.log(rand() + 1e-9)) * Math.cos(2 * Math.PI * rand());
function sample(n, seed) {
  const r = rng(seed), idx = Array.from({ length: N }, (_, i) => i);
  for (let i = 0; i < n; i++) { const j = i + Math.floor(r() * (N - i)); [idx[i], idx[j]] = [idx[j], idx[i]]; }
  return idx.slice(0, n);
}

const ABBR = {
  Crossing: "CRO", Finishing: "FIN", HeadingAccuracy: "HEA", ShortPassing: "SHP", Volleys: "VOL", Dribbling: "DRI",
  Curve: "CUR", FKAccuracy: "FKA", LongPassing: "LGP", BallControl: "BCT", Acceleration: "ACC", SprintSpeed: "SPD",
  Agility: "AGI", Reactions: "REA", Balance: "BAL", ShotPower: "SPW", Jumping: "JMP", Stamina: "STA", Strength: "STR",
  LongShots: "LGS", Aggression: "AGR", Interceptions: "INT", Positioning: "POS", Vision: "VIS", Penalties: "PEN",
  Composure: "CMP", Marking: "MRK", StandingTackle: "STK", SlidingTackle: "SLT", GKDiving: "GKD", GKHandling: "GKH",
  GKKicking: "GKK", GKPositioning: "GKP", GKReflexes: "GKR", HeightCm: "ALT", WeightKg: "PES", "International Reputation": "REP",
};
const PT = {
  Crossing: "cruzamento", Finishing: "finalização", HeadingAccuracy: "cabeceio", ShortPassing: "passe curto",
  Volleys: "voleio", Dribbling: "drible", Curve: "curva", FKAccuracy: "cobrança de falta", LongPassing: "passe longo",
  BallControl: "controle de bola", Acceleration: "aceleração", SprintSpeed: "velocidade", Agility: "agilidade",
  Reactions: "reação", Balance: "equilíbrio", ShotPower: "força do chute", Jumping: "impulsão", Stamina: "fôlego",
  Strength: "força", LongShots: "chute de longe", Aggression: "agressividade", Interceptions: "interceptação",
  Positioning: "posicionamento", Vision: "visão de jogo", Penalties: "pênalti", Composure: "compostura",
  Marking: "marcação", StandingTackle: "desarme", SlidingTackle: "carrinho", GKDiving: "goleiro: mergulho",
  GKHandling: "goleiro: manejo", GKKicking: "goleiro: chute", GKPositioning: "goleiro: posicionamento",
  GKReflexes: "goleiro: reflexo", HeightCm: "altura (cm)", WeightKg: "peso (kg)",
  "International Reputation": "reputação internacional (1–5)",
};

// posição no campo (105 × 68 m, atacando para a direita) e nome em português
const POS = {
  GK: [5, 34, "Goleiro"], CB: [20, 34, "Zagueiro"], LCB: [19, 24, "Zagueiro pela esquerda"], RCB: [19, 44, "Zagueiro pela direita"],
  LB: [24, 8, "Lateral esquerdo"], RB: [24, 60, "Lateral direito"], LWB: [37, 6, "Ala esquerdo"], RWB: [37, 62, "Ala direito"],
  CDM: [36, 34, "Volante"], LDM: [35, 24, "Volante pela esquerda"], RDM: [35, 44, "Volante pela direita"],
  CM: [51, 34, "Meia central"], LCM: [50, 23, "Meia central esquerdo"], RCM: [50, 45, "Meia central direito"],
  LM: [56, 8, "Meia esquerda"], RM: [56, 60, "Meia direita"], CAM: [66, 34, "Meia ofensivo"],
  LAM: [65, 22, "Meia ofensivo esquerdo"], RAM: [65, 46, "Meia ofensivo direito"], LW: [80, 9, "Ponta esquerda"],
  RW: [80, 59, "Ponta direita"], CF: [79, 34, "Segundo atacante"], LF: [79, 22, "Atacante pela esquerda"],
  RF: [79, 46, "Atacante pela direita"], ST: [92, 34, "Centroavante"], LS: [91, 25, "Centroavante pela esquerda"],
  RS: [91, 43, "Centroavante pela direita"],
};

// --------------------------------------------------------------- CAMPO ----
const circ = (x, y, r) => `M${x - r},${y}a${r},${r} 0 1,0 ${2 * r},0a${r},${r} 0 1,0 ${-2 * r},0`;
const PITCH_D = [
  "M0,0H105V68H0Z", "M52.5,0V68", circ(52.5, 34, 9.15),
  "M0,13.84H16.5V54.16H0", "M105,13.84H88.5V54.16H105",
  "M0,24.84H5.5V43.16H0", "M105,24.84H99.5V43.16H105",
  "M16.5,26.69A9.15,9.15 0 0 1 16.5,41.31", "M88.5,26.69A9.15,9.15 0 0 0 88.5,41.31",
  "M0,30.34H-1.8V37.66H0", "M105,30.34H106.8V37.66H105",
].join("");
const SPOTS_D = circ(11, 34, 0.35) + circ(94, 34, 0.35) + circ(52.5, 34, 0.35);
const PITCH_PATH = new Path2D(PITCH_D);
const SPOTS_PATH = new Path2D(SPOTS_D);

function pitchSVG() {
  let s = "";
  for (let i = 0; i < 10; i++) if (i % 2 === 0) s += `<rect class="stripe" x="${i * 10.5}" y="0" width="10.5" height="68"/>`;
  return s + `<path class="line" d="${PITCH_D}"/><path d="${SPOTS_D}" fill="rgba(233,231,223,.55)"/>`;
}

function drawPitch(ctx, r, alpha) {
  if (alpha <= 0.01) return;
  ctx.save();
  ctx.translate(r.x, r.y);
  ctx.scale(r.w / 105, r.h / 68);
  ctx.globalAlpha = alpha;
  ctx.fillStyle = "rgba(255,255,255,.025)";
  for (let i = 0; i < 10; i += 2) ctx.fillRect(i * 10.5, 0, 10.5, 68);
  ctx.lineWidth = 1.1 * (105 / r.w);
  ctx.strokeStyle = "rgba(233,231,223,.5)";
  ctx.stroke(PITCH_PATH);
  ctx.fillStyle = "rgba(233,231,223,.5)";
  ctx.fill(SPOTS_PATH);
  ctx.restore();
}

// ------------------------------------------------------ DADOS DERIVADOS ----
const PC1 = new Float32Array(N), PC2 = new Float32Array(N);
const GRP = new Uint8Array(N), FX = new Float32Array(N), FY = new Float32Array(N), DELAY = new Float32Array(N);
const BY_GROUP = [[], [], [], []];
for (let i = 0; i < N; i++) {
  PC1[i] = P.pc[i][0]; PC2[i] = P.pc[i][1]; GRP[i] = P.grupo[i];
  BY_GROUP[GRP[i]].push(i);
  const [px, py] = POS[P.posicao[i]];
  FX[i] = clamp(px + gauss() * 2.6, 0.8, 104.2);
  FY[i] = clamp(py + gauss() * 2.6, 0.8, 67.2);
  DELAY[i] = clamp(FX[i] / 105 * 0.75 + rand() * 0.25, 0, 1);
}
const BOUNDS = (() => {
  const q = (arr, p) => { const s = Float32Array.from(arr).sort(); return s[Math.floor(p * (s.length - 1))]; };
  const x0 = q(PC1, 0.0005), x1 = q(PC1, 0.9995), y0 = q(PC2, 0.0005), y1 = q(PC2, 0.9995);
  const px = (x1 - x0) * 0.04, py = (y1 - y0) * 0.06;
  return { x0: x0 - px, x1: x1 + px, y0: y0 - py, y1: y1 + py };
})();
const BY_NAME = new Map(P.nome.map((n, i) => [n, i]));
const HIGHLIGHT = D.destaques.map((n) => BY_NAME.get(n)).filter((i) => i !== undefined);
const zOf = (i, j) => (P.atributos[i][j] - D.media[j]) / D.desvio[j];
const rawHeight = (cm) => { const inch = Math.round(cm / 2.54); return `${Math.floor(inch / 12)}'${inch % 12}`; };
const rawWeight = (kg) => `${Math.round(kg / 0.45359237)}lbs`;

// ---------------------------------------------------- CANVAS E LAÇOS ----
function prep(cv) {
  const dpr = Math.min(2, window.devicePixelRatio || 1);
  const w = cv.clientWidth, h = cv.clientHeight;
  const W = Math.round(w * dpr), H = Math.round(h * dpr);
  if (cv.width !== W || cv.height !== H) { cv.width = W; cv.height = H; }
  const ctx = cv.getContext("2d");
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  return { ctx, w, h };
}

function layout(w, h, { top = 46, bottom = 42, side = 22 } = {}) {
  const aw = w - 2 * side, ah = h - top - bottom;
  const fw = Math.min(aw, ah * (105 / 68)), fh = fw * (68 / 105);
  return {
    field: { x: (w - fw) / 2, y: top + (ah - fh) / 2, w: fw, h: fh },
    map: { x: side + 16, y: top, w: aw - 16, h: ah },
  };
}
const mapX = (r, v) => r.x + ((v - BOUNDS.x0) / (BOUNDS.x1 - BOUNDS.x0)) * r.w;
const mapY = (r, v) => r.y + ((BOUNDS.y1 - v) / (BOUNDS.y1 - BOUNDS.y0)) * r.h;

// desenha os jogadores entre o campo (t = 0) e o mapa PCA (t = 1)
function drawPlayers(ctx, L, t, { size = 1.7, alpha = 0.62, filter = null, sx = null, sy = null } = {}) {
  const fr = L.field, mr = L.map, kx = fr.w / 105, ky = fr.h / 68;
  const ax = mr.w / (BOUNDS.x1 - BOUNDS.x0), ay = mr.h / (BOUNDS.y1 - BOUNDS.y0);
  const hs = size / 2;
  ctx.globalAlpha = alpha;
  for (let g = 0; g < 4; g++) {
    const idx = BY_GROUP[g], on = !filter || filter[g];
    ctx.fillStyle = GC[g];
    for (let k = 0; k < idx.length; k++) {
      const i = idx[k];
      if (!on) { if (sx) sx[i] = NaN; continue; }
      let e = (t - DELAY[i] * 0.35) / 0.65;
      e = ease(e < 0 ? 0 : e > 1 ? 1 : e);
      const x0 = fr.x + FX[i] * kx, y0 = fr.y + FY[i] * ky;
      const x1 = mr.x + (PC1[i] - BOUNDS.x0) * ax, y1 = mr.y + (BOUNDS.y1 - PC2[i]) * ay;
      const x = x0 + (x1 - x0) * e, y = y0 + (y1 - y0) * e;
      if (sx) { sx[i] = x; sy[i] = y; }
      ctx.fillRect(x - hs, y - hs, size, size);
    }
  }
  ctx.globalAlpha = 1;
}

function drawMapAxes(ctx, r, alpha) {
  if (alpha <= 0.01) return;
  ctx.save();
  ctx.globalAlpha = alpha;
  ctx.strokeStyle = "rgba(233,231,223,.08)";
  ctx.lineWidth = 1;
  ctx.beginPath();
  for (let v = Math.ceil(BOUNDS.x0); v <= BOUNDS.x1; v += 2) { const x = Math.round(mapX(r, v)) + 0.5; ctx.moveTo(x, r.y); ctx.lineTo(x, r.y + r.h); }
  for (let v = Math.ceil(BOUNDS.y0); v <= BOUNDS.y1; v += 2) { const y = Math.round(mapY(r, v)) + 0.5; ctx.moveTo(r.x, y); ctx.lineTo(r.x + r.w, y); }
  ctx.stroke();
  ctx.strokeStyle = "rgba(233,231,223,.35)";
  ctx.beginPath();
  const x0 = Math.round(mapX(r, 0)) + 0.5, y0 = Math.round(mapY(r, 0)) + 0.5;
  ctx.moveTo(x0, r.y); ctx.lineTo(x0, r.y + r.h); ctx.moveTo(r.x, y0); ctx.lineTo(r.x + r.w, y0);
  ctx.stroke();
  ctx.restore();
}

const loops = [];
const loopIO = new IntersectionObserver((es) => es.forEach((e) => loops.forEach((o) => { if (o.el === e.target) o.vis = e.isIntersecting; })), { rootMargin: "80px" });
function loop(el, fn) { const o = { el, fn, vis: false }; loops.push(o); loopIO.observe(el); return o; }
function frame(now) { for (const o of loops) if (o.vis) o.fn(now); requestAnimationFrame(frame); }

function onSeen(el, fn, threshold = 0.25) {
  const io = new IntersectionObserver((es) => es.forEach((e) => { if (e.isIntersecting) { io.disconnect(); fn(); } }), { threshold });
  io.observe(el);
}
const tc = (sec) => {
  const f = Math.floor((sec % 1) * 30), s = Math.floor(sec) % 60, m = Math.floor(sec / 60) % 60, h = Math.floor(sec / 3600);
  return [h, m, s, f].map((v) => String(v).padStart(2, "0")).join(":");
};

/* ======================================================= CABEÇALHO ===== */
function initHeader() {
  const sections = $$("section.ch");
  $("#tabs").innerHTML = sections.map((s, i) => `<a href="#${s.id}" data-id="${s.id}"><span>${String(i).padStart(2, "0")}</span>${s.dataset.name}</a>`).join("");
  const io = new IntersectionObserver((es) => es.forEach((e) => {
    if (!e.isIntersecting) return;
    const i = sections.indexOf(e.target);
    $$("#tabs a").forEach((a) => a.classList.toggle("on", a.dataset.id === e.target.id));
    $("#chapter-name").textContent = `${String(i).padStart(2, "0")} ${e.target.dataset.name}`;
    const on = $(`#tabs a[data-id="${e.target.id}"]`);
    if (on) on.scrollIntoView({ block: "nearest", inline: "nearest" });
  }), { rootMargin: "-45% 0px -50% 0px" });
  sections.forEach((s) => io.observe(s));

  // barra de progresso da leitura
  const bar = $("#tape-bar");
  function tick() {
    const max = document.documentElement.scrollHeight - innerHeight;
    bar.style.width = (max > 0 ? clamp(scrollY / max, 0, 1) * 100 : 0).toFixed(2) + "%";
    requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);
}

function fillNumbers() {
  const vals = { features: F.length, finais: nf(D.finais), brutas: nf(D.brutas.linhas), colunas: D.brutas.colunas,
    treino: nf(D.treino), teste: nf(D.teste), ignoradas: D.brutas.colunas - F.length - 3 };
  $$("[data-num]").forEach((el) => { el.textContent = vals[el.dataset.num]; });
  $("#kpi-var2").textContent = pct(D.variancia[0] + D.variancia[1], 0);
  const k10 = D.classificador.find((c) => c.k === 10);
  $("#kpi-f1").textContent = nf(k10.f1, 3);
  $("#clf-best").textContent = nf(k10.f1, 3);
  const leg = GROUPS.map((g, i) => `<span><i style="background:${GC[i]}"></i>${g}</span>`).join("");
  $$("[data-legend]").forEach((el) => { el.innerHTML = leg; });
  $$(".ph, .ph-desc, .block, .kpis, .pipeline").forEach((el) => {
    el.classList.add("reveal");
    onSeen(el, () => el.classList.add("in"), 0.1);
  });
}

/* ============================================================ HERO ===== */
function initHero() {
  const cv = $("#hero-canvas"), modeEl = $("#hero-mode"), cap = $("#hero-cap"), tcEl = $("#hero-tc");
  const HOLD_A = 2.8, MOVE = 2.6, HOLD_B = 3.4, CYCLE = HOLD_A + MOVE + HOLD_B + MOVE;
  let start = null, lastMode = "";
  onSeen(cv, () => setTimeout(() => $("#hero-blue").classList.add("off"), REDUCE ? 0 : 1300), 0.2);

  loop(cv, (now) => {
    if (start === null) start = now + (REDUCE ? 0 : 1300);
    const s = Math.max(0, (now - start) / 1000), c = s % CYCLE;
    let t;
    if (c < HOLD_A) t = 0;
    else if (c < HOLD_A + MOVE) t = (c - HOLD_A) / MOVE;
    else if (c < HOLD_A + MOVE + HOLD_B) t = 1;
    else t = 1 - (c - HOLD_A - MOVE - HOLD_B) / MOVE;
    const { ctx, w, h } = prep(cv);
    const L = layout(w, h, { top: 50, bottom: 50, side: 26 });
    ctx.fillStyle = "#0c0d0d"; ctx.fillRect(0, 0, w, h);
    drawPitch(ctx, L.field, 1 - t * 1.4);
    drawMapAxes(ctx, L.map, t * 1.4 - 0.4);
    drawPlayers(ctx, L, t, { size: w < 600 ? 1.3 : 1.7, alpha: 0.6 });
    tcEl.textContent = tc(s);
    const m = t < 0.5 ? "CAMPO" : "MAPA PCA";
    if (m !== lastMode) {
      lastMode = m;
      modeEl.textContent = m;
      cap.textContent = m === "CAMPO" ? "cada jogador na posição de origem" : "PC1 × PC2 · 37 atributos em 2 números";
    }
  });

  // as etapas do pipeline acendem em sequência
  const steps = $$("#pipeline li");
  let k = 0;
  setInterval(() => { steps.forEach((li, i) => li.classList.toggle("lit", i === k)); k = (k + 1) % steps.length; }, 1100);
}

/* ========================================================== 01 DADOS ==== */
function initRaw() {
  const skills = F.slice(0, 34);
  const cols = ["#", "Name", "Pos", "Height", "Weight", ...skills, "International Reputation"];
  // cor do cabeçalho = papel da coluna (identificação, rótulo y ou atributo X)
  const role = (k) => (k === 1 ? "id" : k === 2 ? "y" : k > 2 ? "x" : "");
  $("#raw-head").innerHTML = cols.map((c, k) => `<span class="${role(k)}" title="${esc(PT[c] || c)}">${esc(ABBR[c] || c)}</span>`).join("");
  const iH = fi("HeightCm"), iW = fi("WeightKg"), iR = fi("International Reputation");
  let rows = "";
  for (let i = 0; i < 60; i++) {
    const a = P.atributos[i];
    rows += `<div class="raw-row"><span class="n">${i}</span><span>${esc(P.nome[i])}</span><span>${P.posicao[i]}</span>`
      + `<span>${rawHeight(a[iH])}</span><span>${rawWeight(a[iW])}</span>`
      + skills.map((_, j) => `<span${a[j] >= 85 ? ' class="hi"' : ""}>${a[j]}</span>`).join("")
      + `<span>${a[iR]}</span></div>`;
  }
  $("#raw-roll").innerHTML = rows + rows;

  // arrastar com o mouse também desliza a tabela para o lado
  const sc = $("#raw-scroll");
  let startX = null, startLeft = 0;
  sc.addEventListener("pointerdown", (e) => { if (e.pointerType !== "mouse") return; startX = e.clientX; startLeft = sc.scrollLeft; sc.classList.add("drag"); });
  addEventListener("pointermove", (e) => { if (startX !== null) sc.scrollLeft = startLeft - (e.clientX - startX); });
  addEventListener("pointerup", () => { startX = null; sc.classList.remove("drag"); });
  // exemplo de cada papel de coluna com a linha do Messi
  const m = BY_NAME.get("L. Messi"), ex = D.exemplo_bruto;
  if (m !== undefined) {
    $("#ex-id").textContent = `${P.nome[m]} · ${P.clube[m]}`;
    $("#ex-x").textContent = ["Finishing", "Dribbling", "StandingTackle"].map((f) => `${f} ${P.atributos[m][fi(f)]}`).join(" · ") + " · …";
    $("#ex-y").textContent = `${ex.Position} → ${GROUPS[GRP[m]]}`;
    $("#ex-ig").textContent = `Value ${ex.Value} · Wage ${ex.Wage}`;
  }
  $("#feature-chips").innerHTML = F.map((f) => {
    const cls = f.startsWith("GK") ? "chip gk" : F.indexOf(f) >= 34 ? "chip ex" : "chip";
    return `<span class="${cls}" title="${esc(PT[f])}">${esc(f)}</span>`;
  }).join("");
}

/* ========================================================== 02 CAMPO ==== */
function initPitch() {
  const counts = {}, best = {};
  for (let i = 0; i < N; i++) {
    const c = P.posicao[i];
    counts[c] = (counts[c] || 0) + 1;
    if (best[c] === undefined || P.overall[i] > P.overall[best[c]]) best[c] = i;
  }
  const max = Math.max(...Object.values(counts));
  const groupOf = (c) => GRP[P.posicao.indexOf(c)];
  const codes = Object.keys(POS).filter((c) => counts[c]);
  const svg = $("#pitch-svg");
  svg.innerHTML = pitchSVG() + codes.map((c, k) => {
    const [x, y] = POS[c], r = 1.4 + Math.sqrt(counts[c] / max) * 5;
    return `<g class="pos-node" data-code="${c}" transform="translate(${x},${y})" tabindex="0" role="button" aria-label="${POS[c][2]}">`
      + `<circle class="ring" r="${r + 1.3}"/><circle class="dot" r="${r}" fill="${GC[groupOf(c)]}" style="--d:${k * 35}ms"/>`
      + `<text>${c}</text></g>`;
  }).join("");

  const panel = $("#pos-panel"), screen = $(".pitch-screen");
  const outfield = F.slice(0, 34);
  function show(c) {
    $$(".pos-node", svg).forEach((n) => n.classList.toggle("on", n.dataset.code === c));
    screen.classList.add("dim");
    const g = groupOf(c), mean = new Array(F.length).fill(0);
    let n = 0;
    for (let i = 0; i < N; i++) if (P.posicao[i] === c) { n++; const a = P.atributos[i]; for (let j = 0; j < F.length; j++) mean[j] += a[j]; }
    const top = outfield.map((f, j) => [f, mean[j] / n]).sort((a, b) => b[1] - a[1]).slice(0, 6);
    const b = best[c];
    panel.innerHTML = `<div class="code">${c}</div><div class="name">${POS[c][2]}</div>`
      + `<span class="grp lbl"><i style="background:${GC[g]}"></i>${GROUPS[g]}</span>`
      + `<div class="cnt">${nf(n)}</div><span class="lbl muted">jogadores · ${pct(n / N)} do total</span>`
      + `<div class="bh mt"><h2 style="font-size:16px"><i>μ</i>Perfil médio</h2></div><div class="bars">`
      + top.map(([f, v]) => `<div class="bar"><span class="n lbl" title="${esc(PT[f])}">${f}</span><span class="tr"><b class="f" style="width:${v}%"></b></span><span class="p">${nf(v)}</span></div>`).join("")
      + `</div><div class="star"><span class="lbl muted">maior overall</span><br><b>${esc(P.nome[b])}</b> · ${P.overall[b]}</div>`;
  }
  let auto = true, k = codes.indexOf("ST");
  svg.addEventListener("click", (e) => { const n = e.target.closest(".pos-node"); if (n) { auto = false; show(n.dataset.code); } });
  svg.addEventListener("keydown", (e) => { const n = e.target.closest(".pos-node"); if (n && (e.key === "Enter" || e.key === " ")) { e.preventDefault(); auto = false; show(n.dataset.code); } });
  onSeen(svg, () => {
    svg.classList.add("in");
    show(codes[k]);
    const id = setInterval(() => { if (!auto) return clearInterval(id); k = (k + 1) % codes.length; show(codes[k]); }, 2600);
  });

  const gmax = Math.max(...BY_GROUP.map((g) => g.length));
  $("#group-counts").innerHTML = GROUPS.map((g, i) => {
    const cs = codes.filter((c) => groupOf(c) === i).join(" · ");
    return `<div><span class="lbl"><i style="background:${GC[i]}"></i> ${g}</span><div class="v">${nf(BY_GROUP[i].length)}</div>`
      + `<div class="gbar"><b data-w="${(BY_GROUP[i].length / gmax) * 100}" style="background:${GC[i]}"></b></div><div class="codes">${cs}</div></div>`;
  }).join("");
  onSeen($("#group-counts"), () => $$("#group-counts .gbar b").forEach((b) => { b.style.width = b.dataset.w + "%"; }));
}

/* ======================================================== 03 LIMPEZA ==== */
function initClean() {
  const iH = fi("HeightCm"), iW = fi("WeightKg");
  const who = [...HIGHLIGHT];
  let k = 0;
  const set = (key, txt, flash) => { const el = $(`[data-c="${key}"]`); el.textContent = txt; if (flash) { el.classList.remove("flash"); void el.offsetWidth; el.classList.add("flash"); } };
  function show() {
    const i = who[k % who.length], a = P.atributos[i];
    // a altura bruta é inteira em polegadas; o cm vem da mesma conta do data.py
    const inch = Math.round(a[iH] / 2.54), lbs = Math.round(a[iW] / 0.45359237);
    set("h-from", rawHeight(a[iH])); set("h-to", nf(Math.floor(inch / 12) * 30.48 + (inch % 12) * 2.54, 1) + " cm", true);
    set("w-from", lbs + "lbs"); set("w-to", nf(lbs * 0.45359237, 1) + " kg", true);
    set("p-from", P.posicao[i]); set("p-to", GROUPS[GRP[i]], true);
    set("who", P.nome[i]);
    k++;
  }
  show();
  const box = $("#convs");
  loop(box, (() => { let last = 0; return (now) => { if (now - last > 2800) { last = now; show(); } }; })());

  const raw = D.brutas.linhas, cut = raw - D.finais;
  $("#funnel").innerHTML = `
    <div class="row"><b data-w="100"><span class="lbl">CSV bruto</span></b><span class="num">${nf(raw)}</span></div>
    <div class="row cut"><b data-w="${Math.max(2, (cut / raw) * 100)}"><span class="lbl">sem posição</span></b><span class="num">−${cut}</span></div>
    <div class="row"><b data-w="${(D.finais / raw) * 100}"><span class="lbl">amostra final</span></b><span class="num">${nf(D.finais)}</span></div>`;
  $("#split").innerHTML = `
    <div class="track"><div class="tr-a lbl" data-w="${(D.treino / D.finais) * 100}">TREINO · fit + transform</div><div class="tr-b lbl">TESTE · só transform</div></div>
    <div class="vals"><div><b>${nf(D.treino)}</b><span class="lbl muted">jogadores no treino</span></div><div style="text-align:right"><b>${nf(D.teste)}</b><span class="lbl muted">no teste</span></div></div>`;
  onSeen($("#funnel"), () => $$("#funnel b, #split .tr-a").forEach((b) => { b.style.width = b.dataset.w + "%"; }));
}

/* ======================================================= 04 ESCALA ====== */
function initScale() {
  const feats = ["HeightCm", "Finishing", "International Reputation"].map(fi);
  const S = sample(700, 7);
  const jit = S.map(() => (rand() - 0.5) * 2);
  const cv = $("#scale-canvas"), btn = $("#scale-btn"), modeEl = $("#scale-mode");
  let target = 0, t = 0, auto = true, lastSwitch = 0, last = 0;
  btn.addEventListener("click", () => { auto = false; target = target ? 0 : 1; });

  const messi = BY_NAME.get("L. Messi");
  const rows = ["HeightCm", "WeightKg", "Finishing", "StandingTackle", "International Reputation"].map((f) => {
    const j = fi(f), x = P.atributos[messi][j];
    return `<tr><td>${f}</td><td class="num">${nf(D.media[j], 1)}</td><td class="num">${nf(D.desvio[j], 1)}</td><td class="num">${x}</td><td class="num">${sgn(zOf(messi, j))}</td></tr>`;
  }).join("");
  $("#scale-table").innerHTML = `<thead><tr><th>atributo</th><th>μ</th><th>σ</th><th>x Messi</th><th>z Messi</th></tr></thead><tbody>${rows}</tbody>`;

  loop(cv, (now) => {
    const dt = Math.min(0.05, (now - (last || now)) / 1000); last = now;
    if (auto && now - lastSwitch > 3800) { lastSwitch = now; target = target ? 0 : 1; }
    t += clamp(target - t, -dt / 1.4, dt / 1.4);
    btn.textContent = target ? "◀ VOLTAR" : "▶ PADRONIZAR";
    modeEl.textContent = t > 0.5 ? "z · PADRONIZADO" : "x · BRUTO";
    const { ctx, w, h } = prep(cv);
    ctx.fillStyle = "#0c0d0d"; ctx.fillRect(0, 0, w, h);
    const L = 18, R = w - 18, top = 52, rowH = (h - top - 40) / 3;
    const rx = (v) => L + (v / 210) * (R - L);
    const zx = (v) => L + ((clamp(v, -4.2, 4.2) + 4.5) / 9) * (R - L);
    const e = ease(t);
    // eixo
    ctx.font = "15px VT323, monospace"; ctx.textAlign = "center";
    const ticks = e < 0.5 ? [0, 50, 100, 150, 200].map((v) => [rx(v), String(v)]) : [-4, -2, 0, 2, 4].map((v) => [zx(v), (v > 0 ? "+" : "") + v + "σ"]);
    const ta = Math.abs(e - 0.5) * 2;
    ctx.fillStyle = `rgba(233,231,223,${0.55 * ta})`; ctx.strokeStyle = `rgba(233,231,223,${0.12 * ta})`;
    ticks.forEach(([x, s]) => { ctx.fillText(s, x, h - 16); ctx.beginPath(); ctx.moveTo(x + 0.5, top - 10); ctx.lineTo(x + 0.5, h - 32); ctx.stroke(); });
    feats.forEach((j, r) => {
      const cy = top + rowH * (r + 0.5);
      ctx.textAlign = "left"; ctx.fillStyle = "rgba(233,231,223,.85)"; ctx.font = "11px 'IBM Plex Mono', monospace";
      ctx.fillText(F[j].toUpperCase() + `  μ=${nf(D.media[j], 1)}  σ=${nf(D.desvio[j], 1)}`, L, cy - rowH * 0.36);
      ctx.globalAlpha = 0.7;
      S.forEach((i, k) => {
        const v = P.atributos[i][j], z = (v - D.media[j]) / D.desvio[j];
        const d = clamp((e - DELAY[i] * 0.3) / 0.7, 0, 1), ee = ease(d);
        const x = rx(v) + (zx(z) - rx(v)) * ee, y = cy + jit[k] * rowH * 0.24 + 6;
        ctx.fillStyle = GC[GRP[i]]; ctx.fillRect(x - 1.2, y - 1.2, 2.4, 2.4);
      });
      ctx.globalAlpha = 1;
      // marcador da média
      const mx = rx(D.media[j]) + (zx(0) - rx(D.media[j])) * e;
      ctx.strokeStyle = "#fff"; ctx.lineWidth = 1.5; ctx.beginPath(); ctx.moveTo(mx, cy - rowH * 0.24); ctx.lineTo(mx, cy + rowH * 0.34); ctx.stroke(); ctx.lineWidth = 1;
    });
  });
}

/* ==================================================== 05 CORRELAÇÃO ===== */
function initCorr() {
  const C = D.correlacao, n = F.length, cv = $("#corr-canvas"), read = $("#corr-read");
  const pairs = [];
  for (let i = 0; i < n; i++) for (let j = i + 1; j < n; j++) pairs.push([i, j, C[i][j]]);
  $("#corr-strong").textContent = pairs.filter((p) => Math.abs(p[2]) >= 0.8).length;
  const top = [...pairs].sort((a, b) => b[2] - a[2]).slice(0, 5);
  const neg = [...pairs].sort((a, b) => a[2] - b[2]).slice(0, 2);
  $("#corr-top").innerHTML = [...top, ...neg].map(([i, j, r]) =>
    `<li><span class="t">${F[i]} × ${F[j]}</span><span class="r" style="color:${r < 0 ? "#1f8fc4" : "inherit"}">${sgn(r)}</span></li>`).join("");

  const color = (r) => {
    const a = Math.abs(r), [cr, cg, cb] = r >= 0 ? [255, 138, 31] : [54, 197, 255];
    return `rgb(${12 + (cr - 12) * a | 0},${13 + (cg - 13) * a | 0},${13 + (cb - 13) * a | 0})`;
  };
  let t0 = null, hover = null;
  const geo = (w) => { const ml = 34, mt = 22, cell = (w - ml - 8) / n; return { ml, mt, cell }; };
  cv.addEventListener("mousemove", (e) => {
    const b = cv.getBoundingClientRect(), { ml, mt, cell } = geo(b.width);
    const j = Math.floor((e.clientX - b.left - ml) / cell), i = Math.floor((e.clientY - b.top - mt) / cell);
    hover = i >= 0 && j >= 0 && i < n && j < n ? [i, j] : null;
    read.textContent = hover ? `${F[i]} × ${F[j]}  ·  r = ${sgn(C[i][j])}` : "passe o mouse na matriz";
  });
  cv.addEventListener("mouseleave", () => { hover = null; read.textContent = "passe o mouse na matriz"; });
  loop(cv, (now) => {
    if (t0 === null) t0 = now;
    const t = REDUCE ? 1 : clamp((now - t0) / 1800, 0, 1);
    const { ctx, w } = prep(cv), { ml, mt, cell } = geo(w);
    ctx.fillStyle = "#0c0d0d"; ctx.fillRect(0, 0, w, w);
    ctx.font = `${Math.max(8, Math.min(12, cell * 0.95))}px VT323, monospace`;
    ctx.fillStyle = "rgba(233,231,223,.6)";
    for (let i = 0; i < n; i++) {
      ctx.textAlign = "right"; ctx.fillText(ABBR[F[i]], ml - 4, mt + (i + 0.75) * cell);
      if (i % 2 === 0) { ctx.textAlign = "center"; ctx.fillText(ABBR[F[i]], ml + (i + 0.5) * cell, mt - 6); }
    }
    for (let i = 0; i < n; i++) for (let j = 0; j < n; j++) {
      if ((i + j) / (2 * n - 2) > t) continue;
      ctx.fillStyle = color(C[i][j]);
      ctx.fillRect(ml + j * cell, mt + i * cell, cell - 0.6, cell - 0.6);
    }
    if (hover) {
      const [i, j] = hover;
      ctx.strokeStyle = "rgba(255,255,255,.6)";
      ctx.strokeRect(ml + 0.5, mt + i * cell + 0.5, n * cell, cell);
      ctx.strokeRect(ml + j * cell + 0.5, mt + 0.5, cell, n * cell);
      ctx.strokeStyle = "#fff"; ctx.lineWidth = 2; ctx.strokeRect(ml + j * cell, mt + i * cell, cell, cell); ctx.lineWidth = 1;
    }
  });
}

/* ===================================================== 06 AUTOVETOR ===== */
function initEigen() {
  const jx = fi("Finishing"), jy = fi("StandingTackle");
  const S = sample(1400, 11), X = S.map((i) => zOf(i, jx)), Y = S.map((i) => zOf(i, jy));
  const mx = X.reduce((a, b) => a + b) / X.length, my = Y.reduce((a, b) => a + b) / Y.length;
  let a = 0, b = 0, c = 0;
  for (let k = 0; k < S.length; k++) { const dx = X[k] - mx, dy = Y[k] - my; a += dx * dx; b += dx * dy; c += dy * dy; }
  a /= S.length - 1; b /= S.length - 1; c /= S.length - 1;
  const varAt = (th) => a * Math.cos(th) ** 2 + 2 * b * Math.sin(th) * Math.cos(th) + c * Math.sin(th) ** 2;
  let best = 0.5 * Math.atan2(2 * b, a - c);
  if (best < 0) best += Math.PI;
  const lam1 = varAt(best), lam2 = varAt(best + Math.PI / 2);

  const cv = $("#eig-canvas"), curve = $("#eig-curve"), btn = $("#eig-btn"), angEl = $("#eig-angle"), varEl = $("#eig-var");
  let th = 0.15, mode = "auto", seekFrom = 0, seekT0 = 0, holdUntil = 0, last = 0;
  btn.addEventListener("click", () => { mode = "seek"; seekFrom = th; seekT0 = performance.now(); });
  let drag = false;
  const setFromPointer = (e) => {
    const r = cv.getBoundingClientRect();
    let ang = Math.atan2(-(e.clientY - r.top - r.height / 2), e.clientX - r.left - r.width / 2);
    if (ang < 0) ang += Math.PI;
    th = ang; mode = "hold"; holdUntil = performance.now() + 5000;
  };
  cv.addEventListener("pointerdown", (e) => { drag = true; cv.setPointerCapture(e.pointerId); setFromPointer(e); });
  cv.addEventListener("pointermove", (e) => { if (drag) setFromPointer(e); });
  cv.addEventListener("pointerup", () => { drag = false; });

  loop(cv, (now) => {
    const dt = Math.min(0.05, (now - (last || now)) / 1000); last = now;
    if (mode === "auto") th = (th + dt * 0.32) % Math.PI;
    else if (mode === "seek") {
      let target = best;
      while (target < seekFrom) target += Math.PI;
      if (target - seekFrom > Math.PI / 2) target -= Math.PI;
      const p = clamp((now - seekT0) / 1400, 0, 1);
      th = seekFrom + (target - seekFrom) * ease(p);
      if (p >= 1) { th = ((th % Math.PI) + Math.PI) % Math.PI; mode = "hold"; holdUntil = now + 4500; }
    } else if (mode === "hold" && now > holdUntil && !drag) mode = "auto";

    const { ctx, w, h } = prep(cv), cx = w / 2, cy = h / 2, sc = Math.min(w, h) / 7.6;
    ctx.fillStyle = "#0c0d0d"; ctx.fillRect(0, 0, w, h);
    ctx.strokeStyle = "rgba(233,231,223,.12)"; ctx.beginPath();
    for (let v = -3; v <= 3; v++) { ctx.moveTo(cx + v * sc, 0); ctx.lineTo(cx + v * sc, h); ctx.moveTo(0, cy - v * sc); ctx.lineTo(w, cy - v * sc); }
    ctx.stroke();
    const ux = Math.cos(th), uy = Math.sin(th);
    // pontos e ligações até a reta
    ctx.globalAlpha = 0.5;
    for (let k = 0; k < S.length; k++) {
      ctx.fillStyle = GC[GRP[S[k]]];
      ctx.fillRect(cx + X[k] * sc - 1.3, cy - Y[k] * sc - 1.3, 2.6, 2.6);
    }
    ctx.globalAlpha = 0.18; ctx.strokeStyle = "#fff"; ctx.beginPath();
    for (let k = 0; k < S.length; k += 9) {
      const s = X[k] * ux + Y[k] * uy;
      ctx.moveTo(cx + X[k] * sc, cy - Y[k] * sc); ctx.lineTo(cx + s * ux * sc, cy - s * uy * sc);
    }
    ctx.stroke();
    ctx.globalAlpha = 0.9;
    for (let k = 0; k < S.length; k++) {
      const s = X[k] * ux + Y[k] * uy;
      ctx.fillStyle = GC[GRP[S[k]]];
      ctx.fillRect(cx + s * ux * sc - 1, cy - s * uy * sc - 1, 2, 2);
    }
    ctx.globalAlpha = 1;
    const L = Math.max(w, h);
    const near = Math.abs(((th - best) % Math.PI + Math.PI) % Math.PI) < 0.02 || Math.abs(((th - best) % Math.PI + Math.PI) % Math.PI - Math.PI) < 0.02;
    ctx.strokeStyle = near ? "#ffffff" : "rgba(255,255,255,.75)"; ctx.lineWidth = near ? 2.5 : 1.5;
    ctx.beginPath(); ctx.moveTo(cx - ux * L, cy + uy * L); ctx.lineTo(cx + ux * L, cy - uy * L); ctx.stroke();
    if (near) {
      ctx.setLineDash([5, 5]); ctx.strokeStyle = "rgba(255,255,255,.45)"; ctx.lineWidth = 1.2;
      ctx.beginPath(); ctx.moveTo(cx + uy * L, cy + ux * L); ctx.lineTo(cx - uy * L, cy - ux * L); ctx.stroke(); ctx.setLineDash([]);
      ctx.font = "20px VT323, monospace"; ctx.fillStyle = "#fff"; ctx.textAlign = "left";
      ctx.fillText("PC1 ✓", cx + ux * sc * 2.6 + 8, cy - uy * sc * 2.6);
      ctx.fillStyle = "rgba(255,255,255,.6)"; ctx.fillText("PC2", cx - uy * sc * 2.2 + 8, cy - ux * sc * 2.2);
    }
    ctx.lineWidth = 1;
    const v = varAt(th);
    angEl.textContent = `θ = ${Math.round((th * 180) / Math.PI) % 180}°`;
    varEl.textContent = `${nf(v, 2)} / λ₁ = ${nf(lam1, 2)}`;
    btn.textContent = near ? `λ₁ = ${nf(lam1, 2)} · λ₂ = ${nf(lam2, 2)}` : "▶ ACHAR PC1";

    // curva Var(θ)
    const g = prep(curve), cw = g.w, ch = g.h, x2 = g.ctx;
    x2.fillStyle = "#0c0d0d"; x2.fillRect(0, 0, cw, ch);
    const vy = (val) => ch - 14 - (val / (lam1 * 1.1)) * (ch - 28);
    x2.strokeStyle = "rgba(233,231,223,.8)"; x2.lineWidth = 1.5; x2.beginPath();
    for (let px = 0; px <= cw; px += 2) { const a2 = (px / cw) * Math.PI; px ? x2.lineTo(px, vy(varAt(a2))) : x2.moveTo(px, vy(varAt(a2))); }
    x2.stroke();
    const bx = (best / Math.PI) * cw;
    x2.setLineDash([3, 4]); x2.strokeStyle = "rgba(255,255,255,.4)"; x2.beginPath(); x2.moveTo(bx, 0); x2.lineTo(bx, ch); x2.stroke(); x2.setLineDash([]);
    const ax = ((((th % Math.PI) + Math.PI) % Math.PI) / Math.PI) * cw;
    x2.fillStyle = GC[2]; x2.beginPath(); x2.arc(ax, vy(v), 5, 0, Math.PI * 2); x2.fill();
    x2.font = "15px VT323, monospace"; x2.fillStyle = "rgba(255,255,255,.7)"; x2.textAlign = bx > cw / 2 ? "right" : "left";
    x2.fillText(`máx ${Math.round((best * 180) / Math.PI)}°`, bx + (bx > cw / 2 ? -6 : 6), 14);
  });
}

/* ===================================================== 07 PROJEÇÃO ====== */
function initProjection() {
  const box = $("#proj"), pick = $("#proj-pick");
  let who = BY_NAME.get("L. Messi"), pc = 0, run = 0;
  pick.innerHTML = HIGHLIGHT.map((i) => `<button data-i="${i}">${esc(P.nome[i])}</button>`).join("") + `<button data-i="rand">⟳ ALEATÓRIO</button>`;
  pick.addEventListener("click", (e) => {
    const b = e.target.closest("button"); if (!b) return;
    who = b.dataset.i === "rand" ? Math.floor(Math.random() * N) : +b.dataset.i;
    play();
  });
  $("#proj-pc").addEventListener("click", (e) => {
    const b = e.target.closest("button"); if (!b) return;
    pc = +b.dataset.pc; $$("#proj-pc button").forEach((x) => x.classList.toggle("on", x === b)); play();
  });
  const bar = (v, max, cls = "") => {
    const wd = Math.min(50, (Math.abs(v) / max) * 50);
    return `<span class="dbar ${cls}"><b class="${v < 0 ? "neg" : ""}" style="left:${v < 0 ? 50 - wd : 50}%;width:${wd}%"></b></span>`;
  };
  function play() {
    const id = ++run, W = D.loadings[pc];
    $$("#proj-pick button").forEach((b) => b.classList.toggle("on", +b.dataset.i === who));
    const rows = F.map((f, j) => { const z = zOf(who, j); return { f, j, x: P.atributos[who][j], z, w: W[j], p: z * W[j] }; })
      .sort((a, b) => Math.abs(b.p) - Math.abs(a.p));
    box.innerHTML = `<div class="prow head"><span>atributo</span><span class="x">x</span><span class="zv">z</span><span class="zb">z (−4 a +4)</span><span class="wv">peso w</span><span>contribuição z · w</span><span class="pv">z · w</span></div>`
      + rows.map((r) => `<div class="prow"><span title="${esc(PT[r.f])}">${r.f}</span><span class="x">${r.x}</span><span class="zv">${sgn(r.z)}</span><span class="zb">${bar(r.z, 4)}</span>`
        + `<span class="wv">${sgn(r.w, 3)}</span>${bar(r.p, 1)}<span class="pv">${sgn(r.p)}</span></div>`).join("")
      + `<div class="proj-sum"><div class="eq">PC${pc + 1}(${esc(P.nome[who])}) = Σ z · w = <span id="proj-run">0</span></div><div class="tot"><span id="proj-tot">0,00</span><small id="proj-chk">somando…</small></div></div>`;
    $("#proj-result").textContent = `PC${pc + 1} = ${sgn(rows.reduce((a, r) => a + r.p, 0))}`;
    $("#proj-who").textContent = P.nome[who];
    const els = $$(".prow:not(.head)", box);
    let k = 0, sum = 0;
    const step = () => {
      if (id !== run) return;
      if (k > 0) els[k - 1].classList.remove("cur");
      if (k >= rows.length) {
        const ref = P.pc[who][pc];
        $("#proj-chk").textContent = `PC${pc + 1} no mapa: ${sgn(ref)} ✓`;
        return;
      }
      sum += rows[k].p;
      els[k].classList.add("on", "cur");
      $("#proj-tot").textContent = sgn(sum);
      $("#proj-run").textContent = `${k + 1} de ${rows.length} termos`;
      k++;
      setTimeout(step, REDUCE ? 0 : k < 10 ? 140 : 55);
    };
    step();
  }
  onSeen(box, play, 0.1);
}

/* ========================================================== 08 MAPA ===== */
function initMap() {
  const cv = $("#map-canvas"), screen = $(".map-screen"), tip = $("#map-tip"), panel = $("#player");
  const SX = new Float32Array(N), SY = new Float32Array(N);
  const filter = [true, true, true, true];
  let target = 1, t = 1, last = 0, hover = -1, sel = BY_NAME.get("L. Messi"), neigh = [];
  let L = null;

  $("#map-var").textContent = pct(D.variancia[0] + D.variancia[1]);
  $("#map-mode").addEventListener("click", (e) => {
    const b = e.target.closest("button"); if (!b) return;
    target = +b.dataset.m; $$("#map-mode button").forEach((x) => x.classList.toggle("on", x === b));
  });
  $("#map-legend").innerHTML = GROUPS.map((g, i) => `<button data-g="${i}"><i style="background:${GC[i]}"></i>${g}</button>`).join("");
  $("#map-legend").addEventListener("click", (e) => {
    const b = e.target.closest("button"); if (!b) return;
    const g = +b.dataset.g; filter[g] = !filter[g]; b.classList.toggle("off", !filter[g]);
    $("#map-count").textContent = nf(BY_GROUP.reduce((s, idx, k) => s + (filter[k] ? idx.length : 0), 0));
  });

  function nearest(px, py, maxD = 14) {
    let best = -1, bd = maxD * maxD;
    for (let i = 0; i < N; i++) {
      const dx = SX[i] - px, dy = SY[i] - py, d = dx * dx + dy * dy;
      if (d < bd) { bd = d; best = i; }
    }
    return best;
  }
  cv.addEventListener("mousemove", (e) => {
    const r = cv.getBoundingClientRect(), x = e.clientX - r.left, y = e.clientY - r.top;
    hover = nearest(x, y);
    if (hover < 0) { tip.classList.add("hidden"); return; }
    tip.classList.remove("hidden");
    tip.innerHTML = `<b>${esc(P.nome[hover])}</b>${P.posicao[hover]} · ${esc(P.clube[hover])} · ${P.overall[hover]}`;
    const left = x + 14 + tip.offsetWidth > r.width ? x - 14 - tip.offsetWidth : x + 14;
    tip.style.left = left + "px"; tip.style.top = Math.max(4, y - 40) + "px";
  });
  cv.addEventListener("mouseleave", () => { hover = -1; tip.classList.add("hidden"); });
  cv.addEventListener("click", (e) => {
    const r = cv.getBoundingClientRect(), i = nearest(e.clientX - r.left, e.clientY - r.top, 20);
    if (i >= 0) select(i);
  });

  const KEY = ["Finishing", "Dribbling", "BallControl", "ShortPassing", "StandingTackle", "Interceptions", "Strength", "GKReflexes"];
  function select(i) {
    sel = i;
    const d = [];
    for (let k = 0; k < N; k++) if (k !== i) d.push([k, (PC1[k] - PC1[i]) ** 2 + (PC2[k] - PC2[i]) ** 2]);
    d.sort((a, b) => a[1] - b[1]);
    neigh = d.slice(0, 5);
    const c = P.posicao[i], [px, py] = POS[c], g = GRP[i];
    panel.innerHTML = `<span class="lbl muted">${esc(P.clube[i])}</span><div class="pname">${esc(P.nome[i])}</div>`
      + `<div class="row2"><span class="ovr">${P.overall[i]}</span><span class="lbl"><i style="display:inline-block;width:8px;height:8px;border-radius:50%;background:${GC[g]};margin-right:6px"></i>${c} · ${POS[c][2]}</span></div>`
      + `<div class="pcs"><div class="m"><span class="lbl muted">PC1</span><div class="v" style="font-size:30px">${sgn(PC1[i])}</div></div><div class="m"><span class="lbl muted">PC2</span><div class="v" style="font-size:30px">${sgn(PC2[i])}</div></div></div>`
      + `<div class="mini-pitch"><svg viewBox="-3 -3 111 74">${pitchSVG()}`
      + Object.entries(POS).map(([k, [x, y]]) => `<circle cx="${x}" cy="${y}" r="${k === c ? 3.2 : 1}" fill="${k === c ? GC[g] : "rgba(233,231,223,.3)"}"/>`).join("")
      + `<text x="${px}" y="${py - 5}" fill="#fff" font-family="VT323" font-size="5" text-anchor="middle">${c}</text></svg></div>`
      + `<div class="bars">` + KEY.map((f) => { const v = P.atributos[i][fi(f)]; return `<div class="bar"><span class="n lbl" title="${esc(PT[f])}">${f}</span><span class="tr"><b class="f" style="width:${v}%"></b></span><span class="p">${v}</span></div>`; }).join("") + `</div>`
      + `<div class="bh mt" style="margin-bottom:0"><h2 style="font-size:16px"><i>≈</i>Mais parecidos no mapa</h2></div><ul class="list nb">`
      + neigh.map(([k, dd]) => `<li data-i="${k}"><span class="t">${esc(P.nome[k])} <span class="lbl muted">${P.posicao[k]}</span></span><span class="lbl muted">d = ${nf(Math.sqrt(dd), 2)}</span></li>`).join("") + `</ul>`;
  }
  panel.addEventListener("click", (e) => { const li = e.target.closest("li[data-i]"); if (li) select(+li.dataset.i); });
  select(sel);

  // busca
  const input = $("#map-search"), list = $("#map-results"), NAMES = P.nome.map(strip);
  let hits = [], cur = 0;
  const render = () => { list.innerHTML = hits.map((i, k) => `<li data-i="${i}" class="${k === cur ? "on" : ""}">${esc(P.nome[i])}<span>${P.posicao[i]} · ${P.overall[i]}</span></li>`).join(""); list.classList.toggle("hidden", !hits.length); };
  input.addEventListener("input", () => {
    const q = strip(input.value.trim());
    hits = [];
    if (q.length >= 2) for (let i = 0; i < N && hits.length < 8; i++) if (NAMES[i].includes(q)) hits.push(i);
    cur = 0; render();
  });
  input.addEventListener("keydown", (e) => {
    if (e.key === "ArrowDown") { cur = Math.min(hits.length - 1, cur + 1); render(); e.preventDefault(); }
    else if (e.key === "ArrowUp") { cur = Math.max(0, cur - 1); render(); e.preventDefault(); }
    else if (e.key === "Enter" && hits[cur] !== undefined) { select(hits[cur]); hits = []; render(); }
    else if (e.key === "Escape") { hits = []; render(); }
  });
  list.addEventListener("mousedown", (e) => { const li = e.target.closest("li"); if (li) { select(+li.dataset.i); input.value = P.nome[+li.dataset.i]; hits = []; render(); } });
  input.addEventListener("blur", () => setTimeout(() => { hits = []; render(); }, 150));

  loop(cv, (now) => {
    const dt = Math.min(0.05, (now - (last || now)) / 1000); last = now;
    t += clamp(target - t, -dt / 1.6, dt / 1.6);
    screen.classList.toggle("campo", t < 0.5);
    $("#map-osd").textContent = t < 0.5 ? "CAMPO · POSIÇÃO DE ORIGEM" : "MAPA · PC1 × PC2";
    const { ctx, w, h } = prep(cv);
    L = layout(w, h, { top: 46, bottom: 34, side: 28 });
    ctx.fillStyle = "#0c0d0d"; ctx.fillRect(0, 0, w, h);
    drawPitch(ctx, L.field, 1 - t * 1.4);
    drawMapAxes(ctx, L.map, t * 1.4 - 0.4);
    drawPlayers(ctx, L, t, { size: w < 600 ? 1.5 : 2, alpha: 0.55, filter, sx: SX, sy: SY });

    // destaques com nome (só no mapa assentado)
    const la = clamp((t - 0.8) * 5, 0, 1);
    if (la > 0) {
      ctx.globalAlpha = la; ctx.font = "15px VT323, monospace"; ctx.textAlign = "left";
      HIGHLIGHT.forEach((i) => {
        if (!filter[GRP[i]] || i === sel) return;
        ctx.fillStyle = "#fff"; ctx.fillRect(SX[i] - 2, SY[i] - 2, 4, 4);
        ctx.fillStyle = "rgba(255,255,255,.75)"; ctx.fillText(P.nome[i], SX[i] + 6, SY[i] + 4);
      });
      ctx.globalAlpha = 1;
    }
    // vizinhos + selecionado
    if (sel >= 0 && filter[GRP[sel]]) {
      const x = SX[sel], y = SY[sel];
      ctx.strokeStyle = "rgba(255,255,255,.55)"; ctx.beginPath();
      neigh.forEach(([k]) => { if (!Number.isNaN(SX[k])) { ctx.moveTo(x, y); ctx.lineTo(SX[k], SY[k]); } });
      ctx.stroke();
      ctx.strokeStyle = "rgba(255,255,255,.18)"; ctx.setLineDash([2, 4]); ctx.beginPath();
      ctx.moveTo(x, 0); ctx.lineTo(x, h); ctx.moveTo(0, y); ctx.lineTo(w, y); ctx.stroke(); ctx.setLineDash([]);
      const pulse = 7 + Math.sin(now / 200) * 2;
      ctx.strokeStyle = "#fff"; ctx.lineWidth = 2; ctx.beginPath(); ctx.arc(x, y, pulse, 0, Math.PI * 2); ctx.stroke(); ctx.lineWidth = 1;
      ctx.font = "22px VT323, monospace"; ctx.fillStyle = "#fff"; ctx.fillText(P.nome[sel].toUpperCase(), x + 12, y - 10);
    }
    if (hover >= 0) { ctx.strokeStyle = "#fff"; ctx.strokeRect(SX[hover] - 4, SY[hover] - 4, 8, 8); }
  });

  // loadings
  [0, 1].forEach((c) => {
    const W = D.loadings[c], top = F.map((f, j) => [f, W[j]]).sort((a, b) => Math.abs(b[1]) - Math.abs(a[1])).slice(0, 10);
    const max = Math.abs(top[0][1]);
    $(`#ld-pc${c + 1}`).innerHTML = top.map(([f, v]) => {
      const wd = (Math.abs(v) / max) * 50;
      return `<div class="bar"><span class="n lbl" title="${esc(PT[f])}">${f}</span><span class="tr dv"><b class="f ${v < 0 ? "neg" : ""}" data-l="${v < 0 ? 50 - wd : 50}" data-w="${wd}" style="left:50%"></b></span><span class="p">${sgn(v)}</span></div>`;
    }).join("");
    $(`#ld${c + 1}-var`).textContent = `${pct(D.variancia[c])} da variância`;
    onSeen($(`#ld-pc${c + 1}`), () => $$(`#ld-pc${c + 1} .f`).forEach((b) => { b.style.left = b.dataset.l + "%"; b.style.width = b.dataset.w + "%"; }));
  });
}

/* ===================================================== 09 VARIÂNCIA ===== */
function initVariance() {
  const R = D.variancia, cum = R.reduce((acc, v) => [...acc, (acc.at(-1) || 0) + v], []);
  const kAt = (lv) => cum.findIndex((c) => c >= lv) + 1;
  $("#var-80").textContent = `k = ${kAt(0.8)}`;
  $("#var-90").textContent = `k = ${kAt(0.9)}`;
  const cv = $("#var-canvas"), slider = $("#var-slider");
  let k = 2, t0 = null;
  const upd = () => {
    k = +slider.value;
    $("#var-k").textContent = `k = ${k}`; $("#var-k2").textContent = k; $("#var-pct").textContent = pct(cum[k - 1]);
  };
  slider.addEventListener("input", upd); upd();
  loop(cv, (now) => {
    if (t0 === null) t0 = now;
    const t = REDUCE ? 1 : clamp((now - t0) / 1600, 0, 1);
    const { ctx, w, h } = prep(cv), L = 40, Rt = w - 44, top = 46, bot = h - 34, n = R.length;
    const bw = (Rt - L) / n, ymax = 0.6;
    ctx.fillStyle = "#0c0d0d"; ctx.fillRect(0, 0, w, h);
    ctx.font = "14px VT323, monospace"; ctx.fillStyle = "rgba(233,231,223,.5)"; ctx.strokeStyle = "rgba(233,231,223,.1)";
    [0, 0.25, 0.5, 0.75, 1].forEach((v) => {
      const y = bot - v * (bot - top);
      ctx.beginPath(); ctx.moveTo(L, y + 0.5); ctx.lineTo(Rt, y + 0.5); ctx.stroke();
      ctx.textAlign = "left"; ctx.fillText(Math.round(v * 100) + "%", Rt + 6, y + 4);
      ctx.textAlign = "right"; ctx.fillText(Math.round(v * ymax * 100) + "%", L - 6, y + 4);
    });
    [0.8, 0.9].forEach((v) => {
      const y = bot - v * (bot - top);
      ctx.setLineDash([4, 4]); ctx.strokeStyle = "rgba(255,191,31,.5)"; ctx.beginPath(); ctx.moveTo(L, y); ctx.lineTo(Rt, y); ctx.stroke(); ctx.setLineDash([]);
    });
    for (let i = 0; i < n; i++) {
      const g = ease(clamp(t * 1.6 - i / n * 0.6, 0, 1));
      const bh = (R[i] / ymax) * (bot - top) * g;
      ctx.fillStyle = i < k ? "#e9e7df" : "rgba(233,231,223,.22)";
      ctx.fillRect(L + i * bw + 1, bot - bh, Math.max(1, bw - 2), bh);
    }
    ctx.strokeStyle = GC[2]; ctx.lineWidth = 2; ctx.beginPath();
    const upto = Math.max(1, Math.floor(n * t));
    for (let i = 0; i < upto; i++) { const x = L + (i + 0.5) * bw, y = bot - cum[i] * (bot - top); i ? ctx.lineTo(x, y) : ctx.moveTo(x, y); }
    ctx.stroke(); ctx.lineWidth = 1;
    const kx = L + (k - 0.5) * bw, ky = bot - cum[k - 1] * (bot - top);
    if (t >= 1) {
      ctx.fillStyle = GC[2]; ctx.beginPath(); ctx.arc(kx, ky, 5, 0, Math.PI * 2); ctx.fill();
      ctx.font = "20px VT323, monospace"; ctx.fillStyle = "#fff"; ctx.textAlign = kx > w * 0.6 ? "right" : "left";
      ctx.fillText(`k=${k} · ${pct(cum[k - 1])}`, kx + (kx > w * 0.6 ? -10 : 10), ky - 10);
    }
    ctx.font = "14px VT323, monospace"; ctx.fillStyle = "rgba(233,231,223,.5)"; ctx.textAlign = "center";
    [1, 5, 10, 15, 20, 25, 30, 37].forEach((i) => ctx.fillText("PC" + i, L + (i - 0.5) * bw, bot + 18));
  });
}

/* ======================================================== 10 MODELO ===== */
function initClassifier() {
  const C = D.classificador, bars = $("#clf-bars"), cm = $("#cm");
  const label = (c) => (c.k === 0 ? "Dummy (sempre Meio)" : c.pca ? `PCA k = ${c.k}` : `${c.k} atributos`);
  bars.innerHTML = C.map((c, i) => `<div class="bar ${c.k === 0 ? "dummy" : !c.pca ? "full" : ""}" data-i="${i}"><span class="n lbl">${label(c)}</span><span class="tr"><b class="f" data-w="${c.f1 * 100}"></b></span><span class="p">${nf(c.f1, 3)}</span></div>`).join("");
  const short = ["GOL", "DEF", "MEI", "ATA"];
  function show(i) {
    const c = C[i];
    if (!c.confusao) return;
    $$(".bar", bars).forEach((b) => b.classList.toggle("on", +b.dataset.i === i));
    $("#cm-k").textContent = c.pca ? `k=${c.k}` : "37";
    let html = `<span></span>` + short.map((s, j) => `<span class="h" style="justify-content:center">${s}</span>`).join("");
    c.confusao.forEach((row, r) => {
      const tot = row.reduce((a, b) => a + b, 0);
      html += `<span class="h r"><i style="display:inline-block;width:8px;height:8px;border-radius:50%;background:${GC[r]};margin-right:6px"></i>${GROUPS[r]}</span>`;
      row.forEach((v, j) => {
        const p = v / tot;
        html += `<span class="c ${r === j ? "diag" : ""}" style="background:rgba(18,18,18,${p.toFixed(3)});color:${p > 0.45 ? "#f6f5f1" : "#121212"}"><span>${nf(v)}<small>${pct(p, 0)}</small></span></span>`;
      });
    });
    cm.innerHTML = html;
  }
  bars.addEventListener("click", (e) => { const b = e.target.closest(".bar"); if (b) show(+b.dataset.i); });
  show(C.findIndex((c) => c.k === 2));
  onSeen(bars, () => $$(".f", bars).forEach((b, i) => setTimeout(() => { b.style.width = b.dataset.w + "%"; }, i * 120)));
}

/* ============================================================ INÍCIO ===== */
initHeader();
fillNumbers();
initHero();
initRaw();
initPitch();
initClean();
initScale();
initCorr();
initEigen();
initProjection();
initMap();
initVariance();
initClassifier();
requestAnimationFrame(frame);
