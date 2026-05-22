# Dependencias Tecnicas e Ordem de Execucao

## Decisao de Arquitetura

PostgreSQL/Neon deve ser a fonte de verdade da aplicacao.

Redis pode ser introduzido depois como apoio operacional para:

- locks;
- fila de execucao;
- pub/sub de eventos;
- rate limit;
- cache de leitura;
- coordenacao entre workers.

Redis nao deve substituir o banco relacional para sessoes, documentos, mensagens ou resultados juridicos.

## Sequencia Obrigatoria

1. Persistir sessoes e mensagens.
2. Persistir documentos, paginas e clips.
3. Adaptar endpoints para ler/gravar no banco.
4. Fazer pipeline montar contexto pelo banco.
5. Implementar retomada de runs.
6. Implementar OCR real.
7. Estruturar outputs juridicos por fase.
8. Avaliar Redis para operacao multiworker.

## Tabelas Novas Previstas

### `chat_sessions`

- `session_id`
- `title`
- `phase`
- `created_at`
- `updated_at`
- `metadata`

### `chat_messages`

- `message_id`
- `session_id`
- `role`
- `content`
- `agent_id`
- `phase`
- `metadata`
- `created_at`

### `documents`

- `doc_id`
- `session_id`
- `filename`
- `stored_path`
- `content_type`
- `sha256`
- `total_pages`
- `text_page_count`
- `scanned_page_count`
- `ocr_required`
- `extraction_status`
- `created_at`
- `updated_at`
- `metadata`

### `document_pages`

- `page_id`
- `doc_id`
- `page_number`
- `text`
- `thumbnail_path`
- `image_path`
- `ocr_status`
- `ocr_confidence`
- `metadata`

### `document_clips`

- `clip_id`
- `doc_id`
- `session_id`
- `page_number`
- `label`
- `text`
- `bbox`
- `metadata`
- `created_at`

## Pontos de Integracao

- `core/chat_manager.py`: deve virar fachada sobre repositorio persistente ou ser substituido.
- `core/document_store.py`: deve virar fachada sobre repositorio persistente ou ser substituido.
- `core/pipeline_service.py`: deve parar de depender de objetos em memoria.
- `main.py`: endpoints devem usar repositorios DB-backed.
- `frontend/src/hooks/usePipeline.ts`: deve restaurar run com base em dados persistidos.
- `frontend/src/services/api.ts`: pode precisar de endpoints adicionais para OCR/status documental.

## Riscos

- Misturar estado em memoria e banco durante a transicao pode criar inconsistencia.
- Salvar paginas grandes diretamente no banco pode aumentar custo e latencia; para v1 e aceitavel, mas imagens devem ficar em arquivo/storage.
- Restart no meio de uma chamada LLM exige idempotencia por step.
- OCR pode ser lento; deve rodar como job e nao bloquear request HTTP longa.

## Politica de Idempotencia

- `session_id`, `doc_id`, `message_id`, `run_id` e `step_id` devem ser estaveis.
- Upload deve calcular `sha256` do arquivo.
- Reprocessamento documental deve atualizar o mesmo `doc_id`, nao criar documento duplicado sem acao explicita.
- Step concluido nao deve ser reexecutado em retomada, salvo acao administrativa futura.
