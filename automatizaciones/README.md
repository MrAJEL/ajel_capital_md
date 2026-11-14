# Automatizaciones y bots

Scripts que corren solos en **GitHub Actions** (gratis dentro de la cuota de minutos de repos
privados) y que puedes lanzar a mano desde la app de GitHub del iPhone.

## Estructura

- `automatizaciones/<nombre>.py` — el script (Python 3.11, preferiblemente solo stdlib).
- `.github/workflows/<nombre>.yml` — cuándo y cómo se ejecuta (GitHub solo lee workflows de
  esa carpeta).

## Ejemplo incluido

[`ejemplo_resumen_diario.py`](ejemplo_resumen_diario.py) +
[`../.github/workflows/ejemplo-resumen-diario.yml`](../.github/workflows/ejemplo-resumen-diario.yml):
cuenta las ideas por estado y lista las apps, y lo muestra en el *Summary* del run.
No usa red ni secretos.

- **Automático:** lunes a viernes 07:17 UTC (`cron`).
- **Manual desde el iPhone:** app de GitHub → repo → **Actions** → *Ejemplo: resumen diario*
  → **Run workflow** (puedes cambiar el saludo) → abre el run → *Summary*.
- **Local:** `python3 automatizaciones/ejemplo_resumen_diario.py --saludo "Hola"`

Para desactivarlo: Actions → workflow → `···` → *Disable workflow*.

## Crear una automatización nueva

Pide a Claude: *"Crea una automatización que haga X cada día a las 8:00 hora de Madrid,
basada en el ejemplo"*. Reglas:

1. Siempre `workflow_dispatch` (para lanzarla desde el móvil) además del `cron`.
2. `cron` va en **UTC** (Madrid = UTC+1 en invierno, UTC+2 en verano). Evita minuto `0`.
3. `permissions` mínimos (`contents: read` salvo que necesite escribir).
4. **Secretos** (tokens de Telegram, APIs, etc.): nunca en el código. Créalos en
   Settings → Secrets and variables → Actions y úsalos como `${{ secrets.NOMBRE }}`
   pasados por `env:`. Documenta en el README qué secreto necesita.
5. `timeout-minutes` corto para no gastar minutos si algo se cuelga.
6. GitHub solo ejecuta `cron` y muestra *Run workflow* para workflows que están en la rama
   **por defecto** (`main`): hasta fusionar la rama, el ejemplo no aparecerá/correrá.
7. Si un `cron` deja de ejecutarse, revisa en Actions que el workflow no esté desactivado.
