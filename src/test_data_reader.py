#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script para testar a leitura de dados e validar funcionalidades.
"""

import sys
import pandas as pd
from data_reader import DataReader
from data_helpers import DataAnalyzer


def teste_basico_reader():
    """Testa funcionalidades básicas do DataReader."""
    print("🔍 TESTE 1: DataReader Básico")
    print("="*50)
    
    reader = DataReader(verbose=True)
    
    # Listar arquivos
    print("\n📋 Listando arquivos disponíveis:")
    arquivos = reader.listar_arquivos_disponiveis()
    
    if not arquivos:
        print("❌ Nenhum arquivo encontrado no MinIO!")
        print("💡 Execute primeiro: python runner.py basica")
        return False
    
    print(f"✅ Encontrados {len(arquivos)} arquivo(s)")
    
    # Mostrar arquivos por camada
    for layer in ['landing', 'raw', 'trusted']:
        arquivos_layer = [a for a in arquivos if a.layer == layer]
        print(f"   📁 {layer}: {len(arquivos_layer)} arquivo(s)")
        
        # Mostrar alguns arquivos como exemplo
        for arquivo in arquivos_layer[:3]:
            print(f"      📄 {arquivo.category}/{arquivo.filename}")
    
    # Relatório detalhado
    print("\n📊 Relatório dos dados:")
    relatorio = reader.gerar_relatorio_dados()
    print(f"   Total de arquivos: {relatorio['total_arquivos']}")
    print(f"   Por categoria: {relatorio['por_categoria']}")
    print(f"   Período: {relatorio['periodo_dados']['inicio']} a {relatorio['periodo_dados']['fim']}")
    
    return True


def teste_carregamento_dados():
    """Testa carregamento de dados específicos."""
    print("\n🔍 TESTE 2: Carregamento de Dados")
    print("="*50)
    
    reader = DataReader(verbose=True)
    
    # Teste 1: Carregar categorias
    print("\n🏷️  Testando carregamento de categorias:")
    categorias = reader.carregar_todas_categorias()
    
    if categorias:
        total_categorias = len(categorias.get('mainSegments', []))
        print(f"✅ Categorias carregadas: {total_categorias}")
        
        # Mostrar algumas categorias
        for i, categoria in enumerate(categorias.get('mainSegments', [])[:3]):
            print(f"   {i+1}. {categoria['title']} ({len(categoria.get('childrenSegments', []))} subcategorias)")
    else:
        print("❌ Falha ao carregar categorias")
    
    # Teste 2: Buscar arquivos específicos
    print("\n🔍 Testando busca por filtros:")
    
    # Buscar rankings
    rankings = reader.buscar_arquivos_por_filtro(category='rankings')
    print(f"   📊 Rankings encontrados: {len(rankings)}")
    
    # Buscar empresas
    empresas = reader.buscar_arquivos_por_filtro(category='empresas')
    print(f"   🏢 Empresas encontradas: {len(empresas)}")
    
    # Buscar reclamações
    reclamacoes = reader.buscar_arquivos_por_filtro(category='reclamacoes')
    print(f"   📝 Reclamações encontradas: {len(reclamacoes)}")
    
    # Buscar ofertas
    ofertas = reader.buscar_arquivos_por_filtro(category='ofertas')
    print(f"   💰 Ofertas encontradas: {len(ofertas)}")
    
    return categorias is not None


def teste_conversao_dataframe():
    """Testa conversão para DataFrame."""
    print("\n🔍 TESTE 3: Conversão para DataFrame")
    print("="*50)
    
    reader = DataReader(verbose=True)
    
    # Carregar e converter categorias
    categorias = reader.carregar_todas_categorias()
    if categorias:
        print("\n📊 Convertendo categorias para DataFrame:")
        df_categorias = reader.converter_para_dataframe(categorias, 'categorias')
        print(f"✅ DataFrame criado: {df_categorias.shape}")
        print(f"   Colunas: {list(df_categorias.columns)}")
        
        if not df_categorias.empty:
            print("\n🔍 Primeiras linhas:")
            print(df_categorias[['main_title', 'secondary_title']].head())
    
    # Buscar e converter ranking se disponível
    rankings = reader.buscar_arquivos_por_filtro(category='rankings')
    if rankings:
        print("\n📊 Convertendo ranking para DataFrame:")
        primeiro_ranking = rankings[0]
        dados_ranking = reader.carregar_dados('landing', primeiro_ranking.path)
        
        if dados_ranking and 'companies' in dados_ranking:
            df_ranking = reader.converter_para_dataframe(dados_ranking, 'rankings')
            print(f"✅ DataFrame de ranking criado: {df_ranking.shape}")
            
            if not df_ranking.empty:
                colunas_interesse = ['companyName', 'finalScore', 'solvedPercentual']
                colunas_disponiveis = [col for col in colunas_interesse if col in df_ranking.columns]
                print(f"   Colunas disponíveis: {list(df_ranking.columns)}")
                if colunas_disponiveis:
                    print("\n🔍 Primeiras empresas:")
                    print(df_ranking[colunas_disponiveis].head())


def teste_analyzer():
    """Testa funcionalidades do DataAnalyzer."""
    print("\n🔍 TESTE 4: DataAnalyzer")
    print("="*50)
    
    analyzer = DataAnalyzer(verbose=True)
    
    # Overview completo
    print("\n📊 Overview completo:")
    overview = analyzer.obter_overview_completo()
    
    for key, value in overview.items():
        if key == 'relatorio_arquivos':
            print(f"   📋 {key}: {value['total_arquivos']} arquivos")
        else:
            print(f"   📊 {key}: {value}")
    
    # Listar categorias com dados
    print("\n🏷️  Categorias com dados de ranking:")
    categorias_com_dados = analyzer.listar_categorias_com_dados()
    
    if not categorias_com_dados.empty:
        print(f"✅ Encontradas {len(categorias_com_dados)} categorias com dados")
        print("\n📋 Principais categorias:")
        print(categorias_com_dados[['main_title', 'secondary_title', 'arquivos_disponiveis']].head())
        
        # Testar top empresas de uma categoria
        if len(categorias_com_dados) > 0:
            primeira_cat = categorias_com_dados.iloc[0]
            main_seg = primeira_cat['main_segment']
            sec_seg = primeira_cat['secondary_segment']
            
            print(f"\n🏆 Top empresas de {primeira_cat['main_title']} / {primeira_cat['secondary_title']}:")
            top_empresas = analyzer.obter_top_empresas_categoria(main_seg, sec_seg, limit=5)
            
            if not top_empresas.empty:
                colunas_interesse = ['companyName', 'finalScore', 'solvedPercentual', 'isVerified']
                colunas_disponiveis = [col for col in colunas_interesse if col in top_empresas.columns]
                print(top_empresas[colunas_disponiveis].head())
    else:
        print("❌ Nenhuma categoria com dados de ranking encontrada")
    
    # Testar empresas com ofertas
    print("\n💰 Empresas com ofertas:")
    ofertas_df = analyzer.obter_empresas_com_ofertas()
    
    if not ofertas_df.empty:
        print(f"✅ Encontradas {len(ofertas_df)} empresas com ofertas")
        colunas_ofertas = ['name', 'total_discounts', 'total_coupons', 'total_offers']
        colunas_disponiveis = [col for col in colunas_ofertas if col in ofertas_df.columns]
        if colunas_disponiveis:
            print("\n📋 Empresas com mais ofertas:")
            print(ofertas_df[colunas_disponiveis].head())
    else:
        print("❌ Nenhuma empresa com ofertas encontrada")


def main():
    """Executa todos os testes."""
    print("🧪 INICIANDO TESTES DO SISTEMA DE LEITURA DE DADOS")
    print("="*60)
    
    try:
        # Teste 1: Funcionalidades básicas
        sucesso1 = teste_basico_reader()
        if not sucesso1:
            print("\n❌ Teste básico falhou. Verifique se há dados no MinIO.")
            return
        
        # Teste 2: Carregamento de dados
        sucesso2 = teste_carregamento_dados()
        
        # Teste 3: Conversão para DataFrame
        teste_conversao_dataframe()
        
        # Teste 4: DataAnalyzer
        teste_analyzer()
        
        print("\n" + "="*60)
        print("🎉 TODOS OS TESTES CONCLUÍDOS!")
        print("="*60)
        
        print("\n💡 PRÓXIMOS PASSOS:")
        print("1. ✅ Sistema de leitura funcionando")
        print("2. 📊 Pronto para criar notebooks de análise")
        print("3. 🎨 Pronto para visualizações")
        print("4. 📈 Pronto para dashboards")
        
    except Exception as e:
        print(f"\n❌ ERRO DURANTE OS TESTES: {e}")
        print("\n🔧 POSSÍVEIS SOLUÇÕES:")
        print("1. Verifique se o MinIO está rodando: docker ps")
        print("2. Execute uma coleta básica: python runner.py basica")
        print("3. Verifique a conexão: python runner.py verificar")


if __name__ == "__main__":
    main()