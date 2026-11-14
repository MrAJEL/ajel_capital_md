# Repos open source recomendados, validados (nov 2026)

Investigación para AJEL Studio / Elyza, AJEL Capital, el agente secretaria y los agentes de RRHH.
Datos medidos el 14 nov 2026 con la búsqueda de GitHub, api.npmjs.org, pypistats.org y Docker Hub.

## Estándar de calidad AJEL para aceptar un repo

Un repo **pasa** si cumple los 4 obligatorios:

| # | Criterio | Umbral | Por qué |
|---|---|---|---|
| 1 | Estrellas | **≥ 10.000 ★** | Mide la confianza de la comunidad. |
| 2 | Uso real | Librería: **≥ 45.000 descargas al mes** en npm o PyPI. App o plantilla sin paquete: **≥ 1.000 forks** o **≥ 100.000 pulls** en Docker Hub. | Las estrellas se pueden inflar; el uso real no. Las apps no se publican como paquete, así que su uso se mide por forks o imágenes de Docker. |
| 3 | Actividad | Último commit hace **≤ 90 días** y repo no archivado | Un repo abandonado acumula fallos de seguridad. |
| 4 | Licencia | **MIT / Apache-2.0 / BSD** para usarlo en un producto que vendas | Con GPL, AGPL, fair-code o licencia propia (⚠️) solo vale para uso interno o como referencia, salvo que se revise la licencia. |

Recomendados, que se revisan a mano antes de integrar:
- Que haya releases versionadas en los últimos 6 meses.
- Que tenga CI y tests.
- Que tenga documentación.
- Que los issues tengan respuesta.
- Que su puntuación de seguridad OpenSSF en [scorecard.dev](https://scorecard.dev) sea de 6 o más.

Leyenda: ✅ pasa · ⚠️ pasa con reserva (licencia por revisar o un dato sin verificar) · ❌ no pasa

---

## 1. Web apps de calidad (AJEL Studio / Elyza)

| Repo | ★ | Uso real | Últ. commit | Licencia | Veredicto |
|---|---|---|---|---|---|
| [shadcn-ui/ui](https://github.com/shadcn-ui/ui) | 128k | 62,8M/mes (npm `shadcn`) | 13 nov | MIT | ✅ |
| [supabase/supabase](https://github.com/supabase/supabase) | 115k | 220M/mes (npm `@supabase/supabase-js`) | 13 nov | Apache | ✅ |
| [vercel/chatbot](https://github.com/vercel/chatbot) | 21k | 6,8k forks; usa el AI SDK `ai` (158M/mes) | 3 nov | por revisar | ⚠️ |
| [mastra-ai/mastra](https://github.com/mastra-ai/mastra) | 29,5k | 11,3M/mes (npm `@mastra/core`) | 14 nov | por revisar | ⚠️ |
| [firecrawl/open-lovable](https://github.com/firecrawl/open-lovable) | 29k | 5,5k forks | 9 oct | MIT | ✅ |
| [dyad-sh/dyad](https://github.com/dyad-sh/dyad) | 22k | 2,8k forks | 14 nov | por revisar | ⚠️ |
| ~~nextjs/saas-starter~~ | 16k | 2,7k forks | **dic 2025** | MIT | ❌ inactivo |
| ~~ixartz/SaaS-Boilerplate~~ | 7,5k | — | — | MIT | ❌ < 10k ★ |

**Recomendación:** shadcn/ui + Supabase como base de todas las apps de AJEL Studio, con el AI SDK de Vercel para las funciones de IA. Como ninguna plantilla SaaS pasa el estándar, conviene crear **la plantilla propia de AJEL Studio**.

## 2. AJEL Capital: análisis financiero

| Repo | ★ | Uso real | Últ. commit | Licencia | Veredicto |
|---|---|---|---|---|---|
| [TauricResearch/TradingAgents](https://github.com/TauricResearch/TradingAgents) | 122k | 23k forks | 4 nov | Apache | ✅ |
| [virattt/ai-hedge-fund](https://github.com/virattt/ai-hedge-fund) | 65k | 11k forks | 9 nov | MIT | ✅ |
| [openbq-org/OpenBB](https://github.com/openbq-org/OpenBB) | 75k | 72k/mes (PyPI `openbb`) | 13 nov | por revisar | ⚠️ |
| [ranaroussi/yfinance](https://github.com/ranaroussi/yfinance) | 26k | 17,1M/mes (PyPI) | 12 nov | Apache | ✅ (los datos de Yahoo son para uso personal) |
| ~~AI4Finance-Foundation/FinRobot~~ | 8,4k | 415/mes | — | Apache | ❌ |
| ~~AI4Finance-Foundation/FinGPT~~ | 21,5k | 166/mes | — | MIT | ❌ poco uso |
| ~~virattt/dexter~~ | 28k | — | — | sin licencia | ❌ |

**Recomendación:** construir un comité de agentes al estilo TradingAgents sobre tu `composite_scorer.py`, usando yfinance (y OpenBB, si su licencia lo permite) como fuente de datos.
> Son proyectos de investigación. No den señales de inversión sin backtesting.

## 3. Agente secretaria: citas y calendario

| Repo | ★ | Uso real | Últ. commit | Licencia | Veredicto |
|---|---|---|---|---|---|
| [calcom/cal.diy](https://github.com/calcom/cal.diy) (Cal.com) | 50k | 5,4M pulls en Docker; 3,3M/mes (npm `@calcom/embed-react`) | 13 nov | MIT | ✅ |
| [googleworkspace/cli](https://github.com/googleworkspace/cli) | 32k | 2k forks | 3 nov | Apache | ✅ |
| ~~taylorwilsdon/google_workspace_mcp~~ | 3,5k | 292k/mes (PyPI) | 13 nov | MIT | ❌ < 10k ★ (mucho uso, pero pocas estrellas) |
| ~~langchain-ai/agents-from-scratch~~ | 2,5k | — | — | MIT | ❌ |
| ~~alextselegidis/easyappointments~~ | 4,5k | 156k pulls en Docker | — | GPL | ❌ |

**Recomendación:** Cal.com para las reservas y un agente Claude con Google Calendar y Gmail para la gestión. Esos conectores ya están en esta sesión, así que no hace falta ningún repo extra para empezar.

## 4. Agentes de entrevistas de RRHH

| Repo | ★ | Uso real | Últ. commit | Licencia | Veredicto |
|---|---|---|---|---|---|
| [livekit/agents](https://github.com/livekit/agents) | 15k | 5,0M/mes (PyPI) + 4,6M/mes (npm) | 14 nov | Apache | ✅ |
| [pipecat-ai/pipecat](https://github.com/pipecat-ai/pipecat) | 17k | 1,57M/mes (PyPI) | 14 nov | BSD | ✅ |
| [twentyhq/twenty](https://github.com/twentyhq/twenty) (CRM, como pipeline de candidatos) | 61k | 3,4M pulls en Docker | 14 nov | por revisar | ⚠️ |
| ~~FoloUp/FoloUp~~ | 1,3k | 306 forks | 17 oct | MIT | ❌ < 10k ★ |
| ~~frappe/hrms~~ | 9k | — | — | GPL | ❌ |

**Ningún entrevistador de RRHH ya hecho pasa el estándar.** La opción de calidad es **construirlo sobre LiveKit Agents o Pipecat (voz) + Claude**. FoloUp sirve solo como referencia de diseño.
> Por ley, la decisión final debe ser humana y hay que avisar al candidato de que habla con una IA. En la UE es un sistema de "alto riesgo".

## 5. Frameworks de agentes y automatización

| Repo | ★ | Uso real | Últ. commit | Licencia | Veredicto |
|---|---|---|---|---|---|
| [langchain-ai/langgraph](https://github.com/langchain-ai/langgraph) | 45k | 58,8M/mes (PyPI) | 14 nov | MIT | ✅ |
| [crewAIInc/crewAI](https://github.com/crewAIInc/crewAI) | 61k | 2,6M/mes (PyPI) | 13 nov | MIT | ✅ |
| [anthropics/claude-agent-sdk-python](https://github.com/anthropics/claude-agent-sdk-python) | 8,5k | 36,3M/mes (PyPI) + 64,9M/mes (npm) | 13 nov | MIT | ⚠️ excepción: SDK oficial de Anthropic con uso enorme |
| [n8n-io/n8n](https://github.com/n8n-io/n8n) | 210k | 286M pulls en Docker | 14 nov | fair-code | ⚠️ solo uso interno |
| [activepieces/activepieces](https://github.com/activepieces/activepieces) | 25,5k | 2,4M pulls en Docker | 13 nov | por revisar | ⚠️ |

---

## Cómo validar un repo nuevo (desde el móvil, pidiéndoselo a Claude)
Pide: *"Valida el repo X con el estándar AJEL"*. Claude consulta:
- estrellas, forks, último commit y licencia en GitHub;
- descargas al mes en npm (`api.npmjs.org`) o PyPI (`pypistats.org`);
- pulls en Docker Hub.

Con eso emite el veredicto ✅/⚠️/❌.
