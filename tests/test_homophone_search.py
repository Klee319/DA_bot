#!/usr/bin/env python3
"""
同音異字・表記ゆれ検索のテスト
"""

import sys
import os
import asyncio
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.search_engine import SearchEngine
from src.database import DatabaseManager

async def test_homophone_search():
    """同音異字・表記ゆれ検索のテスト"""
    print("📝 同音異字・表記ゆれ検索テスト開始...")
    
    # 設定
    config = {
        'features': {
            'pagination_size': 10
        }
    }
    
    db_manager = DatabaseManager()
    search_engine = SearchEngine(db_manager, config)
    
    # バリエーション生成のテスト
    print("\n🔧 バリエーション生成テスト:")
    test_queries = [
        "けん",      # 剣
        "いし",      # 石
        "てつ",      # 鉄
        "りゅう",    # 龍/竜
        "あか",      # 赤
        "ひかり",    # 光
        "剣",        # けん
        "石",        # いし
        "ドラゴン",  # カタカナ
    ]
    
    for query in test_queries:
        variations = search_engine._generate_query_variations(query)
        print(f"'{query}' → {variations[:5]}{'...' if len(variations) > 5 else ''} ({len(variations)}個)")
    
    # 実際の検索テスト
    print("\n🔍 実際の検索テスト:")
    search_tests = [
        ("けん", "「剣」系アイテムを読み仮名で検索"),
        ("いし", "「石」系アイテムを読み仮名で検索"),
        ("てつ", "「鉄」系アイテムを読み仮名で検索"),
        ("石", "「石」系アイテムを漢字で検索"),
        ("スライム", "カタカナでモンスター検索"),
        ("すらいむ", "ひらがなでモンスター検索"),
        ("ゴブリン", "カタカナでモンスター検索"),
        ("ごぶりん", "ひらがなでモンスター検索"),
    ]
    
    for query, description in search_tests:
        print(f"\n🎯 {description}")
        print(f"検索クエリ: '{query}'")
        
        results = await search_engine.search(query)
        
        if results:
            print(f"✅ {len(results)}件の結果:")
            for i, result in enumerate(results[:3], 1):  # 最初の3件のみ表示
                formal_name = result.get('formal_name', 'Unknown')
                item_type = result.get('item_type', 'unknown')
                common_name = result.get('common_name', '')
                display_name = f"{formal_name}"
                if common_name:
                    display_name += f" ({common_name})"
                print(f"  {i}. {display_name} [{item_type}]")
            if len(results) > 3:
                print(f"  ... 他{len(results) - 3}件")
        else:
            print("❌ 結果なし")
    
    print("\n✅ 同音異字・表記ゆれ検索テスト完了!")

if __name__ == "__main__":
    asyncio.run(test_homophone_search())