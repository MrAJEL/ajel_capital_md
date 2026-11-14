import json

from conftest import AHORA, ClienteFalso, en, respuesta, texto, uso

from ajel_secretaria.agente import MENSAJE_RECHAZO, Secretaria, prompt_sistema
from ajel_secretaria.herramientas import definiciones_herramientas
from ajel_secretaria.perfil import cargar_perfil


def _secretaria(perfil, calendario, bandeja, respuestas):
    cliente = ClienteFalso(respuestas)
    return Secretaria(perfil, calendario, bandeja, cliente=cliente, reloj=lambda: AHORA), cliente


def test_flujo_buscar_y_proponer(perfil, calendario, bandeja):
    cita = {
        "titulo": "AJEL Studio · Descubrimiento · Ana",
        "inicio": en(17, 10).isoformat(),
        "fin": en(17, 10, 45).isoformat(),
        "invitados": ["ana@example.com"],
        "descripcion": "",
        "ubicacion": "Google Meet",
    }
    sec, cliente = _secretaria(
        perfil,
        calendario,
        bandeja,
        [
            respuesta("tool_use", uso("t1", "buscar_huecos", {"desde": "2026-11-17", "hasta": "2026-11-17", "duracion_min": 45})),
            respuesta("tool_use", uso("t2", "proponer_cita", cita)),
            respuesta("end_turn", texto("Listo, quedó propuesta y pendiente de aprobación.")),
        ],
    )
    r = sec.responder("Agenda a Ana mañana a las 10")

    assert r.motivo_fin == "end_turn"
    assert "pendiente" in r.texto
    assert len(r.propuestas) == 1 and r.propuestas[0].tipo == "crear"
    # Nothing written to the calendar before approval.
    assert calendario.listar_eventos(en(17, 0), en(18, 0)) == []

    # Tool results go back in a single user message with matching ids.
    resultados = cliente.llamadas[1]["messages"][-1]["content"]
    assert resultados[0]["tool_use_id"] == "t1"
    huecos = json.loads(resultados[0]["content"])["huecos"]
    assert huecos[0]["inicio"] == en(17, 9).isoformat()

    # Request shape: model, effort, fallback, cache.
    llamada = cliente.llamadas[0]
    assert llamada["model"] == "claude-opus-5-5"
    assert llamada["output_config"] == {"effort": "medium"}
    assert llamada["fallbacks"] == "default"
    assert llamada["betas"] == ["server-side-fallback-2026-07-01"]
    assert "Ahora: lunes 2026-11-16 08:00" in llamada["messages"][0]["content"]
    assert "2026" not in llamada["system"]  # system prompt stays date-free (cacheable)


def test_error_de_herramienta_vuelve_al_modelo(perfil, calendario, bandeja):
    choque = {
        "titulo": "X",
        "inicio": en(16, 13).isoformat(),
        "fin": en(16, 13, 45).isoformat(),
        "invitados": [],
        "descripcion": "",
        "ubicacion": "",
    }
    sec, cliente = _secretaria(
        perfil,
        calendario,
        bandeja,
        [respuesta("tool_use", uso("t1", "proponer_cita", choque)), respuesta("end_turn", texto("Ese horario no está libre."))],
    )
    r = sec.responder("Pon algo hoy a la 1")
    resultado = cliente.llamadas[1]["messages"][-1]["content"][0]
    assert resultado["is_error"] is True
    assert r.propuestas == [] and bandeja.listar() == []


def test_valida_antelacion_y_correos(perfil, calendario, bandeja):
    pronto = {
        "titulo": "X",
        "inicio": en(16, 9).isoformat(),  # only 1 h of notice
        "fin": en(16, 9, 45).isoformat(),
        "invitados": ["no-es-correo"],
        "descripcion": "",
        "ubicacion": "",
    }
    sec, cliente = _secretaria(
        perfil, calendario, bandeja, [respuesta("tool_use", uso("t1", "proponer_cita", pronto)), respuesta("end_turn", texto("ok"))]
    )
    sec.responder("hoy a las 9")
    assert "Correos inválidos" in cliente.llamadas[1]["messages"][-1]["content"][0]["content"]


def test_rechazo_no_ensucia_el_historial(perfil, calendario, bandeja):
    sec, _ = _secretaria(perfil, calendario, bandeja, [respuesta("refusal")])
    r = sec.responder("algo")
    assert r.texto == MENSAJE_RECHAZO and sec.mensajes == []


def test_historial_se_conserva_entre_turnos(perfil, calendario, bandeja):
    sec, cliente = _secretaria(
        perfil, calendario, bandeja, [respuesta("end_turn", texto("Hola")), respuesta("end_turn", texto("Claro"))]
    )
    sec.responder("hola")
    sec.responder("¿y mañana?")
    assert [m["role"] for m in cliente.llamadas[1]["messages"]] == ["user", "assistant", "user"]


def test_reagendar_y_cancelar_quedan_pendientes(perfil, calendario, bandeja):
    sec, _ = _secretaria(
        perfil,
        calendario,
        bandeja,
        [
            respuesta(
                "tool_use",
                uso("a", "proponer_reagendar", {"evento_id": "e1", "nuevo_inicio": en(17, 11).isoformat(), "nuevo_fin": en(17, 12).isoformat(), "motivo": ""}),
                uso("b", "proponer_cancelacion", {"evento_id": "e1", "motivo": "duplicado"}),
            ),
            respuesta("end_turn", texto("Propuestas listas.")),
        ],
    )
    r = sec.responder("mueve y cancela")
    assert [a.tipo for a in r.propuestas] == ["mover", "cancelar"]
    assert calendario.obtener_evento("e1").inicio == en(16, 13)


def test_herramientas_estrictas():
    for tool in definiciones_herramientas():
        esquema = tool["input_schema"]
        assert tool["strict"] is True
        assert esquema["additionalProperties"] is False
        assert set(esquema["required"]) == set(esquema["properties"])


def test_prompt_oncovanguard_tiene_privacidad():
    sistema = prompt_sistema(cargar_perfil("oncovanguard"))
    assert "Privacidad (estricta)" in sistema
    assert "iniciales" in sistema
    assert "Privacidad (estricta)" not in prompt_sistema(cargar_perfil("ajel_studio"))
