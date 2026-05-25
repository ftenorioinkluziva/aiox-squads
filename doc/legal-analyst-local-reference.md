# Legal Analyst Squad - Referencia Local

Este documento registra como este checkout esta sendo usado como laboratorio local para testar e evoluir a webapp do `squads/legal-analyst`, sem depender da squad mantenedora do projeto original.

## Repositorio

- Pasta local: `C:\projetos\legal-analyst-squad`
- Branch de trabalho: `local/legal-analyst-webapp`
- Fork pessoal: `https://github.com/ftenorioinkluziva/aiox-squads`
- Repositorio original: `https://github.com/SynkraAI/aiox-squads`

Remotes esperados:

```powershell
git remote -v
```

```text
origin   https://github.com/ftenorioinkluziva/aiox-squads.git
upstream https://github.com/SynkraAI/aiox-squads.git
```

O `upstream` deve ser usado apenas para buscar atualizacoes do projeto original. O trabalho local deve ser salvo no `origin`.

## Fluxo Git

Trabalhar sempre na branch local:

```powershell
cd C:\projetos\legal-analyst-squad
git checkout local/legal-analyst-webapp
```

Publicar alteracoes no fork:

```powershell
git status
git add <arquivos>
git commit -m "mensagem objetiva"
git push
```

Atualizar com o projeto original:

```powershell
git checkout main
git pull upstream main
git checkout local/legal-analyst-webapp
git rebase main
git push --force-with-lease
```

## Como Rodar Localmente

Backend:

```powershell
cd C:\projetos\legal-analyst-squad\squads\legal-analyst\webapp\backend

python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Frontend:

```powershell
cd C:\projetos\legal-analyst-squad\squads\legal-analyst\webapp\frontend

npm install
npm run dev
```

URLs usuais:

- Backend: `http://127.0.0.1:8000`
- Frontend Vite: `http://localhost:5173/app`
- Alternativa se especificar porta: `http://127.0.0.1:3000/app`

## Variaveis de Ambiente

Arquivo:

```text
C:\projetos\legal-analyst-squad\squads\legal-analyst\webapp\.env
```

Campos relevantes:

- `ANTHROPIC_API_KEY`
- `ANTHROPIC_MODEL`
- `OPENAI_API_KEY`
- `OPENAI_MODEL`
- `DATABASE_URL`
- `API_PORT`
- `UI_PORT`
- `STRIPE_SECRET_KEY`
- `STRIPE_PUBLISHABLE_KEY`
- `STRIPE_WEBHOOK_SECRET`
- `STRIPE_PRICE_ID`
- `APP_URL`
- `JUSBRASIL_API_KEY`
- `DATAJUD_API_KEY`
- `DATAJUD_BASE_URL`

Sem chave da Anthropic, o backend ainda roda com respostas fallback.

## Validacoes

Backend:

```powershell
cd C:\projetos\legal-analyst-squad\squads\legal-analyst\webapp\backend
.\.venv\Scripts\python.exe -c "import main; print('backend import ok')"
```

Frontend:

```powershell
cd C:\projetos\legal-analyst-squad\squads\legal-analyst\webapp\frontend
npm run typecheck
npm run build
```

Playwright:

```powershell
cd C:\projetos\legal-analyst-squad\squads\legal-analyst\webapp\frontend
npx playwright --version
npx playwright install chromium
```

Teste E2E mockado:

```powershell
cd C:\projetos\legal-analyst-squad\squads\legal-analyst\webapp\frontend
npm run dev -- --host 127.0.0.1 --port 5173
```

Em outro terminal:

```powershell
cd C:\projetos\legal-analyst-squad\squads\legal-analyst\webapp\frontend
npm run test:e2e
```

Smoke test de API com backend e banco reais:

```powershell
cd C:\projetos\legal-analyst-squad\squads\legal-analyst\webapp\backend
.\.venv\Scripts\python.exe scripts\smoke_api.py
```

Smoke test manual com Node:

```powershell
cd C:\projetos\legal-analyst-squad\squads\legal-analyst\webapp\frontend

@'
const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  await page.goto('http://127.0.0.1:3000/app', { waitUntil: 'domcontentloaded', timeout: 15000 });
  console.log(await page.title());
  await browser.close();
})();
'@ | node -
```

## Correcoes Ja Aplicadas

Commits locais principais:

- `c08e6e7 fix: repair legal analyst webapp startup`
- `91feba8 feat: flag scanned legal documents`
- `537482a fix: recover upload sessions after reload`
- `dd8acda fix: reuse analysis on page reload`
- `396d076 chore: add playwright for browser checks`

Resumo das correcoes:

- Corrigidos imports do backend em `agents/loader.py`.
- Corrigido erro de typecheck em `MessageBubble.tsx`.
- Corrigidos YAMLs invalidos em agentes.
- Adicionado diagnostico de PDFs escaneados.
- UI passou a avisar quando documento precisa de OCR.
- Upload recupera sessao se o backend tiver recarregado.
- Reload da pagina reutiliza a analise atual via `localStorage`.
- Playwright instalado para validacoes de navegador.

## Caso de Teste Atual

Arquivo usado:

```text
C:\Users\fteno\Downloads\BUSCA E APREENSÃO EM ALIENAÇÃO FIDUCIÁRIA (81).pdf
```

Resultado esperado no estado atual:

```text
extraction_status: ocr_required
ocr_required: true
text_page_count: 0
scanned_page_count: 2
```

Mensagem esperada ao enviar no chat:

```text
Documento recebido, mas a leitura automatica ainda esta incompleta.
2 de 2 pagina(s) parecem escaneadas e precisam de OCR.
```

## Decisoes de Produto

Direcao acordada:

- Reutilizar a webapp existente como base do MVP.
- Evitar uma interface centrada em CLI/agentes internos.
- Construir uma experiencia guiada para usuario leigo ou advogado.
- Extrair automaticamente o maximo possivel do PDF.
- Perguntar em linguagem simples apenas o que faltar.
- Tratar documentos escaneados como fluxo normal, nao como erro do usuario.

## Planejamento de Implementacao

O planejamento por epicos e sprints esta em:

```text
doc/implementation-plan/README.md
```

Ordem atual recomendada:

1. Persistencia de sessoes e documentos.
2. Pipeline retomavel e DB-backed.
3. OCR real e qualidade juridica dos outputs.

## Pipeline Proposto de Extracao

Ordem recomendada:

1. Extracao textual simples com PyMuPDF.
2. OCR fallback para paginas sem texto.
3. LLM/Vision como fallback para paginas complexas ou OCR ruim.

Para documentos juridicos grandes:

- nao enviar o processo inteiro bruto para o LLM;
- extrair por pagina;
- classificar paginas/blocos;
- gerar chunks juridicos;
- criar resumo por chunk;
- responder perguntas via busca de contexto relevante.

## Proximos Passos Tecnicos

## Pipeline Real Multiagente

Contratos adicionados para execucao real do workflow `wf-analise-processual-completa`:

- `POST /api/pipelines/start` com `session_id` e `workflow_id` opcional.
- `GET /api/pipelines/{run_id}` para estado persistido.
- `GET /api/sessions/{session_id}/pipelines/latest` para restaurar a UI.
- `WS /api/pipelines/{run_id}/ws` para eventos em tempo real.

Persistencia:

- `DATABASE_URL` deve apontar para PostgreSQL/Neon.
- O backend cria as tabelas no startup via SQLAlchemy e tambem inclui Alembic em `backend/alembic`.
- URLs Neon com `sslmode=require` e `channel_binding=require` sao normalizadas para `asyncpg`.

LLM:

- Anthropic continua como provedor primario via `ANTHROPIC_API_KEY` e `ANTHROPIC_MODEL`.
- OpenAI e fallback via `OPENAI_API_KEY` e `OPENAI_MODEL`.
- Default recomendado para fallback: `OPENAI_MODEL=gpt-5.4-mini`.
- O fallback atual usa Chat Completions, que ainda e compativel com `gpt-5.4-mini`.
- Migracao futura recomendada: usar Responses API para raciocinio, workflows multi-turn, tool calling e outputs estruturados.
- Pipeline real nao usa fallback template; se nenhum provedor real estiver configurado, o step falha.

Frontend:

- O pipeline inicia por botao no chat, nao automaticamente apos upload.
- Documento com `ocr_required=true` bloqueia a analise ate a leitura complementar.
- O stepper mostra fases reais a partir de `pipeline_steps`, nao texto mockado.

## Integracao DataJud

A API Publica do DataJud usa a base:

```text
https://api-publica.datajud.cnj.jus.br/{alias_do_tribunal}/_search
```

Autenticacao:

```text
Authorization: APIKey {DATAJUD_API_KEY}
Content-Type: application/json
```

Endpoints locais adicionados:

```text
GET /api/datajud/process/{tribunal_alias}/{process_number}
POST /api/datajud/search
POST /api/intake/datajud
```

Exemplo TJDFT:

```text
GET /api/datajud/process/tjdft/07028077020258070012
```

Intake direto por numero de processo:

```powershell
Invoke-RestMethod -Method Post "http://127.0.0.1:8001/api/intake/datajud" `
  -ContentType "application/json" `
  -Body '{"tribunal_alias":"tjdft","process_number":"07028077020258070012","start_pipeline":false}'
```

Comportamento:

- consulta o processo na API Publica DataJud/CNJ;
- cria uma sessao nova quando `session_id` nao e informado;
- persiste um documento virtual `application/vnd.datajud+json` com uma pagina `extraction_method=datajud`;
- registra mensagem de intake no chat com referencia ao documento virtual;
- permite iniciar o pipeline com `start_pipeline=true`, sem PDF, usando os metadados e movimentacoes DataJud como contexto oficial;
- mantem o aviso de limite: DataJud nao substitui a integra dos autos quando a analise depender de pecas, provas, despachos ou decisoes completas.

## Estudo: Jurisprudencias.ai

Fonte consultada em 22/05/2026:

- `https://jurisprudencias.ai/api`
- `https://jurisprudencias.ai/openapi.json`
- `https://jurisprudencias.ai/llms.txt`

Resumo tecnico:

- Base URL: `https://jurisprudencias.ai/api/v1`.
- Autenticacao: `Authorization: Bearer jur_seu_token`.
- Endpoint para listar bases: `GET /api/v1/courts`.
- Endpoint de busca textual: `GET /api/v1/courts/{court_id}/decisions?q=...&page=0`.
- Filtros de data suportados: `pub_from`, `pub_to`, `trial_from`, `trial_to`.
- Endpoint de lookup por numero: `GET /api/v1/courts/{court_id}/decisions/lookup?n=...`.
- Campos de resposta documentados: `process_number`, `process_type`, `rapporteur`, `adjudicating_body`, `publication_date`, `trial_date`, `excerpt` ou `summary`, `url`, `court`.
- Cobertura informada no OpenAPI/llms.txt: STF, STJ, TST, TRF3, TRF4, TJPR, TJRJ, TJRS, TJSC, TJSP e CARF.
- Limites informados na pagina da API: busca gratuita 10/dia; assinante 500/dia. Lookup gratuito 50/dia; assinante 10.000/dia. Headers de limite: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`.

Encaixe recomendado no Legal Analyst Squad:

- Usar como complemento da fase `pesquisa jurisprudencial`, nao como substituto do DataJud.
- DataJud continua sendo fonte oficial de metadados/movimentacoes do processo.
- Jurisprudencias.ai entra como fonte de precedentes estruturados, principalmente para obter relator, orgao julgador, ementa/trecho e link oficial.
- Criar variaveis futuras:
  - `JURISPRUDENCIAS_API_KEY`;
  - `JURISPRUDENCIAS_BASE_URL=https://jurisprudencias.ai/api/v1`.
- Criar cliente isolado `jurisprudencias_client.py` com:
  - `list_courts()`;
  - `search_decisions(court_id, q, page=0, pub_from=None, pub_to=None, trial_from=None, trial_to=None)`;
  - `lookup_decision(court_id, process_number)`.
- Persistir resultados relevantes em `pipeline_outputs` ou em uma tabela propria de `legal_research_results` se a pesquisa precisar ser reutilizada entre runs.
- Tratar `401`, `422`, `429` e `404` como falhas controladas de ferramenta, sem derrubar todo o pipeline.

Prioridade 1:

- Implementar OCR fallback real no backend.
- Renderizar paginas sem texto como imagem.
- Rodar OCR apenas nas paginas marcadas como `needs_ocr`.
- Atualizar `DocumentPage.text` com o texto OCR.
- Marcar `extraction_method = "ocr"`.

Prioridade 2:

- Criar tela de revisao de dados extraidos.
- Mostrar campos encontrados e pendentes:
  - numero do processo;
  - tribunal/vara;
  - partes;
  - classe;
  - assunto;
  - tipo de acao;
  - fase processual.

Prioridade 3:

- Criar intake guiado para usuario leigo.
- Substituir campos juridicos vazios por perguntas simples.
- Oferecer objetivos comuns:
  - entender o processo;
  - avaliar risco;
  - preparar defesa;
  - gerar resumo para advogado;
  - encontrar prazos ou urgencias.

Prioridade 4:

- Adicionar testes Playwright para:
  - reload nao cria nova analise;
  - upload de PDF escaneado mostra aviso de OCR;
  - navegacao para aba Documentos preserva documento;
  - erro de sessao nao aparece apos reload.
