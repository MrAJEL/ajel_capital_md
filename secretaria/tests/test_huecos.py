from conftest import AHORA, en

from ajel_secretaria.huecos import buscar_huecos, conflictos, dentro_de_horario
from ajel_secretaria.modelos import Evento


def test_respeta_antelacion_horario_y_margen(perfil, calendario):
    eventos = calendario.listar_eventos(en(16, 0), en(17, 0))
    huecos = buscar_huecos(eventos, perfil, en(16, 0), en(17, 0), 45, AHORA, max_resultados=20)
    inicios = [h.inicio for h in huecos if h.inicio.day == 16]

    # Notice of 4 h from 08:00 -> first slot at 12:00. 12:00-12:45 ends 15 min before the
    # 13:00 meeting, so it fits exactly with the margin.
    assert inicios[0] == en(16, 12)
    # Nothing that overlaps 13:00-14:00 plus the 15-minute margin.
    assert all(not (en(16, 12, 15) < h < en(16, 14, 15)) for h in inicios)
    # The "free" (transparent) event at 15:00 does not block.
    assert any(h.inicio < en(16, 16) and h.fin > en(16, 15) for h in huecos)
    # Last slot must end by closing time (18:00).
    assert all(h.fin <= en(16, 18) for h in huecos if h.inicio.day == 16)


def test_fin_de_semana_y_viernes_corto(perfil):
    huecos = buscar_huecos([], perfil, en(20, 0), en(23, 0), 45, AHORA, max_resultados=50)
    assert {h.inicio.day for h in huecos} == {20}  # Fri the 20th only; Sat/Sun closed
    assert max(h.fin for h in huecos) <= en(20, 15)


def test_no_supera_dias_max_adelante(perfil):
    huecos = buscar_huecos([], perfil, en(16, 0), en(30, 0).replace(month=12), 45, AHORA, max_resultados=500)
    assert all((h.inicio - AHORA).days <= perfil.dias_max_adelante for h in huecos)


def test_dentro_de_horario(perfil):
    assert dentro_de_horario(perfil, en(17, 9), en(17, 9, 45))
    assert not dentro_de_horario(perfil, en(17, 17, 30), en(17, 18, 15))
    assert not dentro_de_horario(perfil, en(21, 10), en(21, 11))  # Saturday


def test_conflictos_ignora_evento_movido():
    ev = Evento("x", "A", en(17, 10), en(17, 11))
    assert conflictos([ev], en(17, 10, 30), en(17, 11), 0)
    assert not conflictos([ev], en(17, 10, 30), en(17, 11), 0, ignorar_id="x")
