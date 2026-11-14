"""In-memory calendar for demos and tests."""

from __future__ import annotations

import itertools
from dataclasses import replace
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from ..modelos import Evento


class CalendarioMemoria:
    def __init__(self, eventos: list[Evento] | None = None) -> None:
        self._eventos: dict[str, Evento] = {e.id: e for e in eventos or []}
        self._ids = itertools.count(1)

    def listar_eventos(self, desde: datetime, hasta: datetime) -> list[Evento]:
        return sorted(
            (e for e in self._eventos.values() if e.inicio < hasta and e.fin > desde),
            key=lambda e: e.inicio,
        )

    def obtener_evento(self, evento_id: str) -> Evento | None:
        return self._eventos.get(evento_id)

    def crear_evento(self, titulo, inicio, fin, invitados, descripcion, ubicacion) -> Evento:
        evento = Evento(
            id=f"mem-{next(self._ids)}",
            titulo=titulo,
            inicio=inicio,
            fin=fin,
            invitados=tuple(invitados),
            descripcion=descripcion,
            ubicacion=ubicacion,
        )
        self._eventos[evento.id] = evento
        return evento

    def mover_evento(self, evento_id: str, inicio: datetime, fin: datetime) -> Evento:
        evento = replace(self._requerir(evento_id), inicio=inicio, fin=fin)
        self._eventos[evento_id] = evento
        return evento

    def cancelar_evento(self, evento_id: str) -> None:
        self._requerir(evento_id)
        del self._eventos[evento_id]

    def _requerir(self, evento_id: str) -> Evento:
        if evento_id not in self._eventos:
            raise KeyError(f"No existe el evento {evento_id}")
        return self._eventos[evento_id]


def calendario_demo(zona_horaria: str, ahora: datetime | None = None) -> CalendarioMemoria:
    """A calendar with a few events over the next working days, for trying the agent."""
    tz = ZoneInfo(zona_horaria)
    hoy = (ahora or datetime.now(tz)).astimezone(tz).date()
    dias_laborables = [hoy + timedelta(days=i) for i in range(1, 10)]
    dias_laborables = [d for d in dias_laborables if d.weekday() < 5][:3]

    def ev(i: int, dia, h: int, m: int, dur: int, titulo: str) -> Evento:
        inicio = datetime.combine(dia, time(h, m), tz)
        return Evento(f"demo-{i}", titulo, inicio, inicio + timedelta(minutes=dur))

    d1, d2, d3 = dias_laborables
    return CalendarioMemoria(
        [
            ev(1, d1, 10, 0, 60, "Reunión interna"),
            ev(2, d1, 13, 0, 60, "Comida"),
            ev(3, d2, 9, 0, 120, "Bloque de trabajo"),
            ev(4, d2, 15, 0, 45, "Llamada con proveedor"),
            ev(5, d3, 11, 0, 30, "Seguimiento cliente"),
        ]
    )
