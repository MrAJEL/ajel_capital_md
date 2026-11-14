"""Approval inbox: the agent proposes write actions here; a human approves or rejects them.

Nothing touches the calendar until ``aprobar`` is called. On approval the slot is checked
again, because the calendar may have changed since the agent proposed it.
"""

from __future__ import annotations

import json
import secrets
import threading
from datetime import datetime, timedelta
from pathlib import Path

from .calendarios.base import ProveedorCalendario
from .huecos import conflictos
from .modelos import AccionPendiente, TipoAccion


class BandejaPendientes:
    def __init__(self, ruta: Path | None = None) -> None:
        """``ruta``: JSON file to persist the inbox across runs (None = memory only)."""
        self._ruta = ruta
        self._lock = threading.Lock()
        self._acciones: dict[str, AccionPendiente] = {}
        if ruta and ruta.is_file():
            for dato in json.loads(ruta.read_text(encoding="utf-8")):
                accion = AccionPendiente(**dato)
                self._acciones[accion.id] = accion

    def agregar(self, tipo: TipoAccion, datos: dict, resumen: str) -> AccionPendiente:
        with self._lock:
            accion = AccionPendiente(
                id=secrets.token_hex(3),
                tipo=tipo,
                datos=datos,
                resumen=resumen,
                creada=datetime.now().astimezone().isoformat(timespec="seconds"),
            )
            self._acciones[accion.id] = accion
            self._guardar()
            return accion

    def listar(self, estado: str | None = "pendiente") -> list[AccionPendiente]:
        return [a for a in self._acciones.values() if estado is None or a.estado == estado]

    def obtener(self, accion_id: str) -> AccionPendiente:
        if accion_id not in self._acciones:
            raise KeyError(f"No existe la acción {accion_id}")
        return self._acciones[accion_id]

    def rechazar(self, accion_id: str, motivo: str = "") -> AccionPendiente:
        with self._lock:
            accion = self._pendiente(accion_id)
            accion.estado = "rechazada"
            accion.resultado = motivo or "Rechazada por una persona."
            self._guardar()
            return accion

    def aprobar(
        self, accion_id: str, calendario: ProveedorCalendario, margen_min: int
    ) -> AccionPendiente:
        """Execute the action on the calendar. Returns it with estado aprobada or fallida."""
        with self._lock:
            accion = self._pendiente(accion_id)
            try:
                accion.resultado = self._ejecutar(accion, calendario, margen_min)
                accion.estado = "aprobada"
            except Exception as error:  # the calendar call or the re-check failed
                accion.estado = "fallida"
                accion.resultado = str(error)
            self._guardar()
            return accion

    def _ejecutar(self, accion: AccionPendiente, calendario, margen_min: int) -> str:
        d = accion.datos
        if accion.tipo == "cancelar":
            calendario.cancelar_evento(d["evento_id"])
            return f"Evento {d['evento_id']} cancelado."

        inicio = datetime.fromisoformat(d["inicio"])
        fin = datetime.fromisoformat(d["fin"])
        ignorar = d.get("evento_id")
        margen = timedelta(minutes=margen_min)
        cercanos = calendario.listar_eventos(inicio - margen, fin + margen)
        choques = conflictos(cercanos, inicio, fin, margen_min, ignorar_id=ignorar)
        if choques:
            titulos = ", ".join(f"{c.titulo} ({c.inicio:%H:%M})" for c in choques)
            raise RuntimeError(f"El horario ya no está libre: choca con {titulos}.")

        if accion.tipo == "crear":
            evento = calendario.crear_evento(
                d["titulo"], inicio, fin, d["invitados"], d["descripcion"], d["ubicacion"]
            )
            return f"Cita creada (id {evento.id})."
        evento = calendario.mover_evento(d["evento_id"], inicio, fin)
        return f"Cita movida (id {evento.id})."

    def _pendiente(self, accion_id: str) -> AccionPendiente:
        accion = self.obtener(accion_id)
        if accion.estado != "pendiente":
            raise ValueError(f"La acción {accion_id} ya está {accion.estado}.")
        return accion

    def _guardar(self) -> None:
        if self._ruta is None:
            return
        self._ruta.parent.mkdir(parents=True, exist_ok=True)
        datos = [a.a_dict() for a in self._acciones.values()]
        self._ruta.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")
