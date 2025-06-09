#!/usr/bin/env python3
"""
サンプルデータを使ったページネーション機能の完全テスト
"""

import sys
import os
import asyncio
import aiosqlite
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.search_engine import SearchEngine
from src.database import DatabaseManager
from src.embed_manager import EmbedManager

async def add_sample_data():
    """テスト用のサンプルデータを追加"""
    print("📦 サンプルデータを追加中...")
    
    sample_equipments = [
        ("アイアンソード", "鉄の剣", "equipments"),
        ("シルバーソード", "銀の剣", "equipments"),
        ("ゴールドソード", "金の剣", "equipments"),
        ("ミスリルソード", "ミスリル剣", "equipments"),
        ("ドラゴンソード", "竜の剣", "equipments"),
        ("アイアンアックス", "鉄の斧", "equipments"),
        ("シルバーアックス", "銀の斧", "equipments"),
        ("バトルアックス", "戦闘斧", "equipments"),
        ("アイアンボウ", "鉄の弓", "equipments"),
        ("エルフボウ", "エルフの弓", "equipments"),
    ]
    
    sample_materials = [
        ("鉄鉱石", "鉄の原石", "materials"),
        ("銀鉱石", "銀の原石", "materials"),
        ("金鉱石", "金の原石", "materials"),
        ("ミスリル鉱石", "ミスリルの原石", "materials"),
        ("木材", "普通の木材", "materials"),
        ("硬い木材", "硬質木材", "materials"),
        ("魔法の木材", "マジック木材", "materials"),
        ("皮", "動物の皮", "materials"),
        ("硬い皮", "硬質な皮", "materials"),
        ("竜の皮", "ドラゴン皮", "materials"),
    ]
    
    sample_mobs = [
        ("オーク戦士", "オーク", "mobs"),
        ("オーク将軍", "オーク長", "mobs"),
        ("コボルト", "小鬼", "mobs"),
        ("ホブゴブリン", "大ゴブリン", "mobs"),
        ("スケルトン", "骸骨", "mobs"),
        ("ゾンビ", "死体", "mobs"),
        ("ヴァンパイア", "吸血鬼", "mobs"),
        ("ウェアウルフ", "狼男", "mobs"),
        ("ドラゴン", "竜", "mobs"),
        ("リッチ", "死霊術師", "mobs"),
    ]
    
    try:
        async with aiosqlite.connect("data/test_items.db") as db:
            # テーブルが存在しない場合は作成
            await db.execute("""
                CREATE TABLE IF NOT EXISTS equipments (
                    formal_name TEXT PRIMARY KEY,
                    common_name TEXT,
                    item_type TEXT DEFAULT 'equipments'
                )
            """)
            
            await db.execute("""
                CREATE TABLE IF NOT EXISTS materials (
                    formal_name TEXT PRIMARY KEY,
                    common_name TEXT,
                    item_type TEXT DEFAULT 'materials'
                )
            """)
            
            await db.execute("""
                CREATE TABLE IF NOT EXISTS mobs (
                    formal_name TEXT PRIMARY KEY,
                    common_name TEXT,
                    item_type TEXT DEFAULT 'mobs'
                )
            """)
            
            # サンプルデータを挿入
            for formal_name, common_name, item_type in sample_equipments:
                await db.execute(
                    f"INSERT OR REPLACE INTO {item_type} (formal_name, common_name) VALUES (?, ?)",
                    (formal_name, common_name)
                )
            
            for formal_name, common_name, item_type in sample_materials:
                await db.execute(
                    f"INSERT OR REPLACE INTO {item_type} (formal_name, common_name) VALUES (?, ?)",
                    (formal_name, common_name)
                )
            
            for formal_name, common_name, item_type in sample_mobs:
                await db.execute(
                    f"INSERT OR REPLACE INTO {item_type} (formal_name, common_name) VALUES (?, ?)",
                    (formal_name, common_name)
                )
            
            await db.commit()
            
            # 追加されたデータ数を確認
            total_count = 0
            for table in ['equipments', 'materials', 'mobs']:
                cursor = await db.execute(f"SELECT COUNT(*) FROM {table}")
                count = (await cursor.fetchone())[0]
                print(f"  {table}: {count}件")
                total_count += count
            
            print(f"📦 総計: {total_count}件のサンプルデータを追加")
            
    except Exception as e:
        print(f"❌ サンプルデータ追加エラー: {e}")

async def test_pagination_with_data():
    """サンプルデータを使ったページネーション機能テスト"""
    print("\n📄 ページネーション機能の完全テスト開始...")
    
    # まずサンプルデータを追加
    await add_sample_data()
    
    # 設定（小さなページサイズ）
    config = {
        'features': {
            'pagination_size': 3,  # 3件ずつ表示
            'image_validation': False
        }
    }
    
    # テスト用データベースを使用
    db_manager = DatabaseManager()
    db_manager.db_path = "data/test_items.db"  # テスト用DBに変更
    
    search_engine = SearchEngine(db_manager, config)
    embed_manager = EmbedManager(config)
    
    # 全体検索で多くの結果を得る
    print("\n🔍 全アイテム検索（ページサイズ3件）:")
    results = await search_engine.search("*")
    
    if not results:
        print("❌ 結果が見つかりません")
        return
    
    total_count = len(results)
    page_size = config['features']['pagination_size']
    total_pages = (total_count - 1) // page_size + 1
    
    print(f"✅ 総件数: {total_count}件")
    print(f"📖 総ページ数: {total_pages}ページ")
    print(f"📄 ページサイズ: {page_size}件/ページ")
    
    # 各ページを表示（最大5ページまで）
    display_pages = min(total_pages, 5)
    for page_num in range(display_pages):
        print(f"\n--- ページ {page_num + 1}/{total_pages} ---")
        
        # Embedとビューを作成
        embed, view = await embed_manager.create_search_results_embed(
            results, "*", page_num
        )
        
        # このページの範囲
        start_idx = page_num * page_size
        end_idx = min(start_idx + page_size, total_count)
        page_results = results[start_idx:end_idx]
        
        # 実際のアイテム表示
        print("📋 このページのアイテム:")
        for i, item in enumerate(page_results, start=start_idx + 1):
            formal_name = item.get('formal_name', 'Unknown')
            item_type = item.get('item_type', 'unknown')
            common_name = item.get('common_name', '')
            display_name = formal_name
            if common_name:
                display_name += f" ({common_name})"
            print(f"  {i}. {display_name} [{item_type}]")
        
        # ビューのボタン状態
        if view:
            print("🎛️ ボタン状態:")
            print(f"  ◀️ 前ページ: {'🚫 無効' if view.prev_button.disabled else '✅ 有効'}")
            print(f"  ▶️ 次ページ: {'🚫 無効' if view.next_button.disabled else '✅ 有効'}")
            
            # 期待される状態と実際の状態を確認
            expected_prev_disabled = (page_num == 0)
            expected_next_disabled = (page_num >= total_pages - 1)
            
            prev_ok = view.prev_button.disabled == expected_prev_disabled
            next_ok = view.next_button.disabled == expected_next_disabled
            
            print(f"  ✅ 前ボタン状態: {'正常' if prev_ok else '異常'}")
            print(f"  ✅ 次ボタン状態: {'正常' if next_ok else '異常'}")
    
    if display_pages < total_pages:
        print(f"\n... 他{total_pages - display_pages}ページ")
    
    # 特定の検索クエリでのテスト
    print("\n🔍 特定検索でのページネーションテスト:")
    specific_queries = ["*ソード*", "*アックス*", "*石*"]
    
    for query in specific_queries:
        print(f"\n📝 クエリ: '{query}'")
        results = await search_engine.search(query)
        
        if results:
            total_count = len(results)
            total_pages = (total_count - 1) // page_size + 1
            print(f"  結果: {total_count}件 ({total_pages}ページ)")
            
            # 複数ページある場合は最初と最後のページのボタン状態を確認
            if total_pages > 1:
                # 最初のページ
                _, first_view = await embed_manager.create_search_results_embed(
                    results, query, 0
                )
                # 最後のページ
                _, last_view = await embed_manager.create_search_results_embed(
                    results, query, total_pages - 1
                )
                
                print(f"  最初のページ: 前={first_view.prev_button.disabled}, 次={first_view.next_button.disabled}")
                print(f"  最後のページ: 前={last_view.prev_button.disabled}, 次={last_view.next_button.disabled}")
            else:
                print("  単一ページ")
        else:
            print("  ❌ 結果なし")
    
    print("\n✅ ページネーション機能の完全テスト完了!")

if __name__ == "__main__":
    asyncio.run(test_pagination_with_data())