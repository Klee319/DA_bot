import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from database import DatabaseManager
from search_engine import SearchEngine
import json

async def test_material_search():
    """木の棒を検索するテスト"""
    
    # 設定ファイルを読み込む
    with open('config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    db = DatabaseManager()
    search_engine = SearchEngine(db, config)
    
    print("=== 木の棒の検索テスト ===\n")
    
    # 木の棒を検索
    print("「木の棒」を検索中...")
    results = await search_engine.search("木の棒")
    
    if results:
        for i, result in enumerate(results):
            print(f"\n結果 {i+1}:")
            print(f"  正式名称: {result['formal_name']}")
            print(f"  一般名称: {result.get('common_name', 'なし')}")
            print(f"  タイプ: {result['item_type']}")
    else:
        print("見つかりませんでした")
        
        # データベースで直接確認
        import sqlite3
        conn = sqlite3.connect('data/items.db')
        cursor = conn.cursor()
        
        print("\n材料テーブルで「木」を含むアイテムを検索:")
        cursor.execute("SELECT formal_name FROM materials WHERE formal_name LIKE '%木%' LIMIT 10")
        for row in cursor.fetchall():
            print(f"  - {row[0]}")
            
        print("\nウッドソードの必要素材を確認:")
        cursor.execute("SELECT required_materials FROM equipments WHERE formal_name = 'ウッドソード'")
        result = cursor.fetchone()
        if result:
            print(f"  必要素材: {result[0]}")
        
        conn.close()

if __name__ == "__main__":
    asyncio.run(test_material_search())