"""Scraper para programas de postgrado de la Pontificia Universidad Católica de Chile."""
from typing import List
from .base import BaseScraper
from ..utils.models import Programa

URL_POSTGRADOS = "https://postgrado.uc.cl/programas"


class UCScraper(BaseScraper):
    nombre = "uc"
    url_base = "https://postgrado.uc.cl"

    def scrape(self) -> List[Programa]:
        programas = []
        try:
            soup = self.get(URL_POSTGRADOS)
            cards = soup.select("article.program-card, div.programa-item, .card-programa")
            if not cards:
                # Fallback: buscar cualquier enlace de programa
                cards = soup.select("a[href*='/programas/']")
            for card in cards:
                nombre = (
                    card.select_one("h2, h3, .title, .nombre")
                    or card
                )
                tipo_raw = (card.get("data-tipo") or "").lower()
                tipo = _normalizar_tipo(tipo_raw or card.get_text())
                area_raw = card.get("data-area", "")
                modalidad_raw = (card.get("data-modalidad") or "").lower()
                p = Programa(
                    institucion="Pontificia Universidad Católica de Chile",
                    nombre=nombre.get_text(strip=True) if hasattr(nombre, "get_text") else str(nombre),
                    tipo=tipo,
                    area=area_raw or "Sin clasificar",
                    modalidad=_normalizar_modalidad(modalidad_raw),
                    url=_abs(card.get("href") or card.select_one("a", href=True) and card.select_one("a")["href"] or ""),
                    ciudad="Santiago",
                    region="Región Metropolitana",
                    fuente=self.nombre,
                )
                programas.append(p)
        except Exception as e:
            print(f"[UC] Error scraping: {e}")
        return programas


def _normalizar_tipo(texto: str) -> str:
    t = texto.lower()
    if "magíster" in t or "magister" in t or "máster" in t:
        return "magister"
    if "doctorado" in t or "phd" in t:
        return "doctorado"
    if "diplomado" in t:
        return "diplomado"
    if "especialidad" in t or "especialización" in t:
        return "especialidad"
    if "postítulo" in t or "postítulo" in t:
        return "postitulo"
    return "curso"


def _normalizar_modalidad(texto: str) -> str:
    if "online" in texto or "distancia" in texto or "e-learning" in texto:
        return "online"
    if "híbrido" in texto or "hibrido" in texto or "semipresencial" in texto:
        return "hibrido"
    return "presencial"


def _abs(url: str) -> str:
    if url and not url.startswith("http"):
        return f"https://postgrado.uc.cl{url}"
    return url or ""
