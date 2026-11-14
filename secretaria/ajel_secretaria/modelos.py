"""Data types shared by the calendar providers, the agent and the approval inbox."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Literal

TipoAccion = Literal["crear", "mover", "cancelar"]
EstadoAccion = Literal["pendiente", "aprobada", "rechazada", "fallida"]


@dataclass(frozen=True)
class Evento:
    """A calendar event. Datetimes are always timezone-aware."""

    id: str
    titulo: str
    inicio: datetime
    fin: datetime
    invitados: tuple[str, ...] = ()
    descripcion: str = ""
    ubicacion: str = ""
    ocupa: bool = True  # False when the event is marked "free" (transparent)

    def a_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "titulo": self.titulo,
            "inicio": self.inicio.isoformat(),
            "fin": self.fin.isoformat(),
            "invitados": list(self.invitados),
            "descripcion": self.descripcion,
            "ubicacion": self.ubicacion,
            "ocupa": self.ocupa,
        }


@dataclass(frozen=True)
class Hueco:
    inicio: datetime
    fin: datetime

    def a_dict(self) -> dict[str, str]:
        return {"inicio": self.inicio.isoformat(), "fin": self.fin.isoformat()}


@dataclass
class AccionPendiente:
    """A write action proposed by the agent that waits for a human decision."""

    id: str
    tipo: TipoAccion
    datos: dict[str, Any]
    resumen: str
    creada: str
    estado: EstadoAccion = "pendiente"
    resultado: str = ""

    def a_dict(self) -> dict[str, Any]:
        return asdict(self)
