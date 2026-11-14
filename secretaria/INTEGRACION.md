# Integrar la secretaria en AJEL Studio y OncoVanguard

Los proyectos viven en tu Victus (`IA Studio`, `OncoVanguard8`). Esta sesión en la nube no
puede abrir esas carpetas, así que la integración se hace en tu equipo. Tienes dos caminos.

## Opción A: como paquete (recomendado)

La secretaria vive en un solo sitio (este repo). Cada proyecto la instala y se actualiza con un `pip install` nuevo.

En el entorno Python de cada proyecto:
```powershell
pip install "ajel-secretaria[google,api] @ git+https://github.com/MrAJEL/ajel_capital_md.git@claude/iphone-local-apps-fcvcy0#subdirectory=secretaria"
```
- El repo es privado, así que Git en tu Victus debe tener sesión de GitHub (Git Credential Manager te la pide la primera vez).
- Cuando se fusione a `main`, cambia `@claude/iphone-local-apps-fcvcy0` por `@main`.

## Opción B: copiar la carpeta

Copia `secretaria/` dentro del proyecto, por ejemplo en `OncoVanguard8\secretaria\`, y ejecuta `pip install -e .\secretaria[google,api]`.
Es más simple, pero cada mejora hay que copiarla a mano en cada proyecto.

## Si el proyecto tiene backend FastAPI

```python
from pathlib import Path
from fastapi import Depends

from ajel_secretaria import BandejaPendientes, cargar_perfil
from ajel_secretaria.api import crear_router
from ajel_secretaria.calendarios.google import CalendarioGoogle, conectar_google

perfil = cargar_perfil("oncovanguard")          # o "ajel_studio"
datos = Path.home() / ".ajel_secretaria"
servicio = conectar_google(datos / "credentials.json", datos / perfil.clave / "token.json")
calendario = CalendarioGoogle(servicio, perfil.calendario_id, perfil.zona_horaria)
bandeja = BandejaPendientes(datos / perfil.clave / "pendientes.json")

app.include_router(
    crear_router(perfil, calendario, bandeja, dependencias=[Depends(usuario_actual)]),
    prefix="/api",
)
```

- **Siempre** pasa la dependencia de login de tu app en `dependencias`: esos endpoints aprueban cambios en un calendario real.
- `conectar_google` abre el navegador la primera vez. Hazlo antes en local con `secretaria chat --perfil ...` para que el token ya exista.

**Endpoints:**

| Método | Ruta | Uso |
|---|---|---|
| POST | `/api/secretaria/mensaje` | `{"sesion_id": "...", "texto": "..."}` → respuesta + propuestas |
| GET | `/api/secretaria/pendientes` | Propuestas por aprobar |
| POST | `/api/secretaria/pendientes/{id}/aprobar` | Ejecuta en Google Calendar (409 si ya se decidió) |
| POST | `/api/secretaria/pendientes/{id}/rechazar` | `{"motivo": "..."}` |
| GET | `/api/secretaria/resumen?fecha=YYYY-MM-DD` | Resumen del día |

## Si el proyecto es solo frontend (Next.js / web app)

Sin backend Python, la secretaria corre aparte: `uvicorn` con un `main.py` mínimo que monte el
router de arriba. El frontend la llama por HTTP. **Nunca** pongas `ANTHROPIC_API_KEY` en el frontend.

## Checklist OncoVanguard (datos de salud)

- [ ] Confirmar que `privacidad_estricta = true` en el perfil (viene activado).
- [ ] Usar un calendario **dedicado** de la clínica, no uno personal.
- [ ] Avisar en el chat o la web que la persona habla con un asistente virtual.
- [ ] Revisar con quien lleve lo legal el aviso de privacidad. En México aplica la LFPDPPP, y los datos de salud son sensibles.
- [ ] No pegar historiales ni resultados en el chat.

## Pedírselo a Claude Code en tu Victus

Abre Claude Code (app de escritorio) en la carpeta del proyecto y pídele:
> "Integra la secretaria de `MrAJEL/ajel_capital_md/secretaria` en este proyecto siguiendo su
> INTEGRACION.md, con el perfil oncovanguard."
