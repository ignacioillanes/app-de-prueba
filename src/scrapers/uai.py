"""Scraper para programas de postgrado de la Universidad Adolfo Ibáñez."""
from typing import List
from .base import BaseScraper
from ..utils.models import Programa
from .uc import _normalizar_tipo, _normalizar_modalidad
from .uchile import _extraer_area

URL_POSTGRADOS = "https://postgrado.uai.cl"


class UAIScraper(BaseScraper):
    nombre = "uai"
    url_base = "https://postgrado.uai.cl"

    def scrape(self) -> List[Programa]:
        programas = []
        try:
            soup = self.get(URL_POSTGRADOS)
            items = soup.select(".program-card, .curso-item, article, .card")
            for item in items:
                titulo = item.select_one("h2, h3, h4, .title, .name")
                if not titulo:
                    continue
                nombre = titulo.get_text(strip=True)
                if len(nombre) < 5:
                    continue
                link = item.select_one("a")
                url = ""
                if link and link.get("href"):
                    href = link["href"]
                    url = href if href.startswith("http") else f"{self.url_base}{href}"
                meta = item.get_text(" ", strip=True).lower()
                precio_tag = item.select_one(".precio, .arancel, .price")
                arancel = None
                if precio_tag:
                    arancel = _parsear_precio(precio_tag.get_text())
                p = Programa(
                    institucion="Universidad Adolfo Ibáñez",
                    nombre=nombre,
                    tipo=_normalizar_tipo(meta),
                    area=_extraer_area(meta),
                    modalidad=_normalizar_modalidad(meta),
                    arancel_clp=arancel,
                    url=url,
                    ciudad="Santiago",
                    region="Región Metropolitana",
                    fuente=self.nombre,
                )
                programas.append(p)
        except Exception as e:
            print(f"[UAI] Error scraping: {e}")
        return programas


def _parsear_precio(texto: str) -> int | None:
    import re
    nums = re.findall(r"[\d\.]+", texto.replace(",", "."))
    if nums:
        try:
            val = float(nums[0].replace(".", ""))
            return int(val) if val > 1000 else int(val * 1_000_000)
        except ValueError:
            pass
    return None
