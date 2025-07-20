#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Funções utilitárias para a pipeline do Reclame Aqui.
"""

import re
import unicodedata
from datetime import datetime
from typing import Dict, List, Optional, Any


def normalizar_texto(texto: str) -> str:
    """
    Normaliza texto removendo acentos e caracteres especiais.
    
    Args:
        texto: Texto para normalizar
        
    Returns:
        str: Texto normalizado
    """
    if not texto:
        return ""
    
    # Remove acentos
    texto_normalizado = unicodedata.normalize('NFKD', texto)
    texto_normalizado = ''.join([c for c in texto_normalizado if not unicodedata.combining(c)])
    
    # Converte para minúsculas
    texto_normalizado = texto_normalizado.lower()
    
    # Remove caracteres especiais mas preserva espaços
    texto_normalizado = re.sub(r'[^a-z0-9\s]', '', texto_normalizado)
    texto_normalizado = texto_normalizado.strip()
    
    return texto_normalizado


def extrair_ids_empresas(dados: Dict) -> List[str]:
    """
    Extrai IDs de empresas de diferentes formatos de resposta da API.
    
    Args:
        dados: Dados JSON da API
        
    Returns:
        List[str]: Lista de IDs de empresas
    """
    ids = []
    
    try:
        # Formato 1: ranking com companies
        if 'companies' in dados:
            for empresa in dados['companies']:
                if 'id' in empresa:
                    ids.append(empresa['id'])
        
        # Formato 2: suggestion com id único
        elif 'suggestion' in dados and 'id' in dados['suggestion']:
            ids.append(dados['suggestion']['id'])
        
        # Formato 3: lista direta de empresas
        elif isinstance(dados, list):
            for empresa in dados:
                if isinstance(empresa, dict) and 'id' in empresa:
                    ids.append(empresa['id'])
        
        # Formato 4: empresas dentro de company_info
        elif 'company_info' in dados and 'id' in dados['company_info']:
            ids.append(dados['company_info']['id'])
            
    except Exception as e:
        print(f"Erro ao extrair IDs: {e}")
    
    return list(set(ids))  # Remove duplicatas


def contar_reclamacoes(dados: Dict) -> int:
    """
    Conta reclamações em dados de resposta da API.
    
    Args:
        dados: Dados JSON da API de reclamações
        
    Returns:
        int: Número de reclamações encontradas
    """
    try:
        if ('complainResult' in dados and 
            'complains' in dados['complainResult'] and 
            'data' in dados['complainResult']['complains']):
            
            reclamacoes = dados['complainResult']['complains']['data']
            return len(reclamacoes) if reclamacoes else 0
    except:
        pass
    
    return 0


def gerar_nome_arquivo(tipo: str, empresa_id: str = None, 
                      timestamp: bool = True) -> str:
    """
    Gera nome padronizado para arquivos.
    
    Args:
        tipo: Tipo do arquivo (categorias, empresas, reclamacoes, etc.)
        empresa_id: ID da empresa (opcional)
        timestamp: Se deve incluir timestamp
        
    Returns:
        str: Nome do arquivo
    """
    nome = tipo
    
    if empresa_id:
        nome += f"_{empresa_id}"
    
    if timestamp:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        nome += f"_{ts}"
    
    return f"{nome}.json"


def validar_dados_empresa(dados: Dict) -> Dict[str, Any]:
    """
    Valida e extrai informações básicas de dados de empresa.
    
    Args:
        dados: Dados JSON da empresa
        
    Returns:
        Dict: Informações validadas
    """
    info = {
        'id': dados.get('id'),
        'nome': dados.get('companyName') or dados.get('name'),
        'shortname': dados.get('shortname'),
        'site': dados.get('urlSite') or dados.get('companySite'),
        'verificada': dados.get('isVerified', False),
        'score': None,
        'segmento_principal': None,
        'segmentos_secundarios': []
    }
    
    # Tentar extrair score
    if 'finalScore' in dados:
        info['score'] = dados['finalScore']
    elif 'panels' in dados and dados['panels']:
        # Pegar score do primeiro painel
        info['score'] = dados['panels'][0].get('avg')
    
    # Tentar extrair segmentos
    if 'mainSegment' in dados and dados['mainSegment']:
        info['segmento_principal'] = dados['mainSegment'].get('title')
    
    if 'secondarySegments' in dados and dados['secondarySegments']:
        info['segmentos_secundarios'] = [
            seg.get('title') for seg in dados['secondarySegments'] 
            if seg.get('title')
        ]
    
    return info


def filtrar_empresas_ativas(empresas: List[Dict]) -> List[Dict]:
    """
    Filtra apenas empresas ativas e verificadas.
    
    Args:
        empresas: Lista de empresas
        
    Returns:
        List[Dict]: Empresas filtradas
    """
    empresas_ativas = []
    
    for empresa in empresas:
        # Verificar se tem dados básicos
        if not empresa.get('id') or not empresa.get('companyName'):
            continue
        
        # Verificar se está ativa
        status = empresa.get('status', '').upper()
        if status in ['ACTIVE', 'VERIFIED', '']:
            empresas_ativas.append(empresa)
    
    return empresas_ativas


def extrair_estatisticas_basicas(dados: Dict) -> Dict[str, Any]:
    """
    Extrai estatísticas básicas de dados coletados.
    
    Args:
        dados: Dados para analisar
        
    Returns:
        Dict: Estatísticas básicas
    """
    stats = {
        'total_items': 0,
        'tipos_encontrados': [],
        'tem_metadados': False,
        'tamanho_mb': 0
    }
    
    try:
        # Calcular tamanho aproximado
        import json
        json_str = json.dumps(dados)
        stats['tamanho_mb'] = len(json_str.encode('utf-8')) / (1024 * 1024)
        
        # Contar itens
        if isinstance(dados, list):
            stats['total_items'] = len(dados)
        elif isinstance(dados, dict):
            # Tentar identificar estruturas conhecidas
            if 'mainSegments' in dados:
                stats['total_items'] = len(dados['mainSegments'])
                stats['tipos_encontrados'].append('categorias')
            elif 'companies' in dados:
                stats['total_items'] = len(dados['companies'])
                stats['tipos_encontrados'].append('empresas')
            elif 'complainResult' in dados:
                stats['total_items'] = contar_reclamacoes(dados)
                stats['tipos_encontrados'].append('reclamacoes')
        
        # Verificar metadados
        if 'metadata' in dados:
            stats['tem_metadados'] = True
            
    except Exception as e:
        stats['erro'] = str(e)
    
    return stats


def criar_resumo_coleta(stats: Dict) -> str:
    """
    Cria um resumo legível da coleta de dados.
    
    Args:
        stats: Estatísticas da coleta
        
    Returns:
        str: Resumo formatado
    """
    linhas = []
    
    if stats.get('start_time') and stats.get('end_time'):
        duracao = stats['end_time'] - stats['start_time']
        linhas.append(f"⏱️  Duração: {duracao}")
    
    if 'total_requests' in stats:
        total = stats['total_requests']
        sucesso = stats.get('successful_requests', 0)
        taxa_sucesso = (sucesso / total * 100) if total > 0 else 0
        linhas.append(f"🔄 Requisições: {sucesso}/{total} ({taxa_sucesso:.1f}% sucesso)")
    
    if 'data_collected' in stats and stats['data_collected']:
        linhas.append("📦 Dados coletados:")
        for tipo, quantidade in stats['data_collected'].items():
            linhas.append(f"   • {tipo}: {quantidade}")
    
    return "\n".join(linhas)


if __name__ == "__main__":
    # Testes básicos das funções
    print("🧪 Testando funções utilitárias...")
    
    # Teste normalização
    texto_teste = "Açaí & Cia Ltda."
    normalizado = normalizar_texto(texto_teste)
    print(f"Normalização: '{texto_teste}' → '{normalizado}'")
    
    # Teste geração de nome
    nome_arquivo = gerar_nome_arquivo("empresas", "12345")
    print(f"Nome arquivo: {nome_arquivo}")
    
    print("✅ Testes concluídos!")