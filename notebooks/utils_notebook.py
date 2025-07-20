#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Funções utilitárias específicas para notebooks de análise.
Facilita criação de visualizações e análises no Jupyter.
"""

import sys
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Dict, List, Optional, Tuple, Any

# Adicionar pasta src ao path para imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from data_reader import DataReader
from data_helpers import DataAnalyzer

# Configurações de estilo
plt.style.use('default')
sns.set_palette("husl")

# Configurações do pandas
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
pd.set_option('display.max_colwidth', 50)


class NotebookHelper:
    """
    Classe com funções helper para análises em notebooks.
    """
    
    def __init__(self, verbose: bool = False):
        """
        Inicializa o helper.
        
        Args:
            verbose: Se True, exibe logs detalhados
        """
        self.reader = DataReader(verbose=verbose)
        self.analyzer = DataAnalyzer(verbose=verbose)
        self.cores_primarias = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
        
    def configurar_plots(self, figsize: Tuple[int, int] = (12, 8), 
                        style: str = 'whitegrid'):
        """
        Configura estilo padrão para plots.
        
        Args:
            figsize: Tamanho da figura
            style: Estilo do seaborn
        """
        plt.rcParams['figure.figsize'] = figsize
        plt.rcParams['font.size'] = 11
        plt.rcParams['axes.titlesize'] = 14
        plt.rcParams['axes.labelsize'] = 12
        plt.rcParams['xtick.labelsize'] = 10
        plt.rcParams['ytick.labelsize'] = 10
        plt.rcParams['legend.fontsize'] = 10
        
        sns.set_style(style)
        sns.set_context("notebook")
    
    def carregar_dados_basicos(self) -> Dict[str, pd.DataFrame]:
        """
        Carrega todos os dados básicos disponíveis.
        
        Returns:
            Dict: Dicionário com DataFrames carregados
        """
        print("📥 Carregando dados disponíveis...")
        
        dados = {}
        
        # Categorias
        categorias = self.reader.carregar_todas_categorias()
        if categorias:
            dados['categorias'] = self.reader.converter_para_dataframe(categorias, 'categorias')
            print(f"✅ Categorias: {len(dados['categorias'])} subcategorias")
        
        # Categorias com dados de ranking
        categorias_ranking = self.analyzer.listar_categorias_com_dados()
        if not categorias_ranking.empty:
            dados['categorias_com_ranking'] = categorias_ranking
            print(f"✅ Categorias com ranking: {len(categorias_ranking)}")
        
        # Buscar rankings disponíveis
        for _, cat in categorias_ranking.iterrows():
            main_seg = cat['main_segment']
            sec_seg = cat['secondary_segment']
            
            # Carregar ranking da categoria
            ranking = self.analyzer.obter_top_empresas_categoria(main_seg, sec_seg, limit=20)
            if not ranking.empty:
                key = f"ranking_{main_seg}_{sec_seg}"
                dados[key] = ranking
                print(f"✅ {cat['main_title']} / {cat['secondary_title']}: {len(ranking)} empresas")
        
        # Ofertas (se disponível)
        ofertas = self.analyzer.obter_empresas_com_ofertas()
        if not ofertas.empty:
            dados['ofertas'] = ofertas
            print(f"✅ Ofertas: {len(ofertas)} empresas")
        
        print(f"\n📊 Total de datasets carregados: {len(dados)}")
        return dados
    
    def plot_top_empresas(self, df: pd.DataFrame, metric: str = 'finalScore',
                         title: str = None, top_n: int = 10) -> plt.Figure:
        """
        Cria gráfico de barras das top empresas.
        
        Args:
            df: DataFrame com dados das empresas
            metric: Métrica para ordenar (finalScore, solvedPercentual, etc.)
            title: Título do gráfico
            top_n: Número de empresas a exibir
            
        Returns:
            plt.Figure: Figura do matplotlib
        """
        if metric not in df.columns:
            print(f"❌ Métrica '{metric}' não encontrada. Colunas disponíveis: {list(df.columns)}")
            return None
        
        # Preparar dados
        df_plot = df.nlargest(top_n, metric).copy()
        
        # Criar figura
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Gráfico de barras horizontal
        bars = ax.barh(range(len(df_plot)), df_plot[metric], 
                      color=self.cores_primarias[0], alpha=0.8)
        
        # Personalizar
        ax.set_yticks(range(len(df_plot)))
        ax.set_yticklabels(df_plot['companyName'], fontsize=10)
        ax.invert_yaxis()  # Top empresa no topo
        
        ax.set_xlabel(metric.replace('Percentual', ' (%)'), fontsize=12)
        ax.set_title(title or f'Top {top_n} Empresas por {metric}', fontsize=14, fontweight='bold')
        
        # Adicionar valores nas barras
        for i, bar in enumerate(bars):
            width = bar.get_width()
            ax.text(width + 0.1, bar.get_y() + bar.get_height()/2, 
                   f'{width:.1f}', ha='left', va='center', fontsize=9)
        
        # Grade sutil
        ax.grid(axis='x', alpha=0.3)
        ax.set_axisbelow(True)
        
        plt.tight_layout()
        return fig
    
    def plot_distribuicao_scores(self, df: pd.DataFrame, 
                                metric: str = 'finalScore') -> plt.Figure:
        """
        Cria histograma da distribuição de scores.
        
        Args:
            df: DataFrame com dados das empresas
            metric: Métrica para analisar
            
        Returns:
            plt.Figure: Figura do matplotlib
        """
        if metric not in df.columns:
            print(f"❌ Métrica '{metric}' não encontrada.")
            return None
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # Histograma
        ax1.hist(df[metric], bins=20, color=self.cores_primarias[0], alpha=0.7, edgecolor='black')
        ax1.set_xlabel(metric)
        ax1.set_ylabel('Frequência')
        ax1.set_title(f'Distribuição de {metric}')
        ax1.grid(alpha=0.3)
        
        # Box plot
        box = ax2.boxplot(df[metric], patch_artist=True)
        box['boxes'][0].set_facecolor(self.cores_primarias[1])
        ax2.set_ylabel(metric)
        ax2.set_title(f'Box Plot - {metric}')
        ax2.grid(alpha=0.3)
        
        # Estatísticas
        stats_text = f"""Estatísticas:
        Média: {df[metric].mean():.2f}
        Mediana: {df[metric].median():.2f}
        Desvio: {df[metric].std():.2f}
        Min: {df[metric].min():.2f}
        Max: {df[metric].max():.2f}"""
        
        fig.text(0.02, 0.98, stats_text, fontsize=10, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='lightgray', alpha=0.8))
        
        plt.tight_layout()
        return fig
    
    def plot_scatter_metricas(self, df: pd.DataFrame, x: str, y: str,
                             color_by: str = None, title: str = None) -> plt.Figure:
        """
        Cria scatter plot entre duas métricas.
        
        Args:
            df: DataFrame com dados
            x: Métrica para eixo X
            y: Métrica para eixo Y
            color_by: Coluna para colorir pontos
            title: Título do gráfico
            
        Returns:
            plt.Figure: Figura do matplotlib
        """
        fig, ax = plt.subplots(figsize=(10, 8))
        
        if color_by and color_by in df.columns:
            scatter = ax.scatter(df[x], df[y], c=df[color_by], 
                               cmap='viridis', alpha=0.7, s=50)
            plt.colorbar(scatter, label=color_by)
        else:
            ax.scatter(df[x], df[y], color=self.cores_primarias[0], alpha=0.7, s=50)
        
        ax.set_xlabel(x)
        ax.set_ylabel(y)
        ax.set_title(title or f'{y} vs {x}')
        ax.grid(alpha=0.3)
        
        # Linha de tendência
        z = np.polyfit(df[x], df[y], 1)
        p = np.poly1d(z)
        ax.plot(df[x], p(df[x]), "r--", alpha=0.8, linewidth=2)
        
        # Correlação
        corr = df[x].corr(df[y])
        ax.text(0.05, 0.95, f'Correlação: {corr:.3f}', 
               transform=ax.transAxes, fontsize=12,
               bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        plt.tight_layout()
        return fig
    
    def plot_categorias_overview(self, df_categorias: pd.DataFrame) -> plt.Figure:
        """
        Cria overview das categorias disponíveis.
        
        Args:
            df_categorias: DataFrame com categorias
            
        Returns:
            plt.Figure: Figura do matplotlib
        """
        # Contar subcategorias por categoria principal
        contagem = df_categorias.groupby('main_title').size().sort_values(ascending=False)
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 12))
        
        # Top categorias com mais subcategorias
        top_10 = contagem.head(10)
        bars = ax1.bar(range(len(top_10)), top_10.values, 
                      color=self.cores_primarias[0], alpha=0.8)
        ax1.set_xticks(range(len(top_10)))
        ax1.set_xticklabels(top_10.index, rotation=45, ha='right')
        ax1.set_ylabel('Número de Subcategorias')
        ax1.set_title('Top 10 Categorias com Mais Subcategorias', fontweight='bold')
        ax1.grid(axis='y', alpha=0.3)
        
        # Adicionar valores nas barras
        for bar in bars:
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                    f'{int(height)}', ha='center', va='bottom')
        
        # Pizza das principais categorias
        top_5_nomes = [nome[:20] + '...' if len(nome) > 20 else nome for nome in top_10.head(5).index]
        ax2.pie(top_10.head(5).values, labels=top_5_nomes, autopct='%1.1f%%',
               colors=self.cores_primarias)
        ax2.set_title('Distribuição das Top 5 Categorias', fontweight='bold')
        
        plt.tight_layout()
        return fig
    
    def criar_dashboard_interativo(self, df: pd.DataFrame, 
                                  metric: str = 'finalScore') -> go.Figure:
        """
        Cria dashboard interativo com Plotly.
        
        Args:
            df: DataFrame com dados das empresas
            metric: Métrica principal
            
        Returns:
            go.Figure: Figura do Plotly
        """
        # Criar subplots
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Top 10 Empresas', 'Distribuição de Scores', 
                           'Score vs Reclamações Resolvidas', 'Empresas Verificadas'),
            specs=[[{"type": "bar"}, {"type": "histogram"}],
                   [{"type": "scatter"}, {"type": "pie"}]]
        )
        
        # 1. Top 10 empresas
        top_10 = df.nlargest(10, metric)
        fig.add_trace(
            go.Bar(x=top_10[metric], y=top_10['companyName'],
                  orientation='h', name='Score',
                  text=top_10[metric], textposition='auto',
                  marker_color='lightblue'),
            row=1, col=1
        )
        
        # 2. Distribuição de scores
        fig.add_trace(
            go.Histogram(x=df[metric], name='Distribuição',
                        marker_color='lightgreen'),
            row=1, col=2
        )
        
        # 3. Scatter plot (se tiver dados suficientes)
        if 'solvedPercentual' in df.columns:
            fig.add_trace(
                go.Scatter(x=df['solvedPercentual'], y=df[metric],
                          mode='markers', name='Empresas',
                          text=df['companyName'],
                          marker=dict(size=8, color='orange')),
                row=2, col=1
            )
        
        # 4. Pizza empresas verificadas
        if 'isVerified' in df.columns:
            verificadas = df['isVerified'].value_counts()
            fig.add_trace(
                go.Pie(labels=['Verificada', 'Não Verificada'],
                      values=verificadas.values,
                      name="Verificação"),
                row=2, col=2
            )
        
        # Layout
        fig.update_layout(
            title_text="Dashboard - Análise de Empresas",
            showlegend=False,
            height=800
        )
        
        return fig
    
    def salvar_relatorio_pdf(self, figuras: List[plt.Figure], 
                            nome_arquivo: str = "relatorio_analise.pdf"):
        """
        Salva múltiplas figuras em um PDF.
        
        Args:
            figuras: Lista de figuras do matplotlib
            nome_arquivo: Nome do arquivo PDF
        """
        from matplotlib.backends.backend_pdf import PdfPages
        
        with PdfPages(nome_arquivo) as pdf:
            for fig in figuras:
                pdf.savefig(fig, bbox_inches='tight')
        
        print(f"📄 Relatório salvo: {nome_arquivo}")


def exemplo_uso():
    """Exemplo de como usar as funções do notebook."""
    # Inicializar helper
    helper = NotebookHelper()
    helper.configurar_plots()
    
    # Carregar dados
    dados = helper.carregar_dados_basicos()
    
    if 'categorias' in dados:
        print("📊 Criando gráfico de categorias...")
        fig_cat = helper.plot_categorias_overview(dados['categorias'])
        plt.show()
    
    # Procurar primeiro ranking disponível
    for key, df in dados.items():
        if key.startswith('ranking_') and not df.empty:
            print(f"📊 Criando análise para: {key}")
            
            # Top empresas
            fig_top = helper.plot_top_empresas(df, 'finalScore', f'Top Empresas - {key}')
            plt.show()
            
            # Distribuição
            fig_dist = helper.plot_distribuicao_scores(df, 'finalScore')
            plt.show()
            
            # Dashboard interativo
            if len(df) > 1:
                fig_dash = helper.criar_dashboard_interativo(df)
                fig_dash.show()
            
            break


if __name__ == "__main__":
    exemplo_uso()