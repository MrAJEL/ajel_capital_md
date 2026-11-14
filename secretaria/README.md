# AJEL Secretaria

Agente con Claude que gestiona la agenda en **Google Calendar**:
- consulta la disponibilidad y busca huecos;
- propone citas, cambios y cancelaciones;
- prepara el resumen del día.

**Nada se escribe en el calendario sin que una persona lo apruebe.**

Lo usan **AJEL Studio** y **OncoVanguard**, cada uno con su perfil (horario, tono y reglas de privacidad).

## Cómo funciona

```
Cliente/equipo ──► Secretaria (Claude Opus 5.5)
                     │  ver_agenda · buscar_huecos           → lee el calendario
                     │  proponer_cita · proponer_reagendar
                     │  proponer_cancelacion                 → solo crea PROPUESTAS
                     ▼
              Bandeja de pendientes ──► una persona aprueba ──► Google Calendar
                                        (se revisa otra vez que el hueco siga libre)
```

- **Validaciones antes de proponer:**
  - que la cita caiga en el horario de atención;
  - que haya margen entre citas;
  - que se respete la antelación mínima y el máximo de días;
  - que no choque con otro evento;
  - que los correos sean válidos.
- **Privacidad estricta (OncoVanguard):** sin datos clínicos en el calendario, iniciales en el título y nada de orientación médica.
- **Seguridad:** el contenido de los eventos se trata como datos, no como órdenes; si el modelo rechaza una petición, el historial no se ensucia; si Claude rechaza por seguridad, la API reintenta con otro modelo de forma automática.

## Instalación (Windows / Victus)

```powershell
git clone https://github.com/MrAJEL/ajel_capital_md.git
cd ajel_capital_md\secretaria
py -3.11 -m venv .venv
.venv\Scripts\activate
pip install -e ".[google]"
```

Clave de Claude: crea una en https://platform.claude.com y defínela **solo en tu equipo**:
```powershell
setx ANTHROPIC_API_KEY "sk-ant-..."   # cierra y abre la terminal después
```

### Probar sin tocar tu calendario
```powershell
secretaria chat --perfil ajel_studio --demo
secretaria resumen --perfil oncovanguard --demo
```

### Conectar Google Calendar (una sola vez)
1. Entra en [Google Cloud Console](https://console.cloud.google.com/), crea un proyecto y activa la **Google Calendar API**.
2. Ve a **APIs y servicios → Pantalla de consentimiento OAuth**. Elige tipo *Externo*, deja el modo de prueba y añade tu correo como usuario de prueba.
3. Ve a **Credenciales → Crear credenciales → ID de cliente OAuth**, con tipo **App de escritorio**. Descarga el JSON.
4. Guárdalo como `%USERPROFILE%\.ajel_secretaria\credentials.json`. Está fuera del repo, así que nunca se sube.
5. Ejecuta `secretaria chat --perfil ajel_studio`. Se abrirá el navegador para autorizar, y el token quedará en `%USERPROFILE%\.ajel_secretaria\ajel_studio\token.json`.

> Usa un calendario dedicado por negocio. Pon su ID en `calendario_id` del perfil: Google Calendar → Configuración del calendario → "ID del calendario".

## Uso diario

| Comando | Qué hace |
|---|---|
| `secretaria chat --perfil oncovanguard` | Conversar ("agenda a J.P. para seguimiento el martes por la mañana") |
| `secretaria resumen --perfil ajel_studio` | Agenda de hoy, huecos libres y pendientes |
| `secretaria pendientes --perfil ajel_studio` | Ver las propuestas que esperan aprobación |
| `secretaria aprobar ID --perfil ajel_studio` | Aprobar: crea, mueve o cancela en Google Calendar |
| `secretaria rechazar ID --perfil ajel_studio` | Descartar la propuesta |

Dentro del chat también funcionan `/pendientes`, `/aprobar ID`, `/rechazar ID`, `/resumen` y `/salir`.

## Perfiles

Están en `ajel_secretaria/perfiles/*.toml` y controlan:
- horario por día y zona horaria;
- duración de la cita, margen entre citas y antelación mínima;
- tono e instrucciones del negocio;
- `privacidad_estricta`;
- modelo y esfuerzo.

Para un negocio nuevo, copia uno, cambia `clave` y úsalo con `--perfil nuevo` o `--perfil C:\ruta\perfil.toml`.

## Integrarla en una app (AJEL Studio, OncoVanguard, AJEL Capital)

Ver [INTEGRACION.md](INTEGRACION.md). Incluye un router FastAPI listo (`ajel_secretaria.api.crear_router`).

## Desarrollo

```bash
cd secretaria
pip install -e ".[dev]"
python -m pytest -q        # 20 pruebas, sin red ni API key (cliente de Claude simulado)
```

**Variables de entorno:**
- `ANTHROPIC_API_KEY` (obligatoria).
- `SECRETARIA_DATOS`: carpeta de datos locales. Por defecto `~/.ajel_secretaria`.
- `SECRETARIA_GOOGLE_CREDENCIALES`: ruta del JSON de OAuth.

**Costo:** usa `claude-opus-5-5` con esfuerzo `medium` y caché del prompt de sistema. Si quieres abaratarla, prueba `esfuerzo = "low"` en el perfil.
