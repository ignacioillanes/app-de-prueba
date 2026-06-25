"""Scraper para programas de postgrado de la Universidad de Santiago de Chile."""
from typing import List
from .base import BaseScraper
from ..utils.models import Programa
from .uc import _normalizar_tipo, _normalizar_modalidad
from .uchile import _extraer_area

URL_POSTGRADOS = "https://www.usach.cl/postgrado"


class USACHScraper(BaseScraper):
    nombre = "usach"
    url_base = "https://www.usach.cl"

    def scrape(self) -> List[Programa]:
        programas = []
        try:
            soup = self.get(URL_POSTGRADOS)
            items = soup.select("a[href*='postgrado'], a[href*='magister'], a[href*='doctorado']")
            seen = set()
            for a in items:
                nombre = a.get_text(strip=True)
                if len(nombre) < 8 or nombre in seen:
                    continue
                seen.add(nombre)
                href = a.get("href", "")
                url = href if href.startswith("http") else f"{self.url_base}{href}"
                meta = nombre.lower()
                p = Programa(
                    institucion="Universidad de Santiago de Chile",
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
            print(f"[USACH] Error scraping: {e}")
        return programas
