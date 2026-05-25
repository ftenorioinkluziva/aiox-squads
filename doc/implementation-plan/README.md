# Plano de Implementacao - Legal Analyst Webapp

Este diretorio organiza o plano de execucao para transformar a webapp em uma aplicacao persistente, retomavel e preparada para o pipeline juridico real.

## Objetivo

Tornar a aplicacao confiavel para analise processual com:

- sessoes e documentos persistidos;
- pipeline multiagente retomavel;
- OCR real para PDFs escaneados;
- fallback OpenAI configuravel;
- progresso restauravel no frontend;
- trilha de auditoria suficiente para uso juridico assistido.

## Estado Atual

Ja implementado:

- pipeline real com runs, steps, events e outputs persistidos em PostgreSQL;
- WebSocket para eventos de progresso;
- fallback Anthropic -> OpenAI;
- botao explicito "Iniciar analise";
- bloqueio de pipeline quando `ocr_required=true`;
- documentacao base em `doc/legal-analyst-local-reference.md`.

Ainda pendente:

- ampliar testes de restart com pipeline parcialmente executado;
- OCR ainda nao processa documentos escaneados;
- outputs juridicos ainda sao predominantemente Markdown livre.

## Arquivos

- `epics.md`: epicos, objetivos, escopo e criterios de aceite.
- `dependencies.md`: ordem tecnica, dependencias e decisoes de arquitetura.
- `sprint-01-session-document-persistence.md`: persistencia de sessoes, mensagens e documentos.
- `sprint-01-test-roteiro.md`: roteiro manual/API para validar a Sprint 01.
- `sprint-02-resumable-pipeline.md`: retomada real do pipeline e execucao DB-backed.
- `sprint-03-ocr-and-quality.md`: OCR, outputs estruturados e qualidade juridica.

## Ordem Recomendada

1. Ampliar testes de restart do pipeline parcialmente executado.
2. Sprint 03: OCR e qualidade de entrega.
3. Intake guiado e revisao humana dos dados extraidos.

## Definicao de Pronto Global

Um incremento so deve ser considerado pronto quando:

- migrations rodam em banco limpo;
- backend importa sem erro;
- typecheck/build do frontend passam;
- fluxo principal foi testado com restart do backend;
- comportamento esperado foi registrado na documentacao ou nos testes.
