#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Módulo para leitura de dados das camadas do MinIO.
Facilita o acesso aos dados coletados para análises.
"""

import os
import json
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass

from minio_client import MinIOClient


@dataclass
class DataFile:
    """Representa um arquivo de dados no MinIO."""
    path: str
    layer: str
    category: str
    filename: str
    date: str
    size_mb: float = 0.0


class DataReader:
    """
    Classe principal para leitura de dados do MinIO.
    """
    
    def __init__(self, verbose: bool = True):
        """
        Inicializa o leitor de dados.
        
        Args:
            verbose: Se True, exibe logs detalhados
        """
        self.minio = MinIOClient()
        self.verbose = verbose
        
        # Cache para evitar múltiplas requisições
        self._file_cache = {}
        self._data_cache = {}
    
    def listar_arquivos_disponiveis(self, layer: str = None, category: str = None) -> List[DataFile]:
        """
        Lista todos os arquivos disponíveis no MinIO.
        
        Args:
            layer: Filtrar por camada (landing, raw, trusted)
            category: Filtrar por categoria (categorias, empresas, etc.)
            
        Returns:
            List[DataFile]: Lista de arquivos encontrados
        """
        arquivos = []
        layers = [layer] if layer else ['landing', 'raw', 'trusted']
        
        for current_layer in layers:
            if self.verbose:
                print(f"🔍 Buscando arquivos na camada: {current_layer}")
            
            try:
                objects = self.minio.list_objects(current_layer, category)
                
                for obj_path in objects:
                    # Extrair informações do caminho
                    parts = obj_path.split('/')
                    if len(parts) >= 4:  # categoria/ano/mes/dia/arquivo.json
                        cat = parts[0]
                        filename = parts[-1]
                        date_part = '/'.join(parts[1:4])  # ano/mes/dia
                        
                        arquivo = DataFile(
                            path=obj_path,
                            layer=current_layer,
                            category=cat,
                            filename=filename,
                            date=date_part
                        )
                        arquivos.append(arquivo)
                
                if self.verbose:
                    print(f"   ✅ Encontrados {len([a for a in arquivos if a.layer == current_layer])} arquivos")
                    
            except Exception as e:
                if self.verbose:
                    print(f"   ❌ Erro ao listar {current_layer}: {e}")
        
        # Ordenar por data (mais recente primeiro)
        arquivos.sort(key=lambda x: x.date, reverse=True)
        return arquivos
    
    def buscar_arquivos_por_filtro(self, **filtros) -> List[DataFile]:
        """
        Busca arquivos por filtros específicos.
        
        Args:
            layer: Camada (landing, raw, trusted)
            category: Categoria (categorias, empresas, etc.)
            data_inicio: Data início (YYYY/MM/DD)
            data_fim: Data fim (YYYY/MM/DD)
            filename_contains: Texto que deve estar no nome do arquivo
            
        Returns:
            List[DataFile]: Arquivos que atendem aos filtros
        """
        arquivos = self.listar_arquivos_disponiveis()
        resultado = []
        
        for arquivo in arquivos:
            # Aplicar filtros
            if 'layer' in filtros and arquivo.layer != filtros['layer']:
                continue
            if 'category' in filtros and arquivo.category != filtros['category']:
                continue
            if 'data_inicio' in filtros and arquivo.date < filtros['data_inicio']:
                continue
            if 'data_fim' in filtros and arquivo.date > filtros['data_fim']:
                continue
            if 'filename_contains' in filtros and filtros['filename_contains'] not in arquivo.filename:
                continue
            
            resultado.append(arquivo)
        
        return resultado
    
    def carregar_dados(self, layer: str, object_path: str, use_cache: bool = True) -> Optional[Dict]:
        """
        Carrega dados de um arquivo específico.
        
        Args:
            layer: Camada do arquivo
            object_path: Caminho do objeto no MinIO
            use_cache: Se deve usar cache para evitar downloads repetidos
            
        Returns:
            Dict: Dados JSON carregados ou None se erro
        """
        cache_key = f"{layer}:{object_path}"
        
        # Verificar cache
        if use_cache and cache_key in self._data_cache:
            if self.verbose:
                print(f"📋 Carregando do cache: {object_path}")
            return self._data_cache[cache_key]
        
        # Carregar do MinIO
        if self.verbose:
            print(f"📥 Carregando: {layer}/{object_path}")
        
        dados = self.minio.download_json(layer, object_path)
        
        if dados and use_cache:
            self._data_cache[cache_key] = dados
        
        return dados
    
    def carregar_ultima_coleta(self, category: str, layer: str = 'landing') -> Optional[Dict]:
        """
        Carrega a coleta mais recente de uma categoria.
        
        Args:
            category: Categoria dos dados
            layer: Camada a buscar
            
        Returns:
            Dict: Dados da coleta mais recente
        """
        arquivos = self.buscar_arquivos_por_filtro(layer=layer, category=category)
        
        if not arquivos:
            if self.verbose:
                print(f"❌ Nenhum arquivo encontrado para {category} na camada {layer}")
            return None
        
        # Pegar o mais recente
        arquivo_recente = arquivos[0]
        if self.verbose:
            print(f"📅 Arquivo mais recente: {arquivo_recente.filename} ({arquivo_recente.date})")
        
        return self.carregar_dados(layer, arquivo_recente.path)
    
    def carregar_todas_categorias(self, layer: str = 'landing') -> Optional[Dict]:
        """
        Carrega dados de todas as categorias (última coleta).
        
        Args:
            layer: Camada a buscar
            
        Returns:
            Dict: Dados das categorias
        """
        return self.carregar_ultima_coleta('categorias', layer)
    
    def carregar_rankings_categoria(self, main_segment: str, secondary_segment: str, 
                                   layer: str = 'landing') -> List[Dict]:
        """
        Carrega rankings de uma categoria específica.
        
        Args:
            main_segment: Segmento principal
            secondary_segment: Segmento secundário  
            layer: Camada a buscar
            
        Returns:
            List[Dict]: Lista de dados de ranking encontrados
        """
        # Buscar arquivos de ranking que contenham os segmentos
        filtro_nome = f"ranking_{main_segment}_{secondary_segment}"
        arquivos = self.buscar_arquivos_por_filtro(
            layer=layer, 
            category='rankings',
            filename_contains=filtro_nome
        )
        
        resultados = []
        for arquivo in arquivos:
            dados = self.carregar_dados(layer, arquivo.path)
            if dados:
                resultados.append({
                    'data_coleta': arquivo.date,
                    'arquivo': arquivo.filename,
                    'dados': dados
                })
        
        return resultados
    
    def carregar_dados_empresa(self, shortname: str, layer: str = 'landing') -> Optional[Dict]:
        """
        Carrega dados detalhados de uma empresa.
        
        Args:
            shortname: Nome curto da empresa
            layer: Camada a buscar
            
        Returns:
            Dict: Dados da empresa
        """
        arquivos = self.buscar_arquivos_por_filtro(
            layer=layer,
            category='empresas',
            filename_contains=f"empresa_{shortname}"
        )
        
        if arquivos:
            return self.carregar_dados(layer, arquivos[0].path)
        
        return None
    
    def carregar_reclamacoes_empresa(self, company_id: str, layer: str = 'landing') -> List[Dict]:
        """
        Carrega reclamações de uma empresa.
        
        Args:
            company_id: ID da empresa
            layer: Camada a buscar
            
        Returns:
            List[Dict]: Lista de dados de reclamações
        """
        arquivos = self.buscar_arquivos_por_filtro(
            layer=layer,
            category='reclamacoes',
            filename_contains=company_id
        )
        
        resultados = []
        for arquivo in arquivos:
            dados = self.carregar_dados(layer, arquivo.path)
            if dados:
                resultados.append({
                    'data_coleta': arquivo.date,
                    'tipo': 'avaliadas' if 'avaliadas' in arquivo.filename else 'todas',
                    'dados': dados
                })
        
        return resultados
    
    def gerar_relatorio_dados(self) -> Dict[str, Any]:
        """
        Gera um relatório dos dados disponíveis.
        
        Returns:
            Dict: Relatório completo dos dados
        """
        if self.verbose:
            print("📊 Gerando relatório dos dados disponíveis...")
        
        arquivos = self.listar_arquivos_disponiveis()
        
        relatorio = {
            'total_arquivos': len(arquivos),
            'por_camada': {},
            'por_categoria': {},
            'periodo_dados': {
                'inicio': None,
                'fim': None
            },
            'arquivos_recentes': []
        }
        
        # Agrupar por camada
        for arquivo in arquivos:
            # Por camada
            if arquivo.layer not in relatorio['por_camada']:
                relatorio['por_camada'][arquivo.layer] = 0
            relatorio['por_camada'][arquivo.layer] += 1
            
            # Por categoria
            if arquivo.category not in relatorio['por_categoria']:
                relatorio['por_categoria'][arquivo.category] = 0
            relatorio['por_categoria'][arquivo.category] += 1
        
        # Período dos dados
        if arquivos:
            datas = [arquivo.date for arquivo in arquivos]
            relatorio['periodo_dados']['inicio'] = min(datas)
            relatorio['periodo_dados']['fim'] = max(datas)
            
            # Arquivos mais recentes (últimos 10)
            relatorio['arquivos_recentes'] = [
                {
                    'arquivo': arq.filename,
                    'categoria': arq.category,
                    'camada': arq.layer,
                    'data': arq.date
                }
                for arq in arquivos[:10]
            ]
        
        return relatorio
    
    def converter_para_dataframe(self, dados: Dict, tipo: str = 'auto') -> pd.DataFrame:
        """
        Converte dados JSON para DataFrame do pandas.
        
        Args:
            dados: Dados JSON
            tipo: Tipo dos dados (categorias, empresas, rankings, auto)
            
        Returns:
            pd.DataFrame: DataFrame pronto para análise
        """
        if tipo == 'auto':
            # Tentar detectar o tipo automaticamente
            if 'mainSegments' in dados:
                tipo = 'categorias'
            elif 'companies' in dados:
                tipo = 'rankings'
            elif isinstance(dados, list) and dados and 'company_info' in dados[0]:
                tipo = 'ofertas'
        
        try:
            if tipo == 'categorias':
                # Processar dados de categorias
                categorias = []
                for seg in dados.get('mainSegments', []):
                    for subseg in seg.get('childrenSegments', []):
                        categorias.append({
                            'main_segment': seg['shortname'],
                            'main_title': seg['title'],
                            'secondary_segment': subseg['shortname'],
                            'secondary_title': subseg['title'],
                            'main_icon': seg.get('icon'),
                            'secondary_icon': subseg.get('icon')
                        })
                return pd.DataFrame(categorias)
            
            elif tipo == 'rankings':
                # Processar dados de ranking
                empresas = dados.get('companies', [])
                return pd.DataFrame(empresas)
            
            elif tipo == 'ofertas':
                # Processar dados de ofertas
                empresas_ofertas = []
                for item in dados:
                    if 'company_info' in item:
                        empresa = item['company_info'].copy()
                        empresa.update({
                            'total_discounts': item.get('total_discounts', 0),
                            'total_coupons': item.get('total_coupons', 0),
                            'total_offers': item.get('total_offers', 0)
                        })
                        empresas_ofertas.append(empresa)
                return pd.DataFrame(empresas_ofertas)
            
            else:
                # Tentar conversão genérica
                if isinstance(dados, list):
                    return pd.DataFrame(dados)
                elif isinstance(dados, dict) and len(dados) == 1:
                    key = list(dados.keys())[0]
                    return pd.DataFrame(dados[key])
                else:
                    return pd.DataFrame([dados])
                    
        except Exception as e:
            if self.verbose:
                print(f"⚠️  Erro na conversão para DataFrame: {e}")
            # Fallback: tentar conversão simples
            return pd.DataFrame([dados])
    
    def limpar_cache(self):
        """Limpa o cache de dados."""
        self._data_cache.clear()
        self._file_cache.clear()
        if self.verbose:
            print("🧹 Cache limpo")


def main():
    """Função para testar o módulo."""
    print("🧪 Testando o DataReader...")
    
    reader = DataReader(verbose=True)
    
    # Teste 1: Listar arquivos
    print("\n📋 1. Listando arquivos disponíveis:")
    arquivos = reader.listar_arquivos_disponiveis()
    print(f"Total de arquivos encontrados: {len(arquivos)}")
    
    # Teste 2: Relatório
    print("\n📊 2. Gerando relatório:")
    relatorio = reader.gerar_relatorio_dados()
    print(f"Arquivos por camada: {relatorio['por_camada']}")
    print(f"Arquivos por categoria: {relatorio['por_categoria']}")
    
    # Teste 3: Carregar última coleta de categorias
    print("\n🏷️  3. Carregando categorias:")
    categorias = reader.carregar_todas_categorias()
    if categorias:
        print(f"Categorias carregadas: {len(categorias.get('mainSegments', []))}")
        
        # Teste 4: Converter para DataFrame
        print("\n🔄 4. Convertendo para DataFrame:")
        df = reader.converter_para_dataframe(categorias, 'categorias')
        print(f"DataFrame criado: {df.shape}")
        print(df.head())
    
    print("\n✅ Testes concluídos!")


if __name__ == "__main__":
    main()