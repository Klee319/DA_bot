#!/usr/bin/env python3
"""レベル/ランク付きアイテムの検索テスト"""

import asyncio
import sys
from pathlib import Path

# プロジェクトのルートディレクトリをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.search_engine import SearchEngine
from src.database import DatabaseManager

async def test_level_rank_removal():
    """レベル/ランク表記の除去テスト"""
    # 実際のconfig.jsonを読み込む
    import json
    with open('config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    db_manager = DatabaseManager()
    search_engine = SearchEngine(db_manager, config)
    
    # レベル/ランク表記の除去テスト
    test_cases = [
        ("魔法石Lv1", "魔法石"),
        ("魔法石Lv.1", "魔法石"),
        ("魔法石lv1", "魔法石"),
        ("魔法石レベル1", "魔法石"),
        ("魔法石ランクA", "魔法石"),
        ("魔法石★★", "魔法石"),
        ("魔法石 1", "魔法石"),
        ("重厚な石剣Lv3", "重厚な石剣"),
    ]
    
    print("=== レベル/ランク表記除去テスト ===")
    for input_text, expected in test_cases:
        result = search_engine._remove_level_rank_suffix(input_text)
        status = "✓" if result == expected else "✗"
        print(f"{status} {input_text} → {result} (期待値: {expected})")
    print()

async def test_level_rank_search():
    """レベル/ランク付きアイテムの検索テスト"""
    # 実際のconfig.jsonを読み込む
    import json
    with open('config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    db_manager = DatabaseManager()
    search_engine = SearchEngine(db_manager, config)
    
    # テスト用のクエリ
    test_queries = [
        "魔法石Lv1",
        "魔法石レベル1",
        "重厚な石剣Lv3",
        "エフォート・エビデンスLv1",
    ]
    
    print("=== レベル/ランク付きアイテム検索テスト ===")
    for query in test_queries:
        print(f"\n検索クエリ: {query}")
        results = await search_engine.search(query)
        
        if results:
            print(f"  見つかりました: {len(results)}件")
            for i, result in enumerate(results[:3]):
                formal_name = result.get('formal_name', result.get('name', '不明'))
                item_type = result.get('item_type', '不明')
                original_query = result.get('original_query', '')
                
                # 表示名の決定（embed_manager.pyと同じロジック）
                display_name = formal_name
                if original_query and ('*' in formal_name or '?' in formal_name):
                    display_name = original_query
                
                print(f"  {i+1}. {display_name} ({item_type})")
                if original_query:
                    print(f"     → DB名: {formal_name}, 検索語: {original_query}")
        else:
            print("  見つかりませんでした")
            # レベル/ランクを除去して基本アイテムを検索
            cleaned_query = search_engine._remove_level_rank_suffix(query)
            if cleaned_query != query:
                print(f"  → 基本アイテム「{cleaned_query}」で再検索します")

async def main():
    """メイン処理"""
    print("レベル/ランク付きアイテム検索機能のテスト\n")
    
    # レベル/ランク除去のテスト
    await test_level_rank_removal()
    
    # 実際の検索テスト
    await test_level_rank_search()

if __name__ == "__main__":
    asyncio.run(main())