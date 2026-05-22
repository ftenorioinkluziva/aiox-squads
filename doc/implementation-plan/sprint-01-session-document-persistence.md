# Sprint 01 - Persistencia de Sessoes e Documentos

## Objetivo

Remover a dependencia de memoria para sessoes, mensagens, documentos, paginas e clips.

## Status

Em implementacao.

Primeira fatia tecnica iniciada:

- modelos DB criados para sessoes, mensagens, documentos, paginas e clips;
- migration `0002_chat_document_tables` adicionada;
- repositorios DB-backed criados;
- endpoints principais de sessao, documento, pagina, busca e clip passaram a usar repositorios;
- `agent_engine` e `pipeline_service` passaram a consultar contexto por repositorio persistente nos caminhos principais.

## Resultado Esperado

A aplicacao deve sobreviver a reload e restart do backend mantendo:

- lista de sessoes;
- historico de mensagens;
- documentos vinculados a sessao;
- paginas extraidas;
- clips/recortes;
- status de OCR.

## Escopo

### Backend

- Criar migration Alembic para:
  - `chat_sessions`;
  - `chat_messages`;
  - `documents`;
  - `document_pages`;
  - `document_clips`.
- Criar modelos SQLAlchemy correspondentes.
- Criar repositorios:
  - `session_repository.py`;
  - `document_repository.py`.
- Adaptar `ChatManager` para usar banco ou substituir seu uso nos endpoints.
- Adaptar `DocumentStore` para usar banco ou substituir seu uso nos endpoints.
- Atualizar endpoints:
  - `POST /api/sessions`;
  - `GET /api/sessions`;
  - `GET /api/sessions/{session_id}`;
  - `DELETE /api/sessions/{session_id}`;
  - `POST /api/chat`;
  - `POST /api/documents/upload`;
  - `GET /api/documents`;
  - `GET /api/documents/{doc_id}`;
  - `GET /api/documents/{doc_id}/pages/{page_number}`;
  - busca e clips.

### Frontend

- Confirmar que reload restaura sessoes e documentos via API.
- Remover dependencia de `localStorage` como recuperacao principal, mantendo apenas conveniencia de ultima sessao.
- Exibir estado documental persistido.

### Testes

- Criacao e leitura de sessao no banco.
- Criacao e leitura de mensagens.
- Upload de PDF e persistencia de metadata/paginas.
- Restart simulado: novo app/contexto consegue ler dados existentes.

## Fora de Escopo

- OCR real.
- Redis.
- Autenticacao.
- Storage S3/R2.

## Plano de Implementacao

1. Adicionar modelos DB e migration.
2. Implementar repositorios async.
3. Adaptar endpoints de sessao.
4. Adaptar upload e document endpoints.
5. Ajustar `agent_engine` para gravar mensagens no banco.
6. Ajustar frontend apenas onde a API mudar.
7. Rodar typecheck/build e testes backend.

## Criterios de Aceite

- Depois de reiniciar o backend, `GET /api/sessions/{session_id}` retorna mensagens e documentos.
- Documento carregado antes do restart continua acessivel.
- `document_store._documents`, `_pages` e `_clips` deixam de ser fonte da verdade.
- `chat_manager._sessions` deixa de ser fonte da verdade.
- Pipeline ainda inicia para documento valido apos a mudanca.
