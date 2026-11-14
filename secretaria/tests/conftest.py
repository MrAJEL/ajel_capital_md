from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace
from zoneinfo import ZoneInfo

import pytest

from ajel_secretaria.calendarios.memoria import CalendarioMemoria
from ajel_secretaria.modelos import Evento
from ajel_secretaria.pendientes import BandejaPendientes
from ajel_secretaria.perfil import cargar_perfil

TZ = ZoneInfo("America/Mexico_City")
# Monday 2026-11-16 08:00 local time.
AHORA = datetime(2026, 11, 16, 8, 0, tzinfo=TZ)


def en(dia: int, h: int, m: int = 0) -> datetime:
    """Datetime on 2026-11-<dia> at h:m local time."""
    return datetime(2026, 11, dia, h, m, tzinfo=TZ)


@pytest.fixture
def perfil():
    return cargar_perfil("ajel_studio")  # 09-18 Mon-Thu, 09-15 Fri, 45 min, margin 15, notice 4 h


@pytest.fixture
def calendario():
    return CalendarioMemoria(
        [
            Evento("e1", "Reunión", en(16, 13), en(16, 14)),
            Evento("e2", "Libre", en(16, 15), en(16, 16), ocupa=False),
        ]
    )


@pytest.fixture
def bandeja():
    return BandejaPendientes()


def texto(t: str):
    return SimpleNamespace(type="text", text=t)


def uso(id_: str, nombre: str, entrada: dict):
    return SimpleNamespace(type="tool_use", id=id_, name=nombre, input=entrada)


def respuesta(stop: str, *bloques):
    return SimpleNamespace(stop_reason=stop, content=list(bloques))


class ClienteFalso:
    """Mimics ``client.beta.messages.create`` with scripted responses."""

    def __init__(self, respuestas):
        self._respuestas = list(respuestas)
        self.llamadas: list[dict] = []
        self.beta = SimpleNamespace(messages=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        # Copy the message list: the agent keeps mutating it after the call.
        self.llamadas.append({**kwargs, "messages": list(kwargs["messages"])})
        return self._respuestas.pop(0)
