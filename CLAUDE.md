# CLAUDE.md — contexto para sesiones de Claude Code

Monorepo personal de proyectos "builder". El usuario trabaja casi siempre **desde un iPhone**
con Claude Code en la nube y la app de GitHub. Las sesiones corren en un contenedor **Linux
sin Mac**: nada de iOS nativo (Swift/Xcode). Para apps de iPhone, **siempre PWA**.

## Reglas

- **Responder en español.** Docs, README, plantillas e ideas en español. Código, identificadores
  y mensajes de commit en **inglés**.
- **Nunca** commitear `.env`, claves, tokens ni datos personales. Solo `.env.example` con
  placeholders. Antes de commitear: `git status` y revisa qué entra.
- Trabajar en ramas `claude/*`. Hacer push a la rama de la sesión. **No crear PR** salvo que el
  usuario lo pida.
- Cambios **pequeños y verificables**: commits atómicos, ejecuta los comandos de verificación
  de abajo antes de decir que algo funciona. Si algo no se pudo verificar, dilo.
- No cambiar la lógica de AJEL Capital salvo que se pida explícitamente.
- El repo es privado y **sin GitHub Pages**: no crear workflows de Pages.
- Respuestas cortas: el usuario lee en el móvil.

## Estructura

| Carpeta | Qué es |
|---|---|
| `backend/` | AJEL Capital API: FastAPI 0.111, SQLAlchemy 2, Pydantic 2, slowapi, python-jose, Redis opcional. Python 3.11 (Dockerfile `python:3.11-slim`). |
| `frontend/` | Next.js 14.2 (App Router, `src/app`), React 18, TypeScript, Tailwind 3, Recharts, lucide-react. Cliente API en `src/lib/api.ts`: llama a `/api` en el mismo origen y `next.config.js` lo reenvía al backend (`API_PROXY_TARGET`; en Docker `http://backend:8000`). Cookies httpOnly. |
| `frontend/public/AJEL_Capital_Trading_Webapp/` | HTML estático grande generado externamente; no editar sin motivo. |
| `apps/` | PWAs autocontenidas, una carpeta por app; partir de `apps/_plantilla-pwa/`. |
| `ideas/` | Notas de ideas; copiar `ideas/_plantilla.md`, añadir al índice en `ideas/README.md`. |
| `automatizaciones/` | Scripts Python (solo stdlib si se puede) + workflows en `.github/workflows/`. |
| `secretaria/` | Paquete Python `ajel_secretaria`: agente Claude (Messages API, bucle manual de tools) + Google Calendar. Escrituras solo como propuestas que aprueba un humano. Perfiles TOML en `ajel_secretaria/perfiles/`. Tests: `cd secretaria && pip install -e ".[dev]" && python -m pytest -q`. |
| `docs/` | Guías para el usuario. |

### Backend (detalles)

- `main.py`: crea tablas al arrancar (`Base.metadata.create_all`), cabeceras de seguridad,
  CORS por `ALLOWED_ORIGINS`, `/` y `/api/status`; routers montados con `prefix="/api"`:
  `auth` (login/register/logout/me), `prices` (prices, historical, fundamentals, fear-greed),
  `intelligence` (score, scores), `portfolio` (portfolios, transactions, positions),
  `clients` (clientes, comisiones, HWM, capital).
- `database.py`: `DATABASE_URL` o SQLite `./ajelcapital.db` por defecto.
- `core/security.py`: `JWT_SECRET_KEY` obligatorio si `ENVIRONMENT=production`.
- Variables: ver `.env.example` y `docker-compose.yml` (`FMP_API_KEY` opcional, `REDIS_URL`).
- No hay tests ni alembic migrations aún.

## Comandos verificados (en este contenedor)

```bash
# Backend: compilación (lo que corre el CI)
python3 -m compileall -q backend

# Backend: arrancar en local (requiere Python 3.11; con 3.13 falla numpy==1.26.4)
cd backend && python3.11 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt
ENVIRONMENT=development uvicorn main:app --port 8000   # GET / y /api/status -> 200 (SQLite, sin Redis)

# Frontend
cd frontend && npm ci
npx tsc --noEmit        # typecheck
npm run build           # build de producción (incluye lint/typecheck de Next)

# PWAs: manifests válidos e iconos
python3 -c "import json,glob;[json.load(open(f)) for f in glob.glob('apps/*/manifest.webmanifest')]"
python3 apps/_plantilla-pwa/generar_iconos.py   # requiere Pillow
```

- `npm run lint` (`next lint`) **no** está configurado: no hay `.eslintrc` y pide configuración
  interactiva. No usarlo en CI sin añadir antes una config.
- `docker compose` necesita daemon de Docker; en la nube normalmente no está disponible.
- `npm run build` genera `frontend/tsconfig.tsbuildinfo` y `.next/` (ignorados).

## Convenciones

- PWA: `index.html` + `manifest.webmanifest` + `sw.js` + `icons/` (180, 192, 512), rutas
  **relativas**, datos en `localStorage`, meta tags iOS (ver `apps/README.md`). Al cambiar
  ficheros cacheados, subir la versión del caché en `sw.js`.
- Ideas: nombre de fichero `kebab-case.md`, campo `Estado` actualizado.
- Workflows: deben tener `workflow_dispatch` para poder lanzarlos desde la app de GitHub;
  `permissions` mínimos; sin secretos salvo que se documenten.
- Python nuevo: 3.11+, type hints, preferir stdlib.
