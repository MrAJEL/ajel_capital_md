"""Calendar provider interface. Implementations: in-memory (demo/tests) and Google Calendar."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol

from ..modelos import Evento


class ProveedorCalendario(Protocol):
    def listar_eventos(self, desde: datetime, hasta: datetime) -> list[Evento]: ...

    def obtener_evento(self, evento_id: str) -> Evento | None: ...

    def crear_evento(
        self,
        titulo: str,
        inicio: datetime,
        fin: datetime,
        invitados: list[str],
        descripcion: str,
        ubicacion: str,
    ) -> Evento: ...

    def mover_evento(self, evento_id: str, inicio: datetime, fin: datetime) -> Evento: ...

    def cancelar_evento(self, evento_id: str) -> None: ...
