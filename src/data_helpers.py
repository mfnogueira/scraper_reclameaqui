#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Funções helper para facilitar análises comuns com os dados do Reclame Aqui.
"""

import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from data_reader import DataReader


class DataAnalyzer:
    """
    Classe com funções helper para análises comuns.
    """
    
    def __init__(self, verbose: bool = True):
        """
        Inicializa o analisador.
        
        Args:
            verbose: Se True, exibe logs detalhados
        """
        self.reader = DataReader(verbose=verbose)
        self.verbose = verbose
    
    def obter_overview_completo(self) -> Dict[str, Any]:
        """
        Obtém uma visão geral completa dos dados disponíveis.
        
        Returns:
            Dict: Overview completo dos dados
        """
        if self.verbose:
            print("🔍 Gerando overview completo dos dados...")
        
        overview = {
            'relatorio_arquivos': self.reader.gerar_relatorio_dados(),
            'categorias_disponiveis': None,
            'empresas_com_ranking': 0,
            'empresas_com_ofertas': 0,
            'total_reclamacoes': 0
        }
        
        # Carregar categorias
        categorias = self.reader.carregar_todas_categorias()
        if categorias:
            overview['categorias_disponiveis'] = len(categorias.get('mainSegments', []))
        
        # Contar empresas com ranking
        arquivos_ranking = self.reader.buscar_arquivos_por_filtro(category='rankings')
        overview['empresas_com_ranking'] = len(arquivos_ranking)
        
        # Contar empresas com ofertas
        arquivos_ofertas = self.reader.buscar_arquivos_por_filtro(category='ofertas')
        overview['empresas_com_ofertas'] = len(arquivos_ofertas)
        
        # Contar reclamações
        arquivos_reclamacoes = self.reader.buscar_arquivos_por_filtro(category='reclamacoes')
        overview['total_reclamacoes'] = len(arquivos_reclamacoes)
        
        return overview
    
    def listar_categorias_com_dados(self) -> pd.DataFrame:
        """
        Lista todas as categorias que têm dados de ranking.
        
        Returns:
            pd.DataFrame: Categorias com dados disponíveis
        """
        categorias = self.reader.carregar_todas_categorias()
        if not categorias:
            return pd.DataFrame()
        
        # Buscar arquivos de ranking para ver quais categorias têm dados
        arquivos_ranking = self.reader.buscar_arquivos_por_filtro(category='rankings')
        categorias_com_dados = set()
        
        for arquivo in arquivos_ranking:
            # Extrair categoria do nome do arquivo
            if 'ranking_' in arquivo.filename:
                parts = arquivo.filename.replace('ranking_', '').replace('.json', '').split('_')
                if len(parts) >= 2:
                    main_seg = parts[0]
                    sec_seg = parts[1] if len(parts) > 1 else ''
                    categorias_com_dados.add((main_seg, sec_seg))
        
        # Converter categorias para DataFrame
        df_categorias = self.reader.converter_para_dataframe(categorias, 'categorias')
        
        # Filtrar apenas categorias que têm dados
        df_filtrado = df_categorias[
            df_categorias.apply(
                lambda row: (row['main_segment'], row['secondary_segment']) in categorias_com_dados,
                axis=1
            )
        ].copy()
        
        # Adicionar contagem de arquivos
        df_filtrado['arquivos_disponiveis'] = df_filtrado.apply(
            lambda row: len([
                arq for arq in arquivos_ranking 
                if f"{row['main_segment']}_{row['secondary_segment']}" in arq.filename
            ]),
            axis=1
        )
        
        return df_filtrado.sort_values('arquivos_disponiveis', ascending=False)
    
    def obter_top_empresas_categoria(self, main_segment: str, secondary_segment: str,
                                   limit: int = 10) -> pd.DataFrame:
        """
        Obtém as top empresas de uma categoria específica.
        
        Args:
            main_segment: Segmento principal
            secondary_segment: Segmento secundário
            limit: Limite de empresas
            
        Returns:
            pd.DataFrame: Top empresas da categoria
        """
        rankings = self.reader.carregar_rankings_categoria(main_segment, secondary_segment)
        
        if not rankings:
            if self.verbose:
                print(f"❌ Nenhum ranking encontrado para {main_segment}/{secondary_segment}")
            return pd.DataFrame()
        
        # Pegar o ranking mais recente
        ranking_recente = rankings[0]['dados']
        
        if 'companies' not in ranking_recente:
            if self.verbose:
                print("❌ Dados de empresas não encontrados no ranking")
            return pd.DataFrame()
        
        # Converter para DataFrame
        df = pd.DataFrame(ranking_recente['companies'][:limit])
        
        # Adicionar informações da categoria
        df['main_segment'] = main_segment
        df['secondary_segment'] = secondary_segment
        df['data_coleta'] = rankings[0]['data_coleta']
        
        return df
    
    def comparar_categorias(self, categorias: List[Tuple[str, str]], 
                           metric: str = 'finalScore') -> pd.DataFrame:
        """
        Compara métricas entre diferentes categorias.
        
        Args:
            categorias: Lista de tuplas (main_segment, secondary_segment)
            metric: Métrica para comparar (finalScore, solvedPercentual, etc.)
            
        Returns:
            pd.DataFrame: Comparação entre categorias
        """
        resultados = []
        
        for main_seg, sec_seg in categorias:
            df_categoria = self.obter_top_empresas_categoria(main_seg, sec_seg, limit=50)
            
            if not df_categoria.empty and metric in df_categoria.columns:
                stats = {
                    'main_segment': main_seg,
                    'secondary_segment': sec_seg,
                    'categoria_completa': f"{main_seg}/{sec_seg}",
                    'total_empresas': len(df_categoria),
                    f'{metric}_media': df_categoria[metric].mean(),
                    f'{metric}_mediana': df_categoria[metric].median(),
                    f'{metric}_min': df_categoria[metric].min(),
                    f'{metric}_max': df_categoria[metric].max(),
                    f'{metric}_std': df_categoria[metric].std()
                }
                resultados.append(stats)
        
        return pd.DataFrame(resultados).sort_values(f'{metric}_media', ascending=False)
    
    def obter_empresas_com_ofertas(self) -> pd.DataFrame:
        """
        Obtém dados de empresas que têm ofertas/cupons.
        
        Returns:
            pd.DataFrame: Empresas com ofertas
        """
        # Carregar dados de ofertas mais recentes
        ofertas_data = self.reader.carregar_ultima_coleta('ofertas')
        
        if not ofertas_data:
            if self.verbose:
                print("❌ Dados de ofertas não encontrados")
            return pd.DataFrame()
        
        # Verificar estrutura dos dados
        if isinstance(ofertas_data, dict) and 'empresas' in ofertas_data:
            empresas = ofertas_data['empresas']
        elif isinstance(ofertas_data, list):
            empresas = ofertas_data
        else:
            if self.verbose:
                print("❌ Estrutura de dados de ofertas não reconhecida")
            return pd.DataFrame()
        
        # Converter para DataFrame
        df = self.reader.converter_para_dataframe(empresas, 'ofertas')
        
        # Filtrar apenas empresas com ofertas
        if 'total_offers' in df.columns:
            df = df[df['total_offers'] > 0]
        elif 'total_discounts' in df.columns:
            df = df[df['total_discounts'] > 0]
        
        return df.sort_values('total_discounts', ascending=False)
    
    def buscar_empresa_completa(self, identificador: str, 
                               tipo: str = 'auto') -> Dict[str, Any]:
        """
        Busca dados completos de uma empresa (perfil + reclamações + ofertas).
        
        Args:
            identificador: ID, shortname ou nome da empresa
            tipo: Tipo do identificador (auto, shortname, id, nome)
            
        Returns:
            Dict: Dados completos da empresa
        """
        resultado = {
            'empresa_encontrada': False,
            'dados_empresa': None,
            'reclamacoes': [],
            'ofertas': None,
            'rankings': []
        }
        
        # Buscar dados da empresa
        if tipo in ['auto', 'shortname']:
            dados_empresa = self.reader.carregar_dados_empresa(identificador)
            if dados_empresa:
                resultado['empresa_encontrada'] = True
                resultado['dados_empresa'] = dados_empresa
        
        # Se encontrou a empresa, buscar dados complementares
        if resultado['empresa_encontrada']:
            empresa_id = resultado['dados_empresa'].get('id')
            shortname = resultado['dados_empresa'].get('shortname', identificador)
            
            # Buscar reclamações
            if empresa_id:
                reclamacoes = self.reader.carregar_reclamacoes_empresa(empresa_id)
                resultado['reclamacoes'] = reclamacoes
            
            # Buscar ofertas
            ofertas_df = self.obter_empresas_com_ofertas()
            if not ofertas_df.empty:
                # Procurar empresa nas ofertas
                empresa_ofertas = ofertas_df[
                    (ofertas_df['short_name'] == shortname) |
                    (ofertas_df['name'] == resultado['dados_empresa'].get('companyName', ''))
                ]
                if not empresa_ofertas.empty:
                    resultado['ofertas'] = empresa_ofertas.iloc[0].to_dict()
        
        return resultado
    
    def gerar_dataset_analise(self, incluir_ofertas: bool = True,
                             incluir_reclamacoes: bool = False) -> pd.DataFrame:
        """
        Gera um dataset consolidado para análises.
        
        Args:
            incluir_ofertas: Se deve incluir dados de ofertas
            incluir_reclamacoes: Se deve incluir contagem de reclamações
            
        Returns:
            pd.DataFrame: Dataset consolidado
        """
        if self.verbose:
            print("🔄 Gerando dataset consolidado para análises...")
        
        # Buscar todas as categorias com dados
        categorias_df = self.listar_categorias_com_dados()
        
        todas_empresas = []
        
        # Para cada categoria, buscar as empresas
        for _, categoria in categorias_df.iterrows():
            main_seg = categoria['main_segment']
            sec_seg = categoria['secondary_segment']
            
            empresas_cat = self.obter_top_empresas_categoria(main_seg, sec_seg, limit=20)
            if not empresas_cat.empty:
                todas_empresas.append(empresas_cat)
        
        if not todas_empresas:
            return pd.DataFrame()
        
        # Consolidar todas as empresas
        df_final = pd.concat(todas_empresas, ignore_index=True)
        
        # Remover duplicatas (mesma empresa em múltiplas categorias)
        df_final = df_final.drop_duplicates(subset=['id'], keep='first')
        
        # Incluir dados de ofertas se solicitado
        if incluir_ofertas:
            ofertas_df = self.obter_empresas_com_ofertas()
            if not ofertas_df.empty:
                # Fazer merge com dados de ofertas
                df_final = df_final.merge(
                    ofertas_df[['short_name', 'total_discounts', 'total_coupons', 'total_offers']],
                    left_on='companyShortname',
                    right_on='short_name',
                    how='left'
                )
                # Preencher valores faltantes com 0
                df_final[['total_discounts', 'total_coupons', 'total_offers']] = \
                    df_final[['total_discounts', 'total_coupons', 'total_offers']].fillna(0)
        
        if self.verbose:
            print(f"✅ Dataset gerado com {len(df_final)} empresas")
        
        return df_final


def main():
    """Função para testar as funções helper."""
    print("🧪 Testando DataAnalyzer...")
    
    analyzer = DataAnalyzer(verbose=True)
    
    # Teste 1: Overview completo
    print("\n📊 1. Overview completo:")
    overview = analyzer.obter_overview_completo()
    print(f"Categorias disponíveis: {overview['categorias_disponiveis']}")
    print(f"Arquivos de ranking: {overview['empresas_com_ranking']}")
    
    # Teste 2: Categorias com dados
    print("\n🏷️  2. Categorias com dados:")
    categorias_df = analyzer.listar_categorias_com_dados()
    if not categorias_df.empty:
        print(f"Encontradas {len(categorias_df)} categorias com dados")
        print(categorias_df[['main_title', 'secondary_title', 'arquivos_disponiveis']].head())
    
    # Teste 3: Top empresas de uma categoria
    if not categorias_df.empty:
        primeira_categoria = categorias_df.iloc[0]
        main_seg = primeira_categoria['main_segment']
        sec_seg = primeira_categoria['secondary_segment']
        
        print(f"\n🏆 3. Top empresas de {main_seg}/{sec_seg}:")
        top_empresas = analyzer.obter_top_empresas_categoria(main_seg, sec_seg, limit=5)
        if not top_empresas.empty:
            print(top_empresas[['companyName', 'finalScore', 'solvedPercentual']].head())
    
    # Teste 4: Empresas com ofertas
    print("\n💰 4. Empresas com ofertas:")
    ofertas_df = analyzer.obter_empresas_com_ofertas()
    if not ofertas_df.empty:
        print(f"Encontradas {len(ofertas_df)} empresas com ofertas")
        colunas_ofertas = ['name', 'total_discounts', 'total_coupons', 'total_offers']
        colunas_disponiveis = [col for col in colunas_ofertas if col in ofertas_df.columns]
        print(ofertas_df[colunas_disponiveis].head())
    
    print("\n✅ Testes das funções helper concluídos!")


if __name__ == "__main__":
    main()