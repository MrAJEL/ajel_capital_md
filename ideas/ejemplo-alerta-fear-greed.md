# [EJEMPLO] Alerta diaria de miedo/codicia

> Ejemplo ilustrativo de cómo rellenar la plantilla. Bórralo o reutilízalo.

- **Estado:** 🔍 investigando
- **Fecha:** 2026-11-14
- **Categoría:** automatización · finanzas
- **Issue:** —

## Problema
Reviso a mano el sentimiento de mercado cada mañana y a veces se me olvida.

## Usuario
Yo, antes de abrir mercado.

## Hipótesis
Un aviso automático diario me ahorra 5 min/día; éxito si lo leo ≥ 4 días/semana.

## Investigación
- AJEL Capital ya expone `/api/fear-greed` (backend `api/prices.py`).
- GitHub Actions con `cron` es gratis en repos privados dentro de la cuota de minutos.
- Canal de aviso: issue/comentario en GitHub (notificación en la app) sin secretos;
  Telegram necesitaría un token en *Secrets*.

## MVP
- [ ] Partir de `automatizaciones/ejemplo_resumen_diario.py` y su workflow.

## Riesgos
- La fuente de datos cambia de formato o limita peticiones.

## Siguiente paso
Decidir la fuente (API propia desplegada o pública) y el canal de aviso.
