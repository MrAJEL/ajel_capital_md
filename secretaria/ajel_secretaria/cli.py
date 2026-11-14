"""Command line: ``secretaria chat --perfil oncovanguard`` (or ``python -m ajel_secretaria``)."""

from __future__ import annotations

import argparse
import os
import sys
from datetime import date, datetime
from pathlib import Path

from .calendarios.memoria import calendario_demo
from .pendientes import BandejaPendientes
from .perfil import Perfil, cargar_perfil, perfiles_disponibles
from .resumen import resumen_del_dia


def carpeta_datos(perfil: Perfil) -> Path:
    """Local data (pending actions, Google token). Outside the repo so it is never committed."""
    base = Path(os.environ.get("SECRETARIA_DATOS", Path.home() / ".ajel_secretaria"))
    return base / perfil.clave


def construir(perfil: Perfil, demo: bool):
    if demo:
        return calendario_demo(perfil.zona_horaria), BandejaPendientes()

    from .calendarios.google import CalendarioGoogle, conectar_google

    datos = carpeta_datos(perfil)
    credenciales = Path(
        os.environ.get("SECRETARIA_GOOGLE_CREDENCIALES", datos.parent / "credentials.json")
    )
    servicio = conectar_google(credenciales, datos / "token.json")
    calendario = CalendarioGoogle(servicio, perfil.calendario_id, perfil.zona_horaria)
    return calendario, BandejaPendientes(datos / "pendientes.json")


def _imprimir_pendientes(bandeja: BandejaPendientes) -> None:
    pendientes = bandeja.listar()
    if not pendientes:
        print("No hay propuestas pendientes.")
    for a in pendientes:
        print(f"  [{a.id}] {a.resumen}")


def _aprobar(bandeja, calendario, perfil, accion_id: str) -> None:
    accion = bandeja.aprobar(accion_id, calendario, perfil.margen_min)
    icono = "✅" if accion.estado == "aprobada" else "⚠️"
    print(f"{icono} [{accion.id}] {accion.estado}: {accion.resultado}")


def chat(perfil: Perfil, demo: bool) -> None:
    import anthropic

    from .agente import Secretaria

    calendario, bandeja = construir(perfil, demo)
    secretaria = Secretaria(perfil, calendario, bandeja)
    modo = "DEMO (calendario de prueba)" if demo else f"Google Calendar ({perfil.calendario_id})"
    print(f"Secretaria de {perfil.nombre_negocio} · {modo}")
    print("Comandos: /pendientes  /aprobar ID  /rechazar ID  /resumen  /salir\n")

    while True:
        try:
            texto = input("tú> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if not texto:
            continue
        comando, _, argumento = texto.partition(" ")
        try:
            if comando in ("/salir", "/exit"):
                return
            if comando == "/pendientes":
                _imprimir_pendientes(bandeja)
                continue
            if comando == "/aprobar":
                _aprobar(bandeja, calendario, perfil, argumento.strip())
                continue
            if comando == "/rechazar":
                accion = bandeja.rechazar(argumento.strip())
                print(f"❌ [{accion.id}] rechazada")
                continue
            if comando == "/resumen":
                print(resumen_del_dia(perfil, calendario, bandeja, datetime.now(perfil.tz).date()))
                continue
        except (KeyError, ValueError) as error:
            print(f"⚠️ {error}")
            continue

        try:
            respuesta = secretaria.responder(texto)
        except anthropic.AuthenticationError:
            print("⚠️ Falta o es inválida la clave: define ANTHROPIC_API_KEY.")
            continue
        except anthropic.RateLimitError:
            print("⚠️ Límite de uso de la API alcanzado. Espera un momento.")
            continue
        except anthropic.APIConnectionError:
            print("⚠️ Sin conexión con la API de Claude.")
            continue
        except anthropic.APIStatusError as error:
            print(f"⚠️ Error de la API ({error.status_code}): {error.message}")
            continue

        print(f"\nsecretaria> {respuesta.texto}\n")
        for accion in respuesta.propuestas:
            print(f"  ⏳ [{accion.id}] {accion.resumen}  → /aprobar {accion.id}")
        if respuesta.propuestas:
            print()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="secretaria", description="Agente secretaria AJEL")
    sub = parser.add_subparsers(dest="comando", required=True)

    def con_perfil(nombre: str, ayuda: str) -> argparse.ArgumentParser:
        p = sub.add_parser(nombre, help=ayuda)
        p.add_argument("--perfil", required=True, help="clave (ajel_studio, oncovanguard) o ruta .toml")
        return p

    p_chat = con_perfil("chat", "conversar con la secretaria")
    p_chat.add_argument("--demo", action="store_true", help="calendario de prueba en memoria")
    p_res = con_perfil("resumen", "agenda del día, huecos y pendientes")
    p_res.add_argument("--fecha", type=date.fromisoformat, help="YYYY-MM-DD (por defecto hoy)")
    p_res.add_argument("--demo", action="store_true")
    con_perfil("pendientes", "listar propuestas pendientes")
    p_apr = con_perfil("aprobar", "aprobar y ejecutar una propuesta")
    p_apr.add_argument("id")
    p_rec = con_perfil("rechazar", "rechazar una propuesta")
    p_rec.add_argument("id")
    p_rec.add_argument("--motivo", default="")
    sub.add_parser("perfiles", help="listar perfiles incluidos")

    args = parser.parse_args(argv)
    if args.comando == "perfiles":
        print("\n".join(perfiles_disponibles()))
        return 0

    perfil = cargar_perfil(args.perfil)
    if args.comando == "chat":
        chat(perfil, args.demo)
        return 0

    calendario, bandeja = construir(perfil, getattr(args, "demo", False))
    try:
        if args.comando == "resumen":
            dia = args.fecha or datetime.now(perfil.tz).date()
            print(resumen_del_dia(perfil, calendario, bandeja, dia))
        elif args.comando == "pendientes":
            _imprimir_pendientes(bandeja)
        elif args.comando == "aprobar":
            _aprobar(bandeja, calendario, perfil, args.id)
        elif args.comando == "rechazar":
            bandeja.rechazar(args.id, args.motivo)
            print(f"❌ [{args.id}] rechazada")
    except (KeyError, ValueError) as error:
        print(f"⚠️ {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
