# Setup para trabajar desde el iPhone

Pasos que **solo tú** puedes hacer. Hazlos una vez, en este orden.

## 1. Hacer el repo privado (y sin Pages)

En github.com (Safari, "Solicitar sitio de escritorio" si hace falta):

1. Repo → **Settings** → **General** → baja hasta **Danger Zone**.
2. **Change repository visibility** → **Make private** → confirma escribiendo el nombre.
3. Settings → **Pages**: comprueba que no hay sitio publicado (si lo hay, *Unpublish*).

> El historial ya fue público: si alguna vez hubo un secreto en un commit, **rótalo**
> (cámbialo en el servicio), hacer el repo privado no lo borra.

## 2. Proteger la cuenta

1. github.com → foto de perfil → **Settings** → **Password and authentication**.
2. **Passkeys** → *Add a passkey* (usa Face ID del iPhone).
3. **Two-factor authentication** → actívalo (app de autenticación) y guarda los *recovery codes*
   fuera del teléfono.

## 3. App de GitHub

1. Instala **GitHub** desde la App Store e inicia sesión.
2. Abre el repo → ★ / *Pin* para tenerlo a mano.
3. Activa notificaciones (Ajustes del iPhone → GitHub → Notificaciones).
4. Opcional: crea las etiquetas `idea` y `tarea` (Issues → Labels) para que las plantillas
   las apliquen automáticamente.

## 4. Claude Code en la nube

1. Abre **claude.ai/code** en Safari o la pestaña *Code* de la app de Claude.
2. Conecta GitHub y autoriza **este repo** (acceso a repos privados).
3. Crea una sesión eligiendo este repo. Claude lee `CLAUDE.md` y trabaja en ramas `claude/*`.

## 5. Flujo diario

| Paso | Dónde | Qué haces |
|---|---|---|
| Capturar | App GitHub → Issues → New | Plantilla **Idea** o **Tarea** |
| Investigar | Claude Code | *"Investiga el issue #N y crea la nota en `ideas/`"* |
| Prototipar | Claude Code | *"Crea `apps/mi-app/` desde la plantilla PWA"* o *"Arregla X en el backend"* |
| Revisar | App GitHub → rama `claude/*` → commits / Actions | Lee el diff y mira que el CI esté en verde |
| Fusionar | App GitHub → Pull requests | Pide a Claude que abra el PR (o ábrelo tú) y fusiona |
| Ejecutar bots | App GitHub → Actions → workflow → **Run workflow** | Lanza automatizaciones a mano |

## 6. Instalar tus PWAs en la pantalla de inicio

1. Una vez: conecta el repo a **Cloudflare Pages** (output `apps`, sin build). Detalle en
   [apps/README.md](../apps/README.md#instalarla-en-el-iphone-sin-github-pages).
2. Abre `https://<proyecto>.pages.dev/<app>/` en **Safari**.
3. **Compartir** → **Añadir a pantalla de inicio** → **Añadir**.
4. Ábrela desde el icono: pantalla completa y funciona sin conexión.

## 7. Secretos

- Nunca pegues claves en issues, chats ni ficheros. Para workflows:
  Settings → **Secrets and variables** → **Actions** → *New repository secret*.
- AJEL Capital: copia `.env.example` a `.env` solo en el ordenador donde lo ejecutes.
