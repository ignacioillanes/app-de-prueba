from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


@dataclass
class Programa:
    institucion: str
    nombre: str
    tipo: str                    # magister, doctorado, diplomado, curso, especialidad
    area: str                    # ingenieria, negocios, salud, derecho, humanidades, etc.
    modalidad: str               # presencial, online, hibrido
    duracion_meses: Optional[int] = None
    arancel_clp: Optional[int] = None
    creditos: Optional[int] = None
    url: Optional[str] = None
    ciudad: Optional[str] = None
    region: Optional[str] = None
    fecha_inicio: Optional[str] = None
    requisitos: Optional[str] = None
    fuente: Optional[str] = None
    fecha_scraping: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items()}
