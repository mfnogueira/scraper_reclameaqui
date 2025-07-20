# 📋 Guia Completo de Comandos - Pipeline Reclame Aqui

Referência completa de todos os comandos disponíveis no sistema, organizados por função e com exemplos práticos.

---

## 📚 Índice

- [🔧 Comandos de Setup e Verificação](#-comandos-de-setup-e-verificação)
- [📥 Comandos de Coleta de Dados](#-comandos-de-coleta-de-dados)
- [🔍 Comandos de Busca e Consulta](#-comandos-de-busca-e-consulta)
- [📊 Comandos de Análise](#-comandos-de-análise)
- [🧪 Comandos de Teste](#-comandos-de-teste)
- [📓 Comandos dos Notebooks](#-comandos-dos-notebooks)
- [💾 Comandos de Dados](#-comandos-de-dados)

---

## 🔧 Comandos de Setup e Verificação

### **Verificar Status do Sistema**
```bash
python runner.py verificar
```
- **O que faz:** Verifica se MinIO está conectado e funcionando
- **Quando usar:** Primeira execução, debugging, após reinicializar serviços
- **Dados retornados:** Status de conexão, estatísticas dos buckets (landing/raw/trusted)
- **Exemplo de saída:**
  ```
  ✅ MinIO conectado com sucesso!
  📊 Estatísticas dos buckets:
  ✅ landing: 12 objetos (0.17 MB)
  ✅ raw: 0 objetos (0.0 MB)
  ✅ trusted: 0 objetos (0.0 MB)
  ```

### **Listar Dados Disponíveis**
```bash
python runner.py listar
```
- **O que faz:** Lista todos os dados coletados organizados por camada e categoria
- **Quando usar:** Ver o que já foi coletado, verificar arquivos antes de análise
- **Dados retornados:** Lista completa de arquivos por bucket, categorias, datas
- **Exemplo de saída:**
  ```
  📁 Camada: landing
     📂 categorias: 1 arquivo(s)
        📄 categorias/2025/07/20/categorias_20250720_113542.json
     📂 rankings: 4 arquivo(s)
        📄 rankings/2025/07/20/ranking_bancos-e-financeiras_meios-de-pagamento-eletronico_1.json
  ```

### **Verificar Dependências e Sistema**
```bash
python test_data_reader.py
```
- **O que faz:** Testa todo o sistema de leitura de dados, conversões e funcionalidades
- **Quando usar:** Após instalação, antes de usar notebooks, para debugging
- **Dados retornados:** Relatório completo dos dados disponíveis, testes de conversão DataFrame
- **Exemplo de saída:**
  ```
  📊 Total de arquivos encontrados: 13
  ✅ Categorias carregadas: 32
  📋 Primeiras linhas:
                               main_title                         secondary_title
  0  Agências de Atendimento e Recrutamento                      Agências de Modelo
  ```

---

## 📥 Comandos de Coleta de Dados

### **Coleta Básica (Recomendado para começar)**
```bash
# Coleta padrão - 2 categorias, 3 empresas cada
python runner.py basica

# Coleta expandida
python runner.py basica --limite-categorias 5 --limite-empresas 10
```
- **O que faz:** Executa pipeline completa: categorias → ofertas → rankings → empresas → reclamações
- **Quando usar:** Primeira coleta, quando quiser dados variados para análise
- **Dados retornados:** Categorias, rankings de múltiplas categorias, dados de empresas, reclamações
- **Parâmetros:**
  - `--limite-categorias N`: Quantas categorias processar (padrão: 2)
  - `--limite-empresas N`: Quantas empresas por categoria (padrão: 3)

### **Coleta por Categoria Específica**
```bash
# Meios de pagamento
python runner.py categoria --main-segment bancos-e-financeiras --secondary-segment meios-de-pagamento-eletronico

# Planos de internet
python runner.py categoria --main-segment telefonia-tv-e-internet --secondary-segment planos-de-internet

# Marketplaces
python runner.py categoria --main-segment varejo --secondary-segment marketplaces
```
- **O que faz:** Coleta ranking de uma categoria específica + dados das empresas + reclamações
- **Quando usar:** Análise setorial focada, quando já sabe a categoria de interesse
- **Dados retornados:** Ranking completo da categoria, dados detalhados das empresas, reclamações
- **Parâmetros obrigatórios:**
  - `--main-segment`: Categoria principal
  - `--secondary-segment`: Subcategoria

### **Coleta de Empresa Específica**
```bash
# Por shortname (mais comum)
python runner.py empresa --shortname sumup
python runner.py empresa --shortname telefonica-brasil-s-a

# Exemplos de shortnames comuns
python runner.py empresa --shortname stone
python runner.py empresa --shortname nubank
```
- **O que faz:** Coleta dados detalhados de uma empresa + reclamações
- **Quando usar:** Análise de empresa específica, monitoramento, comparação pontual
- **Dados retornados:** Perfil completo da empresa, métricas de reputação, reclamações (avaliadas e todas)
- **Parâmetros:**
  - `--shortname`: Nome técnico da empresa na API (obrigatório)

---

## 🔍 Comandos de Busca e Consulta

### **Busca Inteligente de Empresas** ⭐
```bash
# Busca automática com coleta completa
python smart_company_finder.py "Vivo"
python smart_company_finder.py "Nubank" 
python smart_company_finder.py "Mercado Livre"

# Modo silencioso (menos logs)
python smart_company_finder.py "Stone" --quiet

# Busca com nomes complexos
python smart_company_finder.py "Banco do Brasil"
python smart_company_finder.py "Cartões Itaú"
```
- **O que faz:** Busca empresa com múltiplas variações do nome + seleciona melhor opção + coleta dados completos
- **Quando usar:** Quando não souber o shortname exato, para automação, primeira busca de empresa
- **Dados retornados:** 
  - Lista de empresas encontradas
  - Seleção automática da melhor opção
  - Dados detalhados da empresa selecionada
  - Reclamações coletadas
  - Relatório completo da operação
- **Parâmetros:**
  - `"Nome da Empresa"`: Nome em linguagem natural (obrigatório)
  - `--quiet`: Modo silencioso, menos logs

### **Rankings por Categoria**
```bash
# Listar categorias disponíveis
python top_empresas.py --listar

# Top 10 (padrão)
python top_empresas.py --main-segment bancos-e-financeiras --secondary-segment meios-de-pagamento-eletronico

# Top personalizado
python top_empresas.py --main-segment varejo --secondary-segment marketplaces --quantidade 20
python top_empresas.py --main-segment saude --secondary-segment planos-de-saude --quantidade 15
```
- **O que faz:** Busca ranking de empresas em categoria específica
- **Quando usar:** Descobrir top empresas de um setor, análise competitiva, pesquisa de mercado
- **Dados retornados:** Lista ordenada das melhores empresas com scores, taxa de resolução, total de reclamações
- **Parâmetros:**
  - `--listar`: Mostra todas as categorias com dados disponíveis
  - `--main-segment`: Categoria principal (obrigatório quando não usar --listar)
  - `--secondary-segment`: Subcategoria (obrigatório quando não usar --listar)
  - `--quantidade N`: Quantas empresas buscar (padrão: 10)

### **Exemplos de Rankings Populares**
```bash
# Fintech - Bancos digitais
python top_empresas.py --main-segment bancos-e-financeiras --secondary-segment bancos-digitais

# E-commerce - Moda
python top_empresas.py --main-segment moda --secondary-segment e-commerce-moda

# Saúde - Planos de saúde
python top_empresas.py --main-segment saude --secondary-segment planos-de-saude

# Veículos - Concessionárias
python top_empresas.py --main-segment veiculos-e-acessorios --secondary-segment concessionarias-de-veiculos

# Telefonia - Internet
python top_empresas.py --main-segment telefonia-tv-e-internet --secondary-segment planos-de-internet
```

---

## 📊 Comandos de Análise

### **Overview Completo dos Dados**
```python
# Execute no Python interativo ou notebook
from data_helpers import DataAnalyzer

analyzer = DataAnalyzer()
overview = analyzer.obter_overview_completo()
print(overview)
```
- **O que faz:** Gera visão geral de todos os dados coletados
- **Quando usar:** Antes de análises detalhadas, para entender o que está disponível
- **Dados retornados:** Total de arquivos, categorias disponíveis, empresas com ranking/ofertas

### **Top Empresas de Categoria**
```python
from data_helpers import DataAnalyzer

analyzer = DataAnalyzer()
top10 = analyzer.obter_top_empresas_categoria(
    'bancos-e-financeiras', 
    'meios-de-pagamento-eletronico',
    limit=10
)
print(top10[['companyName', 'finalScore', 'solvedPercentual']])
```
- **O que faz:** Retorna DataFrame com top empresas de uma categoria
- **Quando usar:** Análises programáticas, comparações, geração de relatórios
- **Dados retornados:** DataFrame pandas pronto para análise

### **Comparação Entre Categorias**
```python
analyzer = DataAnalyzer()
comparacao = analyzer.comparar_categorias([
    ('bancos-e-financeiras', 'bancos-digitais'),
    ('varejo', 'marketplaces'),
    ('telefonia-tv-e-internet', 'planos-de-internet')
])
print(comparacao)
```
- **O que faz:** Compara métricas entre diferentes categorias
- **Quando usar:** Análise cross-setorial, identificar melhores setores
- **Dados retornados:** DataFrame com estatísticas comparativas por categoria

### **Dataset Consolidado**
```python
dataset = analyzer.gerar_dataset_analise(
    incluir_ofertas=True,
    incluir_reclamacoes=False
)
print(f"Dataset: {dataset.shape}")
print(dataset.nlargest(10, 'finalScore')[['companyName', 'finalScore']])
```
- **O que faz:** Gera dataset único com todas as empresas coletadas
- **Quando usar:** Análises globais, machine learning, exportar para outras ferramentas
- **Dados retornados:** DataFrame consolidado com todas as empresas e métricas

---

## 🧪 Comandos de Teste

### **Teste Completo do Sistema**
```bash
python test_data_reader.py
```
- **O que faz:** Executa bateria completa de testes: leitura, conversão, análise
- **Quando usar:** Após mudanças no código, verificação pós-instalação, debugging
- **Dados retornados:** Relatório de testes, exemplos de dados carregados, diagnósticos

### **Teste dos Notebooks**
```bash
cd notebooks/
python test_notebooks.py
```
- **O que faz:** Verifica se notebooks vão funcionar: dependências, dados, visualizações
- **Quando usar:** Antes de usar notebooks, após mudanças no ambiente
- **Dados retornados:** Status de dependências, teste de gráficos, verificação de dados

### **Busca Manual de Empresas**
```python
# Execute no Python para testar busca manual
from reclame_aqui_pipeline import ReclameAquiPipeline

pipeline = ReclameAquiPipeline(verbose=True)
empresa = pipeline.coletar_empresa_detalhada('shortname-teste')
```
- **O que faz:** Teste manual de busca de empresa específica
- **Quando usar:** Debugging, verificar se shortname existe, teste pontual

---

## 📓 Comandos dos Notebooks

### **Iniciar Notebooks**
```bash
cd notebooks/
jupyter notebook
```
- **O que faz:** Abre interface Jupyter para análises visuais
- **Quando usar:** Análises exploratórias, criação de gráficos, relatórios visuais
- **Arquivos disponíveis:**
  - `01_exploracao_inicial.ipynb`: Primeira análise dos dados
  - `02_rankings_comparacoes.ipynb`: Rankings e comparações detalhadas

### **Funções Helper nos Notebooks**
```python
# Dentro dos notebooks
from utils_notebook import NotebookHelper

helper = NotebookHelper()
helper.configurar_plots()

# Carregar todos os dados
dados = helper.carregar_dados_basicos()

# Criar visualizações
fig1 = helper.plot_top_empresas(df, 'finalScore')
fig2 = helper.plot_distribuicao_scores(df, 'finalScore')
fig3 = helper.criar_dashboard_interativo(df)
```
- **O que faz:** Funções prontas para gráficos e análises visuais
- **Quando usar:** Criação rápida de visualizações, dashboards, relatórios

---

## 💾 Comandos de Dados

### **Carregar Dados Específicos**
```python
from data_reader import DataReader

reader = DataReader()

# Carregar categorias
categorias = reader.carregar_todas_categorias()

# Carregar empresa específica
empresa = reader.carregar_dados_empresa('sumup')

# Buscar arquivos por filtro
rankings = reader.buscar_arquivos_por_filtro(
    layer='landing',
    category='rankings',
    filename_contains='bancos'
)
```

### **Listar Arquivos Programaticamente**
```python
# Ver todos os arquivos disponíveis
arquivos = reader.listar_arquivos_disponiveis()
for arquivo in arquivos:
    print(f"{arquivo.layer}/{arquivo.category}/{arquivo.filename}")

# Filtrar por data
arquivos_hoje = reader.buscar_arquivos_por_filtro(
    data_inicio='2025/07/20',
    data_fim='2025/07/20'
)
```

### **Conversão para DataFrame**
```python
# Converter dados para análise
df_categorias = reader.converter_para_dataframe(categorias, 'categorias')
df_ranking = reader.converter_para_dataframe(ranking_data, 'rankings')

# Análise rápida
print(df_ranking.groupby('main_segment')['finalScore'].mean())
```

---

## 🎯 Fluxos de Trabalho Comuns

### **Fluxo 1: Primeira Execução**
```bash
# 1. Verificar sistema
python runner.py verificar

# 2. Coleta inicial
python runner.py basica

# 3. Ver o que foi coletado
python runner.py listar

# 4. Análise visual
cd notebooks/ && jupyter notebook
```

### **Fluxo 2: Análise de Empresa Específica**
```bash
# 1. Busca inteligente
python smart_company_finder.py "Nome da Empresa"

# 2. Verificar dados coletados
python test_data_reader.py

# 3. Análise programática
python -c "
from data_helpers import DataAnalyzer
analyzer = DataAnalyzer()
resultado = analyzer.buscar_empresa_completa('shortname')
print(resultado)
"
```

### **Fluxo 3: Análise Setorial**
```bash
# 1. Descobrir categorias
python top_empresas.py --listar

# 2. Coletar categoria específica
python runner.py categoria --main-segment CATEGORIA --secondary-segment SUBCATEGORIA

# 3. Análise comparativa
cd notebooks/ && jupyter notebook
# Abrir: 02_rankings_comparacoes.ipynb
```

### **Fluxo 4: Monitoramento Contínuo**
```bash
# 1. Atualizar dados existentes
python runner.py basica --limite-categorias 5 --limite-empresas 10

# 2. Empresas específicas
python smart_company_finder.py "Empresa 1"
python smart_company_finder.py "Empresa 2"

# 3. Relatório automático
python -c "
from data_helpers import DataAnalyzer
analyzer = DataAnalyzer()
overview = analyzer.obter_overview_completo()
print('Relatório:', overview)
"
```

---

## 🔍 Comandos de Debug e Troubleshooting

### **Verificar Conexão MinIO**
```bash
# Status detalhado
python -c "
from minio_client import MinIOClient
client = MinIOClient()
stats = client.get_stats()
for layer, info in stats.items():
    print(f'{layer}: {info}')
"
```

### **Verificar Requisições da API**
```bash
# Teste manual de API
python -c "
import cloudscraper
scraper = cloudscraper.create_scraper()
response = scraper.get('https://iosearch.reclameaqui.com.br/raichu-io-site-search-v1/segments/main')
print(f'Status: {response.status_code}')
print(f'Tamanho: {len(response.text)} chars')
"
```

### **Limpar Cache**
```python
from data_reader import DataReader
reader = DataReader()
reader.limpar_cache()
print("Cache limpo")
```

---

## 📋 Resumo de Comandos por Frequência de Uso

### **🔥 Mais Usados (Diário)**
```bash
python smart_company_finder.py "Nome da Empresa"    # Busca inteligente
python runner.py verificar                          # Status do sistema
python runner.py listar                             # Ver dados disponíveis
python test_data_reader.py                          # Verificar dados
```

### **📊 Análise (Semanal)**
```bash
python top_empresas.py --listar                     # Descobrir categorias
python runner.py basica --limite-categorias 3       # Coleta ampla
cd notebooks/ && jupyter notebook                   # Análises visuais
```

### **🔧 Manutenção (Quando necessário)**
```bash
python test_notebooks.py                            # Teste dos notebooks  
python runner.py categoria --main-segment X --secondary-segment Y  # Categoria específica
python runner.py empresa --shortname SHORTNAME      # Empresa específica
```

---

## 💡 Dicas e Melhores Práticas

### **Para Coleta Eficiente:**
- Use `smart_company_finder.py` quando não souber o shortname exato
- Use `runner.py basica` para primeira coleta ampla
- Use `top_empresas.py --listar` para descobrir categorias disponíveis

### **Para Análise:**
- Sempre execute `test_data_reader.py` antes de análises importantes
- Use notebooks para visualizações, Python direto para automação
- Combine dados de diferentes categorias para análises cross-setoriais

### **Para Troubleshooting:**
- `runner.py verificar` é sempre o primeiro comando para debug
- Use `--quiet` em scripts automatizados
- Verifique logs detalhados removendo `--quiet` quando houver problemas

**🎯 Este guia cobre 100% dos comandos disponíveis no sistema!**