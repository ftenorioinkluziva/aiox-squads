# Epicos - Legal Analyst Webapp

## E1 - Persistencia de Sessoes e Documentos

**Objetivo:** remover sessao, mensagens, documentos, paginas e clips da memoria do processo.

**Problema:** o pipeline persiste no banco, mas ainda depende de `ChatManager` e `DocumentStore` em memoria. Um restart perde contexto operacional.

**Escopo:**

- criar modelos SQLAlchemy e migration para sessoes, mensagens, documentos, paginas e clips;
- implementar repositorios DB-backed;
- adaptar endpoints de sessao, upload, documentos, paginas, busca e clips;
- preservar arquivos fisicos em storage persistente local;
- garantir hidratacao da sessao apos reload/restart.

**Fora de escopo:**

- Redis como fonte de verdade;
- storage S3/R2;
- multiusuario/autenticacao;
- migracao de sessoes antigas em memoria.

**Criterios de aceite:**

- criar sessao, enviar mensagem, subir PDF e recarregar a pagina mantendo estado;
- reiniciar backend e recuperar sessao/documento pelo `session_id`;
- buscar paginas/documentos/clips sem depender de dicionarios em memoria;
- testes cobrem persistencia basica e restart simulado.

## E2 - Pipeline Retomavel e DB-backed

**Objetivo:** fazer o pipeline usar somente contexto persistido e retomar execucao apos restart.

**Problema:** runs e steps estao no banco, mas a montagem de contexto ainda consulta a sessao em memoria.

**Escopo:**

- alterar o executor para ler sessao, mensagens, documentos e paginas do banco;
- substituir `mark_interrupted_runs()` por politica de retomada/stale lock;
- registrar tentativa, provider e erro tecnico por step;
- permitir retomada de runs `queued` e `running`;
- manter WebSocket como canal de progresso em tempo real.

**Fora de escopo:**

- fila distribuida com Redis;
- execucao em multiplos workers;
- workflow editor visual.

**Criterios de aceite:**

- pipeline iniciado antes do restart continua ou retoma de forma previsivel;
- steps ja concluidos nao sao reexecutados sem motivo;
- runs bloqueados por OCR permanecem bloqueados com motivo acionavel;
- output final e mensagem do `@legal-chief` persistem e reaparecem apos reload.

## E3 - OCR Real e Preparacao Documental

**Objetivo:** transformar `ocr_required=true` em fluxo resolvivel, nao em bloqueio permanente.

**Problema:** documentos escaneados sao detectados, mas ainda nao passam por OCR.

**Escopo:**

- adicionar job/endpoint para executar OCR por documento/pagina;
- persistir texto extraido, status por pagina e confianca quando disponivel;
- atualizar `ocr_required` apos OCR bem-sucedido;
- expor status no frontend;
- permitir iniciar pipeline apos OCR.

**Fora de escopo:**

- OCR juridico especializado pago;
- revisao humana pagina a pagina;
- extracao de layout avancado.

**Criterios de aceite:**

- PDF escaneado entra como pendente de OCR;
- usuario aciona/processo dispara OCR;
- paginas recebem texto persistido;
- pipeline deixa de bloquear quando o documento fica processavel.

## E4 - Qualidade Juridica e Outputs Estruturados

**Objetivo:** reduzir Markdown livre e aumentar rastreabilidade juridica.

**Escopo:**

- definir schemas de output por fase;
- separar achados, evidencias, fundamentos, riscos e recomendacoes;
- registrar referencias a paginas/clips do documento;
- gerar relatorio Markdown final a partir de dados estruturados.

**Criterios de aceite:**

- cada fase grava output estruturado;
- relatorio final inclui referencias verificaveis;
- validacao CNJ/CPC e admissibilidade aparecem como secoes separadas;
- frontend consegue exibir resumo por fase.

## E5 - Operacao, Observabilidade e Escala

**Objetivo:** preparar a aplicacao para uso continuo.

**Escopo:**

- logs estruturados por `session_id` e `run_id`;
- health checks com banco e provider LLM;
- politica de retry e timeout;
- plano futuro para Redis como locks/fila/pubsub;
- documentacao de deploy com Neon e storage persistente.

**Criterios de aceite:**

- falhas de provider sao diagnosticaveis;
- endpoints de health indicam dependencia indisponivel;
- documentacao explica restore, migrations e variaveis de ambiente.
