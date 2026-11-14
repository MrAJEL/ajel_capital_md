# [EJEMPLO] Diario de trading en el iPhone

> Ejemplo ilustrativo de cómo rellenar la plantilla. Bórralo o reutilízalo.

- **Estado:** 💡 idea
- **Fecha:** 2026-11-14
- **Categoría:** app PWA · finanzas
- **Issue:** —

## Problema
Anoto las razones de cada operación en notas sueltas y luego no puedo revisarlas.

## Usuario
Yo, justo después de abrir o cerrar una posición, desde el móvil.

## Hipótesis
Si registro cada operación con tesis y emoción en <30 s, revisaré mis errores cada semana
y lo sabré si tengo ≥ 20 entradas en un mes.

## Investigación
- Apps existentes (Edgewonk, Tradervue): de pago y orientadas a escritorio.
- AJEL Capital ya tiene `/api/transactions`; a futuro se podría sincronizar.

## MVP
- [ ] PWA desde `apps/_plantilla-pwa/`: ticker, lado, precio, tesis, emoción.
- [ ] Datos en `localStorage` y exportar CSV.

## Riesgos
- Perder datos si se borra Safari → exportación periódica.

## Siguiente paso
Pedir a Claude: "crea `apps/diario-trading/` a partir de la plantilla".
