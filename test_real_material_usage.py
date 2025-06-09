#!/usr/bin/env python3
"""
実際のデータベースを使った_extract_material_usage関数のテスト
"""

import asyncio
import sys
import os
import json

# パスを追加してsrcモジュールをインポート可能にする
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from database import DatabaseManager
from search_engine import SearchEngine


async def test_real_material_usage():
    """実際のデータベースを使った材料使用テスト"""
    
    # 設定読み込み
    with open('config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # データベースと検索エンジンを初期化
    db_manager = DatabaseManager(config['database']['path'])
    search_engine = SearchEngine(db_manager, config)
    
    # テスト用の材料名
    test_materials = ["石", "木の枝", "トトの羽", "ボアの皮"]
    
    print("=== 実際のデータベースでの材料使用テスト ===\n")
    
    for material in test_materials:
        print(f"--- {material}の使用先を検索 ---")
        
        # 材料を検索
        material_data = await search_engine.search(material)
        if not material_data:
            print(f"❌ {material}がデータベースに見つかりません\n")
            continue
            
        material_info = material_data[0]
        print(f"検索対象: {material_info['formal_name']} ({material_info['item_type']})")
        
        # 関連アイテムを検索
        related_items = await search_engine.search_related_items(material_info)
        
        # 使用先（usage_destinations）の詳細を表示
        if 'usage_destinations' in related_items:
            usage_destinations = related_items['usage_destinations']
            print(f"使用先アイテム数: {len(usage_destinations)}")
            
            for i, usage_item in enumerate(usage_destinations[:5], 1):  # 最初の5件を表示
                item_name = usage_item.get('formal_name', 'Unknown')
                relation_detail = usage_item.get('relation_detail', '')
                required_materials = usage_item.get('required_materials', '')
                
                print(f"  {i}. {item_name}")
                print(f"     必要材料: {required_materials}")
                print(f"     関係詳細: {relation_detail}")
                
                # _extract_material_usage関数の動作を直接テスト
                usage_detail = await search_engine._extract_material_usage(required_materials, material)
                print(f"     抽出結果: '{usage_detail}'")
                
                # 期待される結果と比較
                if material in required_materials and ':' in required_materials:
                    expected_found = True
                    # 実際の数量を抽出してチェック
                    for item in required_materials.split(','):
                        item = item.strip()
                        if ':' in item:
                            mat_name, quantity = item.split(':', 1)
                            if mat_name.strip() == material:
                                expected_detail = f"必要数: {quantity.strip()}"
                                if usage_detail == expected_detail:
                                    print(f"     ✅ 正しく抽出されました")
                                else:
                                    print(f"     ❌ 抽出に問題があります")
                                    print(f"        期待値: '{expected_detail}'")
                                    print(f"        実際値: '{usage_detail}'")
                                break
                else:
                    if usage_detail == '':
                        print(f"     ✅ 正しく処理されました（該当なし）")
                    else:
                        print(f"     ❌ 予期しない結果: '{usage_detail}'")
                
                print()
        else:
            print("❌ usage_destinationsが見つかりません")
        
        print()


if __name__ == "__main__":
    asyncio.run(test_real_material_usage())