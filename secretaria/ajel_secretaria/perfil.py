"""Per-project configuration ("perfil"): business hours, timezone, tone, privacy rules, model."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from datetime import time
from pathlib import Path
from zoneinfo import ZoneInfo

CARPETA_PERFILES = Path(__file__).parent / "perfiles"

DIAS = {"lun": 0, "mar": 1, "mie": 2, "jue": 3, "vie": 4, "sab": 5, "dom": 6}
NOMBRES_DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
ESFUERZOS = {"low", "medium", "high", "xhigh", "max"}


@dataclass(frozen=True)
class Perfil:
    clave: str
    nombre_negocio: str
    zona_horaria: str
    horario: dict[int, tuple[time, time]]  # weekday (0 = Monday) -> (opens, closes)
    duracion_cita_min: int = 30
    margen_min: int = 10
    antelacion_min_horas: int = 2
    dias_max_adelante: int = 30
    calendario_id: str = "primary"
    tono: str = "Cordial, profesional y breve."
    privacidad_estricta: bool = False
    instrucciones_extra: str = ""
    modelo: str = "claude-opus-5-5"
    esfuerzo: str = "medium"

    @property
    def tz(self) -> ZoneInfo:
        return ZoneInfo(self.zona_horaria)

    def horario_legible(self) -> str:
        lineas = []
        for dia in range(7):
            if dia in self.horario:
                abre, cierra = self.horario[dia]
                lineas.append(f"- {NOMBRES_DIAS[dia]}: {abre:%H:%M}–{cierra:%H:%M}")
            else:
                lineas.append(f"- {NOMBRES_DIAS[dia]}: cerrado")
        return "\n".join(lineas)


def _hora(texto: str) -> time:
    return time.fromisoformat(texto)


def perfil_desde_dict(datos: dict) -> Perfil:
    horario: dict[int, tuple[time, time]] = {}
    for dia, rango in datos.get("horario", {}).items():
        if dia not in DIAS:
            raise ValueError(f"Día desconocido en [horario]: {dia!r} (usa {', '.join(DIAS)})")
        abre, cierra = _hora(rango[0]), _hora(rango[1])
        if abre >= cierra:
            raise ValueError(f"Horario inválido para {dia}: {rango}")
        horario[DIAS[dia]] = (abre, cierra)
    if not horario:
        raise ValueError("El perfil necesita al menos un día en [horario]")

    modelo = datos.get("modelo", {})
    esfuerzo = modelo.get("esfuerzo", "medium")
    if esfuerzo not in ESFUERZOS:
        raise ValueError(f"esfuerzo debe ser uno de {sorted(ESFUERZOS)}")

    perfil = Perfil(
        clave=datos["clave"],
        nombre_negocio=datos["nombre_negocio"],
        zona_horaria=datos.get("zona_horaria", "America/Mexico_City"),
        horario=horario,
        duracion_cita_min=int(datos.get("duracion_cita_min", 30)),
        margen_min=int(datos.get("margen_min", 10)),
        antelacion_min_horas=int(datos.get("antelacion_min_horas", 2)),
        dias_max_adelante=int(datos.get("dias_max_adelante", 30)),
        calendario_id=datos.get("calendario_id", "primary"),
        tono=datos.get("tono", Perfil.tono),
        privacidad_estricta=bool(datos.get("privacidad_estricta", False)),
        instrucciones_extra=datos.get("instrucciones_extra", "").strip(),
        modelo=modelo.get("id", "claude-opus-5-5"),
        esfuerzo=esfuerzo,
    )
    perfil.tz  # fail early on an unknown timezone
    return perfil


def cargar_perfil(clave_o_ruta: str | Path) -> Perfil:
    """Load a profile by key (e.g. ``oncovanguard``) or by path to a .toml file."""
    ruta = Path(clave_o_ruta)
    if ruta.suffix != ".toml":
        ruta = CARPETA_PERFILES / f"{clave_o_ruta}.toml"
    if not ruta.is_file():
        disponibles = ", ".join(perfiles_disponibles()) or "ninguno"
        raise FileNotFoundError(f"No existe el perfil {clave_o_ruta!r}. Disponibles: {disponibles}")
    with ruta.open("rb") as f:
        return perfil_desde_dict(tomllib.load(f))


def perfiles_disponibles() -> list[str]:
    return sorted(p.stem for p in CARPETA_PERFILES.glob("*.toml"))
