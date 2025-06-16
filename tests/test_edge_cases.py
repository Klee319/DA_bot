#!/usr/bin/env python3
"""
_extract_material_usage関数のエッジケーステスト
"""

import asyncio
import sys
import os

# パスを追加してsrcモジュールをインポート可能にする
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from search_engine import SearchEngine


async def test_edge_cases():
    """エッジケースのテスト"""
    
    # 疑似的なSearchEngineインスタンスを作成
    search_engine = SearchEngine(None, {'features': {'pagination_size': 20}})
    
    # エッジケース
    edge_cases = [
        # (materials_str, target_material, expected_result, description)
        ("石:9,石:15", "石", "必要数: 9", "重複する材料名（最初の一致を返す）"),
        ("石の欠片:3,石:9", "石", "必要数: 9", "部分一致せず完全一致のみ"),
        ("水の石:5,石:7", "石", "必要数: 7", "部分一致と完全一致が混在"),
        ("石:abc", "石", "必要数: abc", "数値以外の数量"),
        ("石:", "石", "必要数: ", "空の数量"),
        ("石::9", "石", "必要数: :9", "複数コロンの処理"),
        ("石 : 9", "石", "", "スペースを含む材料名（マッチしない）"),
        ("石:9:15", "石", "必要数: 9:15", "数量部分にコロンが含まれる"),
        ("石材:9", "石", "", "類似名称はマッチしない"),
        ("鉄の石:8", "石", "", "材料名の一部がターゲットと同じ"),
        ("、石:9,鉄:5", "石", "必要数: 9", "先頭に余分な文字がある"),
        ("石:9、", "石", "必要数: 9", "末尾に余分な文字がある"),
        ("石:9,", "石", "必要数: 9", "末尾にカンマがある"),
        (",石:9", "石", "必要数: 9", "先頭にカンマがある"),
        ("  石  :  9  ", "石", "", "スペースを含む場合"),
        ("石石:9", "石", "", "重複文字を含む材料名"),
        ("石材の石:5", "石材", "", "長い名前の部分一致"),
        ("STONE:9", "石", "", "英語名は一致しない"),
        ("石:+9", "石", "必要数: +9", "符号付き数値"),
        ("石:-5", "石", "必要数: -5", "負の数値"),
    ]
    
    print("=== _extract_material_usageエッジケーステスト ===\n")
    
    for i, (materials_str, target_material, expected, description) in enumerate(edge_cases, 1):
        try:
            result = await search_engine._extract_material_usage(materials_str, target_material)
            
            status = "✅ OK" if result == expected else "❌ NG"
            print(f"テスト{i}: {status} - {description}")
            print(f"  入力: materials_str='{materials_str}', target_material='{target_material}'")
            print(f"  期待値: '{expected}'")
            print(f"  実際値: '{result}'")
            
            if result != expected:
                print(f"  ❌ 不一致が検出されました！")
            print()
            
        except Exception as e:
            print(f"テスト{i}: ❌ エラー - {description}")
            print(f"  入力: materials_str='{materials_str}', target_material='{target_material}'")
            print(f"  エラー: {e}")
            print()
    
    print("=== テスト完了 ===")


if __name__ == "__main__":
    asyncio.run(test_edge_cases())