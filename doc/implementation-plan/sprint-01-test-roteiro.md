# Roteiro de Teste - Sprint 01

Este roteiro valida a persistencia de sessoes, mensagens, documentos, paginas e pipeline apos a primeira fatia da Sprint 01.

## Objetivo

Confirmar que a aplicacao nao depende mais de memoria para os fluxos principais de:

- criacao/listagem/recuperacao de sessoes;
- historico de mensagens;
- upload e recuperacao de documentos;
- paginas extraidas;
- status de OCR;
- inicio do pipeline com documento persistido.

## Pre-requisitos

Backend:

```powershell
cd C:\projetos\legal-analyst-squad\squads\legal-analyst\webapp\backend
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Frontend:

```powershell
cd C:\projetos\legal-analyst-squad\squads\legal-analyst\webapp\frontend
npm install
```

Variaveis obrigatorias em `squads/legal-analyst/webapp/.env`:

```text
DATABASE_URL=postgresql://...
ANTHROPIC_API_KEY=...
ANTHROPIC_MODEL=claude-sonnet-4-20250514
OPENAI_API_KEY=...
OPENAI_MODEL=gpt-5.4-mini
```

Para testar somente persistencia, `DATABASE_URL` e o minimo necessario. Para testar pipeline real com LLM, configure Anthropic ou OpenAI.

## Subir com Logs Capturaveis

Crie a pasta de logs:

```powershell
cd C:\projetos\legal-analyst-squad
New-Item -ItemType Directory -Force -Path .logs | Out-Null
```

Backend:

```powershell
cd C:\projetos\legal-analyst-squad\squads\legal-analyst\webapp\backend
.\.venv\Scripts\Activate.ps1
uvicorn main:app --reload --host 127.0.0.1 --port 8000 2>&1 | Tee-Object -FilePath C:\projetos\legal-analyst-squad\.logs\backend.log
```

Frontend:

```powershell
cd C:\projetos\legal-analyst-squad\squads\legal-analyst\webapp\frontend
npm run dev -- --host 127.0.0.1 2>&1 | Tee-Object -FilePath C:\projetos\legal-analyst-squad\.logs\frontend.log
```

Se o backend estiver temporariamente em outra porta:

```powershell
$env:VITE_API_PROXY_TARGET="http://127.0.0.1:8001"
npm run dev -- --host 127.0.0.1 2>&1 | Tee-Object -FilePath C:\projetos\legal-analyst-squad\.logs\frontend.log
```

URLs:

```text
Backend:  http://127.0.0.1:8000/api/health
Frontend: http://localhost:5173/app
```

## Acompanhar Logs

Em outro terminal:

```powershell
Get-Content C:\projetos\legal-analyst-squad\.logs\backend.log -Wait -Tail 80
```

```powershell
Get-Content C:\projetos\legal-analyst-squad\.logs\frontend.log -Wait -Tail 80
```

Se o Vite reclamar de chunks inexistentes em `node_modules/.vite/deps`, parar o frontend e rodar:

```powershell
cd C:\projetos\legal-analyst-squad\squads\legal-analyst\webapp\frontend
Remove-Item -Recurse -Force node_modules\.vite
npm run dev -- --force
```

## Teste 1 - Healthcheck

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/health
```

Esperado:

```text
status: ok
squad: legal-analyst
```

## Teste 2 - Criar e Recuperar Sessao

```powershell
$session = Invoke-RestMethod -Method Post "http://127.0.0.1:8000/api/sessions?title=Teste%20Sprint%2001"
$session.session_id
Invoke-RestMethod "http://127.0.0.1:8000/api/sessions/$($session.session_id)"
```

Esperado:

- resposta contem `session_id`;
- `messages` contem mensagem de sistema e boas-vindas;
- `documents` vazio;
- `phase` igual a `intake`.

## Teste 3 - Reload no Frontend

1. Abrir `http://localhost:5173/app`.
2. Criar ou usar uma sessao.
3. Recarregar a pagina.

Esperado:

- a tela nao quebra;
- a sessao atual reaparece;
- nao ha erro no console nem no terminal do Vite.

## Teste 4 - Upload de PDF

No frontend:

1. enviar um PDF;
2. confirmar que aparece no chat/painel;
3. copiar o `doc_id` se exibido.

Via API, se quiser validar direto:

```powershell
$sessionId = $session.session_id
$pdf = "C:\Users\fteno\Downloads\BUSCA E APREENSÃO EM ALIENAÇÃO FIDUCIÁRIA (81).pdf"
curl.exe -F "file=@$pdf" "http://127.0.0.1:8000/api/documents/upload?session_id=$sessionId"
```

Esperado:

- upload retorna `doc_id`;
- documento fica associado a sessao;
- `total_pages`, `ocr_required`, `text_page_count` e `scanned_page_count` aparecem na metadata.

## Teste 5 - Persistencia Apos Restart

1. Com sessao e documento criados, anotar:
   - `session_id`;
   - `doc_id`.
2. Parar o backend com `Ctrl+C`.
3. Subir o backend novamente.
4. Rodar:

```powershell
Invoke-RestMethod "http://127.0.0.1:8000/api/sessions/SEU_SESSION_ID"
Invoke-RestMethod "http://127.0.0.1:8000/api/documents/SEU_DOC_ID"
Invoke-RestMethod "http://127.0.0.1:8000/api/documents/SEU_DOC_ID/pages/1"
```

Esperado:

- sessao ainda existe;
- mensagens ainda existem;
- documento ainda existe;
- pagina 1 ainda retorna texto/status.

## Teste 6 - Chat com Documento Persistido

No frontend, enviar:

## Teste 6A - Intake Somente por Numero do Processo via DataJud

```powershell
$body = @{
  tribunal_alias = "tjdft"
  process_number = "07028077020258070012"
  start_pipeline = $false
} | ConvertTo-Json

$intake = Invoke-RestMethod -Method Post "http://127.0.0.1:8001/api/intake/datajud" -ContentType "application/json" -Body $body
$intake.session.session_id
$intake.document.doc_id
Invoke-RestMethod "http://127.0.0.1:8001/api/documents/$($intake.document.doc_id)/pages/1"
```

Esperado:

- resposta contem `session.session_id`;
- resposta contem `document.doc_id`;
- `document.extraction_status` igual a `extracted`;
- `document.ocr_required` igual a `false`;
- pagina 1 tem `extraction_method` igual a `datajud`;
- texto da pagina inicia com `Documento virtual DataJud`;
- a sessao possui mensagem de intake e resposta do `@legal-chief`.

Para iniciar o pipeline junto com a consulta, repetir com `start_pipeline = $true`.

```text
analisar viabilidade de recurso
```

Esperado:

- mensagem do usuario fica persistida;
- resposta do agente aparece;
- ao recarregar a pagina, historico permanece.

Validacao via API:

```powershell
Invoke-RestMethod "http://127.0.0.1:8000/api/sessions/SEU_SESSION_ID"
```

## Teste 7 - Pipeline com Documento Valido

No frontend:

1. carregar documento que nao esteja bloqueado por OCR;
2. clicar em `Iniciar analise`.

Via API:

```powershell
$body = @{ session_id = "SEU_SESSION_ID"; workflow_id = "wf-analise-processual-completa" } | ConvertTo-Json
Invoke-RestMethod -Method Post -ContentType "application/json" -Body $body http://127.0.0.1:8000/api/pipelines/start
```

Esperado:

- retorna `run_id`;
- steps aparecem como `queued/running/completed`;
- WebSocket atualiza frontend;
- output final aparece quando concluido.

## Teste 8 - Pipeline Bloqueado por OCR

Com documento `ocr_required=true`, clicar em `Iniciar analise`.

Esperado:

- run fica `blocked`;
- nenhum step chama LLM;
- motivo menciona OCR pendente;
- frontend mostra estado acionavel.

## Teste 9 - Fallback OpenAI

Para simular fallback:

1. remover temporariamente `ANTHROPIC_API_KEY` do `.env`;
2. manter `OPENAI_API_KEY` e `OPENAI_MODEL`;
3. reiniciar backend;
4. iniciar pipeline ou enviar mensagem que acione LLM.

Esperado:

- backend usa OpenAI;
- se OpenAI tambem estiver ausente, erro deve ser explicito de configuracao.

## Erros Que Devem Ser Investigados

- `DATABASE_URL nao configurada`: `.env` nao foi carregado ou variavel ausente.
- `relation ... does not exist`: migration/create_all nao executou no banco usado.
- `Sessao nao encontrada` apos restart: sessao ainda nao esta persistida ou frontend usa session antiga inexistente.
- `Documento nao encontrado` apos restart: documento nao foi vinculado/persistido.
- erro Vite em `node_modules/.vite/deps`: limpar cache do Vite.
- `WebSocket connection failed`: conferir backend em `8000` e URL gerada pelo frontend.

## Evidencias Para Registrar

Ao final de um ciclo valido, registrar:

- `session_id`;
- `doc_id`;
- `run_id`;
- prints ou trechos de log de upload;
- resposta de `GET /api/sessions/{session_id}`;
- resposta de `GET /api/sessions/{session_id}/pipelines/latest`;
- resultado de restart.
