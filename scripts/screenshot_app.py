"""Tira capturas de tela de cada aba do protótipo para o README.

Sobe o app Streamlit e usa Playwright com o Chromium do sistema (CHROMIUM_PATH
ou `chromium` no PATH) ou o do `playwright install chromium`.

    uv run python scripts/screenshot_app.py
"""

import os
import shutil
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

PORT = 8599
URL = f"http://localhost:{PORT}"
OUT_DIR = Path("docs/img")
VIEWPORT = {"width": 1400, "height": 900}
# O Streamlit marca o app como "running" e os elementos antigos com data-stale
# enquanto um rerun não termina.
IDLE_JS = """() => {
  const app = document.querySelector('[data-testid="stApp"]');
  return app && app.dataset.testScriptState !== "running"
    && !document.querySelector('[data-stale="true"]');
}"""


def start_app() -> subprocess.Popen:
    cmd = [
        sys.executable, "-m", "streamlit", "run", "src/football_pca_map/app.py",
        "--server.headless", "true",
        "--server.port", str(PORT),
        "--browser.gatherUsageStats", "false",
        "--theme.base", "light",
        "--client.toolbarMode", "minimal",
    ]  # fmt: skip
    app = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(120):
        try:
            urllib.request.urlopen(f"{URL}/_stcore/health", timeout=1)  # noqa: S310
            return app
        except OSError:
            time.sleep(0.5)
    app.terminate()
    raise RuntimeError("O app Streamlit não respondeu em 60 s")


def settle(page: Page) -> None:
    page.wait_for_timeout(250)
    page.wait_for_function(IDLE_JS, timeout=120000)
    page.wait_for_timeout(1500)


def open_tab(page: Page, tab: str) -> None:
    page.get_by_role("tab", name=tab).click()
    page.get_by_role("tabpanel", name=tab).locator(".js-plotly-plot").first.wait_for()
    settle(page)


def prepare_create(page: Page) -> None:
    """Messi com atributos de goleiro no máximo: o exemplo usado no README."""
    for label in ["GKDiving", "GKHandling", "GKPositioning", "GKReflexes"]:
        slider = (
            page.locator('[data-testid="stSlider"]')
            .filter(has_text=label)
            .get_by_role("slider")
        )
        slider.focus()
        page.keyboard.press("End")
        settle(page)


def prepare_challenge(page: Page) -> None:
    page.get_by_text("I. Gueye (RDM)", exact=True).click()
    settle(page)


# nome do arquivo → (aba, preparação antes da captura)
SHOTS = {
    "prototipo_mapa": ("Mapa", None),
    "prototipo_crie_jogador": ("Crie seu jogador", prepare_create),
    "prototipo_eixos": ("O que são os eixos?", None),
    "prototipo_desafio": ("Desafie o modelo", prepare_challenge),
}


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    chromium = os.environ.get("CHROMIUM_PATH") or shutil.which("chromium")
    app = start_app()
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(executable_path=chromium)
            page = browser.new_page(viewport=VIEWPORT, device_scale_factor=1)
            page.goto(URL)
            page.get_by_text("Busque um jogador").wait_for(timeout=180000)
            settle(page)
            for name, (tab, prepare) in SHOTS.items():
                open_tab(page, tab)
                if prepare:
                    prepare(page)
                path = OUT_DIR / f"{name}.png"
                page.screenshot(path=path)
                print(path)
            browser.close()
    finally:
        app.terminate()


if __name__ == "__main__":
    main()
