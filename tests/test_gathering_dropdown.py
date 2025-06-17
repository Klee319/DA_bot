#!/usr/bin/env python3
"""
採集詳細画面のドロップダウン機能テスト
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database import DatabaseManager
from src.search_engine import SearchEngine
from src.embed_manager import EmbedManager
import json

# 設定ファイルを読み込み
with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

async def test_gathering_dropdown():
    """採集詳細画面のドロップダウン機能をテスト"""
    db = DatabaseManager()
    search_engine = SearchEngine(db, config)
    embed_manager = EmbedManager(config)
    
    print("=== 採集詳細画面のドロップダウン機能テスト ===\n")
    
    # 1. 採集系の素材を検索
    print("1. 採集系素材「木の棒」を検索")
    results = await search_engine.search("木の棒")
    
    if results:
        print(f"   - 検索結果: {len(results)}件")
        for result in results:
            print(f"     - {result['formal_name']} ({result['item_type']})")
            if result['item_type'] == 'materials':
                print(f"       入手カテゴリ: {result.get('acquisition_category', '')}")
                print(f"       入手方法: {result.get('acquisition_method', '')}")
    else:
        print("   - 結果なし")
    
    print("\n2. 採集場所情報を検索")
    # gatheringsテーブルから採集場所を検索
    import aiosqlite
    async with aiosqlite.connect(db.db_path) as conn:
        conn.row_factory = aiosqlite.Row
        
        # 採集・採掘・釣りの場所を検索
        cursor = await conn.execute(
            "SELECT * FROM gatherings WHERE collection_method IN ('採取', '採掘', '釣り') LIMIT 5"
        )
        rows = await cursor.fetchall()
        
        if rows:
            print(f"   - 採集場所: {len(rows)}件")
            for row in rows:
                gathering = dict(row)
                print(f"\n   場所: {gathering.get('location', '')}")
                print(f"   方法: {gathering.get('collection_method', '')}")
                print(f"   入手可能素材: {gathering.get('obtained_materials', '')}")
                
                # 入手可能素材をパース
                materials_str = gathering.get('obtained_materials', '')
                if materials_str:
                    materials = [m.strip() for m in materials_str.split(',')]
                    print(f"   素材リスト: {materials}")
        else:
            print("   - 採集場所情報なし")
    
    print("\n3. 関連アイテム検索のテスト")
    # 素材の関連アイテムを検索
    if results and results[0]['item_type'] == 'materials':
        print(f"   - 「{results[0]['formal_name']}」の関連アイテムを検索")
        related = await search_engine.search_related_items(results[0])
        
        if related.get('acquisition_sources'):
            gathering_sources = [s for s in related['acquisition_sources'] if s.get('relation_type') == 'gathering_location']
            print(f"   - 採集場所: {len(gathering_sources)}件")
            for source in gathering_sources[:3]:
                print(f"     - {source.get('location', '')} ({source.get('collection_method', '')})")

if __name__ == "__main__":
    asyncio.run(test_gathering_dropdown())