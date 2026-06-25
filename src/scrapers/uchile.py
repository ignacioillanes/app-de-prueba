"""Scraper para programas de postgrado de la Universidad de Chile."""
from typing import List
from .base import BaseScraper
from ..utils.models import Programa
from .uc import _normalizar_tipo, _normalizar_modalidad

URL_POSTGRADOS = "https://www.postgrados.uchile.cl/programas"


class UChileScraper(BaseScraper):
    nombre = "uchile"
    url_base = "https://www.postgrados.uchile.cl"

    def scrape(self) -> List[Programa]:
        programas = []
        try:
            soup = self.get(URL_POSTGRADOS)
            items = soup.select(".programa, .program, article, .card")
            for item in items:
                titulo = item.select_one("h2, h3, h4, .title")
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
                p = Programa(
                    institucion="Universidad de Chile",
                    nombre=nombre,
                    tipo=_normalizar_tipo(meta),
                    area=_extraer_area(meta),
                    modalidad=_normalizar_modalidad(meta),
                    url=url,
                    ciudad="Santiago",
                    region="Región Metropolitana",
                    fuente=self.nombre,
                )
                programas.append(p)
        except Exception as e:
            print(f"[UChile] Error scraping: {e}")
        return programas


def _extraer_area(texto: str) -> str:
    areas = {
        "ingeniería": "ingenieria",
        "negocios": "negocios",
        "administración": "negocios",
        "mba": "negocios",
        "derecho": "derecho",
        "medicina": "salud",
        "salud": "salud",
        "educación": "educacion",
        "ciencias": "ciencias",
        "humanidades": "humanidades",
        "arte": "artes",
        "comunicación": "comunicacion",
        "psicología": "psicologia",
        "economía": "economia",
    }
    for kw, area in areas.items():
        if kw in texto:
            return area
    return "otros"
