#!/usr/bin/env python3
"""
実際のデータベースアイテムでの表記ゆれ検索テスト
"""

import sys
import os
import asyncio
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.search_engine import SearchEngine
from src.database import DatabaseManager

async def test_real_variations():
    """実際のデータベースアイテムでの表記ゆれ検索テスト"""
    print("📝 実際のデータでの表記ゆれ検索テスト開始...")
    
    # 設定
    config = {
        'features': {
            'pagination_size': 10
        }
    }
    
    db_manager = DatabaseManager()
    search_engine = SearchEngine(db_manager, config)
    
    # 実際のデータに基づいたテスト
    search_tests = [
        # 既知のアイテムでのかなカナ変換テスト
        ("とと", "トト"),
        ("すらいむ", "スライム"), 
        ("ごぶりん", "ゴブリン"),
        ("おーく", "オーク"),
        ("ぼあ", "ボア"),
        
        # 漢字を含むアイテム
        ("いし", "石"),
        ("ほうせき", "宝石"),
        ("あかいほうせき", "赤い宝石"),
        ("みどりのほうせき", "緑の宝石"),  # 想定される変換
        
        # 武器系
        ("そーど", "ソード"),
        ("あっくす", "アックス"),
        ("すたっふ", "スタッフ"),
    ]
    
    for hira_query, expected_match in search_tests:
        print(f"\n🔍 表記ゆれテスト: '{hira_query}' → '{expected_match}'")
        
        # ひらがなでの検索
        hira_results = await search_engine.search(hira_query)
        
        # カタカナ/漢字での検索
        expected_results = await search_engine.search(expected_match)
        
        print(f"  ひらがな検索: {len(hira_results)}件")
        print(f"  正規検索: {len(expected_results)}件")
        
        if hira_results:
            print("  ひらがな検索結果:")
            for i, result in enumerate(hira_results[:2], 1):
                formal_name = result.get('formal_name', 'Unknown')
                item_type = result.get('item_type', 'unknown')
                print(f"    {i}. {formal_name} [{item_type}]")
        
        if expected_results:
            print("  正規検索結果:")
            for i, result in enumerate(expected_results[:2], 1):
                formal_name = result.get('formal_name', 'Unknown')
                item_type = result.get('item_type', 'unknown')
                print(f"    {i}. {formal_name} [{item_type}]")
        
        # 結果の比較
        if hira_results and expected_results:
            hira_names = {r['formal_name'] for r in hira_results}
            expected_names = {r['formal_name'] for r in expected_results}
            if hira_names & expected_names:  # 共通するアイテムがある
                print("  ✅ 表記ゆれ検索成功")
            else:
                print("  ⚠️ 異なる結果")
        elif not hira_results and not expected_results:
            print("  ➖ 両方とも結果なし")
        elif hira_results:
            print("  ➕ ひらがな検索でのみ結果あり")
        else:
            print("  ➖ ひらがな検索で結果なし")
    
    print("\n✅ 実際のデータでの表記ゆれ検索テスト完了!")

if __name__ == "__main__":
    asyncio.run(test_real_variations())