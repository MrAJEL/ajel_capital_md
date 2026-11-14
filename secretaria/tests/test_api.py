from conftest import AHORA, ClienteFalso, en, respuesta, texto, uso
from fastapi import FastAPI
from fastapi.testclient import TestClient

from ajel_secretaria import agente
from ajel_secretaria.api import crear_router


def test_endpoints(perfil, calendario, bandeja, monkeypatch):
    cita = {
        "titulo": "Demo",
        "inicio": en(17, 10).isoformat(),
        "fin": en(17, 10, 45).isoformat(),
        "invitados": [],
        "descripcion": "",
        "ubicacion": "",
    }
    cliente = ClienteFalso(
        [respuesta("tool_use", uso("t", "proponer_cita", cita)), respuesta("end_turn", texto("Propuesta lista."))]
    )
    original = agente.Secretaria.__init__

    def con_reloj(self, *a, **k):
        original(self, *a, **{**k, "reloj": lambda: AHORA})

    monkeypatch.setattr(agente.Secretaria, "__init__", con_reloj)

    app = FastAPI()
    app.include_router(crear_router(perfil, calendario, bandeja, cliente=cliente), prefix="/api")
    http = TestClient(app)

    r = http.post("/api/secretaria/mensaje", json={"sesion_id": "s1", "texto": "agenda demo"})
    assert r.status_code == 200
    accion_id = r.json()["propuestas"][0]["id"]

    assert [p["id"] for p in http.get("/api/secretaria/pendientes").json()] == [accion_id]
    r = http.post(f"/api/secretaria/pendientes/{accion_id}/aprobar")
    assert r.json()["estado"] == "aprobada"
    assert http.post(f"/api/secretaria/pendientes/{accion_id}/aprobar").status_code == 409
    assert http.post("/api/secretaria/pendientes/nope/rechazar", json={}).status_code == 404
    assert "Demo" in http.get("/api/secretaria/resumen", params={"fecha": "2026-11-17"}).json()["resumen"]
