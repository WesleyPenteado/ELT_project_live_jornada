# Plano de Implementação de Features - PRDs

**Documento:** Descritivo de todas as features a implementar para desenvolver os PRDs
**Data:** 12/03/2026
**PRDs Analisados:** 
1. PRD - Agente de Dados com Bot Telegram
2. PRD - Dashboard Streamlit

---

## 1. PRD - AGENTE DE DADOS COM BOT TELEGRAM

### 1.1 Infraestrutura Base

#### Feature 1.1.1: Gerenciamento de Variáveis de Ambiente
- **Descrição:** Sistema centralizado de configuração via `.env`
- **Variáveis obrigatórias:** 
  - `TELEGRAM`: Token do bot Telegram (obtido via @BotFather)
  - `POSTGRES_URL`: Connection string completa do PostgreSQL/Supabase
  - `ANTHROPIC_API_KEY`: Chave da API do Claude
  - `CHAT_ID`: ID do chat para envio automático (auto-preenchido na primeira interação)
- **Arquivo:** `.env` (não commitado)
- **Template:** `.env.example` com instruções de preenchimento
- **Tecnologia:** python-dotenv

#### Feature 1.1.2: Conexão com Banco de Dados PostgreSQL
- **Descrição:** Módulo `db.py` com interface SQLAlchemy para executar queries no banco
- **Função principal:** `execute_query(sql: str) -> list[dict]`
- **Segurança:**
  - Validação de syntax: apenas SELECT e WITH permitidos
  - Rejeição automática de queries de escrita (INSERT, UPDATE, DELETE, DROP)
  - Limite de 10 iterações de tool use por pergunta
- **Tratamento de erros:** Exceções com mensagens amigáveis
- **Cache:** Não usar cache agressivo (dados gold mudam após cada `dbt run`)
- **Logging:** Registrar todas as queries executadas com timestamp

#### Feature 1.1.3: Schema Completo das Tabelas Gold
- **Descrição:** Documentação estruturada e consultável das 3 tabelas gold
- **Tabelas:**
  1. `public_gold_sales.vendas_temporais` - Vendas temporais e receita
  2. `public_gold_cs.clientes_segmentacao` - Segmentação e comportamento de clientes
  3. `public_gold_pricing.precos_competitividade` - Posicionamento de preços vs concorrência
- **Informações por tabela:**
  - Nome da coluna, tipo de dado, descrição, regras de negócio
  - Exemplo de valores
  - Cardinalidade estimada
- **Arquivo:** `.llm/database.md` (consumido pelo agente)

---

### 1.2 Funcionalidade: Chat Livre (Qualquer Pergunta)

#### Feature 1.2.1: Agente de IA com Tool Use
- **Descrição:** Integração com Claude API com capacidade de executar SQL dinamicamente
- **Modelo:** claude-sonnet-4-20250514 (otimizado para tool use)
- **Tool use workflow:**
  1. Usuário envia pergunta textual no Telegram
  2. Agente recebe pergunta + schema das 3 tabelas
  3. Claude decide quais queries SQL executar via tool `executar_sql`
  4. Agent executa cada query no banco
  5. Claude recebe resultados e gera resposta em português
  6. Bot envia resposta no Telegram
- **Limite de iterações:** 10 por pergunta (evita loops infinitos)
- **Tecnologia:** anthropic SDK com streaming

#### Feature 1.2.2: Ferramenta `executar_sql` (Tool Definition)
- **Nome:** `executar_sql`
- **Descrição:** Executa query SQL SELECT no banco PostgreSQL do e-commerce
- **Input Schema:**
  ```json
  {
    "type": "object",
    "properties": {
      "sql": {
        "type": "string",
        "description": "Query SQL SELECT ou WITH para executar"
      }
    },
    "required": ["sql"]
  }
  ```
- **Validações:**
  - Apenas SELECT e WITH permitidos
  - Rejeição de queries de escrita com mensagem de erro
- **Timeout:** 30 segundos por query
- **Limite de resultados:** 10.000 linhas

#### Feature 1.2.3: System Prompt para Chat
- **Contexto passado ao Claude:**
  - Você é um analista de dados de e-commerce brasileiro
  - Schema completo das 3 tabelas gold
  - Instruções: use `executar_sql` para consultar dados
  - Formatar valores monetários em R$
  - Responder em português, ser conciso
- **Ajustes por contexto:** Suportar perguntas de diferentes diretores (Comercial, CS, Pricing)

#### Feature 1.2.4: Split Automático de Mensagens Longas
- **Descrição:** Dividir respostas > 4096 caracteres em múltiplas mensagens
- **Comportamento:**
  - Quebra inteligente em pontos de parágrafo ou seções
  - Numeração de partes (1/3, 2/3, 3/3)
  - Fallback para texto puro se Markdown falhar
- **Limite Telegram:** 4096 caracteres por mensagem

#### Feature 1.2.5: Indicador "Digitando..." no Telegram
- **Descrição:** Mostrar typing indicator enquanto o agente processa
- **Tecnologia:** `telegram.constants.ChatAction.TYPING`
- **Duração:** Do início da requisição até o envio da primeira mensagem

---

### 1.3 Funcionalidade: Relatório Executivo

#### Feature 1.3.1: Gerador de Relatório
- **Descrição:** Função `gerar_relatorio()` que executa 4 queries pré-definidas e compila dado em relatório
- **Entrada:** Nenhuma (usa dados atuais do banco)
- **Saída:** 
  - String formatada do relatório (retorno)
  - Arquivo `relatorio_YYYY-MM-DD.md` (salvo em disco)
- **Processo interno:**
  1. Executar 4 queries pré-definidas no banco
  2. Formatar dados em DataFrames (pandas)
  3. Converter cada DataFrame para Markdown table via `.to_markdown()`
  4. Enviar prompt com dados + instruções para Claude
  5. Claude gera relatório em Markdown formatado
  6. Salvar arquivo com timestamp
  7. Retornar conteúdo do relatório

#### Feature 1.3.2: Query 1 - Resumo de Vendas (Últimos 7 Dias)
- **Origem:** `public_gold_sales.vendas_temporais`
- **SQL:**
  ```sql
  SELECT data_venda, dia_semana_nome,
      SUM(receita_total) AS receita,
      SUM(total_vendas) AS vendas,
      SUM(total_clientes_unicos) AS clientes,
      AVG(ticket_medio) AS ticket_medio
  FROM public_gold_sales.vendas_temporais
  WHERE data_venda >= CURRENT_DATE - INTERVAL '7 days'
  GROUP BY data_venda, dia_semana_nome
  ORDER BY data_venda DESC
  LIMIT 7
  ```
- **Propósito:** Base para insights do Diretor Comercial
- **Validações:** Verificar se há dados nos últimos 7 dias

#### Feature 1.3.3: Query 2 - Segmentação de Clientes
- **Origem:** `public_gold_cs.clientes_segmentacao`
- **SQL:**
  ```sql
  SELECT segmento_cliente,
      COUNT(*) AS total_clientes,
      SUM(receita_total) AS receita_total,
      AVG(ticket_medio) AS ticket_medio_avg,
      AVG(total_compras) AS compras_avg
  FROM public_gold_cs.clientes_segmentacao
  GROUP BY segmento_cliente
  ORDER BY receita_total DESC
  ```
- **Propósito:** Base para insights da Diretora de CS
- **Segmentos esperados:** VIP, TOP_TIER, REGULAR

#### Feature 1.3.4: Query 3 - Alertas de Pricing
- **Origem:** `public_gold_pricing.precos_competitividade`
- **SQL:**
  ```sql
  SELECT classificacao_preco,
      COUNT(*) AS total_produtos,
      AVG(diferenca_percentual_vs_media) AS dif_media_pct,
      SUM(receita_total) AS receita_impactada
  FROM public_gold_pricing.precos_competitividade
  GROUP BY classificacao_preco
  ORDER BY total_produtos DESC
  ```
- **Propósito:** Overview de posicionamento de preços
- **Classificações esperadas:** MAIS_CARO_QUE_TODOS, ACIMA_MEDIA, NA_MEDIA, ABAIXO_MEDIA, MAIS_BARATO_QUE_TODOS

#### Feature 1.3.5: Query 4 - Produtos Críticos (Top 10 Mais Caros)
- **Origem:** `public_gold_pricing.precos_competitividade`
- **SQL:**
  ```sql
  SELECT nome_produto, categoria, nosso_preco,
      preco_medio_concorrentes,
      diferenca_percentual_vs_media,
      receita_total
  FROM public_gold_pricing.precos_competitividade
  WHERE classificacao_preco = 'MAIS_CARO_QUE_TODOS'
  ORDER BY diferenca_percentual_vs_media DESC
  LIMIT 10
  ```
- **Propósito:** Alertas imediatos para repricing
- **Ordenação:** Por diferença percentual (maiores desvios primeiro)

#### Feature 1.3.6: System Prompt para Geração de Relatório
- **Contexto passado ao Claude:**
  - Você é um analista de dados senior de e-commerce
  - 3 diretores com necessidades diferentes:
    - Diretor Comercial: receita, vendas, ticket, tendências
    - Diretora de CS: VIPs, segmentação, riscos
    - Diretor de Pricing: posicionamento vs concorrência
  - Regras: direto, acionável, sugerir ações, R$ formatado, máx 1 página por diretor
- **Saída esperada:** Markdown com seções por diretor

#### Feature 1.3.7: Template de Relatório Formatado
- **Estrutura:**
  - Cabeçalho com: Título, Data, Resumo Executivo (3 linhas)
  - Seção 1: Comercial (Diretor Comercial)
  - Seção 2: Customer Success (Diretora de CS)
  - Seção 3: Pricing (Diretor de Pricing)
- **Formato:** Markdown com tabelas, bullets e highlights
- **Exemplo de saída:** Incluído no PRD

#### Feature 1.3.8: Salvamento de Relatório em Disco
- **Padrão de nome:** `relatorio_YYYY-MM-DD.md`
- **Diretório:** Raiz do projeto (pode ser configurável)
- **Permissões:** Leitura/escrita normal
- **Retenção:** Sem limpeza automática (manutenção manual ou via cron)

---

### 1.4 Funcionalidade: Envio Automático via Telegram

#### Feature 1.4.1: Função `enviar_telegram()`
- **Descrição:** Envia mensagem diretamente para o Telegram via API HTTP (sem precisar do bot rodando)
- **Assinatura:**
  ```python
  def enviar_telegram(texto: str, chat_id: str = None) -> bool
  ```
- **Comportamento:**
  - Se `chat_id` não fornecido: usa variável de ambiente `CHAT_ID`
  - Se `CHAT_ID` não configurado: exibe mensagem de erro no terminal
- **Retorno:** True se sucesso, False se falha
- **Erros capturados:** Conexão, timeout, rate limit
- **Tecnologia:** urllib ou requests (não precisa do bot rodando)

#### Feature 1.4.2: Split Automático de Mensagens no Envio
- **Descrição:** Dividir automaticamente mensagens > 4096 chars
- **Algoritmo:**
  - Quebra em ponto de parágrafo quando possível
  - Fallback para quebra em espaço em branco
  - Numeração de partes: "1/3", "2/3", "3/3"
- **Parse mode:** Markdown no primeiro envio; fallback para texto puro se falhar

#### Feature 1.4.3: Fallback Markdown → Texto Puro
- **Descrição:** Se envio com `parse_mode=Markdown` falhar, reenvia como texto puro
- **Tratamento:** Log de warning no terminal (qual mensagem teve fallback)

---

### 1.5 Funcionalidade: Auto-Registro do CHAT_ID

#### Feature 1.5.1: Função `salvar_chat_id()`
- **Descrição:** Salva `CHAT_ID` do usuário no `.env` automaticamente
- **Assinatura:**
  ```python
  def salvar_chat_id(chat_id: int) -> None
  ```
- **Lógica:**
  1. Ler `.env` atual
  2. Se `CHAT_ID` não existe: adicionar nova linha `CHAT_ID=xxx`
  3. Se `CHAT_ID` existe com valor diferente: atualizar (sobrescrever)
  4. Se `CHAT_ID` existe com mesmo valor: nada fazer
  5. Atualizar `os.environ["CHAT_ID"]` em memória
  6. Log: `CHAT_ID=xxx salvo no .env`
- **Arquivos afetados:** `.env` (criado se não existir)

#### Feature 1.5.2: Registo Automático na Primeira Interação
- **Disparadores:**
  - Qualquer mensagem de texto
  - Comando `/start`
  - Comando `/relatorio`
- **Timing:** Antes de processar a mensagem
- **Feedback ao usuário:** Log no terminal (não interrompe fluxo)

#### Feature 1.5.3: Tratamento de Duplicatas no .env
- **Descrição:** Evitar duplicações ou corrupção do `.env`
- **Comportamento:** Atualizar valor existente em vez de adicionar nova linha
- **Validação:** Verificar formato `CHAT_ID=xxx` antes de salvar

---

### 1.6 Bot Telegram Interativo

#### Feature 1.6.1: Comando `/start`
- **Comportamento:**
  - Auto-registra `CHAT_ID`
  - Envia mensagem de boas-vindas
  - Explica funcionalidades disponíveis
  - Exemplo de comandos
- **Texto esperado:**
  ```
  Olá! 👋 Sou o assistente de IA de dados do e-commerce.
  
  Posso ajudar você de 3 formas:
  
  1. **Chat Livre** - Faça qualquer pergunta sobre vendas, clientes ou preços
     Exemplo: "Qual foi meu melhor dia de vendas?"
  
  2. **Relatório Executivo** - Geno relatório diário com insights para sua área
     Use: /relatorio
  
  3. **Análise em tempo real** - Consulte dados diretamente
     Exemplo: "Quantos clientes VIP temos?"
  
  Vamos começar! 😊
  ```
- **Tecnologia:** Handler assíncrono no python-telegram-bot

#### Feature 1.6.2: Comando `/relatorio`
- **Comportamento:**
  1. Mostra "digitando..."
  2. Chama `gerar_relatorio()`
  3. Envia relatório em partes (se necessário split)
  4. Salva versão `.md` em disco
  5. Confirma envio no terminal
- **Tecnologia:** Handler assíncrono

#### Feature 1.6.3: Handler para Mensagens de Texto Livre
- **Comportamento:**
  1. Auto-registra `CHAT_ID`
  2. Mostra "digitando..."
  3. Chama `agente.chat(pergunta)`
  4. Executa tool use conforme necessário
  5. Envia resposta com split automático
- **Tratamento de erros:** Mensagem amigável se algo der errado

#### Feature 1.6.4: Modo Polling (vs Webhook)
- **Descrição:** Bot escuta continuamente por novas mensagens
- **Tipo:** Polling (mais simples para desenvolvimento local)
- **Tratamento:** Signal handling para Ctrl+C gracioso

---

### 1.7 Modo Standalone (Execução via Terminal)

#### Feature 1.7.1: Execução de `python agente.py`
- **Comportamento:**
  1. Gera relatório via `gerar_relatorio()`
  2. Imprime relatório no terminal
  3. Salva como `relatorio_YYYY-MM-DD.md`
  4. Se `CHAT_ID` configurado: envia para Telegram via `enviar_telegram()`
  5. Se `CHAT_ID` não configurado: exibe mensagem dizendo para rodar o bot primeiro
- **Logging:** Timestamps em cada etapa
- **Exit codes:** 0 (sucesso), 1 (erro)

---

### 1.8 Agendamento Automático

#### Feature 1.8.1: Instrções para Cron
- **Objetivo:** Gerar relatório automático em horários pré-definidos
- **Exemplos fornecidos:**
  ```bash
  # Relatório diário às 8h
  0 8 * * * cd /caminho && python agente.py >> /tmp/agente.log 2>&1
  
  # A cada 6 horas
  0 */6 * * * cd /caminho && python agente.py >> /tmp/agente.log 2>&1
  
  # A cada 2 horas em dias úteis
  0 */2 * * 1-5 cd /caminho && python agente.py >> /tmp/agente.log 2>&1
  ```
- **Logging:** Redirecionado para arquivo de log

#### Feature 1.8.2: Arquivo de Log
- **Padrão de nome:** `/tmp/agente.log`
- **Conteúdo:** Timestamp + mensagens de execução
- **Rotação:** Manual ou via logrotate (fora do escopo deste PRD)

---

### 1.9 Tratamento de Erros Robusto

#### Feature 1.9.1: Erros de Conectividade
- **Banco fora do ar:** Retorna erro sem chamar API do Claude
- **API Claude indisponível:** Salva dados brutos em Markdown como fallback
- **Telegram indisponível:** Log de erro + retry com backoff exponencial
- **SQL inválido:** Apenas SELECT/WITH; queries de escrita rejeitadas com mensagem

#### Feature 1.9.2: Erros de Limites
- **Limite de tool use (10 iterações):** Parar e enviar "Desculpe, não consegui responder"
- **Timeout de query (30s):** Cancelar query e reportar ao usuário
- **Mensagem > 4096 chars após split:** Truncar com mensagem "Ver relatório completo em arquivo"

---

### 1.10 Logging e Observabilidade

#### Feature 1.10.1: Logs Estruturados com Timestamp
- **Formato:** `[YYYY-MM-DD HH:MM:SS] Mensagem`
- **Eventos registrados:**
  - Inicialização do bot
  - Auto-registro de CHAT_ID
  - Início e fim de geração de relatório
  - Cada query consultada
  - Envio para Telegram
  - Erros e exceções
- **Saída:** Terminal (stdout)

#### Feature 1.10.2: Arquivo de Log (Opcional)
- **Quando usado:** Com cron / agendador
- **Padrão:** `/tmp/agente.log`
- **Rotação:** Recomendação ao usuário

---

### 1.11 Estrutura de Arquivos

#### Feature 1.11.1: Arquivos Python
- `db.py`: Conexão e execução de queries
- `agente.py`: Lógica de IA + envio direto Telegram
- `bot.py`: Bot Telegram interativo
- `requirements.txt`: Dependências Python

#### Feature 1.11.2: Arquivos de Configuração
- `.env`: Variáveis de ambiente (não commitado)
- `.env.example`: Template com instruções
- `.gitignore`: Ignora .env, __pycache__, *.pyc, relatorio_*.md
- `.llm/database.md`: Schema das tabelas gold

#### Feature 1.11.3: Saídas
- `relatorio_YYYY-MM-DD.md`: Relatório gerado

---

### 1.12 Dependências Python

- `python-dotenv`: Leitura de `.env`
- `sqlalchemy`: ORM para conexão PostgreSQL
- `psycopg2-binary`: Driver PostgreSQL
- `anthropic`: SDK da API do Claude (tool use)
- `pandas`: Manipulação de dados e `.to_markdown()`
- `tabulate`: Formatação adicional de tabelas
- `python-telegram-bot>=20.0`: Bot assíncrono

---

### 1.13 Custo Estimado (API Claude)

- Relatório diário: ~$0.01/execução
- Chat simples: ~$0.005/pergunta
- Chat complexo (múltiplos tool use): ~$0.02/pergunta
- **Modelo recomendado:** claude-sonnet-4-20250514

---

---

## 2. PRD - DASHBOARD STREAMLIT

### 2.1 Infraestrutura Base

#### Feature 2.1.1: Gerenciamento de Variáveis de Ambiente
- **Variáveis obrigatórias:**
  - `SUPABASE_HOST`: Host do Supabase (ex: seu-host.supabase.co)
  - `SUPABASE_PORT`: Porta (padrão: 5432)
  - `SUPABASE_DB`: Nome do banco (padrão: postgres)
  - `SUPABASE_USER`: Usuário PostgreSQL
  - `SUPABASE_PASSWORD`: Senha PostgreSQL
- **Arquivo:** `.env` (não commitado)
- **Template:** `.env.example` com instruções
- **Tecnologia:** python-dotenv

#### Feature 2.1.2: Conexão com Banco de Dados PostgreSQL
- **Função reutilizável:** `execute_query(sql: str) -> pd.DataFrame`
- **Retorno:** DataFrame pandas pronto para visualização
- **Cache:** **Não usar cache agressivo** (dados mudam após cada `dbt run`)
- **Tratamento de erros:** Mostrar mensagem amigável se banco estiver fora
- **Timeout:** 30 segundos por query
- **Tecnologia:** psycopg2-binary

#### Feature 2.1.3: Formatação de Números em Padrão Brasileiro
- **Moeda:** R$ com ponto de milhar e vírgula decimal (ex: R$ 1.234,56)
- **Percentual:** Vírgula decimal (ex: 12,34%)
- **Inteiros:** Ponto de milhar (ex: 1.234)
- **Função auxiliar:** `formatar_brazilian(valor, tipo='moeda')`
- **Aplicação:** Em todos os KPIs, tabelas e labels de gráficos

#### Feature 2.1.4: Configuração da Página
- **Layout:** `st.set_page_config(layout="wide")` para usar tela inteira
- **Título:** "E-commerce Analytics"
- **Ícone:** Emoji ou ícone do Streamlit
- **Descrição:** "Análise de dados para 3 diretores"

---

### 2.2 Layout Global e Navegação

#### Feature 2.2.1: Sidebar com Navegação
- **Componente:** `st.sidebar.selectbox()` ou `st.sidebar.radio()`
- **Opções:**
  1. Vendas
  2. Clientes
  3. Pricing
- **Padrão:** Vendas (primeira página ao carregar)
- **Logo/Título:** "E-commerce Analytics" no topo da sidebar

#### Feature 2.2.2: Estrutura de Páginas
- **Padrão para todas:** KPIs no topo → Gráficos → Tabela detalhada
- **Responsividade:** Usar `st.columns()` para layout adaptativo
- **Espaçamento:** `st.divider()` entre seções

---

### 2.3 Página 1: Vendas (Diretor Comercial)

#### Feature 2.3.1: KPIs de Vendas
- **Layout:** 4 KPIs em uma linha usando `st.columns(4)`
- **KPIs:**
  1. **Receita Total**: SUM(receita_total) → Formato: R$ XXX.XXX,XX
  2. **Total de Vendas**: SUM(total_vendas) → Formato: X.XXX
  3. **Ticket Médio**: Receita Total / Total de Vendas → Formato: R$ XXX,XX
  4. **Clientes Únicos**: SUM(total_clientes_unicos) ponderado → Formato: XXX
- **Componente:** `st.metric()` para cada KPI
- **Fonte:** `public_gold_sales.vendas_temporais`

#### Feature 2.3.2: Query para KPIs de Vendas
- **SQL:**
  ```sql
  SELECT 
      SUM(receita_total) AS receita_total,
      SUM(total_vendas) AS total_vendas,
      SUM(total_clientes_unicos) AS total_clientes_unicos
  FROM public_gold_sales.vendas_temporais
  ```

#### Feature 2.3.3: Gráfico 1 - Receita Diária (Linha)
- **Tipo:** Plotly line chart (`px.line`)
- **Dados:** 
  - Query: SUM(receita_total) GROUP BY data_venda
  - Eixo X: data_venda (formatado DD/MM)
  - Eixo Y: receita_total (formatado R$)
- **Título:** "Receita Diária"
- **Cores:** Azul padrão Plotly

#### Feature 2.3.4: Gráfico 2 - Receita por Dia da Semana (Barras)
- **Tipo:** Plotly bar chart (`px.bar`)
- **Dados:**
  - Query: SUM(receita_total) GROUP BY dia_semana_nome
  - Eixo X: dia_semana_nome (ordem: Segunda, Terça, ..., Domingo)
  - Eixo Y: receita_total
- **Título:** "Receita por Dia da Semana"
- **Ordenação:** Segunda → Domingo (usar parameter order em pandas antes do gráfico)

#### Feature 2.3.5: Gráfico 3 - Volume de Vendas por Hora (Barras)
- **Tipo:** Plotly bar chart (`px.bar`)
- **Dados:**
  - Query: SUM(total_vendas) GROUP BY hora_venda (0-23)
  - Eixo X: hora_venda (00:00, 01:00, ... 23:00)
  - Eixo Y: total_vendas
- **Título:** "Volume de Vendas por Hora"
- **Insight:** Padrão horário de compras

#### Feature 2.3.6: Filtro de Mês (Opcional)
- **Componente:** `st.selectbox()` ou `st.date_input()`
- **Opções:** Todos os meses com dados + "Todos os meses"
- **Efeito:** Filtrar todos os gráficos pelo mês selecionado
- **Local:** No topo da página, acima dos KPIs

---

### 2.4 Página 2: Clientes (Diretora de Customer Success)

#### Feature 2.4.1: KPIs de Clientes
- **Layout:** 4 KPIs em uma linha usando `st.columns(4)`
- **KPIs:**
  1. **Total Clientes**: COUNT(*) → Formato: XXX
  2. **Clientes VIP**: COUNT(*) WHERE segmento = 'VIP' → Formato: XX
  3. **Receita VIP**: SUM(receita_total) WHERE segmento = 'VIP' → Formato: R$ XXX.XXX
  4. **Ticket Médio Geral**: AVG(ticket_medio) → Formato: R$ XXX,XX
- **Componente:** `st.metric()`
- **Fonte:** `public_gold_cs.clientes_segmentacao`

#### Feature 2.4.2: Gráfico 1 - Distribuição por Segmento (Pizza/Donut)
- **Tipo:** Plotly pie chart (`px.pie`)
- **Dados:**
  - Query: COUNT(*) GROUP BY segmento_cliente
  - Labels: VIP, TOP_TIER, REGULAR
  - Values: contagem
- **Título:** "Distribuição de Clientes por Segmento"
- **Insight:** Proporção de clientes por segmento

#### Feature 2.4.3: Gráfico 2 - Receita por Segmento (Barras)
- **Tipo:** Plotly bar chart (`px.bar`)
- **Dados:**
  - Query: SUM(receita_total) GROUP BY segmento_cliente
  - Eixo X: segmento_cliente
  - Eixo Y: receita_total (formatado R$)
- **Título:** "Receita por Segmento"
- **Insight:** Concentração de receita

#### Feature 2.4.4: Gráfico 3 - Top 10 Clientes por Receita (Barras Horizontais)
- **Tipo:** Plotly bar chart horizontal (`px.bar` com `orientation='h'`)
- **Dados:**
  - Query: TOP 10 por receita_total
  - Eixo Y: nome_cliente (top 10)
  - Eixo X: receita_total
- **Título:** "Top 10 Clientes"
- **Insight:** Clientes mais valiosos

#### Feature 2.4.5: Gráfico 4 - Clientes por Estado (Barras)
- **Tipo:** Plotly bar chart (`px.bar`)
- **Dados:**
  - Query: COUNT(*) GROUP BY estado
  - Eixo X: estado (em order DESC de quantidade)
  - Eixo Y: quantidade
- **Título:** "Clientes por Estado"
- **Ordenação:** TOP estados primeiro (DESC by count)

#### Feature 2.4.6: Tabela Detalhada com Filtro
- **Componente:** `st.dataframe()` interativo
- **Colunas:** Todas da tabela `clientes_segmentacao`
- **Filtro:** `st.selectbox()` por `segmento_cliente`
- **Comportamento:**
  1. Usuário seleciona segmento
  2. Tabela mostra apenas clientes daquele segmento
  3. Dados carregam sob demanda (sem cache agressivo)

#### Feature 2.4.7: Filtro de Segmento
- **Componente:** `st.selectbox()`
- **Opções:** VIP, TOP_TIER, REGULAR, Todos
- **Local:** Acima da tabela detalhada
- **Efeito:** Filtra tabela e pode opcionalmente filtrar gráficos

---

### 2.5 Página 3: Pricing (Diretor de Pricing)

#### Feature 2.5.1: KPIs de Pricing
- **Layout:** 4 KPIs em uma linha usando `st.columns(4)`
- **KPIs:**
  1. **Total Produtos Monitorados**: COUNT(*) → Formato: XXX
  2. **Mais Caros que Todos**: COUNT(*) WHERE classificacao = 'MAIS_CARO_QUE_TODOS' → XX
  3. **Mais Baratos que Todos**: COUNT(*) WHERE classificacao = 'MAIS_BARATO_QUE_TODOS' → XX
  4. **Diferença Média vs Mercado**: AVG(diferenca_percentual_vs_media) → +X.X%
- **Componente:** `st.metric()`
- **Fonte:** `public_gold_pricing.precos_competitividade`

#### Feature 2.5.2: Gráfico 1 - Distribuição por Classificação (Pizza)
- **Tipo:** Plotly pie chart (`px.pie`)
- **Dados:**
  - Query: COUNT(*) GROUP BY classificacao_preco
  - Labels: MAIS_CARO_QUE_TODOS, ACIMA_MEDIA, NA_MEDIA, ABAIXO_MEDIA, MAIS_BARATO_QUE_TODOS
  - Values: contagem
- **Título:** "Posicionamento de Preço vs Concorrência"
- **Insight:** Distribuição geral da estratégia de pricing

#### Feature 2.5.3: Gráfico 2 - Competitividade por Categoria (Barras com Cores)
- **Tipo:** Plotly bar chart (`px.bar`)
- **Dados:**
  - Query: AVG(diferenca_percentual_vs_media) GROUP BY categoria
  - Eixo X: categoria
  - Eixo Y: diferenca_percentual_vs_media (normalizado em %)
- **Cores:**
  - Verde: valores negativos (mais barato)
  - Vermelho: valores positivos (mais caro)
  - Usar color_discrete_sequence ou color_continuous_scale
- **Título:** "Competitividade por Categoria"
- **Insight:** Qual categoria é mais cara/barata

#### Feature 2.5.4: Gráfico 3 - Scatter: Competitividade vs Volume
- **Tipo:** Plotly scatter plot (`px.scatter`)
- **Dados:**
  - Eixo X: diferenca_percentual_vs_media
  - Eixo Y: quantidade_total (volume)
  - Tamanho dos pontos: receita_total (bubble size)
  - Cor: classificacao_preco (legenda)
- **Título:** "Competitividade x Volume de Vendas"
- **Insight:** Relação entre preço e volume sold

#### Feature 2.5.5: Tabela de Alertas (Produtos Mais Caros)
- **Componente:** `st.dataframe()` apenas leitura
- **Filtro:** Apenas produtos com classificacao = 'MAIS_CARO_QUE_TODOS'
- **Colunas:**
  - produto_id
  - nome_produto
  - categoria
  - nosso_preco (formatado R$)
  - preco_maximo_concorrentes (formatado R$)
  - diferenca_percentual_vs_media (formatado %)
  - receita_total (formatado R$)
- **Ordenação:** Por diferenca_percentual_vs_media DESC (maiores desvios primeiro)
- **Título:** "⚠️ Produtos em Alerta (mais caros que todos os concorrentes)"

#### Feature 2.5.6: Filtro de Categoria
- **Componente:** `st.multiselect()`
- **Opções:** Todas as categorias únicas no banco + "Todas"
- **Local:** Acima dos gráficos
- **Efeito:** Filtra todos os gráficos e tabelas pela(s) categoria(s) selecionada(s)
- **Padrão:** "Todas" checada

---

### 2.6 Requisitos Não Funcionais

#### Feature 2.6.1: Tratamento de Erros de Conexão
- **Mensagem amigável** se banco estiver fora
- **Exemplo:** "❌ Não conseguimos conectar ao banco. Tente novamente em alguns segundos."
- **Try/Except:** Envolver todas as queries
- **Retry:** Não tentar reconectar automaticamente (deixar para o usuário)

#### Feature 2.6.2: Sem Cache Agressivo
- **Sem use_cache=True** global
- **Sem Query caching** (dados mudam após cada `dbt run`)
- **Comportamento:** Cada acesso à página recarrega dados do banco

#### Feature 2.6.3: Layout Responsivo
- **Wide layout:** `st.set_page_config(layout="wide")`
- **Columns:** Usar `st.columns()` para distribuir espaço
- **Mobile:** Aceitar que mobile pode ser menos ideal (não é foco)

#### Feature 2.6.4: Cores Consistentes
- **Plotly:** Usar paleta consistente entre páginas
- **Recomendação:** Plotly default ou paleta "Viridis" / "Blues"

---

### 2.7 Estrutura de Arquivos

#### Feature 2.7.1: Organização do Projeto
```
case-01-dashboard/
├── app.py              # App Streamlit completo
├── requirements.txt    # Dependências Python
├── .env.example        # Template de variáveis
└── .gitignore          # Ignora .env, __pycache__, etc
```

#### Feature 2.7.2: Arquivo `app.py`
- **Seções principais:**
  1. Imports e configuração
  2. Função de conexão com banco
  3. Funções de formatação
  4. Funções auxiliares de queries
  5. Função main() com navigation
  6. Funções for cada página (vendas, clientes, pricing)
  7. Chamada: `if __name__ == "__main__": main()`

---

### 2.8 Dependências Python

- `streamlit`: Framework web
- `psycopg2-binary`: Driver PostgreSQL
- `pandas`: Manipulação de dados
- `plotly`: Gráficos interativos
- `python-dotenv`: Leitura de `.env`

---

### 2.9 Instruções de Execução

#### Feature 2.9.1: Setup Inicial
```bash
cd case-01-dashboard
cp .env.example .env
# Editar .env com credenciais reais do Supabase
pip install -r requirements.txt
streamlit run app.py
```

#### Feature 2.9.2: Acesso
- **URL padrão:** http://localhost:8501
- **Reload:** Automático ao detectar mudanças em `app.py`

---

---

## 3. RESUMO DE DESENVOLVIMENTO

### 3.1 Etapas de Implementação Recomendadas

#### Phase 1: Infraestrutura (Semana 1)
1. Criar estrutura de arquivos para ambos PRDs
2. Implementar `.env` e gerenciamento de variáveis
3. Criar módulo de conexão com PostgreSQL (reutilizável)
4. Criar `.llm/database.md` com schema completo

#### Phase 2: Agente Telegram (Semana 2-3)
1. Implementar `db.py` com executor de queries
2. Implementar `agente.py` com tool use
3. Implementar `bot.py` com comandos básicos
4. Testar chat livre, relatório, envio automático

#### Phase 3: Dashboard Streamlit (Semana 3-4)
1. Implementar `app.py` básico com scaffold
2. Implementar Página de Vendas
3. Implementar Página de Clientes
4. Implementar Página de Pricing
5. Testes e ajustes de layout

#### Phase 4: Integração e Deploy (Semana 5)
1. Agendamento via cron
2. Tratamento de erros robusto
3. Logging completo
4. Deploy (heroku, railway, etc)

---

### 3.2 Total de Features por PRD

**PRD 1 - Agente Telegram:**
- 28 features principais

**PRD 2 - Dashboard Streamlit:**
- 23 features principais

**Total:** 51 features de implementação

---

### 3.3 Ordem de Priorização

1. **Alta Prioridade:**
   - Conexão com banco (ambos)
   - Chat livre (PRD 1)
   - Página Vendas (PRD 2)

2. **Média Prioridade:**
   - Relatório executivo (PRD 1)
   - Página Clientes (PRD 2)
   - Página Pricing (PRD 2)

3. **Baixa Prioridade:**
   - Agendamento (PRD 1)
   - Auto-registro CHAT_ID (PRD 1)
   - Filtros avançados (PRD 2)

---

**Documento Finalizado:** 12/03/2026
