#!/usr/bin/env python3
"""
_extract_material_usage関数のテストスクリプト
「石:9」のような形式から数量が正しく抽出されるかを確認
"""

import asyncio
import sys
import os

# パスを追加してsrcモジュールをインポート可能にする
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from search_engine import SearchEngine


async def test_extract_material_usage():
    """_extract_material_usage関数のテスト"""
    
    # 疑似的なSearchEngineインスタンスを作成
    # db_managerとconfigは実際には使用されないのでNoneでOK
    search_engine = SearchEngine(None, {'features': {'pagination_size': 20}})
    
    # テストケース
    test_cases = [
        # (materials_str, target_material, expected_result)
        ("石:9", "石", "必要数: 9"),
        ("木の棒:8,トトの羽:4", "木の棒", "必要数: 8"),
        ("木の棒:8,トトの羽:4", "トトの羽", "必要数: 4"),
        ("石:9,鉄:5,木:3", "鉄", "必要数: 5"),
        ("石:9,鉄:5,木:3", "木", "必要数: 3"),
        ("石:9,鉄:5,木:3", "存在しない素材", ""),
        ("", "石", ""),
        ("石", "石", ""),  # 数量が指定されていない場合
        ("石:9", "違う素材", ""),
        ("石:10,石:20", "石", "必要数: 10"),  # 重複がある場合（最初にマッチしたもの）
        ("水の石:5", "石", ""),  # 部分一致しないことを確認
        ("石の欠片:3", "石", ""),  # 部分一致しないことを確認
        ("石:15,水の石:2", "石", "必要数: 15"),  # 完全一致を優先
    ]
    
    print("=== _extract_material_usage関数のテスト ===\n")
    
    for i, (materials_str, target_material, expected) in enumerate(test_cases, 1):
        try:
            result = await search_engine._extract_material_usage(materials_str, target_material)
            
            status = "✅ OK" if result == expected else "❌ NG"
            print(f"テスト{i}: {status}")
            print(f"  入力: materials_str='{materials_str}', target_material='{target_material}'")
            print(f"  期待値: '{expected}'")
            print(f"  実際値: '{result}'")
            
            if result != expected:
                print(f"  ❌ 不一致が検出されました！")
            print()
            
        except Exception as e:
            print(f"テスト{i}: ❌ エラー")
            print(f"  入力: materials_str='{materials_str}', target_material='{target_material}'")
            print(f"  エラー: {e}")
            print()
    
    print("=== テスト完了 ===")


async def test_parse_material_list_with_quantity():
    """_parse_material_list_with_quantity関数のテスト"""
    
    search_engine = SearchEngine(None, {'features': {'pagination_size': 20}})
    
    test_cases = [
        ("石:9", [("石", "9")]),
        ("木の棒:8,トトの羽:4", [("木の棒", "8"), ("トトの羽", "4")]),
        ("石:9,鉄:5,木:3", [("石", "9"), ("鉄", "5"), ("木", "3")]),
        ("", []),
        ("石", [("石", "1")]),  # 数量が指定されていない場合は1
        ("石:10, 鉄:20 ", [("石", "10"), ("鉄", "20")]),  # 空白の処理
    ]
    
    print("\n=== _parse_material_list_with_quantity関数のテスト ===\n")
    
    for i, (materials_str, expected) in enumerate(test_cases, 1):
        try:
            result = await search_engine._parse_material_list_with_quantity(materials_str)
            
            status = "✅ OK" if result == expected else "❌ NG"
            print(f"テスト{i}: {status}")
            print(f"  入力: '{materials_str}'")
            print(f"  期待値: {expected}")
            print(f"  実際値: {result}")
            
            if result != expected:
                print(f"  ❌ 不一致が検出されました！")
            print()
            
        except Exception as e:
            print(f"テスト{i}: ❌ エラー")
            print(f"  入力: '{materials_str}'")
            print(f"  エラー: {e}")
            print()
    
    print("=== テスト完了 ===")


if __name__ == "__main__":
    asyncio.run(test_extract_material_usage())
    asyncio.run(test_parse_material_list_with_quantity())