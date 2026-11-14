# Apps para iPhone (PWA)

Cada app es una **carpeta autocontenida** de HTML/CSS/JS sin build, que se instala en el
iPhone desde Safari ("Añadir a pantalla de inicio") y funciona **offline**. No hace falta Mac
ni Xcode: todo se crea desde Claude Code en la nube.

```
apps/
├── _plantilla-pwa/          ← copia esta carpeta para cada app nueva
│   ├── index.html           UI + lógica (datos en localStorage)
│   ├── manifest.webmanifest nombre, colores, iconos, display standalone
│   ├── sw.js                service worker (caché offline)
│   ├── icons/               icon-180.png (apple-touch-icon), icon-192.png, icon-512.png
│   └── generar_iconos.py    genera los iconos con Pillow
└── mi-app/                  ...
```

## Crear una app nueva

Pídeselo a Claude: *"Crea `apps/mi-app/` a partir de `_plantilla-pwa` para ..."*. A mano:

```bash
cp -r apps/_plantilla-pwa apps/mi-app
cd apps/mi-app
python3 generar_iconos.py MA 0f172a 22c55e   # letras, fondo, color (requiere: pip install pillow)
```

Luego cambia en la copia:

1. `manifest.webmanifest`: `name`, `short_name`, `description`, colores.
2. `index.html`: `<title>`, `apple-mobile-web-app-title`, `STORAGE_KEY` (único por app).
3. `sw.js`: `CACHE_VERSION` (único por app) y la lista `ASSETS` si añades ficheros.

Reglas que la plantilla ya cumple (mantenlas):

- Rutas **relativas** (`./`, `icons/...`) para que funcione en cualquier subcarpeta/dominio.
- Meta tags iOS: `viewport-fit=cover`, `apple-mobile-web-app-capable`,
  `apple-mobile-web-app-status-bar-style`, `apple-touch-icon` (180×180) y padding con
  `env(safe-area-inset-*)` para el notch y la barra de inicio.
- Inputs con `font-size: 16px` (evita el zoom automático de Safari).
- **Cada vez que cambies un fichero, sube `CACHE_VERSION`** en `sw.js`; si no, el iPhone
  seguirá mostrando la versión cacheada.

Notas de iOS: `localStorage` es por app instalada y Safari puede borrarlo si la app no se usa
durante semanas; añade un botón de exportar (JSON/CSV) si los datos importan. Las
notificaciones push web requieren iOS 16.4+ y la app instalada.

## Probar en local / en la nube

```bash
python3 -m http.server 8080      # desde la raíz del repo
# abrir http://localhost:8080/apps/mi-app/
```

Los service workers solo funcionan en `https://` o `localhost`.

## Instalarla en el iPhone (sin GitHub Pages)

El repo es **privado** y no usamos GitHub Pages, así que la carpeta tiene que servirse por
HTTPS desde otro sitio:

| Opción | Pros | Contras |
|---|---|---|
| **Cloudflare Pages** (conectado al repo privado) | Gratis, ilimitado en ancho de banda, deploy automático en cada push, preview por rama, se puede proteger con Cloudflare Access (gratis hasta 50 usuarios) | La URL `*.pages.dev` es pública si no activas Access |
| **Netlify** | Muy fácil, previews por rama, varios sites del mismo repo con "base directory" | Proteger con contraseña es de pago; límites del plan gratis |
| **Vercel** | Previews por rama, buen panel móvil | Plan Hobby solo uso personal/no comercial; protección limitada en gratis |
| **Artifact de claude.ai** | Cero configuración, privado por defecto, se crea desde la propia sesión de Claude | No está pensado como hosting de PWA: service worker/offline e instalación probablemente no funcionen igual (no verificado); sin deploy automático desde git |

**Recomendación:** Cloudflare Pages conectado al repo privado, con *Build command* vacío y
*Build output directory* = `apps` (todas las apps en `https://<proyecto>.pages.dev/<app>/`).
Si alguna app guarda datos sensibles, actívale Cloudflare Access. Usa un Artifact solo para
enseñar un prototipo rápido.

Pasos (una vez, desde el móvil o el ordenador):
1. dash.cloudflare.com → Workers & Pages → Create → Pages → *Connect to Git*.
2. Autoriza GitHub **solo para este repo**.
3. Production branch: `main` (o la rama que quieras). Framework: *None*. Build command:
   vacío. Output directory: `apps`.
4. Deploy. Cada push redepliega; cada rama `claude/*` obtiene su propia URL de preview.

### "Añadir a pantalla de inicio" en Safari

1. Abre la URL de la app en **Safari** (no en la app de GitHub ni en Chrome).
2. Espera a que cargue por completo una vez (así se cachea para offline).
3. Pulsa **Compartir** (cuadrado con flecha hacia arriba).
4. Desliza y elige **Añadir a pantalla de inicio**.
5. Ajusta el nombre si quieres → **Añadir**.
6. Ábrela desde el icono: se verá a pantalla completa, sin barra de Safari, y funciona en modo
   avión.

Para actualizarla: tras un nuevo deploy, abre la app con conexión, ciérrala desde el
multitarea y vuelve a abrirla.
