# Repos open source recomendados (nov 2026)

Investigación para AJEL Studio / Elyza, AJEL Capital, el agente secretaria y los agentes de RRHH.
Estrellas y fecha de última actividad tomadas de la búsqueda de GitHub el 14 nov 2026.

**Leyenda de licencias**
- ✅ MIT / Apache / BSD: puedes usar y modificar el código, también en un producto comercial.
- ⚠️ GPL / AGPL / fair-code: si lo ofreces como servicio, puede obligarte a liberar tu código, o tener límites comerciales. Úsalo como herramienta interna o como referencia.
- ❌ Sin licencia: solo sirve para aprender. No copies su código.

---

## 1. Desarrollo de web apps de calidad (AJEL Studio / Elyza)

| Repo | ★ | Licencia | Para qué |
|---|---|---|---|
| [shadcn-ui/ui](https://github.com/shadcn-ui/ui) | 128k | ✅ MIT | Base de componentes UI. Es el estándar de calidad en Next.js + Tailwind, que es el stack que ya usa AJEL Capital. |
| [supabase/supabase](https://github.com/supabase/supabase) | 115k | ✅ Apache | Postgres, auth, storage y realtime ya hechos. Sirve para lanzar apps de clientes rápido. |
| [nextjs/saas-starter](https://github.com/nextjs/saas-starter) | 16k | ✅ MIT | Plantilla oficial: Next.js + Postgres + Stripe + shadcn. Buen punto de partida para cada app nueva. |
| [ixartz/SaaS-Boilerplate](https://github.com/ixartz/SaaS-Boilerplate) | 7.5k | ✅ MIT | Plantilla SaaS más completa: multi-tenant, i18n, tests. Muy mantenida. |
| [vercel/chatbot](https://github.com/vercel/chatbot) | 21k | ⚠️ revisar | Chat de IA de referencia en Next.js. Sirve para la interfaz de Elyza si es un asistente. |
| [mastra-ai/mastra](https://github.com/mastra-ai/mastra) | 29k | ⚠️ revisar | Framework de agentes en TypeScript, para meter IA dentro de las apps web. |
| [dyad-sh/dyad](https://github.com/dyad-sh/dyad) | 22k | ⚠️ revisar | Constructor de apps con IA local (alternativa a v0, Lovable o Bolt), para prototipar rápido. |
| [firecrawl/open-lovable](https://github.com/firecrawl/open-lovable) | 29k | ✅ MIT | Convierte un sitio web en una app React. Útil para rediseñar webs de clientes. |

**Recomendación:** estandarizar AJEL Studio en Next.js + shadcn/ui + Supabase o Postgres, partiendo de `nextjs/saas-starter`. Es el mismo stack que AJEL Capital, así que el conocimiento se reutiliza.

## 2. AJEL Capital: análisis financiero con IA

| Repo | ★ | Licencia | Para qué |
|---|---|---|---|
| [TauricResearch/TradingAgents](https://github.com/TauricResearch/TradingAgents) | 122k | ✅ Apache | Equipo de agentes que imita una mesa de trading: analistas fundamental, técnico, de sentimiento y de noticias, debate alcista/bajista, y gestor de riesgo. Es la mejor referencia de arquitectura. |
| [virattt/ai-hedge-fund](https://github.com/virattt/ai-hedge-fund) | 65k | ✅ MIT | Agentes con el estilo de inversores conocidos (value, growth, etc.) más gestión de riesgo y de cartera. Muy fácil de leer. |
| [openbq-org/OpenBB](https://github.com/openbq-org/OpenBB) | 75k | ⚠️ revisar | Plataforma de datos financieros para analistas y agentes de IA. Podría ser la fuente de datos del backend. |
| [AI4Finance-Foundation/FinRobot](https://github.com/AI4Finance-Foundation/FinRobot) | 8.4k | ✅ Apache | Agentes para informes de análisis de acciones. |
| [AI4Finance-Foundation/FinGPT](https://github.com/AI4Finance-Foundation/FinGPT) | 22k | ✅ MIT | LLMs financieros y datasets (sentimiento de noticias). |
| [virattt/dexter](https://github.com/virattt/dexter) | 28k | ❌ sin licencia | Agente de investigación financiera profunda. Solo como ideas. |
| [ranaroussi/yfinance](https://github.com/ranaroussi/yfinance) | 26k | ✅ Apache | Precios gratuitos de Yahoo Finance. Es un complemento rápido para `backend/api/prices.py`. |

**Recomendación:** el backend ya tiene `core/composite_scorer.py` y `core/technical_analysis.py`. El siguiente paso natural es una capa de agentes inspirada en TradingAgents: cada agente usa tus scorers como herramienta, y un agente "comité" emite la tesis final. Implementarlo en el backend FastAPI con el Claude Agent SDK ([anthropics/claude-agent-sdk-python](https://github.com/anthropics/claude-agent-sdk-python)). Las skills de [anthropics/skills](https://github.com/anthropics/skills) sirven de ejemplo de formato.
> Estos proyectos son de investigación y educativos. No den señales de inversión sin validación ni backtesting.

## 3. Agente secretaria: citas y calendario

| Repo | ★ | Licencia | Para qué |
|---|---|---|---|
| [calcom/cal.diy](https://github.com/calcom/cal.diy) | 50k | ✅ MIT | Cal.com, la infraestructura de reservas open source. Páginas de reserva, disponibilidad y API. Lo puedes autoalojar. |
| [taylorwilsdon/google_workspace_mcp](https://github.com/taylorwilsdon/google_workspace_mcp) | 3.5k | ✅ MIT | Servidor MCP para Gmail, Calendar, Docs y Drive. Le da "manos" al agente. |
| [googleworkspace/cli](https://github.com/googleworkspace/cli) | 32k | ✅ Apache | CLI oficial de Google Workspace, pensada para humanos y agentes. |
| [langchain-ai/agents-from-scratch](https://github.com/langchain-ai/agents-from-scratch) | 2.5k | ✅ MIT | Tutorial de asistente de email y calendario con aprobación humana y memoria. Es la mejor guía de diseño. |
| [ridafkih/keeper.sh](https://github.com/ridafkih/keeper.sh) | 1.5k | ⚠️ AGPL | Sincroniza Google, Outlook e iCloud, y es MCP de calendario universal. |
| [tavily-ai/meeting-prep-agent](https://github.com/tavily-ai/meeting-prep-agent) | 207 | ✅ MIT | Investiga a los asistentes antes de cada reunión. |
| [thunderbird/appointment](https://github.com/thunderbird/appointment) | 558 | ⚠️ MPL | Alternativa ligera a Calendly. |
| [alextselegidis/easyappointments](https://github.com/alextselegidis/easyappointments) | 4.5k | ⚠️ GPL | Agenda de citas autoalojada, para negocios con servicios (clínicas, salones). |

**Recomendación:** Cal.com para la reserva pública (link para clientes) y un agente Claude con un MCP de Google Calendar y Gmail para la gestión: confirmar, reagendar, recordatorios y resumen diario. Siempre con aprobación humana antes de enviar o aceptar algo. Para voz o teléfono, ver la sección 4.
> En esta sesión de Claude ya están conectados Google Calendar y Gmail, así que se puede prototipar el agente ya mismo.

## 4. Agentes de IA para entrevistas de RRHH

| Repo | ★ | Licencia | Para qué |
|---|---|---|---|
| [FoloUp/FoloUp](https://github.com/FoloUp/FoloUp) | 1.3k | ✅ MIT | Entrevistador de voz con IA para contratación: crea la entrevista, el candidato habla y la IA genera un análisis. Es el más cercano a lo que buscas. |
| [livekit/agents](https://github.com/livekit/agents) | 15k | ✅ Apache | Framework de agentes de voz en tiempo real. Es la base para un entrevistador por voz o video. |
| [pipecat-ai/pipecat](https://github.com/pipecat-ai/pipecat) | 17k | ✅ BSD | Alternativa a LiveKit para agentes de voz y multimodales. Tiene muchos ejemplos. |
| [minthcm/minthcm](https://github.com/minthcm/minthcm) | 438 | ⚠️ AGPL | Sistema de RRHH (HCM) con agentes de IA y MCP. |
| [frappe/hrms](https://github.com/frappe/hrms) | 9k | ⚠️ GPL | Sistema de RRHH y nómina completo, que incluye reclutamiento. |
| [twentyhq/twenty](https://github.com/twentyhq/twenty) | 61k | ⚠️ revisar | CRM open source, usable como pipeline de candidatos. |

**Recomendación:** partir de FoloUp, o construir uno propio con LiveKit Agents y Claude. El agente necesita:
- un banco de preguntas por puesto;
- una rúbrica de evaluación;
- transcripción y un informe con evidencias;
- **decisión final siempre humana**.

Esto último importa por ley: en la UE y en varios estados de EE. UU. la IA de contratación es "alto riesgo" o requiere avisos y auditorías de sesgo. Hay que informar al candidato de que habla con una IA.

## 5. Transversal: frameworks de agentes y automatización

| Repo | ★ | Licencia | Para qué |
|---|---|---|---|
| [anthropics/claude-agent-sdk-python](https://github.com/anthropics/claude-agent-sdk-python) | 8.5k | ✅ MIT | SDK para crear agentes con Claude. Encaja con el backend en Python. |
| [anthropics/claude-cookbooks](https://github.com/anthropics/claude-cookbooks) | 55k | ✅ MIT | Recetas: tool use, RAG, agentes, etc. |
| [langchain-ai/langgraph](https://github.com/langchain-ai/langgraph) | 45k | ✅ MIT | Agentes con estado y flujos con aprobación humana. |
| [crewAIInc/crewAI](https://github.com/crewAIInc/crewAI) | 61k | ✅ MIT | Equipos de agentes por roles, que encaja con el "comité" de AJEL Capital. |
| [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers) | 92k | ⚠️ revisar | Servidores MCP de referencia, para conectar agentes con herramientas. |
| [n8n-io/n8n](https://github.com/n8n-io/n8n) | 210k | ⚠️ fair-code | Automatizaciones visuales con IA. Bien como uso interno, no para revenderlo como servicio. |
| [activepieces/activepieces](https://github.com/activepieces/activepieces) | 26k | ⚠️ revisar | Alternativa a n8n con unos 400 MCPs. |

---

## Siguientes pasos propuestos
1. **Agente secretaria (MVP):** un agente Claude con Google Calendar y Gmail que haga el resumen diario de la agenda, proponga huecos y redacte confirmaciones. Es lo más rápido y ya tenemos los conectores.
2. **AJEL Capital, comité de agentes:** prototipo estilo TradingAgents sobre los scorers existentes.
3. **Entrevistador de RRHH:** probar FoloUp tal cual y luego decidir si se adapta o se hace desde cero con LiveKit.
4. **AJEL Studio:** crear un repo plantilla (Next.js + shadcn + Supabase) para cada app nueva.
