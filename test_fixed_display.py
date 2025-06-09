import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from database import DatabaseManager
from search_engine import SearchEngine
from embed_manager import EmbedManager
import json

async def test_fixed_display():
    """修正後の表示をテスト"""
    
    # 設定ファイルを読み込む
    with open('config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    db = DatabaseManager()
    search_engine = SearchEngine(db, config)
    embed_manager = EmbedManager(config)
    
    print("=== 修正後の表示テスト ===\n")
    
    # テスト1: 石 (材料) - 利用先で必要数が正しく表示されるかテスト
    print("【テスト1: 石の関連アイテム】")
    material_results = await search_engine.search("石")
    if material_results:
        material = material_results[0]
        print(f"検索対象: {material['formal_name']} (type: {material['item_type']})")
        
        related = await search_engine.search_related_items(material)
        print(f"関連アイテム取得結果: {len(related)} カテゴリ")
        
        if related.get('usage_destinations'):
            print(f"\n■ 利用先 ({len(related['usage_destinations'])}件):")
            for i, item in enumerate(related['usage_destinations'][:5]):
                detail = item.get('relation_detail', '')
                print(f"  {i+1}. {item['formal_name']} - {detail}")
        
        print("\n" + "-"*40)
    
    # テスト2: ウッドソード（装備）- 必要素材の必要数表示テスト
    print("\n【テスト2: ウッドソードの関連アイテム】")
    equipment_results = await search_engine.search("ウッドソード")
    if equipment_results:
        equipment = equipment_results[0]
        print(f"検索対象: {equipment['formal_name']} (type: {equipment['item_type']})")
        
        related = await search_engine.search_related_items(equipment)
        
        if related.get('materials'):
            print(f"\n■ 必要素材 ({len(related['materials'])}件):")
            for i, item in enumerate(related['materials']):
                quantity = item.get('required_quantity', '1')
                print(f"  {i+1}. {item['formal_name']} x{quantity}")
    
    print("\n" + "="*50)
    print("修正内容:")
    print("1. 必要数の表示: 「x数量」形式で統一")
    print("2. 絵文字とフォーマット: mobのembedのように美しく")
    print("3. セレクトメニューのインデックス問題を修正")

if __name__ == "__main__":
    asyncio.run(test_fixed_display())