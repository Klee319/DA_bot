#!/usr/bin/env python3
"""
全角ワイルドカード検索のテスト
"""

import sys
import os
import asyncio
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.search_engine import SearchEngine
from src.database import DatabaseManager

async def test_fullwidth_wildcard():
    """全角ワイルドカード検索のテスト"""
    print("📝 全角ワイルドカード検索テスト開始...")
    
    # 設定
    config = {
        'features': {
            'pagination_size': 10
        }
    }
    
    db_manager = DatabaseManager()
    search_engine = SearchEngine(db_manager, config)
    
    # 全角と半角のワイルドカード比較テスト
    test_pairs = [
        ("*ソード*", "＊ソード＊"),    # 半角 vs 全角
        ("ウッド*", "ウッド＊"),       # 半角 vs 全角
        ("?ト", "？ト"),              # 半角 vs 全角
        ("???", "？？？"),            # 半角 vs 全角
    ]
    
    for half_query, full_query in test_pairs:
        print(f"\n🔍 比較テスト:")
        print(f"  半角: '{half_query}'")
        print(f"  全角: '{full_query}'")
        
        # 半角での検索
        half_results = await search_engine.search(half_query)
        print(f"  半角結果: {len(half_results)}件")
        
        # 全角での検索
        full_results = await search_engine.search(full_query)
        print(f"  全角結果: {len(full_results)}件")
        
        # 結果が同じかどうか確認
        if len(half_results) == len(full_results):
            half_names = {r['formal_name'] for r in half_results}
            full_names = {r['formal_name'] for r in full_results}
            if half_names == full_names:
                print("  ✅ 結果が一致")
            else:
                print("  ❌ 結果の内容が異なる")
        else:
            print("  ❌ 結果件数が異なる")
        
        # 最初の3件を表示
        if full_results:
            print("  全角検索結果:")
            for i, result in enumerate(full_results[:3], 1):
                formal_name = result.get('formal_name', 'Unknown')
                item_type = result.get('item_type', 'unknown')
                print(f"    {i}. {formal_name} [{item_type}]")
    
    print("\n✅ 全角ワイルドカード検索テスト完了!")

if __name__ == "__main__":
    asyncio.run(test_fullwidth_wildcard())