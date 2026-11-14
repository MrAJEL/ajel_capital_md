"""Daily briefing built without the model: today's events, free slots and pending approvals."""

from __future__ import annotations

from datetime import date, datetime, time, timedelta

from .calendarios.base import ProveedorCalendario
from .huecos import buscar_huecos
from .pendientes import BandejaPendientes
from .perfil import NOMBRES_DIAS, Perfil


def resumen_del_dia(
    perfil: Perfil,
    calendario: ProveedorCalendario,
    bandeja: BandejaPendientes,
    dia: date,
    ahora: datetime | None = None,
) -> str:
    tz = perfil.tz
    inicio = datetime.combine(dia, time(0), tz)
    fin = inicio + timedelta(days=1)
    eventos = calendario.listar_eventos(inicio, fin)

    lineas = [f"📅 {perfil.nombre_negocio} · {NOMBRES_DIAS[dia.weekday()]} {dia:%d/%m/%Y}", ""]
    if eventos:
        lineas.append(f"Citas ({len(eventos)}):")
        for e in eventos:
            lineas.append(f"  • {e.inicio.astimezone(tz):%H:%M}–{e.fin.astimezone(tz):%H:%M}  {e.titulo}")
    else:
        lineas.append("Sin citas.")

    if dia.weekday() in perfil.horario:
        # Use the start of the day as "now" so the briefing shows the day's whole capacity.
        referencia = ahora or (inicio - timedelta(hours=perfil.antelacion_min_horas))
        huecos = buscar_huecos(
            eventos, perfil, inicio, fin, perfil.duracion_cita_min, referencia, max_resultados=20
        )
        horas = ", ".join(f"{h.inicio:%H:%M}" for h in huecos) or "ninguno"
        lineas += ["", f"Huecos de {perfil.duracion_cita_min} min: {horas}"]
    else:
        lineas += ["", "Día sin horario de atención."]

    pendientes = bandeja.listar()
    if pendientes:
        lineas += ["", f"⏳ Pendientes de aprobar ({len(pendientes)}):"]
        lineas += [f"  [{a.id}] {a.resumen}" for a in pendientes]
    return "\n".join(lineas)
