"""Free-slot search: business hours minus busy events, with buffer and minimum notice."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime, timedelta

from .modelos import Evento, Hueco
from .perfil import Perfil


def _redondear_arriba(momento: datetime, paso_min: int) -> datetime:
    """Round up to the next multiple of ``paso_min`` minutes (local wall clock)."""
    base = momento.replace(second=0, microsecond=0)
    if base < momento:
        base += timedelta(minutes=1)
    resto = (base.hour * 60 + base.minute) % paso_min
    return base if resto == 0 else base + timedelta(minutes=paso_min - resto)


def limites_validos(perfil: Perfil, ahora: datetime) -> tuple[datetime, datetime]:
    """Earliest and latest moments the profile allows booking, from ``ahora``."""
    ahora = ahora.astimezone(perfil.tz)
    return (
        ahora + timedelta(hours=perfil.antelacion_min_horas),
        ahora + timedelta(days=perfil.dias_max_adelante),
    )


def dentro_de_horario(perfil: Perfil, inicio: datetime, fin: datetime) -> bool:
    inicio, fin = inicio.astimezone(perfil.tz), fin.astimezone(perfil.tz)
    rango = perfil.horario.get(inicio.weekday())
    if rango is None or inicio.date() != fin.date():
        return False
    return rango[0] <= inicio.time() and fin.time() <= rango[1]


def conflictos(
    eventos: Iterable[Evento],
    inicio: datetime,
    fin: datetime,
    margen_min: int,
    ignorar_id: str | None = None,
) -> list[Evento]:
    """Busy events that overlap [inicio, fin] once the buffer is applied on both sides."""
    margen = timedelta(minutes=margen_min)
    return [
        e
        for e in eventos
        if e.ocupa and e.id != ignorar_id and inicio < e.fin + margen and fin > e.inicio - margen
    ]


def buscar_huecos(
    eventos: Iterable[Evento],
    perfil: Perfil,
    desde: datetime,
    hasta: datetime,
    duracion_min: int,
    ahora: datetime,
    max_resultados: int = 8,
    paso_min: int = 15,
) -> list[Hueco]:
    """Return up to ``max_resultados`` free slots of ``duracion_min`` minutes."""
    if duracion_min <= 0:
        raise ValueError("duracion_min debe ser positiva")
    tz = perfil.tz
    ocupados = [e for e in eventos if e.ocupa]
    minimo, maximo = limites_validos(perfil, ahora)
    desde = max(desde.astimezone(tz), minimo)
    hasta = min(hasta.astimezone(tz), maximo)
    duracion = timedelta(minutes=duracion_min)
    salto_tras_hueco = duracion + timedelta(minutes=perfil.margen_min)

    resultados: list[Hueco] = []
    dia = desde.date()
    while dia <= hasta.date() and len(resultados) < max_resultados:
        rango = perfil.horario.get(dia.weekday())
        if rango:
            abre = datetime.combine(dia, rango[0], tz)
            cierra = datetime.combine(dia, rango[1], tz)
            cursor = _redondear_arriba(max(abre, desde), paso_min)
            limite = min(cierra, hasta)
            while cursor + duracion <= limite and len(resultados) < max_resultados:
                fin = cursor + duracion
                if conflictos(ocupados, cursor, fin, perfil.margen_min):
                    cursor += timedelta(minutes=paso_min)
                else:
                    resultados.append(Hueco(cursor, fin))
                    cursor = _redondear_arriba(cursor + salto_tras_hueco, paso_min)
        dia += timedelta(days=1)
    return resultados
