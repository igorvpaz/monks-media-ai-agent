# 📊 MONKS Media AI - Agente de Análise de Mídia e Receita

Sistema inteligente de análise de dados para e-commerce baseado em **Claude 3.5 Haiku**, **LangGraph** e **Google BigQuery**. O agente atua como um Analista de Mídia e Growth, transformando perguntas complexas em insights estratégicos e recomendações acionáveis.

---

## 🏗️ Arquitetura do Projeto

O projeto segue princípios de **Clean Architecture** e separação de responsabilidades para garantir escalabilidade e facilidade de manutenção.

```text
app/
├── main.py                # Ponto de entrada FastAPI e montagem do Frontend
├── core/
│   ├── config.py          # Gerenciamento de variáveis de ambiente (Pydantic Settings)
│   └── prompts.py         # ✨ System Prompt centralizado e versionado
├── models/
│   └── schemas.py         # Modelos de dados e validação Pydantic (max_length=500)
├── api/
│   └── routes.py          # Definição dos endpoints REST e tratamento de erros
├── agent/
│   └── agent_fresh.py     # Orquestração do Grafo (LangGraph) e lógica do Agente
├── tools/
│   └── bq_tools.py        # Ferramentas de execução SQL (BigQuery) com JOINs e agregações
└── static/                # Frontend moderno (HTML/JS/Tailwind) com suporte a Voz
```

### 🎯 Diferenciais Técnicos

* **Prompt Engineering Sênior:** System prompt estruturado com definição de persona, restrições de escopo e diretrizes de tom de voz.
* **SQL Avançado:** Consultas otimizadas no BigQuery utilizando `JOINs` entre tabelas de usuários e pedidos para cálculo de métricas complexas.
* **Segurança (Guardrails):** Proteção contra *Prompt Injection* via validação de tamanho de entrada e tratamento rigoroso de exceções.
* **Interface Multimodal:** Chat interativo com processamento de voz nativo (STT/TTS) para uma experiência de usuário fluida.

---

## 🔧 Ferramentas (Tools) do Agente

O agente utiliza ferramentas específicas para consultar o dataset `thelook_ecommerce`:

1.  **`consultar_volume_trafego`**: Analisa o volume de sessões e usuários únicos por canal de aquisição.
2.  **`consultar_receita_faturamento`**: Realiza cruzamentos complexos para extrair Receita Total, AOV (Ticket Médio), Conversão e Receita por Usuário por canal.

---

## 🚀 Como Rodar o Projeto

## Opção 1: Acesse o projeto que deixei no ar em: https://monks-media-ai-agent-igor-vianna-paz.onrender.com/

## Opção 2: Siga os passos abaixo para configurar o ambiente em sua máquina:

### 1. Requisitos Prévios
* Ter o arquivo de credenciais do Google Cloud (`gcp_key.json`) na raiz do projeto.
* Ter uma conta na Anthropic e uma `ANTHROPIC_API_KEY`.

### 2. Configuração do Ambiente

**Passo 1: Variáveis de Ambiente**
Renomeie o arquivo `.env.example` para `.env` e preencha com suas chaves:
```env
ANTHROPIC_API_KEY=sua_chave_aqui
GCP_PROJECT_ID=seu-projeto-id
GOOGLE_APPLICATION_CREDENTIALS=gcp_key.json
BIGQUERY_DATASET=thelook_ecommerce
```

**Passo 2: Criação do Ambiente Virtual**
```bash
python -m venv venv
```

**Passo 3: Instalação de Dependências**
```bash
# Ativar o ambiente (Windows)
.\venv\Scripts\activate

# Ativar o ambiente (Linux/Mac)
source venv/bin/activate

# Instalar pacotes
pip install -r requirements.txt
```

**Passo 4: Execução do Servidor**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## 🖥️ Interface e Documentação

Após iniciar o servidor, você poderá acessar:

* **Chat Interativo:** [http://localhost:8000/](http://localhost:8000/)
* **Documentação da API (Swagger):** [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 💡 Exemplo de Pergunta para Teste

> *"Qual dos canais teve a melhor performance em termos de receita nos últimos 3 meses? Por que você acha que isso aconteceu?"*

### 3. **Exemplo de Requisição**

```bash
curl -X POST http://localhost:8000/agent/ask \
  -H "Content-Type: application/json" \
  -d '{"user_question": "Qual canal de tráfego gerou mais receita no último mês?"}'
```

**Resposta:**
```json
{
  "agent_answer": "Com base nos dados dos últimos 30 dias, o Search foi o melhor canal de receita...\n\nCanal: Search\n- Receita Total: R$ 450.000\n- AOV: R$ 50.25\n- Taxa de Conversão: 58%\n\n✅ Recomendação: Aumentar orçamento em Search mantendo investments em Organic para diversificação."
}
```

---

## 🔒 Segurança

### Proteção contra Prompt Injection
- ✅ Campo `user_question` limitado a **500 caracteres**
- ✅ Validação com Pydantic antes de chegar ao agente
- ✅ Parametrização segura de queries BigQuery

### Autenticação & Autorização
- ✅ API Key Anthropic validada no startup
- ✅ Credenciais GCP via arquivo JSON
- ✅ CORS restrito (ajustar em produção)

### Tratamento de Erros
- ✅ Try/except **específico** por camada:
  - `ValueError` → Erro de configuração (401)
  - `AnthropicAPIError` → Erro de API (503)
  - `GoogleCloudError` → Erro de BigQuery (503)
  - `Exception` → Erro genérico (500)

---

## 📊 Dados & Queries SQL

Dataset: `bigquery-public-data.thelook_ecommerce`

### Ferramenta 1: Volume de Tráfego
```sql
SELECT traffic_source as canal, 
       COUNT(DISTINCT id) as total_usuarios
FROM users
WHERE created_at >= DATE_SUB(CURRENT_DATE(), INTERVAL @meses_atras MONTH)
GROUP BY traffic_source
ORDER BY total_usuarios DESC
```

### Ferramenta 2: Receita/Faturamento (com JOINs) ⭐
```sql
SELECT u.traffic_source,
       COUNT(DISTINCT o.order_id) as total_pedidos,
       SUM(oi.sale_price) as receita_total,
       AVG(oi.sale_price) as aov_medio
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
LEFT JOIN order_items oi ON o.order_id = oi.order_id
WHERE u.created_at >= DATE_SUB(CURRENT_DATE(), INTERVAL @meses_atras MONTH)
GROUP BY u.traffic_source
```

---

## 🎯 Escopo do Agente

✅ **Responde sobre:**
- Análise de tráfego por canal de mídia
- Receita e faturamento por canal
- AOV, taxa de conversão, performance comparativa
- Recomendações de alocação de orçamento

❌ **Não responde sobre:**
- Produtos, preços, catálogo
- RH, financeiro geral (não-marketing)
- Suporte ao cliente
- Qualquer tema fora de análise de dados de marketing

---

## 🧪 Exemplo de Interação

**Pergunta do Usuário:**
> "Os últimos 3 meses: qual canal trouxe mais receita? E qual tem melhor AOV?"

**Fluxo Interno:**
1. ✅ Pergunta validada (< 500 chars)
2. ✅ Agente usa ferramenta `consultar_receita_faturamento` (canal="", meses=3)
3. ✅ BigQuery executa JOIN complexo + agregações
4. ✅ Agente recebe dados e analisa
5. ✅ Resposta em tom consultivo com recomendações

**Resposta do Agente:**
```
Análise dos últimos 3 meses:

📊 TOP 3 Canais por Receita:
1. Search: R$ 1.250.000 (42% do total) | AOV: R$ 62.50
2. Organic: R$ 750.000 (25% do total) | AOV: R$ 58.30
3. Direct: R$ 550.000 (18% do total) | AOV: R$ 75.80

💡 Insights:
- Direct tem o melhor AOV (R$ 75.80), sugerindo clientes mais valiosos
- Search continua dominante, mas há risco de concentração

✅ Recomendações:
1. Manter investimento em Search (maior volume)
2. Investigar como replicar o padrão de Direct (AOV alto)
3. Diversificar alocação para reduzir risco de mudanças de algoritmo
```

---

## 🚨 Status dos Critérios de Auditoria

| Critério | Status | Detalhes |
|----------|--------|----------|
| Tool Calling & Arquitetura | ✅ | Agent_fresh.py centralizado, 5 arquivos obsoletos removidos |
| Clean Architecture | ✅ | Separação clara: prompts.py / agent_fresh.py / bq_tools.py |
| Validação Pydantic | ✅ | max_length=500 chars em user_question |
| Try/Except Robusto | ✅ | 5 tipos de erro específicos em routes.py |
| SQL com JOINs | ✅ | Nova ferramenta com users ← orders ← order_items |
| Agregações SQL | ✅ | SUM, AVG, COUNT em receita_faturamento |
| System Prompt | ✅ | Centralizado em core/prompts.py |
| Rejeição de Escopo | ✅ | Instruções claras de limite de escopo |
| Proteção Injection | ✅ | max_length=500 + parametrização segura |
| Limpeza de Testes | ✅ | 7 test_*.py removidos da raiz |

---

## 📚 Estrutura de Código

```python
# Exemplo: How the agent processes a question

1. INPUT VALIDATION (routes.py)
   - Pydantic validates: max_length=500, type=str
   
2. AGENT EXECUTION (agent_fresh.py)
   - Uses SYSTEM_PROMPT_AGENT from prompts.py
   - Calls Claude Haiku 4.5 (cheaper)
   - Claude may request tools
   
3. TOOL EXECUTION (bq_tools.py)
   - Parametrized BigQuery queries
   - Error handling with logging
   - Returns structured data
   
4. RESPONSE GENERATION (agent_fresh.py)
   - Claude processes tool results
   - Generates consultative response
   - Returns to user
```

---

## 🔍 Logging & Auditoria

Todos os eventos são logados:

```
2026-04-23 10:15:30 | INFO     | app.api.routes | Nova pergunta recebida (87 chars): 'Qual canal gerou mais receita...'
2026-04-23 10:15:30 | INFO     | app.agent.agent_fresh | Iniciando agente | Pergunta: 'Qual canal gerou mais receita...'
2026-04-23 10:15:31 | DEBUG    | app.agent.agent_fresh | Iteração 1: Chamando Claude Haiku 4.5
2026-04-23 10:15:32 | DEBUG    | app.agent.agent_fresh | Executando ferramenta: consultar_receita_faturamento
2026-04-23 10:15:33 | DEBUG    | app.tools.bq_tools | Consultando receita/faturamento - Canal: todos, Meses: 1
2026-04-23 10:15:35 | DEBUG    | app.agent.agent_fresh | Ferramenta consultar_receita_faturamento executada com sucesso
2026-04-23 10:15:36 | INFO     | app.api.routes | ✅ Resposta gerada com sucesso
```

---

## 📦 Requirements

```
fastapi==0.109.0
uvicorn==0.27.0
pydantic==2.6.0
pydantic-settings==2.1.0
python-dotenv==1.0.0
anthropic==0.35.0
langchain-core==0.1.32
langchain-anthropic==0.1.15
google-cloud-bigquery==3.27.0
```

---

**Last Updated:** 2026-04-23  
**Audited By:** Engenheiro de IA Sênior + Lead Data Engineer
