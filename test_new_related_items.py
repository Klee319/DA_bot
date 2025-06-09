import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from database import DatabaseManager
from search_engine import SearchEngine
import json

async def test_new_related_items():
    """新しい関連アイテム仕様のテスト"""
    
    print("\n" + "="*50)
    print("テスト用サンプルデータ:")
    print("- 素材: 強固な砂岩")
    print("- 装備: ウッドソード")
    print("- モブ: トト")
    print("="*50 + "\n")
    
    # 設定ファイルを読み込む
    with open('config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    db = DatabaseManager()
    search_engine = SearchEngine(db, config)
    
    print("=== 新仕様の関連アイテム検索テスト ===\n")
    
    # テスト1: material（素材）の関連アイテム
    print("【テスト1: 素材の関連アイテム検索】")
    material_results = await search_engine.search("強固な砂岩")
    if material_results:
        material = material_results[0]
        print(f"検索対象: {material['formal_name']} (type: {material['item_type']})")
        
        related = await search_engine.search_related_items(material)
        
        if related.get('usage_destinations'):
            print("\n■ 利用先:")
            for item in related['usage_destinations']:
                print(f"  - {item['formal_name']} ({item.get('relation_detail', '')})")
        
        if related.get('acquisition_sources'):
            print("\n■ 入手元:")
            for item in related['acquisition_sources']:
                print(f"  - {item['formal_name']} ({item.get('relation_type', '')})")
        elif related.get('acquisition_info'):
            info = related['acquisition_info']
            method = info.get('method', '')
            if method:
                print(f"\n■ 入手方法: {info.get('category', '')} - {method}")
            else:
                print(f"\n■ 入手方法: {info.get('category', '')}")
    
    print("\n" + "="*50 + "\n")
    
    # テスト2: equipment（装備）の関連アイテム
    print("【テスト2: 装備の関連アイテム検索】")
    equipment_results = await search_engine.search("ウッドソード")
    if equipment_results:
        equipment = equipment_results[0]
        print(f"検索対象: {equipment['formal_name']} (type: {equipment['item_type']})")
        
        related = await search_engine.search_related_items(equipment)
        
        if related.get('materials'):
            print("\n■ 必要素材:")
            for item in related['materials']:
                print(f"  - {item['formal_name']}: {item.get('required_quantity', '1')}")
        
        if related.get('acquisition_sources'):
            print("\n■ 入手元:")
            for item in related['acquisition_sources']:
                print(f"  - {item['formal_name']} (ドロップ)")
    
    print("\n" + "="*50 + "\n")
    
    # テスト3: mob（モンスター）の関連アイテム
    print("【テスト3: モンスターの関連アイテム検索】")
    mob_results = await search_engine.search("トト")
    if mob_results:
        mob = mob_results[0]
        print(f"検索対象: {mob['formal_name']} (type: {mob['item_type']})")
        
        related = await search_engine.search_related_items(mob)
        
        if related.get('dropped_items'):
            print("\n■ ドロップアイテム:")
            for item in related['dropped_items']:
                print(f"  - {item['formal_name']} ({item['item_type']})")

if __name__ == "__main__":
    asyncio.run(test_new_related_items())