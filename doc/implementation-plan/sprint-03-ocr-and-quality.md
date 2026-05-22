# Sprint 03 - OCR e Qualidade de Entrega

## Objetivo

Destravar documentos escaneados e aumentar a qualidade/rastreabilidade dos outputs juridicos.

## Resultado Esperado

PDF escaneado deve passar por OCR, persistir texto por pagina e permitir execucao do pipeline quando processavel.

## Escopo

### OCR

- Definir motor inicial:
  - Tesseract local para MVP; ou
  - servico externo se a qualidade local for insuficiente.
- Criar status por pagina:
  - `pending`;
  - `processing`;
  - `completed`;
  - `failed`.
- Criar endpoint/job de OCR por documento.
- Atualizar `ocr_required` e `extraction_status` apos OCR.
- Exibir progresso/resultado no frontend.

### Qualidade Juridica

- Definir contratos de output por fase:
  - triagem;
  - pesquisa;
  - analise;
  - fundamentacao;
  - validacao;
  - entrega.
- Persistir outputs estruturados alem do Markdown final.
- Incluir referencias a paginas/clips quando houver.
- Manter relatorio final Markdown como entregavel v1.

### Testes

- Documento escaneado fica bloqueado antes do OCR.
- OCR gera texto persistido.
- Documento deixa de bloquear pipeline apos OCR bem-sucedido.
- Relatorio final inclui referencias documentais.

## Fora de Escopo

- Edicao humana de OCR.
- Exportacao PDF/DOCX.
- Jurimetria externa real.
- Integracao completa com DATAJUD/JusBrasil.

## Plano de Implementacao

1. Escolher motor OCR e dependencias.
2. Implementar job/endpoint de OCR.
3. Persistir texto/status por pagina.
4. Atualizar fluxo do frontend para documentos escaneados.
5. Criar schemas de output por fase.
6. Gerar Markdown final a partir dos outputs estruturados.

## Criterios de Aceite

- Usuario consegue processar um PDF escaneado sem reenviar arquivo.
- Pipeline nao roda com OCR pendente.
- Pipeline roda apos OCR concluido.
- Relatorio final deixa claro de onde vieram os achados principais.
