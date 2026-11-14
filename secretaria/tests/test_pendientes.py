import pytest
from conftest import en

from ajel_secretaria.modelos import Evento
from ajel_secretaria.pendientes import BandejaPendientes


def _crear(bandeja, inicio, fin):
    return bandeja.agregar(
        "crear",
        {
            "titulo": "Demo",
            "inicio": inicio.isoformat(),
            "fin": fin.isoformat(),
            "invitados": ["a@b.com"],
            "descripcion": "",
            "ubicacion": "",
        },
        "Crear demo",
    )


def test_aprobar_crea_evento(bandeja, calendario):
    accion = _crear(bandeja, en(17, 10), en(17, 10, 45))
    resultado = bandeja.aprobar(accion.id, calendario, 15)
    assert resultado.estado == "aprobada"
    assert any(e.titulo == "Demo" for e in calendario.listar_eventos(en(17, 0), en(18, 0)))
    with pytest.raises(ValueError):
        bandeja.aprobar(accion.id, calendario, 15)  # already decided


def test_aprobar_falla_si_el_hueco_se_ocupo(bandeja, calendario):
    accion = _crear(bandeja, en(17, 10), en(17, 10, 45))
    calendario.crear_evento("Otro", en(17, 10, 30), en(17, 11), [], "", "")
    resultado = bandeja.aprobar(accion.id, calendario, 15)
    assert resultado.estado == "fallida"
    assert "ya no está libre" in resultado.resultado
    assert len(calendario.listar_eventos(en(17, 0), en(18, 0))) == 1


def test_mover_y_cancelar(bandeja, calendario):
    mover = bandeja.agregar(
        "mover", {"evento_id": "e1", "inicio": en(16, 13, 30).isoformat(), "fin": en(16, 14, 30).isoformat()}, "m"
    )
    # Overlaps its own old slot only: must be allowed.
    assert bandeja.aprobar(mover.id, calendario, 15).estado == "aprobada"
    assert calendario.obtener_evento("e1").inicio == en(16, 13, 30)

    cancelar = bandeja.agregar("cancelar", {"evento_id": "e1", "motivo": ""}, "c")
    assert bandeja.aprobar(cancelar.id, calendario, 15).estado == "aprobada"
    assert calendario.obtener_evento("e1") is None


def test_rechazar_no_toca_el_calendario(bandeja, calendario):
    accion = _crear(bandeja, en(17, 10), en(17, 10, 45))
    assert bandeja.rechazar(accion.id).estado == "rechazada"
    assert bandeja.listar() == []
    assert calendario.listar_eventos(en(17, 0), en(18, 0)) == []


def test_persistencia(tmp_path, calendario):
    ruta = tmp_path / "pendientes.json"
    accion = _crear(BandejaPendientes(ruta), en(17, 10), en(17, 10, 45))
    recargada = BandejaPendientes(ruta)
    assert [a.id for a in recargada.listar()] == [accion.id]
    assert recargada.aprobar(accion.id, calendario, 15).estado == "aprobada"
    assert BandejaPendientes(ruta).listar() == []


def test_evento_libre_no_bloquea(bandeja):
    from ajel_secretaria.calendarios.memoria import CalendarioMemoria

    cal = CalendarioMemoria([Evento("f", "Libre", en(17, 10), en(17, 11), ocupa=False)])
    accion = _crear(bandeja, en(17, 10), en(17, 10, 45))
    assert bandeja.aprobar(accion.id, cal, 15).estado == "aprobada"
