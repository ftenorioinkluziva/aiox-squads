# Consolidado - Legal Analyst Squad

Este documento condensa as respostas dos quatro modelos sobre o Legal Analyst Squad, organizando os pontos comuns, as recomendações práticas e os próximos passos para transformar a squad em uma solução vendável para escritórios de advocacia.

## 1. Explicação simples para um advogado

O Legal Analyst Squad pode ser apresentado como uma equipe digital de análise jurídica. Em vez de ser apenas um chatbot genérico, ele organiza o trabalho entre agentes especializados, cada um responsável por uma parte da análise: triagem, classificação, admissibilidade, jurisprudência, precedentes, relator, estratégia, validação e consolidação.

Pitch curto:

> "Doutor, pense em uma equipe virtual de especialistas jurídicos. O advogado fornece o caso, os documentos e o objetivo da análise. A ferramenta organiza o material, pesquisa jurisprudência, avalia riscos, identifica teses, aplica checklists e entrega um relatório estruturado para revisão profissional. Ela não substitui o advogado; ela acelera a parte repetitiva, documental e analítica."

O ponto central para o advogado não é "usar IA", mas ganhar:

- velocidade na pesquisa e estruturação de casos;
- padronização de análises;
- rastreabilidade das conclusões;
- redução de pontos cegos;
- apoio para tomada de decisão;
- relatórios e pareceres com evidência verificável.

## 2. O que não prometer

Para evitar expectativa errada, a comunicação comercial deve ser conservadora:

- não dizer que substitui o advogado;
- não dizer que peticiona automaticamente;
- não dizer que acessa qualquer processo sozinho;
- não prometer acerto jurídico sem revisão humana;
- não tratar resposta de LLM como fonte de verdade;
- não entregar jurisprudência sem fonte verificável.

A proposta correta é "suporte analítico com supervisão humana", não "advocacia autônoma".

## 3. Modelo mental de funcionamento

O fluxo ideal é:

1. O usuário cria um caso.
2. Faz upload de documentos ou descreve o problema.
3. Define o objetivo da análise.
4. A squad executa um workflow multiagente.
5. O sistema produz entregáveis parciais e finais.
6. O advogado revisa, ajusta, aprova e exporta.

Entradas possíveis:

- PDF de processo;
- petição inicial;
- contestação;
- sentença;
- acórdão;
- contrato;
- procuração;
- e-mails;
- transcrição de áudio;
- número do processo;
- descrição livre do caso.

Saídas esperadas:

- relatório jurídico consolidado;
- mapa jurisprudencial;
- tese dominante e teses alternativas;
- análise de admissibilidade;
- checklist processual;
- riscos jurídicos e financeiros;
- perfil do relator;
- estratégia recursal;
- sumário executivo;
- minuta ou fundamentação revisável;
- exportação em PDF, DOCX ou Markdown.

## 4. Como usar a squad tecnicamente

As respostas apontam que a squad opera dentro do ecossistema AIOX/AIOS e segue uma filosofia CLI-first. Ou seja: a operação canônica nasce em comandos, arquivos, agentes, tarefas e workflows.

Essa camada técnica deve ser mantida como motor interno, mas não deve ser exposta ao advogado.

Arquitetura recomendada:

```text
[Interface para o advogado]
        |
[API / Orquestrador / Fila]
        |
[Worker que chama AIOX CLI ou SDK]
        |
[Legal Analyst Squad]
        |
[Outputs estruturados]
```

Na prática, a TI instala, configura API keys/modelos, disponibiliza o squad em ambiente controlado e encapsula a execução em workers. O advogado apenas usa telas, botões, formulários, notificações e documentos finais.

Observação: os comandos citados pelos modelos devem ser validados no repositório e na versão instalada antes de virarem documentação oficial, porque algumas respostas tratam comandos como exemplos conceituais.

## 5. Produto recomendado: Case Operating System

A recomendação mais forte entre as respostas é não criar "mais um chat jurídico". O produto deve ser pensado como um sistema operacional de casos:

- cada caso tem documentos, histórico, objetivos, análises e versões;
- cada análise passa por etapas visíveis;
- cada conclusão tem fonte, evidência e responsável;
- cada parecer pode ser revisado, comentado e exportado;
- cada tese pode ser reaproveitada em casos futuros.

Nome conceitual:

> Case Operating System ou Legal Case OS

Internamente:

> CLI-first, workflow-first, auditável e versionável.

Externamente:

> case-first, visual, jurídico, simples e orientado a resultado.

## 6. Interface recomendada para advogados

### MVP web

O melhor ponto de partida é uma aplicação web simples.

Funcionalidades do MVP:

- login;
- cadastro de cliente/caso;
- upload de documentos;
- escolha do tipo de análise;
- campo para objetivo da análise;
- dashboard de análises em andamento/concluídas;
- visualizador do relatório;
- exportação PDF/DOCX;
- histórico por caso.

Stack sugerida:

- frontend: Next.js, React, Tailwind, shadcn/ui;
- backend: FastAPI ou Node.js/Fastify;
- fila: Redis + BullMQ, Celery ou equivalente;
- banco: PostgreSQL;
- storage: S3/MinIO;
- worker: container que executa a squad;
- OCR: Tesseract, AWS Textract, Azure Document Intelligence ou similar.

### UX essencial

O advogado deve ver:

- "Novo caso", não "run squad";
- "Dossiê do caso", não "context package";
- "Especialista processual", não "agent";
- "Revisão técnica", não "validator";
- "Análise em andamento", não "pipeline";
- "Pendência encontrada", não "quality gate".

Componentes importantes:

- stepper de progresso;
- timeline do caso;
- split screen com documento original e análise;
- cards de alerta para inconsistências;
- matriz de risco;
- comentários e revisão humana;
- botão de exportação;
- notificação por e-mail/WhatsApp quando terminar.

## 7. Funcionalidades para aproveitar ao máximo a squad

### 7.1 Intake e saneamento de dados

- Upload de PDF, DOCX, ZIP, e-mails e transcrições.
- OCR para documentos digitalizados.
- Extração automática de partes, tribunal, relator, número CNJ, fatos, pedidos, fundamentos e jurisprudência citada.
- Classificação por área do direito, tipo processual, urgência, complexidade e tipo de análise.
- Criação de timeline: fatos, petição, sentença, acórdão, recurso.

### 7.2 Jurisprudência inteligente

- Busca de precedentes por tema, tribunal, data, relator e órgão julgador.
- Identificação de tese dominante e tese minoritária.
- Similaridade fática, não apenas busca por palavra-chave.
- Detecção de distinguishing.
- Alerta de overruling ou jurisprudência enfraquecida.
- Exigência de fonte verificável para cada precedente.

### 7.3 Inteligência processual

- Checklist automático por tipo de peça/recurso.
- Exemplo para RESP: prequestionamento, tempestividade, preparo, cabimento, súmulas impeditivas e violação direta.
- Detecção de nulidades, preclusão, decadência e prescrição.
- Análise de admissibilidade.
- Pontuação de risco processual.

### 7.4 Estratégia jurídica

- Geração de tese principal e teses subsidiárias.
- Comparação de estratégias por chance, risco e custo.
- Simulação de cenários: mudar tese, remover pedido, priorizar fundamento, acrescentar precedente.
- Sugestão de linha argumentativa conforme jurisprudência encontrada.

### 7.5 Relator intelligence e jurimetria

- Perfil de julgadores e relatores.
- Tendência decisória por tema.
- Tempo médio de julgamento.
- Alinhamento com precedentes.
- Taxa de provimento/improvimento por tipo de caso.
- Dashboard visual para sócios.

### 7.6 Knowledge system

- Biblioteca de teses.
- Teses versionadas em Markdown/Git.
- Reuso de argumentos aprovados.
- Base interna de precedentes.
- Memória institucional por escritório.
- Integração com Obsidian ou outro knowledge base.
- "Tese-as-Code" e "Case-as-Code".

### 7.7 Governança e auditoria

- Human-in-the-loop obrigatório.
- Aprovação por etapa.
- Registro de quem rodou a análise, quando, para qual cliente e com quais documentos.
- Log de fontes usadas.
- Registro da versão do modelo.
- Registro da versão da tese/parecer.
- Trilha LGPD e sigilo profissional.
- Alertas quando a squad encontrar inconsistência ou falta de documento.

### 7.8 Entregáveis e colaboração

- Parecer técnico.
- Sumário executivo para cliente.
- Minuta de peça revisável.
- Exportação PDF/DOCX.
- Markdown versionado.
- Comentários por trecho.
- Diff entre versões de tese.
- Aprovação final antes de uso externo.

## 8. Roadmap recomendado

### Fase 0 - Validação com advogados

Antes de construir, fazer entrevistas e shadowing com pelo menos 5 perfis:

- sócio decisor;
- advogado pleno;
- advogado júnior;
- estagiário;
- secretária/paralegal.

Objetivo: entender o fluxo real, onde perdem tempo, quais ferramentas usam, quanto gastam, que tipo de caso mais aparece e qual dor é mais monetizável.

### Fase 1 - MVP web

Entrega em 4 a 6 semanas:

- login;
- cadastro de caso;
- upload de documento;
- objetivo da análise;
- execução assíncrona da squad;
- status de progresso;
- relatório em HTML;
- exportação PDF/DOCX;
- histórico básico.

### Fase 2 - Experiência jurídica nativa

- OCR robusto;
- busca jurisprudencial inline;
- análise de admissibilidade;
- painel de riscos;
- jurimetria simples;
- chat de refinamento sobre o relatório;
- editor jurídico embutido;
- notificações por e-mail/WhatsApp.

### Fase 3 - Integrações

- Word Add-in;
- Google Docs;
- WhatsApp corporativo;
- sistemas jurídicos existentes;
- Google Drive/OneDrive;
- API DATAJUD quando aplicável.

### Fase 4 - Produto enterprise

- multi-tenant;
- isolamento por escritório;
- RBAC/perfis de usuário;
- auditoria OAB/LGPD;
- relatórios gerenciais;
- billing;
- modo treinamento para estagiários;
- on-premise ou modelo privado para clientes sensíveis.

## 9. Pesquisa com usuários: roteiro condensado

Perguntas centrais para entrevistas:

1. Como um caso novo entra hoje no escritório?
2. Quem faz a triagem inicial?
3. Quanto tempo leva uma pesquisa de jurisprudência completa?
4. Onde você pesquisa jurisprudência?
5. Como você decide se um precedente é bom?
6. Você consulta perfil de relator?
7. Como organiza julgados encontrados?
8. Como revisa citações antes de protocolar?
9. Quais tarefas você delega?
10. Qual tarefa jurídica mais repetitiva você eliminaria?
11. Quais sistemas jurídicos o escritório já paga?
12. Qual sua maior preocupação com IA: sigilo, erro, custo, OAB ou alucinação?
13. Você pagaria por uma ferramenta que reduzisse pesquisa de 4h para 30min com citações verificadas?
14. Você prefere web, Word, WhatsApp ou integração com sistema atual?

Métricas a coletar no shadowing:

- tempo total da tarefa;
- número de abas abertas;
- número de alternâncias entre sistemas;
- número de copy-pastes;
- retrabalho de formatação;
- erros de citação;
- pontos de frustração;
- interrupções;
- tarefas que podem ser automatizadas.

## 10. Posicionamento comercial

Não vender como "IA jurídica". Vender como ganho operacional mensurável:

- menos tempo de pesquisa;
- mais análises por advogado;
- menor risco de citação errada;
- padronização do trabalho do escritório;
- rastreabilidade para o sócio;
- melhor treinamento de juniors e estagiários;
- reaproveitamento de teses e precedentes.

Pitch para sócio:

> "Hoje sua equipe gasta horas pesquisando jurisprudência e estruturando fundamentos. A proposta é transformar esse trabalho repetitivo em um fluxo auditável: o advogado sobe o caso, a ferramenta organiza os documentos, pesquisa precedentes verificáveis, aponta riscos e entrega um relatório revisável. O profissional continua decidindo e assinando, mas recebe um raio-X do caso com muito menos esforço operacional."

## 11. Riscos que precisam entrar nos requisitos

- Alucinação de jurisprudência.
- Vazamento de dados e sigilo profissional.
- Responsabilidade por erro analítico.
- Uso indevido sem revisão humana.
- Processos sob segredo de justiça.
- Dependência de LLM externo.
- Falta de rastreabilidade das fontes.
- Comandos e workflows técnicos instáveis entre versões do AIOX/AIOS.

Requisitos não funcionais obrigatórios:

- anonimização de dados sensíveis;
- criptografia em repouso e em trânsito;
- controle de acesso por perfil;
- logs de auditoria;
- isolamento por cliente/escritório;
- retenção e exclusão de dados;
- exportação de evidências;
- validação humana antes de qualquer uso externo.

## 12. Recomendação final

O melhor caminho é tratar o Legal Analyst Squad como motor técnico e construir por cima uma experiência jurídica de caso.

Prioridade prática:

1. Validar dor e nicho com shadowing.
2. Escolher um recorte vertical: consumidor, trabalhista, tributário, cível estratégico etc.
3. Construir MVP web com upload, análise, progresso, relatório e exportação.
4. Garantir evidência verificável para jurisprudência.
5. Adicionar governança: revisão humana, auditoria, LGPD e histórico.
6. Depois expandir para Word, WhatsApp, sistemas jurídicos e knowledge base.

Resumo em uma frase:

> A oportunidade não é criar um chatbot para advogados; é criar um sistema operacional de análise jurídica, com a squad como motor, uma interface simples para o advogado e uma camada forte de evidência, auditoria e reaproveitamento de conhecimento.

## 13. Plano revisado após análise da webapp existente

Após verificar a implementação real em `squads/legal-analyst/webapp`, o plano deve mudar de "construir uma interface do zero" para "reutilizar e endurecer a webapp existente".

A pasta `webapp` já contém uma base relevante de produto:

- frontend React/Vite/Tailwind;
- backend FastAPI;
- upload e processamento de PDF com PyMuPDF;
- visualizador de documentos;
- recortes de páginas e trechos;
- chat jurídico com sessões;
- painel de agentes;
- carregamento dos agentes reais a partir de `squads/legal-analyst/agents`;
- uso dos prompts dos agentes como system prompt para Anthropic;
- geração de minuta e relatório estratégico;
- landing/VSL comercial;
- planos de preço;
- checkout Stripe;
- docker-compose e scripts de deploy.

Portanto, a direção correta agora é:

```text
Webapp existente
  -> validar comportamento real
  -> corrigir gaps de produto
  -> persistir dados
  -> proteger acesso
  -> auditar fontes e saídas
  -> transformar em MVP vendável
```

### 13.1 O que já deve ser reaproveitado

#### Frontend

Reaproveitar:

- `frontend/src/App.tsx` como shell principal da aplicação;
- `ChatInterface` para interação em linguagem natural;
- `PDFViewer` para leitura, busca e recorte de documentos;
- `AgentPanel` para navegação e acionamento de agentes;
- `LegalEditor` como base do editor jurídico;
- `VSLPage` como primeira versão de landing comercial;
- design atual como protótipo funcional, mas sujeito a revisão de copy e UX jurídica.

Observação: o frontend já cobre boa parte do que planejamos como MVP web. Ele precisa menos de invenção e mais de refinamento, validação e organização em fluxo de caso.

#### Backend

Reaproveitar:

- `backend/main.py` como API principal;
- endpoints de sessões, chat, documentos, páginas, thumbnails, busca e recortes;
- loader de agentes em `backend/agents/loader.py`;
- motor de resposta em `backend/core/agent_engine.py`;
- processamento de PDF em `backend/core/pdf_processor.py`;
- modelos Pydantic em `backend/core/models.py`;
- integração Stripe em `backend/core/stripe_service.py`.

O backend já lê arquivos do squad original:

- `agents`;
- `data`;
- `templates`;
- `workflows`;
- `checklists`.

Isso confirma que a webapp não é apenas uma tela solta. Ela usa a estrutura do squad como fonte de prompts e contexto. Ainda assim, ela parece executar uma orquestração própria, via FastAPI + Anthropic, e não necessariamente o workflow completo via AIOX CLI.

#### Comercialização

O commit `08b64fec321cc8c5d3de7cfc7bc455afc0df720d` adicionou uma direção comercial clara:

- Stripe Checkout;
- planos Starter, Profissional e Enterprise;
- VSL/landing page;
- fluxo de sucesso redirecionando para `/app`;
- webhook Stripe;
- status e cancelamento de assinatura.

Isso deve ser aproveitado, mas não tratado como pronto para produção ainda.

### 13.2 Gaps críticos identificados

#### Persistência

Hoje há sinais fortes de dados em memória:

- sessões ficam em `ChatManager._sessions`;
- documentos ficam em `DocumentStore._documents`, `_pages`, `_clips`;
- tokens de acesso Stripe ficam em `_access_tokens`.

Isso é suficiente para demonstração, mas não para produto real. Ao reiniciar o backend, o estado tende a se perder.

Prioridade:

- adicionar banco de dados;
- persistir usuários;
- persistir casos;
- persistir sessões;
- persistir documentos e metadados;
- persistir clips;
- persistir assinaturas/acessos;
- versionar outputs jurídicos.

#### Autenticação e autorização

O plano previa login e controle por escritório. A webapp ainda não mostra uma camada robusta de autenticação, RBAC ou multi-tenant.

Prioridade:

- criar login;
- vincular usuário a escritório;
- vincular assinatura Stripe ao usuário/escritório;
- bloquear `/app` sem acesso ativo;
- separar permissões: sócio, advogado, estagiário, admin;
- garantir isolamento de dados por escritório.

#### Stripe

A integração existe, mas ainda precisa ser endurecida:

- tokens de acesso não podem ficar apenas em memória;
- o acesso pós-pagamento precisa criar ou liberar conta real;
- webhooks precisam gravar eventos no banco;
- planos precisam controlar limites reais de uso;
- o app precisa verificar assinatura antes de permitir análise;
- cancelamento e expiração precisam afetar acesso de forma persistente.

#### Fluxo de caso

O frontend trabalha com "sessões", mas o produto planejado deve trabalhar com "casos".

Próximo passo:

- criar entidade `Case`;
- cada caso deve ter cliente, processo, documentos, sessões, relatórios, minutas e histórico;
- renomear UX de "Sessões" para "Casos" ou "Análises";
- manter sessão de chat como detalhe interno do caso.

#### Execução assíncrona

O plano previa fila e worker. A implementação atual parece processar diretamente no request.

Isso pode travar ou degradar em análises longas.

Prioridade:

- criar jobs assíncronos para análise;
- adicionar status por etapa;
- permitir retomada;
- registrar logs por agente;
- mostrar progresso real no frontend.

#### Exportação

O editor tem botão visual de exportação, mas não foi identificado endpoint claro para gerar DOCX/PDF.

Prioridade:

- exportar relatório em PDF;
- exportar minuta em DOCX;
- manter Markdown como formato intermediário;
- aplicar template/timbre;
- incluir referências documentais e recortes.

#### Evidência jurídica e fontes

A webapp usa prompts e templates para jurisprudência, jurimetria, relator e DATAJUD, mas precisa validação de integração real.

Prioridade:

- verificar se `DATAJUD_API_KEY` e `JUSBRASIL_API_KEY` são realmente usados;
- não prometer jurisprudência verificável sem integração real;
- exigir URL, número do processo, relator, órgão julgador e data;
- marcar claramente quando a saída é inferência do modelo;
- bloquear ou alertar citações sem fonte.

#### LGPD e promessas comerciais

A landing afirma LGPD, criptografia e segurança, mas a implementação ainda precisa comprovar isso.

Prioridade:

- revisar copy comercial para não prometer o que não está implementado;
- adicionar política de retenção de documentos;
- adicionar exclusão de dados;
- criptografar dados sensíveis;
- registrar consentimento;
- documentar uso de LLM externo.

### 13.3 Novo roadmap recomendado

#### Fase A - Auditoria técnica da webapp existente

Objetivo: saber exatamente o que funciona hoje.

Checklist:

- rodar a webapp localmente;
- subir backend e frontend;
- validar upload de PDF real;
- testar extração de texto;
- testar busca no documento;
- testar clips;
- testar chat com `ANTHROPIC_API_KEY`;
- testar fallback sem chave;
- testar lista de agentes;
- testar geração de relatório;
- testar geração de minuta;
- testar Stripe em modo teste;
- verificar se o webhook funciona;
- verificar se o acesso pós-checkout realmente protege o app.

Resultado esperado:

- relatório de gaps reais;
- prints ou evidências dos fluxos;
- lista de bugs;
- decisão sobre manter arquitetura atual ou refatorar.

#### Fase B - Transformar a webapp em MVP vendável

Prioridade 1:

- login;
- usuários;
- escritórios;
- casos;
- banco de dados;
- assinatura Stripe persistente;
- bloqueio de acesso por assinatura;
- upload e histórico por caso;
- exportação PDF/DOCX;
- ajustes de copy para promessas verificáveis.

Prioridade 2:

- fila assíncrona;
- status de análise;
- logs de agente;
- stepper de progresso;
- tela de resultado mais jurídica;
- revisão humana e aprovação final.

#### Fase C - Fortalecer o diferencial jurídico

- integração real com DATAJUD ou outra fonte oficial;
- jurisprudência com fonte verificável;
- checklist processual por tipo de peça;
- admissibilidade por recurso;
- matriz de risco;
- relatório executivo;
- histórico de teses;
- biblioteca de modelos.

#### Fase D - Produto de escritório

- multi-tenant;
- RBAC;
- auditoria OAB/LGPD;
- relatórios de uso;
- limites por plano;
- billing completo;
- backup;
- retenção/exclusão;
- integrações com Drive, Word, WhatsApp ou software jurídico.

### 13.4 Decisão de arquitetura revisada

Antes:

```text
Construir uma nova interface para esconder a CLI.
```

Agora:

```text
Usar a webapp existente como base e evoluir para um Legal Case OS.
```

O produto deve ser reposicionado assim:

- a webapp atual vira o protótipo/MVP base;
- a squad existente vira a camada de agentes e conhecimento;
- o backend atual vira a primeira API de orquestração;
- Stripe vira a primeira camada comercial;
- o próximo grande bloco é persistência, autenticação, governança e fontes verificáveis.

### 13.5 Próxima ação recomendada

A próxima ação objetiva é clonar o repositório em um diretório de trabalho, rodar a webapp e produzir um diagnóstico prático:

```powershell
cd squads/legal-analyst/webapp
Copy-Item .env.example .env
# preencher ANTHROPIC_API_KEY e Stripe test keys quando necessário
docker compose up --build
```

Depois validar:

- `http://localhost:3000` para a UI;
- `http://localhost:8000/api/health` para a API;
- fluxo `/app`;
- upload de PDF;
- resposta de agente;
- geração de relatório;
- geração de minuta;
- checkout Stripe em modo teste.

Esse diagnóstico deve orientar o backlog real, substituindo suposições por evidência do software já implementado.

## 14. Auditoria técnica inicial da webapp

Foi feita uma primeira execução técnica em clone local do repositório:

```text
C:\tmp\aiox-squads-analysis
```

### 14.1 Resultado da preparação

Ambiente disponível:

- Python 3.11.9;
- Node 22.16.0;
- npm 11.4.1;
- Docker instalado, mas Docker Desktop/daemon não estava ativo.

O `docker compose up --build -d` não pôde ser usado porque o daemon `dockerDesktopLinuxEngine` não estava disponível. A auditoria seguiu por execução direta com Python/Node.

Dependências instaladas:

- backend: `python -m venv .venv` + `pip install -r requirements.txt`;
- frontend: `npm install`.

### 14.2 Bloqueios encontrados antes de rodar

Foram encontrados dois bugs reais no clone analisado:

#### Backend

Arquivo:

```text
squads/legal-analyst/webapp/backend/agents/loader.py
```

Problema:

```text
ImportError: attempted relative import beyond top-level package
```

Causa:

```python
from ..core.config import AGENTS_DIR, DATA_DIR, WORKFLOWS_DIR
from ..core.models import AgentInfo, AgentTier
```

Quando o backend é iniciado a partir da pasta `backend` com `uvicorn main:app`, o pacote `agents` é importado como pacote top-level. Nesse contexto, `..core` fica acima do pacote raiz e quebra.

Correção aplicada no clone:

```python
from core.config import AGENTS_DIR, DATA_DIR, WORKFLOWS_DIR
from core.models import AgentInfo, AgentTier
```

#### Frontend

Arquivo:

```text
squads/legal-analyst/webapp/frontend/src/components/MessageBubble.tsx
```

Problema:

```text
TS2322: Type 'unknown' is not assignable to type 'ReactNode'
```

Causa: `message.metadata?.phase` é tipado como `unknown` e estava sendo usado diretamente em JSX.

Correção aplicada no clone:

```tsx
const phase = message.metadata?.phase;

{phase != null && (
  <span className="badge-gray text-[10px]">
    {String(phase)}
  </span>
)}
```

### 14.3 Checks após correção

Após as correções:

- `python -c "import main"` passou;
- `npm run typecheck` passou;
- `npm run build` passou.

Observação do build:

- o bundle principal ficou acima de 500 kB após minificação;
- isso não bloqueia o MVP, mas sugere code splitting futuramente.

### 14.4 Fluxos validados via API

A aplicação foi rodada em jobs temporários para auditoria, sem manter servidores persistentes ativos.

Endpoints/fluxos validados:

#### Health

```json
{"status":"ok","squad":"legal-analyst","version":"1.0.0"}
```

#### Frontend

`http://127.0.0.1:5173` respondeu HTTP 200 quando o Vite foi iniciado temporariamente.

#### Stripe plans

`GET /api/stripe/plans` retornou:

- Starter: R$ 97/mês, 10 análises/mês, 5 agentes;
- Profissional: R$ 197/mês, 50 análises/mês, 15 agentes;
- Enterprise: R$ 497/mês, análises ilimitadas, 15 agentes + custom.

#### Agentes

`GET /api/agents` retornou 13 agentes parseados no teste inicial.

Primeiros agentes carregados:

- `barbosa-classifier`;
- `barroso-strategist`;
- `carmem-relator`.

Diagnóstico posterior: havia 15 arquivos `.md` em `squads/legal-analyst/agents`, mas 2 não eram parseados por YAML inválido.

Agentes afetados:

- `mendes-researcher.md`;
- `nunes-quantitative.md`.

Causa:

- valores com `ex:` sem aspas dentro do bloco YAML.

Correções aplicadas no clone:

```yaml
- periodo: 'string (opcional — ex: "2020-2025")'
```

```yaml
when: "Tendencia temporal de mudanca (ex: procedencia caindo nos ultimos 3 anos)"
```

Após a correção, `load_all_agents()` e `GET /api/agents` passaram a retornar 15 agentes.

#### Sessão

`POST /api/sessions?title=Auditoria` criou sessão com:

- `session_id`;
- 2 mensagens iniciais;
- fase inicial controlada pelo backend.

#### Chat fallback

Com `ANTHROPIC_API_KEY` vazia, `POST /api/chat` funcionou via fallback/template.

Exemplo:

```text
*pesquisar dano moral inscricao indevida
```

Roteou para:

```text
mendes-researcher
```

#### Upload de PDF

Foi criado um PDF sintético simples e enviado para:

```text
POST /api/documents/upload?session_id=...
```

Resultado:

- upload aceito;
- `total_pages = 1`;
- número do processo extraído;
- tribunal extraído;
- partes extraídas.

Exemplo extraído:

```text
Processo: 1234567-89.2024.8.07.0001
Tribunal: TRIBUNAL DE JUSTICA DO DISTRITO FEDERAL
Partes: JOAO DA SILVA; BANCO EXEMPLO S.A.
```

#### Página e busca

`GET /api/documents/{doc_id}/pages/1` retornou conteúdo da página.

`GET /api/documents/{doc_id}/search?q=dano` retornou 2 ocorrências.

#### Relatório estratégico

`POST /api/report` gerou relatório via `legal-chief`, incluindo síntese processual com dados do documento carregado.

### 14.5 Achados técnicos importantes

#### A webapp é funcional como protótipo

A base é tecnicamente válida para MVP:

- API sobe;
- frontend compila;
- agentes são carregados;
- PDF é processado;
- chat fallback funciona;
- relatórios são gerados;
- planos Stripe são expostos.

#### Ainda não é produto pronto

Os principais limitadores continuam:

- dados em memória;
- sem login real;
- sem controle de acesso persistente;
- Stripe sem persistência de acesso;
- execução síncrona;
- sem exportação DOCX/PDF confirmada;
- sem integração real validada com DATAJUD/JusBrasil;
- promessas comerciais de LGPD/criptografia ainda precisam implementação verificável;
- divergência "15 agentes" vs. 13 agentes parseados foi diagnosticada e corrigida no clone: dois arquivos tinham YAML inválido por `ex:` sem aspas.

### 14.6 Próximo backlog técnico imediato

Prioridade 1:

- aplicar correção definitiva do import em `backend/agents/loader.py`;
- aplicar correção TypeScript em `MessageBubble.tsx`;
- criar teste mínimo de import do backend;
- criar typecheck/build no CI;
- aplicar definitivamente a correção dos YAMLs em `mendes-researcher.md` e `nunes-quantitative.md`;
- rodar UI manualmente com Docker Desktop ativo ou execução direta persistente.

Prioridade 2:

- adicionar persistência com banco;
- modelar `User`, `Organization`, `Case`, `Document`, `ChatSession`, `Subscription`;
- vincular Stripe a usuário/escritório;
- proteger `/app`;
- transformar "Sessões" em "Casos" na UX;
- adicionar exportação real de relatório/minuta.

Prioridade 3:

- auditar claims da landing;
- substituir promessas não comprovadas por linguagem verificável;
- implementar política de retenção/exclusão;
- validar integrações oficiais de jurisprudência/dados processuais.
