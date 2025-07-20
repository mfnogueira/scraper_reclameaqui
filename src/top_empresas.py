#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script para buscar top empresas por categoria do Reclame Aqui.
"""

import json
from reclame_aqui_pipeline import ReclameAquiPipeline


class TopEmpresasFinder:
    """Classe para encontrar top empresas por categoria."""
    
    def __init__(self):
        self.pipeline = ReclameAquiPipeline(verbose=True)
    
    def listar_categorias_populares(self):
        """Lista as categorias mais populares."""
        print("🏷️  Buscando categorias disponíveis...")
        
        # Buscar categorias
        sucesso = self.pipeline.coletar_categorias()
        if not sucesso:
            print("❌ Erro ao buscar categorias")
            return []
        
        # Pegar dados da landing
        try:
            objects = self.pipeline.minio.list_objects('landing', 'categorias')
            if objects:
                latest_file = sorted(objects)[-1]
                categorias_data = self.pipeline.minio.download_json('landing', latest_file)
                
                if categorias_data and 'mainSegments' in categorias_data:
                    categorias_populares = []
                    
                    for categoria in categorias_data['mainSegments'][:15]:  # Top 15 categorias
                        info = {
                            'main_segment': categoria['shortname'],
                            'titulo_principal': categoria['title'],
                            'subcategorias': []
                        }
                        
                        # Pegar subcategorias
                        for sub in categoria.get('childrenSegments', [])[:5]:  # Top 5 subcategorias
                            info['subcategorias'].append({
                                'secondary_segment': sub['shortname'],
                                'titulo': sub['title']
                            })
                        
                        categorias_populares.append(info)
                    
                    return categorias_populares
        except Exception as e:
            print(f"❌ Erro ao processar categorias: {e}")
        
        return []
    
    def buscar_top10_categoria(self, main_segment: str, secondary_segment: str, quantidade: int = 10):
        """
        Busca top empresas de uma categoria específica.
        
        Args:
            main_segment: Categoria principal
            secondary_segment: Subcategoria  
            quantidade: Quantas empresas buscar (default 10)
            
        Returns:
            List: Lista das top empresas
        """
        print(f"\n🏆 Buscando TOP {quantidade} de: {main_segment}/{secondary_segment}")
        
        # Buscar ranking
        ranking_data = self.pipeline.coletar_ranking_categoria(
            main_segment, secondary_segment, quantidade=quantidade
        )
        
        if not ranking_data or 'companies' not in ranking_data:
            print("❌ Nenhuma empresa encontrada para esta categoria")
            return []
        
        empresas = ranking_data['companies'][:quantidade]
        top_empresas = []
        
        print(f"\n✅ Encontradas {len(empresas)} empresas!")
        print("="*60)
        
        for i, empresa in enumerate(empresas, 1):
            info = {
                'posicao': i,
                'nome': empresa.get('companyName', 'Nome não disponível'),
                'shortname': empresa.get('companyShortname', ''),
                'score_final': empresa.get('finalScore', 0),
                'status': empresa.get('companyIndex', ''),
                'resolvidas_pct': empresa.get('solvedPercentual', 0),
                'respondidas_pct': empresa.get('answeredPercentual', 0),
                'total_reclamacoes': empresa.get('complainsCount', 0),
                'verificada': empresa.get('isVerified', False)
            }
            
            top_empresas.append(info)
            
            # Imprimir informações
            verificada = "✅" if info['verificada'] else "⭕"
            print(f"{i:2d}. {verificada} {info['nome']}")
            print(f"    📊 Score: {info['score_final']:.1f} | Status: {info['status']}")
            print(f"    🎯 Resolvidas: {info['resolvidas_pct']:.1f}% | Respondidas: {info['respondidas_pct']:.1f}%")
            print(f"    📝 Total reclamações: {info['total_reclamacoes']}")
            print()
        
        # Salvar resultado no MinIO
        resultado = {
            'categoria': {
                'main_segment': main_segment,
                'secondary_segment': secondary_segment
            },
            'top_empresas': top_empresas,
            'total_encontradas': len(empresas),
            'data_coleta': ranking_data.get('pagination', {})
        }
        
        filename = f"top{quantidade}_{main_segment}_{secondary_segment}.json"
        self.pipeline.minio.upload_json(resultado, 'landing', 'top_empresas', filename)
        
        return top_empresas
    
    def buscar_categoria_interativa(self):
        """Busca interativa de categorias."""
        print("🔍 BUSCA INTERATIVA DE TOP EMPRESAS")
        print("="*50)
        
        # Listar categorias
        categorias = self.listar_categorias_populares()
        if not categorias:
            return
        
        print("\n📋 CATEGORIAS PRINCIPAIS DISPONÍVEIS:")
        print("-"*40)
        
        for i, cat in enumerate(categorias[:10], 1):
            print(f"{i:2d}. {cat['titulo_principal']}")
            print(f"    🔗 {cat['main_segment']}")
            if cat['subcategorias']:
                print(f"    📂 {len(cat['subcategorias'])} subcategorias disponíveis")
            print()
        
        print("💡 Para buscar top empresas de uma categoria, use:")
        print("   python top_empresas.py --main-segment CATEGORIA --secondary-segment SUBCATEGORIA")
        print("\n📋 EXEMPLOS POPULARES:")
        print("-"*25)
        
        exemplos = [
            ("bancos-e-financeiras", "meios-de-pagamento-eletronico", "💳 Meios de Pagamento"),
            ("telefonia-tv-e-internet", "planos-de-internet", "🌐 Planos de Internet"),
            ("varejo", "marketplaces", "🛒 Marketplaces"),
            ("saude", "planos-de-saude", "🏥 Planos de Saúde"),
            ("veiculos-e-acessorios", "concessionarias-de-veiculos", "🚗 Concessionárias")
        ]
        
        for main, secondary, desc in exemplos:
            print(f"• {desc}")
            print(f"  python top_empresas.py --main-segment {main} --secondary-segment {secondary}")
            print()


def main():
    """Função principal."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Buscar top empresas por categoria')
    parser.add_argument('--main-segment', type=str, help='Categoria principal')
    parser.add_argument('--secondary-segment', type=str, help='Subcategoria')
    parser.add_argument('--quantidade', type=int, default=10, help='Quantidade de empresas (default: 10)')
    parser.add_argument('--listar', action='store_true', help='Listar categorias disponíveis')
    
    args = parser.parse_args()
    
    finder = TopEmpresasFinder()
    
    if args.listar or (not args.main_segment and not args.secondary_segment):
        finder.buscar_categoria_interativa()
    elif args.main_segment and args.secondary_segment:
        finder.buscar_top10_categoria(args.main_segment, args.secondary_segment, args.quantidade)
    else:
        print("❌ Erro: Forneça --main-segment e --secondary-segment")
        print("💡 Use --listar para ver categorias disponíveis")


if __name__ == "__main__":
    main()