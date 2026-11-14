"""FastAPI router to embed the secretary in a backend (AJEL Studio, OncoVanguard, AJEL Capital).

    from ajel_secretaria.api import crear_router
    app.include_router(crear_router(perfil, calendario, bandeja, dependencias=[Depends(usuario_actual)]),
                       prefix="/api")

Always pass your app's auth dependency in ``dependencias``: these endpoints can approve
changes to a real calendar.
"""

from __future__ import annotations

from collections import OrderedDict
from datetime import date, datetime
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from .agente import Secretaria
from .calendarios.base import ProveedorCalendario
from .pendientes import BandejaPendientes
from .perfil import Perfil
from .resumen import resumen_del_dia

MAX_SESIONES = 200


class Mensaje(BaseModel):
    sesion_id: str = Field(min_length=1, max_length=100)
    texto: str = Field(min_length=1, max_length=4000)


class Rechazo(BaseModel):
    motivo: str = Field(default="", max_length=500)


def crear_router(
    perfil: Perfil,
    calendario: ProveedorCalendario,
    bandeja: BandejaPendientes,
    cliente: Any = None,
    dependencias: list | None = None,
) -> APIRouter:
    router = APIRouter(prefix="/secretaria", tags=["secretaria"], dependencies=dependencias or [])
    sesiones: OrderedDict[str, Secretaria] = OrderedDict()

    def sesion(sesion_id: str) -> Secretaria:
        if sesion_id in sesiones:
            sesiones.move_to_end(sesion_id)
        else:
            sesiones[sesion_id] = Secretaria(perfil, calendario, bandeja, cliente=cliente)
            if len(sesiones) > MAX_SESIONES:
                sesiones.popitem(last=False)
        return sesiones[sesion_id]

    @router.post("/mensaje")
    def mensaje(cuerpo: Mensaje) -> dict:
        import anthropic

        try:
            respuesta = sesion(cuerpo.sesion_id).responder(cuerpo.texto)
        except anthropic.RateLimitError as error:
            raise HTTPException(429, "Límite de uso de la API de Claude alcanzado.") from error
        except anthropic.APIError as error:
            raise HTTPException(502, "La API de Claude no respondió correctamente.") from error
        return {
            "respuesta": respuesta.texto,
            "propuestas": [a.a_dict() for a in respuesta.propuestas],
            "motivo_fin": respuesta.motivo_fin,
        }

    @router.get("/pendientes")
    def pendientes() -> list[dict]:
        return [a.a_dict() for a in bandeja.listar()]

    @router.post("/pendientes/{accion_id}/aprobar")
    def aprobar(accion_id: str) -> dict:
        try:
            return bandeja.aprobar(accion_id, calendario, perfil.margen_min).a_dict()
        except KeyError as error:
            raise HTTPException(404, str(error)) from error
        except ValueError as error:
            raise HTTPException(409, str(error)) from error

    @router.post("/pendientes/{accion_id}/rechazar")
    def rechazar(accion_id: str, cuerpo: Rechazo) -> dict:
        try:
            return bandeja.rechazar(accion_id, cuerpo.motivo).a_dict()
        except KeyError as error:
            raise HTTPException(404, str(error)) from error
        except ValueError as error:
            raise HTTPException(409, str(error)) from error

    @router.get("/resumen")
    def resumen(fecha: date | None = None) -> dict:
        dia = fecha or datetime.now(perfil.tz).date()
        return {"resumen": resumen_del_dia(perfil, calendario, bandeja, dia)}

    return router
