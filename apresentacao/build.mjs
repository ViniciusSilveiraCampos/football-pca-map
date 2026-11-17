#!/usr/bin/env node
// Monta a apresentação a partir de deck.json + slides/<id>.html (o mesmo formato do deck
// "Slides" do Claude: um <section> de 1920×1080 por arquivo, estilos inline, notas no <aside>).
//
//   node apresentacao/build.mjs          -> apresentacao/dist/index.html (navegável)
//   node apresentacao/build.mjs --pdf    -> também apresentacao/dist/apresentacao.pdf
//
// Para o PDF usa o Chrome/Chromium instalado (ou o caminho em $CHROME). Sem dependências npm.
import { spawnSync } from "node:child_process";
import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const dist = join(here, "dist");
const deck = JSON.parse(readFileSync(join(here, "deck.json"), "utf8"));

const ID = /^[A-Za-z0-9_-]{1,64}$/;
const slides = deck.order.map((id) => {
  if (!ID.test(id)) throw new Error(`id de slide inválido em deck.json: ${id}`);
  const file = join(here, "slides", `${id}.html`);
  if (!existsSync(file)) throw new Error(`slide ausente: slides/${id}.html`);
  return readFileSync(file, "utf8").trim();
});

const fonts = Object.values(deck.faces || {})
  .filter((f) => f.href?.startsWith("https://fonts.googleapis.com/"))
  .map((f) => `<link rel="stylesheet" href="${f.href}">`)
  .join("\n");

// Padrões do formato Slides: canvas fixo, h1–h3/p sem margem (96/64/44/32 px),
// tabela com linhas finas e cabeçalho em negrito, <aside> = notas do apresentador.
const css = `
* { margin: 0; }
html, body { background: #0b0b0b; }
body { overflow: hidden; }
.deck section { width: 1920px; height: 1080px; position: relative; overflow: hidden; box-sizing: border-box; }
.deck h1 { font-size: 96px; font-weight: 600; }
.deck h2 { font-size: 64px; font-weight: 600; }
.deck h3 { font-size: 44px; font-weight: 600; }
.deck p { font-size: 32px; font-weight: 400; }
.deck table { width: 100%; border-collapse: collapse; }
.deck th, .deck td { padding: .35em .6em; text-align: left; vertical-align: top; font-weight: 400;
  border-bottom: 1px solid color-mix(in srgb, currentColor 28%, transparent); }
.deck tr:first-child th { font-weight: 700; border-bottom-width: 2px; }
.deck aside { display: none; }

/* tela: um slide por vez, escalado para caber */
@media screen {
  .deck { position: fixed; left: 50%; top: 50%; width: 1920px; height: 1080px;
    transform: translate(-50%, -50%) scale(var(--s, .5)); }
  .deck section { position: absolute; inset: 0; display: none; }
  .deck section.cur { display: block; animation: in .25s ease-out; }
  @keyframes in { from { opacity: 0; } }
  .hud { position: fixed; right: 14px; bottom: 10px; font: 13px/1 'IBM Plex Mono', monospace;
    color: #888; letter-spacing: 1px; user-select: none; }
  .notes { position: fixed; left: 0; right: 0; bottom: 0; max-height: 34vh; overflow: auto; display: none;
    background: rgba(12, 13, 13, .94); color: #e9e7df; font: 18px/1.5 'IBM Plex Mono', monospace;
    padding: 18px 28px 34px; border-top: 2px solid #2340ff; }
  body.show-notes .notes { display: block; }
}
@media print {
  @page { size: 1920px 1080px; margin: 0; }
  html, body { background: none; overflow: visible; }
  .deck section { break-after: page; }
  .hud, .notes { display: none; }
}
`;

const js = `
const S = [...document.querySelectorAll(".deck section")];
const hud = document.querySelector(".hud"), notes = document.querySelector(".notes");
let i = 0;
function fit() {
  const s = Math.min(innerWidth / 1920, innerHeight / 1080);
  document.documentElement.style.setProperty("--s", s);
}
function go(n) {
  i = Math.max(0, Math.min(S.length - 1, n));
  S.forEach((s, k) => s.classList.toggle("cur", k === i));
  hud.textContent = (i + 1) + " / " + S.length;
  const a = S[i].querySelector("aside");
  notes.textContent = a ? a.textContent.trim() : "";
  history.replaceState(null, "", "#" + (i + 1));
}
addEventListener("resize", fit);
addEventListener("keydown", (e) => {
  if (["ArrowRight", "ArrowDown", "PageDown", " ", "Enter"].includes(e.key)) go(i + 1);
  else if (["ArrowLeft", "ArrowUp", "PageUp", "Backspace"].includes(e.key)) go(i - 1);
  else if (e.key === "Home") go(0);
  else if (e.key === "End") go(S.length - 1);
  else if (e.key === "n" || e.key === "N") document.body.classList.toggle("show-notes");
  else if (e.key === "f" || e.key === "F") document.fullscreenElement ? document.exitFullscreen() : document.documentElement.requestFullscreen();
  else return;
  e.preventDefault();
});
addEventListener("click", (e) => { if (!e.target.closest(".notes")) go(i + (e.clientX < innerWidth / 3 ? -1 : 1)); });
fit();
go((parseInt(location.hash.slice(1), 10) || 1) - 1);
`;

const html = `<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>${deck.title}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
${fonts}
<style>${css}</style>
</head>
<body>
<!-- gerado por apresentacao/build.mjs a partir de deck.json e slides/; não edite à mão -->
<div class="deck">
${slides.join("\n")}
</div>
<div class="hud"></div>
<div class="notes"></div>
<script>${js}</script>
</body>
</html>
`;

mkdirSync(dist, { recursive: true });
const out = join(dist, "index.html");
writeFileSync(out, html);
console.log(`${slides.length} slides -> ${out}`);

if (process.argv.includes("--pdf")) {
  const candidates = [process.env.CHROME, "google-chrome", "google-chrome-stable", "chromium", "chromium-browser"].filter(Boolean);
  const chrome = candidates.find((c) => spawnSync(c, ["--version"], { stdio: "ignore" }).status === 0);
  if (!chrome) throw new Error("Chrome/Chromium não encontrado (defina $CHROME)");
  const pdf = join(dist, "apresentacao.pdf");
  // virtual-time-budget dá tempo para as fontes do Google Fonts carregarem antes de imprimir
  const r = spawnSync(chrome, [
    "--headless=new", "--disable-gpu", "--no-sandbox", "--no-pdf-header-footer",
    "--virtual-time-budget=20000", "--run-all-compositor-stages-before-draw",
    `--print-to-pdf=${pdf}`, "file://" + resolve(out),
  ], { stdio: ["ignore", "inherit", "inherit"] });
  if (r.status !== 0 || !existsSync(pdf)) throw new Error(`falha ao gerar o PDF (status ${r.status})`);
  console.log(`PDF -> ${pdf}`);
}
