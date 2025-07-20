#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Cliente MinIO para gerenciar upload e download de dados na pipeline.
"""

import json
import os
from datetime import datetime
from io import BytesIO
from typing import Dict, List, Optional, Any
from minio import Minio
from minio.error import S3Error


class MinIOClient:
    """
    Cliente para operações com MinIO na pipeline de dados.
    """
    
    def __init__(self, endpoint: str = "localhost:9000", 
                 access_key: str = "minioadmin", 
                 secret_key: str = "minioadmin123"):
        """
        Inicializa o cliente MinIO.
        
        Args:
            endpoint: Endpoint do MinIO
            access_key: Chave de acesso
            secret_key: Chave secreta
        """
        self.client = Minio(
            endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=False  # HTTP para desenvolvimento local
        )
        
        # Buckets das camadas da pipeline
        self.buckets = {
            'landing': 'reclameaqui-landing',
            'raw': 'reclameaqui-raw',
            'trusted': 'reclameaqui-trusted'
        }
        
        self._verificar_buckets()
    
    def _verificar_buckets(self):
        """
        Verifica se os buckets existem, se não, cria.
        """
        for layer, bucket_name in self.buckets.items():
            try:
                if not self.client.bucket_exists(bucket_name):
                    self.client.make_bucket(bucket_name)
                    print(f"Bucket '{bucket_name}' criado.")
                else:
                    print(f"Bucket '{bucket_name}' já existe.")
            except S3Error as e:
                print(f"Erro ao verificar bucket {bucket_name}: {e}")
    
    def upload_json(self, data: Dict[str, Any], layer: str, 
                   category: str, filename: str = None) -> str:
        """
        Faz upload de dados JSON para uma camada específica.
        
        Args:
            data: Dados para upload
            layer: Camada (landing, raw, trusted)
            category: Categoria dos dados (categorias, empresas, reclamacoes, etc.)
            filename: Nome do arquivo (opcional, gera automático se None)
            
        Returns:
            str: Caminho do objeto no MinIO
        """
        # Gerar nome do arquivo se não fornecido
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{category}_{timestamp}.json"
        
        # Caminho do objeto no bucket
        object_path = f"{category}/{datetime.now().strftime('%Y/%m/%d')}/{filename}"
        
        # Converter dados para JSON bytes
        json_data = json.dumps(data, indent=2, ensure_ascii=False)
        json_bytes = BytesIO(json_data.encode('utf-8'))
        
        try:
            # Fazer upload
            bucket_name = self.buckets[layer]
            self.client.put_object(
                bucket_name,
                object_path,
                json_bytes,
                length=len(json_data.encode('utf-8')),
                content_type='application/json'
            )
            
            full_path = f"{bucket_name}/{object_path}"
            print(f"Upload realizado: {full_path}")
            return full_path
            
        except S3Error as e:
            print(f"Erro no upload: {e}")
            return None
    
    def download_json(self, layer: str, object_path: str) -> Optional[Dict]:
        """
        Faz download de arquivo JSON de uma camada.
        
        Args:
            layer: Camada (landing, raw, trusted)
            object_path: Caminho do objeto no bucket
            
        Returns:
            Dict: Dados JSON ou None se erro
        """
        try:
            bucket_name = self.buckets[layer]
            response = self.client.get_object(bucket_name, object_path)
            
            # Ler e decodificar JSON
            json_data = response.read().decode('utf-8')
            return json.loads(json_data)
            
        except S3Error as e:
            print(f"Erro no download: {e}")
            return None
        finally:
            if 'response' in locals():
                response.close()
                response.release_conn()
    
    def list_objects(self, layer: str, category: str = None) -> List[str]:
        """
        Lista objetos de uma camada e categoria.
        
        Args:
            layer: Camada (landing, raw, trusted)
            category: Categoria específica (opcional)
            
        Returns:
            List[str]: Lista de caminhos dos objetos
        """
        try:
            bucket_name = self.buckets[layer]
            prefix = f"{category}/" if category else ""
            
            objects = self.client.list_objects(bucket_name, prefix=prefix, recursive=True)
            return [obj.object_name for obj in objects]
            
        except S3Error as e:
            print(f"Erro ao listar objetos: {e}")
            return []
    
    def get_stats(self) -> Dict[str, Dict]:
        """
        Retorna estatísticas dos buckets.
        
        Returns:
            Dict: Estatísticas por camada
        """
        stats = {}
        
        for layer, bucket_name in self.buckets.items():
            try:
                objects = list(self.client.list_objects(bucket_name, recursive=True))
                total_size = sum(obj.size for obj in objects)
                
                stats[layer] = {
                    'bucket': bucket_name,
                    'total_objects': len(objects),
                    'total_size_mb': round(total_size / (1024 * 1024), 2),
                    'categories': {}
                }
                
                # Agrupar por categoria
                for obj in objects:
                    category = obj.object_name.split('/')[0]
                    if category not in stats[layer]['categories']:
                        stats[layer]['categories'][category] = 0
                    stats[layer]['categories'][category] += 1
                    
            except S3Error as e:
                stats[layer] = {'error': str(e)}
        
        return stats
    
    def backup_to_raw(self, landing_object_path: str, 
                     raw_category: str = None) -> Optional[str]:
        """
        Move dados da camada landing para raw com transformações básicas.
        
        Args:
            landing_object_path: Caminho do objeto na camada landing
            raw_category: Categoria na camada raw (usa a mesma se None)
            
        Returns:
            str: Caminho na camada raw ou None se erro
        """
        # Download da landing
        data = self.download_json('landing', landing_object_path)
        if not data:
            return None
        
        # Extrair categoria do caminho se não fornecida
        if raw_category is None:
            raw_category = landing_object_path.split('/')[0]
        
        # Adicionar metadados de processamento
        processed_data = {
            'metadata': {
                'processed_at': datetime.now().isoformat(),
                'source_path': f"landing/{landing_object_path}",
                'pipeline_stage': 'raw'
            },
            'data': data
        }
        
        # Upload para raw
        return self.upload_json(processed_data, 'raw', raw_category)


if __name__ == "__main__":
    # Teste básico do cliente
    client = MinIOClient()
    
    # Dados de teste
    test_data = {
        'test': True,
        'timestamp': datetime.now().isoformat(),
        'message': 'Cliente MinIO funcionando!'
    }
    
    # Upload de teste
    path = client.upload_json(test_data, 'landing', 'test')
    if path:
        print(f"Teste de upload bem-sucedido: {path}")
    
    # Estatísticas
    stats = client.get_stats()
    print("\nEstatísticas dos buckets:")
    for layer, info in stats.items():
        print(f"{layer}: {info}")