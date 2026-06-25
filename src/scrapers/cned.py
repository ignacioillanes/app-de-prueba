"""
Cliente para datos públicos del CNED (Consejo Nacional de Educación).
Consume el portal de datos abiertos datos.cned.cl / API CNED.
"""
import httpx
from typing import List
from ..utils.models import Programa
from .uc import _normalizar_tipo, _normalizar_modalidad
from .uchile import _extraer_area

# Portal de datos abiertos CNED
CNED_API = "https://api.cned.cl/api/programas"
CNED_PORTAL = "https://datos.cned.cl"


class CNEDClient:
    nombre = "cned"

    def __init__(self):
        self.client = httpx.Client(timeout=60, follow_redirects=True, verify=False)

    def fetch(self) -> List[Programa]:
        programas = []
        try:
            r = self.client.get(
                CNED_API,
                params={"nivel": "postgrado", "limit": 500},
            )
            if r.status_code == 200:
                data = r.json()
                items = data if isinstance(data, list) else data.get("data", data.get("results", []))
                for item in items:
                    p = self._parse(item)
                    if p:
                        programas.append(p)
        except Exception as e:
            print(f"[CNED] API no disponible ({e}), intenta con scraping manual")
        return programas

    def _parse(self, item: dict) -> Programa | None:
        nombre = item.get("nombre_programa") or item.get("nombre") or ""
        if not nombre:
            return None
        return Programa(
            institucion=item.get("institucion") or item.get("nombre_institucion") or "Desconocida",
            nombre=nombre,
            tipo=_normalizar_tipo(item.get("nivel", "") + " " + nombre),
            area=_extraer_area((item.get("area_conocimiento") or nombre).lower()),
            modalidad=_normalizar_modalidad(item.get("modalidad", "")),
            duracion_meses=_to_int(item.get("duracion_semestres", 0)) * 6 if item.get("duracion_semestres") else None,
            arancel_clp=_to_int(item.get("arancel")),
            ciudad=item.get("ciudad"),
            region=item.get("region"),
            fuente=self.nombre,
        )

    def close(self):
        self.client.close()


def _to_int(val) -> int | None:
    try:
        return int(float(str(val).replace(".", "").replace(",", ".")))
    except (ValueError, TypeError):
        return None
