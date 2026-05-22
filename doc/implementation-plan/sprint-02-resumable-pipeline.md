# Sprint 02 - Pipeline Retomavel

## Objetivo

Tornar o pipeline independente de estado em memoria e retomavel apos restart.

## Resultado Esperado

Um run iniciado deve poder ser consultado e retomado usando apenas PostgreSQL e arquivos persistidos.

## Escopo

### Backend

- Alterar montagem de contexto em `pipeline_service.py` para usar repositorios persistentes.
- Migrar fallback OpenAI para Responses API quando o step exigir raciocinio, workflow multi-turn, tool calling ou output estruturado.
- Substituir `mark_interrupted_runs()` por uma politica de retomada:
  - `queued`: pode ser agendado novamente;
  - `running`: se lock estiver expirado, volta para `queued` ou `failed` conforme criterio;
  - `blocked`: permanece bloqueado;
  - `completed` e `failed`: permanecem finais.
- Adicionar campos de execucao quando necessario:
  - `attempt_count`;
  - `locked_at`;
  - `locked_by`;
  - `provider_used`;
  - `model_used`;
  - `last_error`.
- Garantir idempotencia de step concluido.
- Persistir mensagem final do `@legal-chief` no banco.

### Frontend

- Restaurar ultimo pipeline ativo/concluido ao abrir a sessao.
- Exibir status real de retomada.
- Mostrar erro tecnico, bloqueio documental ou conclusao em estados distintos.

### Testes

- Run criado e consultado pelo banco.
- Step concluido nao reexecuta apos restart.
- Run `running` stale e retomado.
- Run `blocked` por OCR nao chama LLM.
- Output final persiste e reaparece no chat.

## Fora de Escopo

- Redis/fila distribuida.
- Multiplos workers.
- Cancelamento manual de run.
- Reexecucao seletiva de fase.

## Plano de Implementacao

1. Ajustar schema/migration para locks e tentativa se necessario.
2. Mover leitura de contexto para repositorios persistentes.
3. Implementar retomada no startup.
4. Adicionar protecao de idempotencia por step.
5. Persistir mensagem final via repositorio de mensagens.
6. Validar fluxo com restart manual.

## Criterios de Aceite

- Restart nao perde contexto do run.
- Frontend restaura progresso real sem mensagens mockadas.
- Runs bloqueados continuam bloqueados com motivo claro.
- Falhas de Anthropic ainda tentam OpenAI antes de falhar o step.
