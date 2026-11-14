# Proyectos de builder (monorepo)

Repositorio personal para investigar, prototipar y mejorar proyectos, pensado para
trabajar **desde el iPhone** con Claude Code en la nube (web/app móvil) y la app de GitHub.

Contiene:

1. **AJEL Capital** — plataforma de inversión (backend FastAPI + frontend Next.js + Postgres/Redis).
2. **apps/** — mini‑apps para iPhone en forma de **PWA** (HTML/JS autocontenido, funcionan offline).
3. **ideas/** — notas de investigación e ideas con una plantilla común.
4. **automatizaciones/** — scripts y bots que corren con GitHub Actions (disparables desde el móvil).

> El repo debe ser **privado** y **sin GitHub Pages**. Ver [docs/SETUP_MOVIL.md](docs/SETUP_MOVIL.md).

## Mapa de carpetas

```
.
├── backend/                 AJEL Capital API (FastAPI, Python 3.11)
│   ├── main.py              App, middlewares (CORS, cabeceras), /  y /api/status
│   ├── api/                 Routers bajo /api: auth, prices, intelligence, portfolio, clients
│   ├── core/                Seguridad (JWT), rate limiting, análisis técnico, scoring
│   ├── data/                Datos de mercado (FMP opcional) y caché Redis
│   ├── models/              Modelos SQLAlchemy
│   └── database.py          DATABASE_URL (Postgres) o SQLite local por defecto
├── frontend/                AJEL Capital UI (Next.js 14 App Router, React 18, Tailwind, Recharts)
├── docker-compose.yml       frontend :3000, backend :8000, Postgres 16, Redis 7
├── START_AI_PLATFORM.bat    Arranque en Windows (docker-compose up -d --build)
├── .env.example             Variables de entorno (copiar a .env, nunca commitear .env)
├── apps/                    PWAs para iPhone (una carpeta por app) + _plantilla-pwa/
├── ideas/                   Ideas e investigación (_plantilla.md + índice)
├── automatizaciones/        Scripts + workflows de GitHub Actions
├── docs/SETUP_MOVIL.md      Pasos manuales para trabajar desde el iPhone
├── .github/                 Plantillas de issues/PR y workflows (CI, automatizaciones)
└── CLAUDE.md                Contexto y reglas para sesiones de Claude Code
```

## AJEL Capital: cómo arrancarlo

### Opción A — Docker Compose (todo junto)

```bash
cp .env.example .env          # rellena POSTGRES_PASSWORD y JWT_SECRET_KEY
# generar secreto:  python -c "import secrets; print(secrets.token_hex(32))"
docker compose up -d --build  # en Windows también: START_AI_PLATFORM.bat
```

| Servicio | URL |
|---|---|
| Frontend | http://localhost:3000 |
| API + Swagger | http://localhost:8000/docs |
| Estado | http://localhost:8000/api/status |
| Postgres | 127.0.0.1:5432 |
| Redis | 127.0.0.1:6379 |

### Opción B — Local sin Docker

Backend (Python **3.11**; `numpy==1.26.4` no tiene wheels para 3.13):

```bash
cd backend
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
ENVIRONMENT=development uvicorn main:app --reload --port 8000
```

Sin `DATABASE_URL` usa SQLite (`backend/ajelcapital.db`, ignorado por git). Redis es
opcional: `/api/status` mostrará `"redis": "unavailable"`. Con `ENVIRONMENT=production`
el backend exige `JWT_SECRET_KEY` (el `.env.example` trae `production` por defecto).

Frontend (Node 18+):

```bash
cd frontend
npm ci
npm run dev          # http://localhost:3000, API en NEXT_PUBLIC_API_URL (por defecto http://localhost:8000/api)
npm run build        # build de producción (también hace typecheck)
```

## Flujo de trabajo desde el iPhone

1. **Capturar**: en la app de GitHub → Issues → New → plantilla *Idea* o *Tarea*.
2. **Investigar**: abre Claude Code (claude.ai/code o la app de Claude) sobre este repo y pide
   p. ej. *"Investiga la idea del issue #12 y crea `ideas/mi-idea.md` con la plantilla"*.
3. **Prototipar**: *"Crea una PWA en `apps/mi-app/` copiando `_plantilla-pwa`"*. Claude trabaja
   en una rama `claude/*` y hace push.
4. **Revisar**: en la app de GitHub revisa el diff/commits de la rama; abre un PR solo cuando
   quieras fusionar. El CI valida backend, frontend y manifests.
5. **Usar**: instala la PWA en la pantalla de inicio (ver [apps/README.md](apps/README.md)).
6. **Automatizar**: Actions → workflow → *Run workflow* desde la app de GitHub.

Detalles y pasos que solo puedes hacer tú: [docs/SETUP_MOVIL.md](docs/SETUP_MOVIL.md).
