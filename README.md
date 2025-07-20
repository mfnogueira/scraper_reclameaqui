# 🏆 Pipeline Reclame Aqui - Documentação Completa

Sistema completo para coleta, armazenamento e análise de dados do Reclame Aqui com pipeline automatizada, armazenamento MinIO e análises visuais em notebooks.

## 📋 Índice

- [Visão Geral](#-visão-geral)
- [Estrutura do Projeto](#-estrutura-do-projeto)
- [Setup e Instalação](#-setup-e-instalação)
- [APIs Integradas](#-apis-integradas)
- [Scripts Principais](#-scripts-principais)
- [Comandos de Execução](#-comandos-de-execução)
- [Sistema de Dados](#-sistema-de-dados)
- [Notebooks de Análise](#-notebooks-de-análise)
- [Exemplos de Uso](#-exemplos-de-uso)
- [Troubleshooting](#-troubleshooting)

---

## 🎯 Visão Geral

### Objetivo
Coletar, processar e analisar dados de empresas e reclamações do Reclame Aqui de forma automatizada, com foco em:
- Rankings de empresas por categoria
- Dados detalhados de empresas específicas
- Reclamações e métricas de reputação
- Ofertas e cupons de desconto
- Análises visuais e insights

### Funcionalidades Principais
- ✅ **Coleta automatizada** de dados via 5 APIs diferentes
- ✅ **Armazenamento estruturado** em MinIO (S3-compatible)
- ✅ **Pipeline de dados** com 3 camadas (landing/raw/trusted)
- ✅ **Sistema de busca inteligente** de empresas
- ✅ **Análises visuais** em notebooks Jupyter
- ✅ **Dashboards interativos** com Plotly
- ✅ **Exportação de relatórios** em PDF/Excel

---

## 📁 Estrutura do Projeto

```
projeto/
├── minio/                          # Infraestrutura MinIO
│   └── docker-compose.yml          # Setup do MinIO via Docker
├── src/                            # Scripts principais
│   ├── reclame_aqui_pipeline.py    # Pipeline core de coleta
│   ├── minio_client.py             # Cliente para MinIO
│   ├── data_reader.py              # Sistema de leitura de dados
│   ├── data_helpers.py             # Funções de análise
│   ├── utils.py                    # Utilitários gerais
│   ├── runner.py                   # Script de execução principal
│   ├── top_empresas.py             # Coleta de rankings
│   ├── smart_company_finder.py     # Busca inteligente de empresas
│   └── test_data_reader.py         # Testes do sistema
├── notebooks/                      # Análises visuais
│   ├── utils_notebook.py           # Funções para notebooks
│   ├── 01_exploracao_inicial.ipynb # Análise exploratória
│   ├── 02_rankings_comparacoes.ipynb # Rankings e comparações
│   ├── test_notebooks.py           # Teste dos notebooks
│   └── SETUP_NOTEBOOKS.md          # Guia dos notebooks
├── requirements.txt                # Dependências Python
└── README.md                       # Esta documentação
```

---

## 🚀 Setup e Instalação

### 1. Pré-requisitos
- Python 3.8+
- Docker e Docker Compose
- Git

### 2. Clonagem e Setup
```bash
# Clonar projeto
git clone <url-do-projeto>
cd scraper_reclameaqui

# Criar ambiente virtual
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# ou
.venv\Scripts\activate     # Windows

# Instalar dependências
pip install -r requirements.txt
```

### 3. Configurar MinIO
```bash
# Subir MinIO via Docker
cd minio/
docker-compose up -d

# Verificar se está rodando
docker ps
```

### 4. Verificar Instalação
```bash
cd src/
python runner.py verificar
```

**Resultado esperado:**
```
✅ MinIO conectado com sucesso!
📊 Estatísticas dos buckets:
✅ landing: 0 objetos (0.0 MB)
✅ raw: 0 objetos (0.0 MB)  
✅ trusted: 0 objetos (0.0 MB)
```

---

## 🌐 APIs Integradas

O sistema integra **5 APIs** diferentes do Reclame Aqui:

### 1. **API de Categorias**
- **URL:** `https://iosearch.reclameaqui.com.br/raichu-io-site-search-v1/segments/main`
- **Função:** Lista todas as categorias e subcategorias disponíveis
- **Dados:** Hierarquia completa de segmentos de mercado

### 2. **API de Ofertas/Cupons**
- **URL:** `https://ramais-api.reclameaqui.com.br/v1/discounts/summary`
- **Função:** Empresas que oferecem cupons e descontos
- **Dados:** Informações promocionais e ofertas ativas

### 3. **API de Rankings**
- **URL:** `https://api.reclameaqui.com.br/segments/api/ranking/best-verified/{main}/{secondary}`
- **Função:** Rankings de melhores empresas por categoria
- **Dados:** Empresas verificadas ordenadas por reputação

### 4. **API de Empresa Detalhada**
- **URL:** `https://iosite.reclameaqui.com.br/raichu-io-site-v1/company/shortname/{shortname}`
- **Função:** Dados completos de uma empresa específica
- **Dados:** Perfil, scores, segmentos, histórico

### 5. **API de Busca de Empresas**
- **URL:** `https://iosearch.reclameaqui.com.br/raichu-io-site-search-v1/companies/search/{nome}`
- **Função:** Buscar empresas por nome
- **Dados:** Lista de empresas que correspondem ao termo

### 6. **API de Reclamações**
- **URL:** `https://iosearch.reclameaqui.com.br/raichu-io-site-search-v1/query/companyComplains/{qty}/{offset}`
- **Função:** Reclamações de uma empresa específica
- **Dados:** Reclamações, respostas, status de resolução

---

## 📝 Scripts Principais

### 1. **reclame_aqui_pipeline.py**
**Pipeline principal de coleta de dados**

**Funcionalidades:**
- Coleta dados de todas as APIs
- Gerencia sessões e headers
- Controla rate limiting
- Salva dados automaticamente no MinIO

**Métodos principais:**
- `coletar_categorias()` - Coleta categorias
- `coletar_ofertas_empresas()` - Coleta ofertas
- `coletar_ranking_categoria()` - Rankings por categoria
- `coletar_empresa_detalhada()` - Dados de empresa
- `coletar_reclamacoes()` - Reclamações

### 2. **minio_client.py**
**Cliente para interação com MinIO**

**Funcionalidades:**
- Upload/download de dados JSON
- Gerenciamento de buckets
- Sistema de camadas (landing/raw/trusted)
- Metadados e versionamento

**Métodos principais:**
- `upload_json()` - Upload de dados
- `download_json()` - Download de dados
- `list_objects()` - Listar arquivos
- `get_stats()` - Estatísticas dos buckets

### 3. **data_reader.py**
**Sistema de leitura de dados do MinIO**

**Funcionalidades:**
- Leitura de dados das 3 camadas
- Busca e filtros avançados
- Conversão para DataFrames
- Cache para otimização

**Métodos principais:**
- `listar_arquivos_disponiveis()` - Lista arquivos
- `carregar_dados()` - Carrega arquivo específico
- `carregar_ultima_coleta()` - Última coleta de categoria
- `converter_para_dataframe()` - Converte para pandas

### 4. **data_helpers.py**
**Funções de análise e insights**

**Funcionalidades:**
- Análises prontas de dados
- Comparações entre categorias
- Datasets consolidados
- Métricas de performance

**Métodos principais:**
- `obter_overview_completo()` - Overview dos dados
- `obter_top_empresas_categoria()` - Top empresas
- `comparar_categorias()` - Comparações
- `gerar_dataset_analise()` - Dataset consolidado

### 5. **runner.py**
**Script principal de execução**

**Funcionalidades:**
- Interface unificada para todas as operações
- Múltiplos modos de execução
- Verificação de status
- Listagem de dados

### 6. **top_empresas.py**
**Coleta especializada de rankings**

**Funcionalidades:**
- Busca interativa de categorias
- Coleta de top N empresas
- Análise automática de rankings
- Exemplos pré-configurados

### 7. **smart_company_finder.py** ⭐
**Busca inteligente de empresas**

**Funcionalidades:**
- Busca com múltiplas variações de nome
- Seleção automática da melhor opção
- Coleta completa de dados
- Relatório detalhado de resultados

---

## ⚡ Comandos de Execução

### 🔧 **Comandos de Setup e Verificação**

```bash
# Verificar status do sistema
python runner.py verificar

# Listar dados disponíveis
python runner.py listar

# Testar sistema de leitura
python test_data_reader.py

# Testar notebooks
cd ../notebooks/
python test_notebooks.py
```

### 📥 **Comandos de Coleta de Dados**

#### **Coleta Básica (Recomendado para começar)**
```bash
# Coleta básica - 2 categorias, 3 empresas cada
python runner.py basica

# Coleta expandida - 5 categorias, 10 empresas cada
python runner.py basica --limite-categorias 5 --limite-empresas 10
```

#### **Coleta por Categoria Específica**
```bash
# Categoria específica
python runner.py categoria --main-segment bancos-e-financeiras --secondary-segment meios-de-pagamento-eletronico

# Categoria de telefonia
python runner.py categoria --main-segment telefonia-tv-e-internet --secondary-segment planos-de-internet
```

#### **Coleta de Empresa Específica**
```bash
# Empresa por shortname
python runner.py empresa --shortname sumup

# Empresa por shortname (telefonia)
python runner.py empresa --shortname telefonica-brasil-s-a
```

### 🏆 **Comandos de Rankings**

#### **Listar Categorias Disponíveis**
```bash
# Ver todas as categorias com dados
python top_empresas.py --listar
```

#### **Top Empresas por Categoria**
```bash
# Top 10 meios de pagamento
python top_empresas.py --main-segment bancos-e-financeiras --secondary-segment meios-de-pagamento-eletronico

# Top 20 marketplaces
python top_empresas.py --main-segment varejo --secondary-segment marketplaces --quantidade 20

# Top 15 planos de internet
python top_empresas.py --main-segment telefonia-tv-e-internet --secondary-segment planos-de-internet --quantidade 15
```

#### **Exemplos de Categorias Populares**
```bash
# Bancos digitais
python top_empresas.py --main-segment bancos-e-financeiras --secondary-segment bancos-digitais

# E-commerce moda
python top_empresas.py --main-segment moda --secondary-segment e-commerce-moda

# Planos de saúde
python top_empresas.py --main-segment saude --secondary-segment planos-de-saude

# Concessionárias
python top_empresas.py --main-segment veiculos-e-acessorios --secondary-segment concessionarias-de-veiculos
```

### 🔍 **Comandos de Busca Inteligente** ⭐

#### **Busca Automática de Empresas**
```bash
# Buscar e coletar dados da Vivo automaticamente
python smart_company_finder.py "Vivo"

# Buscar Tim
python smart_company_finder.py "Tim"

# Buscar Claro  
python smart_company_finder.py "Claro"

# Buscar Nubank
python smart_company_finder.py "Nubank"

# Buscar Mercado Livre
python smart_company_finder.py "Mercado Livre"

# Modo silencioso
python smart_company_finder.py "Stone" --quiet
```

**O que cada comando faz:**
- 🔍 Busca empresa com múltiplas variações do nome
- 📊 Lista todas as opções encontradas
- ✅ Seleciona automaticamente a melhor opção
- 🏢 Coleta dados detalhados da empresa
- 📝 Coleta reclamações (avaliadas e todas)
- 📋 Gera relatório completo
- 💾 Salva tudo no MinIO

---

## 💾 Sistema de Dados

### **Arquitetura MinIO**
O sistema usa MinIO (S3-compatible) com 3 camadas:

#### **🚢 Landing Layer** (`reclameaqui-landing`)
- **Função:** Dados brutos das APIs
- **Conteúdo:** JSON original sem processamento
- **Estrutura:** `categoria/ano/mes/dia/arquivo.json`

#### **🔧 Raw Layer** (`reclameaqui-raw`)
- **Função:** Dados com metadados básicos
- **Conteúdo:** JSON + informações de processamento
- **Estrutura:** Mesma da landing + metadados

#### **✅ Trusted Layer** (`reclameaqui-trusted`)
- **Função:** Dados processados e validados
- **Conteúdo:** Datasets prontos para análise
- **Estrutura:** Formato otimizado para consultas

### **Categorias de Dados**

#### **📂 categorias/**
- **Conteúdo:** Hierarquia completa de categorias
- **Fonte:** API de categorias
- **Uso:** Navegação e descoberta

#### **🏆 rankings/**
- **Conteúdo:** Top empresas por categoria
- **Fonte:** API de rankings
- **Uso:** Análises comparativas

#### **🏢 empresas/**
- **Conteúdo:** Dados detalhados de empresas
- **Fonte:** API de empresa detalhada
- **Uso:** Perfis e análises específicas

#### **📝 reclamacoes/**
- **Conteúdo:** Reclamações por empresa
- **Fonte:** API de reclamações
- **Uso:** Análise de satisfação

#### **💰 ofertas/**
- **Conteúdo:** Empresas com cupons/ofertas
- **Fonte:** API de ofertas
- **Uso:** Correlação promoção vs reputação

#### **🔍 top_empresas/**
- **Conteúdo:** Rankings processados
- **Fonte:** Script top_empresas.py
- **Uso:** Análises de ranking

### **Acesso ao MinIO Console**
- **URL:** http://localhost:9090
- **Login:** minioadmin
- **Senha:** minioadmin123

---

## 📓 Notebooks de Análise

### **Localização:** `notebooks/`

#### **1. 01_exploracao_inicial.ipynb**
**Primeira análise visual dos dados coletados**

**Conteúdo:**
- ✅ Carregamento e overview dos dados
- 📊 Análise das categorias disponíveis  
- 🏆 Análise detalhada dos rankings
- 📈 Visualizações básicas (barras, histogramas, scatter)
- 🌐 Dashboard interativo com Plotly
- 🧠 Insights e descobertas automáticas

**Como usar:**
```bash
cd notebooks/
jupyter notebook
# Abrir: 01_exploracao_inicial.ipynb
```

#### **2. 02_rankings_comparacoes.ipynb**
**Análise focada em rankings e comparações**

**Conteúdo:**
- 🥇 Rankings detalhados por categoria
- 📊 Comparações cross-categoria
- 🎯 Identificação de padrões
- 📈 Métricas de performance avançadas
- 🌟 Identificação de empresas benchmark
- 🚀 Recomendações baseadas em dados

#### **3. utils_notebook.py**
**Funções helper para notebooks**

**Funções principais:**
- `carregar_dados_basicos()` - Carrega todos os dados
- `plot_top_empresas()` - Gráfico de ranking
- `plot_distribuicao_scores()` - Histograma + box plot
- `criar_dashboard_interativo()` - Dashboard Plotly
- `salvar_relatorio_pdf()` - Export para PDF

---

## 💡 Exemplos de Uso

### **Cenário 1: Análise de Concorrência - Fintech**
```bash
# 1. Coletar dados do setor
python top_empresas.py --main-segment bancos-e-financeiras --secondary-segment meios-de-pagamento-eletronico --quantidade 20

# 2. Coletar dados específicos de fintechs
python smart_company_finder.py "Stone"
python smart_company_finder.py "SumUp"  
python smart_company_finder.py "PagSeguro"

# 3. Analisar no notebook
cd notebooks/
jupyter notebook
# Abrir: 02_rankings_comparacoes.ipynb
```

### **Cenário 2: Análise de Operadoras de Telecom**
```bash
# 1. Coletar ranking geral
python top_empresas.py --main-segment telefonia-tv-e-internet --secondary-segment planos-de-internet --quantidade 30

# 2. Coletar dados das principais operadoras
python smart_company_finder.py "Vivo"
python smart_company_finder.py "Tim"
python smart_company_finder.py "Claro"

# 3. Análise comparativa no notebook
```

### **Cenário 3: Monitoramento de Empresa Específica**
```bash
# 1. Coleta completa de uma empresa
python smart_company_finder.py "Nubank"

# 2. Ver dados coletados
python test_data_reader.py

# 3. Análise detalhada
cd notebooks/
jupyter notebook
# Usar utils_notebook para análise específica
```

### **Cenário 4: Análise Setorial Completa**
```bash
# 1. Descobrir categorias disponíveis
python top_empresas.py --listar

# 2. Coletar múltiplas categorias
python runner.py basica --limite-categorias 10 --limite-empresas 15

# 3. Análise cross-setorial
cd notebooks/
jupyter notebook
# Abrir: 01_exploracao_inicial.ipynb
```

---

## 🛠️ Troubleshooting

### **Problemas Comuns**

#### **❌ MinIO não conecta**
```bash
# Verificar se Docker está rodando
docker ps

# Reiniciar MinIO
cd minio/
docker-compose down
docker-compose up -d

# Testar conexão
cd ../src/
python runner.py verificar
```

#### **❌ Nenhum dado encontrado**
```bash
# Executar coleta básica
python runner.py basica

# Verificar dados
python test_data_reader.py
```

#### **❌ Empresa não encontrada**
```bash
# Usar busca inteligente
python smart_company_finder.py "Nome da Empresa"

# Ou listar categorias primeiro
python top_empresas.py --listar
```

#### **❌ Jupyter não funciona**
```bash
# Instalar Jupyter
pip install jupyter

# Verificar notebooks
cd notebooks/
python test_notebooks.py
```

#### **❌ Erro de dependências**
```bash
# Reinstalar dependências
pip install -r requirements.txt --upgrade

# Verificar versão Python
python --version  # Deve ser 3.8+
```

### **Logs e Debug**

#### **Ativar logs detalhados:**
```bash
# Modo verbose em qualquer comando
python runner.py basica --verbose
python smart_company_finder.py "Empresa" --verbose
```

#### **Verificar arquivos coletados:**
```bash
# Listar todos os arquivos
python runner.py listar

# Estatísticas detalhadas
python -c "
from minio_client import MinIOClient
client = MinIOClient()
stats = client.get_stats()
print(stats)
"
```

---

## 🎯 Roadmap e Próximos Passos

### **Implementados ✅**
- [x] Pipeline completa de coleta
- [x] Armazenamento estruturado MinIO
- [x] Sistema de leitura de dados
- [x] Busca inteligente de empresas
- [x] Notebooks de análise visual
- [x] Dashboards interativos

### **Planejado 🎯**
- [ ] Processamento Raw → Trusted automatizado
- [ ] Análise temporal (dados históricos)
- [ ] Dashboard web (Flask/Streamlit)
- [ ] API REST para consultas
- [ ] Machine Learning (clustering, predições)
- [ ] Alertas de mudanças de reputação
- [ ] Análise de sentimento em reclamações
- [ ] Integração com outras fontes de dados

### **Ideias Futuras 💡**
- [ ] Scheduler automatizado (Airflow)
- [ ] Análise de rede social empresarial
- [ ] Predição de scores futuros
- [ ] Detecção de anomalias
- [ ] Export para BI tools (Power BI, Tableau)
- [ ] Mobile app para monitoramento

---

## 📞 Suporte e Contribuição

### **Como Contribuir**
1. Fork o projeto
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

### **Reportar Problemas**
- Abra uma issue descrevendo o problema
- Inclua logs e comando executado
- Especifique ambiente (OS, Python version)

### **Melhorias Sugeridas**
- Novos tipos de análise
- Integração com outras APIs
- Otimizações de performance
- Novas visualizações

---

## 📄 Licença

Este projeto está sob licença MIT. Veja o arquivo LICENSE para detalhes.

---

## 🎉 Conclusão

Este sistema oferece uma **pipeline completa** para análise de dados do Reclame Aqui, desde a coleta automatizada até visualizações interativas. 

**Principais benefícios:**
- ⚡ **Rapidez:** Coleta automatizada com poucos comandos
- 🎯 **Precisão:** Busca inteligente de empresas
- 📊 **Insights:** Análises visuais prontas
- 🔧 **Flexibilidade:** Múltiplos modos de uso
- 📈 **Escalabilidade:** Arquitetura preparada para crescimento

**Para começar rapidamente:**
```bash
# Setup
cd minio && docker-compose up -d
cd ../src && python runner.py verificar

# Primeira coleta
python runner.py basica

# Primeira análise
cd ../notebooks && jupyter notebook
```

**🎯 O sistema está pronto para uso em produção e análises profissionais!**