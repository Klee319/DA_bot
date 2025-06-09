#!/usr/bin/env python3
"""
実際のデータを使ったワイルドカード検索のテスト
"""

import sys
import os
import asyncio
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.search_engine import SearchEngine
from src.database import DatabaseManager

async def test_wildcard_real():
    """実際のデータを使ったワイルドカード検索のテスト"""
    print("📝 実際のデータでワイルドカード検索テスト開始...")
    
    # 設定
    config = {
        'features': {
            'pagination_size': 10
        }
    }
    
    db_manager = DatabaseManager()
    search_engine = SearchEngine(db_manager, config)
    
    # 実際のデータに基づいたテストクエリ
    test_queries = [
        "*ソード*",     # 「ソード」を含む装備
        "ウッド*",      # 「ウッド」で始まる装備
        "*スライム",    # 「スライム」で終わるモブ
        "*の*",        # 「の」を含むアイテム
        "*石*",        # 「石」を含むアイテム
        "?ト",         # 2文字目が「ト」のアイテム（?ワイルドカード）
        "???",         # 3文字のアイテム
        "*破片",       # 「破片」で終わる素材
        "魔法石*",     # 「魔法石」で始まる素材
    ]
    
    for query in test_queries:
        print(f"\n🔍 検索クエリ: '{query}'")
        results = await search_engine.search(query)
        
        if results:
            print(f"✅ {len(results)}件の結果:")
            for i, result in enumerate(results[:5], 1):  # 最初の5件のみ表示
                formal_name = result.get('formal_name', 'Unknown')
                item_type = result.get('item_type', 'unknown')
                common_name = result.get('common_name', '')
                display_name = f"{formal_name}"
                if common_name:
                    display_name += f" ({common_name})"
                print(f"  {i}. {display_name} [{item_type}]")
            if len(results) > 5:
                print(f"  ... 他{len(results) - 5}件")
        else:
            print("❌ 結果なし")
    
    print("\n✅ 実際のデータでワイルドカード検索テスト完了!")

if __name__ == "__main__":
    asyncio.run(test_wildcard_real())