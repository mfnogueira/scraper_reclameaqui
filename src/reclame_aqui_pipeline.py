#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Pipeline principal para coleta de dados do Reclame Aqui.
Integra coleta de dados com armazenamento no MinIO.
"""

import time
import random
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import cloudscraper

from minio_client import MinIOClient


class ReclameAquiPipeline:
    """
    Pipeline completa para coleta e armazenamento de dados do Reclame Aqui.
    """
    
    def __init__(self, tempo_espera_min: int = 3, tempo_espera_max: int = 7, verbose: bool = True):
        """
        Inicializa a pipeline.
        
        Args:
            tempo_espera_min: Tempo mínimo entre requisições (segundos)
            tempo_espera_max: Tempo máximo entre requisições (segundos)
            verbose: Se True, exibe logs detalhados
        """
        self.tempo_espera_min = tempo_espera_min
        self.tempo_espera_max = tempo_espera_max
        self.verbose = verbose
        
        # Cliente MinIO
        self.minio = MinIOClient()
        
        # User agents para rotação
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0"
        ]
        
        # Estatísticas da execução
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'data_collected': {},
            'start_time': None,
            'end_time': None
        }
    
    def _criar_scraper(self):
        """Cria uma nova instância do CloudScraper."""
        user_agent = random.choice(self.user_agents)
        
        scraper = cloudscraper.create_scraper(
            browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True},
            delay=5
        )
        
        headers = {
            "User-Agent": user_agent,
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            "Origin": "https://www.reclameaqui.com.br",
            "Referer": "https://www.reclameaqui.com.br/"
        }
        
        scraper.headers.update(headers)
        return scraper
    
    def _fazer_requisicao(self, url: str) -> Optional[Dict]:
        """
        Faz requisição com controle de tempo e tratamento de erros.
        
        Args:
            url: URL da API
            
        Returns:
            Dict ou None: Dados JSON ou None em caso de erro
        """
        self.stats['total_requests'] += 1
        scraper = self._criar_scraper()
        
        try:
            if self.verbose:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Coletando: {url}")
            
            # Pausa aleatória
            pausa = random.uniform(self.tempo_espera_min, self.tempo_espera_max)
            time.sleep(pausa)
            
            response = scraper.get(url, timeout=30)
            response.raise_for_status()
            
            dados = response.json()
            self.stats['successful_requests'] += 1
            
            if self.verbose:
                print(f"✅ Sucesso - {len(str(dados))} chars")
            
            return dados
            
        except Exception as e:
            self.stats['failed_requests'] += 1
            if self.verbose:
                print(f"❌ Erro: {str(e)}")
            return None
    
    def coletar_categorias(self) -> bool:
        """
        Coleta todas as categorias e salva na camada landing.
        
        Returns:
            bool: True se sucesso, False caso contrário
        """
        if self.verbose:
            print("\n🏷️  Coletando categorias...")
        
        url = "https://iosearch.reclameaqui.com.br/raichu-io-site-search-v1/segments/main"
        dados = self._fazer_requisicao(url)
        
        if dados:
            path = self.minio.upload_json(dados, 'landing', 'categorias')
            if path:
                self.stats['data_collected']['categorias'] = len(dados.get('mainSegments', []))
                return True
        
        return False
    
    def coletar_ofertas_empresas(self) -> bool:
        """
        Coleta ofertas/cupons de empresas e salva na camada landing.
        
        Returns:
            bool: True se sucesso, False caso contrário
        """
        if self.verbose:
            print("\n💰 Coletando ofertas de empresas...")
        
        url = "https://ramais-api.reclameaqui.com.br/v1/discounts/summary"
        dados = self._fazer_requisicao(url)
        
        if dados and isinstance(dados, list):
            path = self.minio.upload_json({'empresas': dados}, 'landing', 'ofertas')
            if path:
                self.stats['data_collected']['ofertas'] = len(dados)
                return True
        
        return False
    
    def coletar_ranking_categoria(self, main_segment: str, secondary_segment: str, 
                                 pagina: int = 1, quantidade: int = 20) -> Optional[Dict]:
        """
        Coleta ranking de empresas de uma categoria específica.
        
        Args:
            main_segment: Segmento principal
            secondary_segment: Segmento secundário
            pagina: Página do ranking
            quantidade: Quantidade de empresas
            
        Returns:
            Dict: Dados do ranking ou None
        """
        if self.verbose:
            print(f"\n🏆 Coletando ranking: {main_segment}/{secondary_segment}")
        
        url = f"https://api.reclameaqui.com.br/segments/api/ranking/best-verified/{main_segment}/{secondary_segment}?page={pagina}&size={quantidade}"
        dados = self._fazer_requisicao(url)
        
        if dados:
            filename = f"ranking_{main_segment}_{secondary_segment}_{pagina}.json"
            path = self.minio.upload_json(dados, 'landing', 'rankings', filename)
            
            if path and 'companies' in dados:
                empresas_count = len(dados['companies'])
                self.stats['data_collected'][f'ranking_{main_segment}_{secondary_segment}'] = empresas_count
                return dados
        
        return None
    
    def coletar_empresa_detalhada(self, shortname: str) -> Optional[Dict]:
        """
        Coleta dados detalhados de uma empresa específica.
        
        Args:
            shortname: Nome curto da empresa
            
        Returns:
            Dict: Dados da empresa ou None
        """
        if self.verbose:
            print(f"\n🏢 Coletando empresa: {shortname}")
        
        url = f"https://iosite.reclameaqui.com.br/raichu-io-site-v1/company/shortname/{shortname}"
        dados = self._fazer_requisicao(url)
        
        if dados:
            filename = f"empresa_{shortname}.json"
            path = self.minio.upload_json(dados, 'landing', 'empresas', filename)
            
            if path:
                return dados
        
        return None
    
    def coletar_reclamacoes(self, company_id: str, quantidade: int = 20) -> Optional[Dict]:
        """
        Coleta reclamações de uma empresa.
        
        Args:
            company_id: ID da empresa
            quantidade: Quantidade de reclamações
            
        Returns:
            Dict: Dados das reclamações ou None
        """
        if self.verbose:
            print(f"\n📝 Coletando reclamações: {company_id}")
        
        # Tentar primeiro reclamações avaliadas
        url = f"https://iosearch.reclameaqui.com.br/raichu-io-site-search-v1/query/companyComplains/{quantidade}/20?company={company_id}&evaluated=bool:true"
        dados = self._fazer_requisicao(url)
        
        if dados:
            filename = f"reclamacoes_{company_id}.json"
            path = self.minio.upload_json(dados, 'landing', 'reclamacoes', filename)
            
            if path:
                # Contar reclamações encontradas
                reclamacoes = 0
                if ('complainResult' in dados and 
                    'complains' in dados['complainResult'] and 
                    'data' in dados['complainResult']['complains']):
                    reclamacoes = len(dados['complainResult']['complains']['data'])
                
                self.stats['data_collected'][f'reclamacoes_{company_id}'] = reclamacoes
                return dados
        
        return None
    
    def executar_pipeline_basica(self, limite_categorias: int = 3, 
                                limite_empresas: int = 5) -> Dict:
        """
        Executa uma pipeline básica de coleta de dados.
        
        Args:
            limite_categorias: Quantas categorias processar
            limite_empresas: Quantas empresas por categoria
            
        Returns:
            Dict: Estatísticas da execução
        """
        self.stats['start_time'] = datetime.now()
        
        if self.verbose:
            print("🚀 Iniciando Pipeline Reclame Aqui")
            print("=" * 50)
        
        # 1. Coletar categorias
        sucesso_categorias = self.coletar_categorias()
        if not sucesso_categorias:
            if self.verbose:
                print("❌ Falha ao coletar categorias. Abortando pipeline.")
            return self.stats
        
        # 2. Coletar ofertas
        self.coletar_ofertas_empresas()
        
        # 3. Buscar dados da camada landing para processar categorias
        try:
            categorias_objects = self.minio.list_objects('landing', 'categorias')
            if categorias_objects:
                # Pegar o arquivo mais recente
                latest_file = sorted(categorias_objects)[-1]
                categorias_data = self.minio.download_json('landing', latest_file)
                
                if categorias_data and 'mainSegments' in categorias_data:
                    # Processar algumas categorias
                    for i, categoria in enumerate(categorias_data['mainSegments'][:limite_categorias]):
                        main_segment = categoria['shortname']
                        
                        # Pegar alguns segmentos secundários
                        for j, sub_categoria in enumerate(categoria.get('childrenSegments', [])[:2]):
                            secondary_segment = sub_categoria['shortname']
                            
                            # Coletar ranking da categoria
                            ranking_data = self.coletar_ranking_categoria(main_segment, secondary_segment)
                            
                            if ranking_data and 'companies' in ranking_data:
                                # Coletar dados detalhados de algumas empresas
                                for k, empresa in enumerate(ranking_data['companies'][:limite_empresas]):
                                    shortname = empresa.get('companyShortname')
                                    company_id = empresa.get('id')
                                    
                                    if shortname:
                                        # Dados detalhados da empresa
                                        self.coletar_empresa_detalhada(shortname)
                                        
                                        # Reclamações (se tiver ID)
                                        if company_id:
                                            self.coletar_reclamacoes(company_id)
                                    
                                    # Pausa entre empresas
                                    if k < limite_empresas - 1:
                                        time.sleep(random.uniform(2, 4))
                            
                            # Pausa entre subcategorias
                            if j < len(categoria.get('childrenSegments', [])) - 1:
                                time.sleep(random.uniform(3, 6))
                        
                        # Pausa entre categorias principais
                        if i < limite_categorias - 1:
                            time.sleep(random.uniform(5, 10))
        
        except Exception as e:
            if self.verbose:
                print(f"❌ Erro durante processamento: {e}")
        
        self.stats['end_time'] = datetime.now()
        
        # Salvar estatísticas da execução
        stats_path = self.minio.upload_json(self.stats, 'landing', 'pipeline_stats')
        
        if self.verbose:
            self._imprimir_relatorio_final()
        
        return self.stats
    
    def _imprimir_relatorio_final(self):
        """Imprime relatório final da execução."""
        duracao = self.stats['end_time'] - self.stats['start_time']
        
        print("\n" + "=" * 50)
        print("📊 RELATÓRIO FINAL DA PIPELINE")
        print("=" * 50)
        print(f"⏱️  Duração: {duracao}")
        print(f"🔄 Total de requisições: {self.stats['total_requests']}")
        print(f"✅ Requisições bem-sucedidas: {self.stats['successful_requests']}")
        print(f"❌ Requisições falharam: {self.stats['failed_requests']}")
        
        if self.stats['data_collected']:
            print("\n📦 Dados coletados:")
            for tipo, quantidade in self.stats['data_collected'].items():
                print(f"   {tipo}: {quantidade}")
        
        # Estatísticas do MinIO
        minio_stats = self.minio.get_stats()
        print(f"\n💾 Estatísticas MinIO:")
        for layer, info in minio_stats.items():
            if 'error' not in info:
                print(f"   {layer}: {info['total_objects']} objetos ({info['total_size_mb']} MB)")


def main():
    """Função principal para executar a pipeline."""
    # Criar e executar pipeline
    pipeline = ReclameAquiPipeline(verbose=True)
    
    # Executar pipeline básica
    stats = pipeline.executar_pipeline_basica(limite_categorias=2, limite_empresas=3)
    
    print(f"\n🎉 Pipeline finalizada!")
    return stats


if __name__ == "__main__":
    main()