#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script inteligente para buscar empresas na API do Reclame Aqui e coletar dados automaticamente.
Resolve o problema de encontrar o nome/shortname correto na API.
"""

import time
import random
import cloudscraper
import json
from typing import List, Dict, Optional, Tuple
from reclame_aqui_pipeline import ReclameAquiPipeline


class SmartCompanyFinder:
    """
    Busca inteligente de empresas no Reclame Aqui com coleta automática de dados.
    """
    
    def __init__(self, verbose: bool = True):
        """
        Inicializa o buscador inteligente.
        
        Args:
            verbose: Se True, exibe logs detalhados
        """
        self.verbose = verbose
        self.pipeline = ReclameAquiPipeline(verbose=verbose)
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0"
        ]
    
    def _criar_scraper(self):
        """Cria scraper configurado."""
        scraper = cloudscraper.create_scraper()
        headers = {
            "User-Agent": random.choice(self.user_agents),
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            "Origin": "https://www.reclameaqui.com.br",
            "Referer": "https://www.reclameaqui.com.br/"
        }
        scraper.headers.update(headers)
        return scraper
    
    def buscar_empresa_api(self, nome: str) -> List[Dict]:
        """
        Busca empresa na API de search e retorna todas as opções encontradas.
        
        Args:
            nome: Nome da empresa para buscar
            
        Returns:
            List[Dict]: Lista de empresas encontradas
        """
        if self.verbose:
            print(f"🔍 Buscando '{nome}' na API do Reclame Aqui...")
        
        # Normalizar nome para URL
        nome_url = nome.lower().replace(' ', '%20').replace('&', '%26')
        url = f"https://iosearch.reclameaqui.com.br/raichu-io-site-search-v1/companies/search/{nome_url}"
        
        scraper = self._criar_scraper()
        
        try:
            response = scraper.get(url, timeout=30)
            response.raise_for_status()
            dados = response.json()
            
            empresas_encontradas = []
            
            # Formato 1: suggestion única
            if 'suggestion' in dados and dados['suggestion'] and 'id' in dados['suggestion']:
                empresa = dados['suggestion']
                empresas_encontradas.append({
                    'nome_busca': nome,
                    'nome_oficial': empresa.get('companyName', ''),
                    'id': empresa.get('id', ''),
                    'shortname': empresa.get('shortname', ''),
                    'site': empresa.get('companySite', ''),
                    'verificada': empresa.get('hasVerificada', False),
                    'status': empresa.get('status', ''),
                    'total_reclamacoes': empresa.get('count', 0),
                    'fonte': 'suggestion'
                })
            
            # Formato 2: lista de companies
            if 'companies' in dados and isinstance(dados['companies'], list):
                for empresa in dados['companies']:
                    if 'id' in empresa:
                        empresas_encontradas.append({
                            'nome_busca': nome,
                            'nome_oficial': empresa.get('companyName', ''),
                            'id': empresa.get('id', ''),
                            'shortname': empresa.get('shortname', ''),
                            'site': empresa.get('url', ''),
                            'verificada': empresa.get('hasVerificada', False),
                            'status': empresa.get('status', ''),
                            'total_reclamacoes': empresa.get('count', 0),
                            'fonte': 'companies_list'
                        })
            
            if self.verbose:
                if empresas_encontradas:
                    print(f"✅ Encontradas {len(empresas_encontradas)} empresa(s)")
                else:
                    print("❌ Nenhuma empresa encontrada")
            
            return empresas_encontradas
            
        except Exception as e:
            if self.verbose:
                print(f"❌ Erro na busca: {e}")
            return []
    
    def buscar_multiplas_variacoes(self, nome_base: str) -> List[Dict]:
        """
        Busca empresa com múltiplas variações do nome.
        
        Args:
            nome_base: Nome base da empresa
            
        Returns:
            List[Dict]: Todas as empresas encontradas
        """
        if self.verbose:
            print(f"🔍 BUSCA INTELIGENTE: {nome_base}")
            print("=" * 50)
        
        # Gerar variações do nome
        variações = [
            nome_base,
            nome_base.lower(),
            nome_base.upper(),
            nome_base.replace(' ', ''),
            nome_base.replace(' ', '-'),
            nome_base.replace('&', 'e'),
            nome_base.replace('ç', 'c'),
            nome_base.replace('ã', 'a'),
            nome_base.replace('õ', 'o')
        ]
        
        # Adicionar variações específicas comuns
        if 'vivo' in nome_base.lower():
            variações.extend(['telefonica', 'telefônica', 'telefonica brasil'])
        
        if 'tim' in nome_base.lower():
            variações.extend(['tim brasil', 'tim participacoes'])
        
        if 'claro' in nome_base.lower():
            variações.extend(['claro brasil', 'america movil'])
        
        # Remover duplicatas
        variações = list(set(variações))
        
        todas_empresas = []
        empresas_unicas = {}  # Para evitar duplicatas por ID
        
        for i, variação in enumerate(variações):
            if self.verbose:
                print(f"\n🔍 Testando variação {i+1}/{len(variações)}: '{variação}'")
            
            empresas = self.buscar_empresa_api(variação)
            
            for empresa in empresas:
                empresa_id = empresa['id']
                if empresa_id not in empresas_unicas:
                    empresas_unicas[empresa_id] = empresa
                    todas_empresas.append(empresa)
            
            # Pausa entre requisições
            if i < len(variações) - 1:
                time.sleep(random.uniform(2, 4))
        
        return todas_empresas
    
    def exibir_opcoes_empresa(self, empresas: List[Dict]) -> None:
        """
        Exibe opções de empresas encontradas de forma organizada.
        
        Args:
            empresas: Lista de empresas encontradas
        """
        if not empresas:
            print("❌ Nenhuma empresa encontrada")
            return
        
        print(f"\n📊 EMPRESAS ENCONTRADAS: {len(empresas)}")
        print("=" * 60)
        
        for i, empresa in enumerate(empresas, 1):
            status_icon = "✅" if empresa['verificada'] else "⭕"
            status_color = {
                'RECOMMENDED': '🟢',
                'NOT_RECOMMENDED': '🔴', 
                'NO_INDEX': '⚪',
                '': '⚫'
            }.get(empresa.get('status', ''), '⚫')
            
            print(f"{i:2d}. {status_icon} {empresa['nome_oficial']}")
            print(f"    🆔 ID: {empresa['id']}")
            print(f"    🔗 Shortname: {empresa['shortname']}")
            print(f"    📊 Status: {status_color} {empresa.get('status', 'N/A')}")
            print(f"    📝 Reclamações: {empresa['total_reclamacoes']}")
            if empresa['site']:
                print(f"    🌐 Site: {empresa['site']}")
            print()
    
    def selecionar_empresa(self, empresas: List[Dict]) -> Optional[Dict]:
        """
        Permite seleção interativa da empresa ou seleciona automaticamente.
        
        Args:
            empresas: Lista de empresas encontradas
            
        Returns:
            Dict: Empresa selecionada ou None
        """
        if not empresas:
            return None
        
        if len(empresas) == 1:
            empresa = empresas[0]
            if self.verbose:
                print(f"✅ Empresa única encontrada: {empresa['nome_oficial']}")
            return empresa
        
        # Tentar seleção automática baseada em critérios
        # 1. Priorizar empresas verificadas
        verificadas = [e for e in empresas if e['verificada']]
        if len(verificadas) == 1:
            if self.verbose:
                print(f"✅ Seleção automática (única verificada): {verificadas[0]['nome_oficial']}")
            return verificadas[0]
        
        # 2. Priorizar por status RECOMMENDED
        recomendadas = [e for e in empresas if e.get('status') == 'RECOMMENDED']
        if len(recomendadas) == 1:
            if self.verbose:
                print(f"✅ Seleção automática (única recomendada): {recomendadas[0]['nome_oficial']}")
            return recomendadas[0]
        
        # 3. Priorizar por maior número de reclamações (empresa principal)
        empresa_principal = max(empresas, key=lambda x: x['total_reclamacoes'])
        if self.verbose:
            print(f"✅ Seleção automática (mais reclamações): {empresa_principal['nome_oficial']}")
        return empresa_principal
    
    def coletar_dados_completos(self, empresa: Dict) -> Dict:
        """
        Coleta todos os dados disponíveis de uma empresa.
        
        Args:
            empresa: Dados da empresa
            
        Returns:
            Dict: Resultado da coleta
        """
        if self.verbose:
            print(f"\n🚀 COLETANDO DADOS COMPLETOS: {empresa['nome_oficial']}")
            print("=" * 60)
        
        resultado = {
            'empresa': empresa,
            'dados_detalhados': None,
            'reclamacoes': [],
            'sucesso': False,
            'erros': []
        }
        
        # 1. Dados detalhados da empresa
        if self.verbose:
            print("🏢 Coletando dados detalhados da empresa...")
        
        try:
            dados_detalhados = self.pipeline.coletar_empresa_detalhada(empresa['shortname'])
            if dados_detalhados:
                resultado['dados_detalhados'] = dados_detalhados
                if self.verbose:
                    print("✅ Dados detalhados coletados")
            else:
                resultado['erros'].append("Falha ao coletar dados detalhados")
                if self.verbose:
                    print("⚠️  Dados detalhados não disponíveis")
        except Exception as e:
            erro = f"Erro nos dados detalhados: {e}"
            resultado['erros'].append(erro)
            if self.verbose:
                print(f"❌ {erro}")
        
        # Pausa entre requisições
        time.sleep(random.uniform(3, 6))
        
        # 2. Reclamações
        if self.verbose:
            print("📝 Coletando reclamações...")
        
        try:
            # Tentar reclamações avaliadas primeiro
            caminho_avaliadas, dados_avaliadas = self.pipeline.coletar_reclamacoes_avaliadas(
                empresa['id'], quantidade=30, offset=0
            )
            
            if dados_avaliadas:
                resultado['reclamacoes'].append({
                    'tipo': 'avaliadas',
                    'dados': dados_avaliadas,
                    'caminho': caminho_avaliadas
                })
                if self.verbose:
                    print("✅ Reclamações avaliadas coletadas")
            
            # Pausa
            time.sleep(random.uniform(2, 4))
            
            # Tentar todas as reclamações
            caminho_todas, dados_todas = self.pipeline.coletar_reclamacoes_todas(
                empresa['id'], quantidade=30, offset=0
            )
            
            if dados_todas:
                resultado['reclamacoes'].append({
                    'tipo': 'todas',
                    'dados': dados_todas,
                    'caminho': caminho_todas
                })
                if self.verbose:
                    print("✅ Todas as reclamações coletadas")
            
        except Exception as e:
            erro = f"Erro nas reclamações: {e}"
            resultado['erros'].append(erro)
            if self.verbose:
                print(f"❌ {erro}")
        
        # Determinar sucesso
        resultado['sucesso'] = (
            resultado['dados_detalhados'] is not None or 
            len(resultado['reclamacoes']) > 0
        )
        
        return resultado
    
    def buscar_e_coletar(self, nome_empresa: str, auto_select: bool = True) -> Dict:
        """
        Método principal: busca empresa e coleta dados automaticamente.
        
        Args:
            nome_empresa: Nome da empresa para buscar
            auto_select: Se True, seleciona automaticamente a melhor opção
            
        Returns:
            Dict: Resultado completo da operação
        """
        if self.verbose:
            print(f"🎯 BUSCA E COLETA INTELIGENTE: {nome_empresa}")
            print("=" * 70)
        
        # 1. Buscar empresa
        empresas = self.buscar_multiplas_variacoes(nome_empresa)
        
        if not empresas:
            return {
                'sucesso': False,
                'erro': 'Nenhuma empresa encontrada',
                'empresas_encontradas': [],
                'empresa_selecionada': None,
                'dados_coletados': None
            }
        
        # 2. Exibir opções
        self.exibir_opcoes_empresa(empresas)
        
        # 3. Selecionar empresa
        empresa_selecionada = self.selecionar_empresa(empresas)
        
        if not empresa_selecionada:
            return {
                'sucesso': False,
                'erro': 'Nenhuma empresa selecionada',
                'empresas_encontradas': empresas,
                'empresa_selecionada': None,
                'dados_coletados': None
            }
        
        # 4. Coletar dados completos
        dados_coletados = self.coletar_dados_completos(empresa_selecionada)
        
        # 5. Resultado final
        resultado = {
            'sucesso': dados_coletados['sucesso'],
            'empresas_encontradas': empresas,
            'empresa_selecionada': empresa_selecionada,
            'dados_coletados': dados_coletados,
            'resumo': self._gerar_resumo(dados_coletados)
        }
        
        if self.verbose:
            self._imprimir_resumo_final(resultado)
        
        return resultado
    
    def _gerar_resumo(self, dados_coletados: Dict) -> Dict:
        """Gera resumo dos dados coletados."""
        resumo = {
            'dados_detalhados': dados_coletados['dados_detalhados'] is not None,
            'total_reclamacoes_coletadas': 0,
            'tipos_reclamacoes': [],
            'erros': dados_coletados['erros']
        }
        
        for rec in dados_coletados['reclamacoes']:
            resumo['tipos_reclamacoes'].append(rec['tipo'])
            # Contar reclamações se possível
            dados = rec['dados']
            if (dados and 'complainResult' in dados and 
                'complains' in dados['complainResult'] and
                'data' in dados['complainResult']['complains']):
                resumo['total_reclamacoes_coletadas'] += len(dados['complainResult']['complains']['data'])
        
        return resumo
    
    def _imprimir_resumo_final(self, resultado: Dict):
        """Imprime resumo final da operação."""
        print("\n" + "=" * 70)
        print("📊 RESUMO FINAL")
        print("=" * 70)
        
        empresa = resultado['empresa_selecionada']
        dados = resultado['dados_coletados']
        resumo = resultado['resumo']
        
        print(f"🎯 Empresa: {empresa['nome_oficial']}")
        print(f"🆔 ID: {empresa['id']}")
        print(f"🔗 Shortname: {empresa['shortname']}")
        print(f"📊 Status: {empresa.get('status', 'N/A')}")
        print()
        
        print("📋 DADOS COLETADOS:")
        print(f"   🏢 Dados detalhados: {'✅' if resumo['dados_detalhados'] else '❌'}")
        print(f"   📝 Reclamações: {resumo['total_reclamacoes_coletadas']} coletadas")
        print(f"   📂 Tipos: {', '.join(resumo['tipos_reclamacoes'])}")
        
        if resumo['erros']:
            print(f"\n⚠️  Erros encontrados: {len(resumo['erros'])}")
            for erro in resumo['erros']:
                print(f"   • {erro}")
        
        print(f"\n🎉 Operação {'concluída com sucesso' if resultado['sucesso'] else 'concluída com problemas'}!")


def main():
    """Função principal para teste e uso direto."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Busca e coleta inteligente de empresas')
    parser.add_argument('empresa', help='Nome da empresa para buscar')
    parser.add_argument('--quiet', action='store_true', help='Modo silencioso')
    
    args = parser.parse_args()
    
    finder = SmartCompanyFinder(verbose=not args.quiet)
    resultado = finder.buscar_e_coletar(args.empresa)
    
    return resultado


if __name__ == "__main__":
    main()