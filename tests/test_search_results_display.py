#!/usr/bin/env python3
"""
検索結果一覧表示のテスト（一般名称なし）
"""

import sys
import os
import asyncio
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.search_engine import SearchEngine
from src.database import DatabaseManager
from src.embed_manager import EmbedManager

async def test_search_results_display():
    """検索結果一覧の表示形式をテスト"""
    print("📋 検索結果一覧表示テスト開始...")
    
    # 設定
    config = {
        'features': {
            'pagination_size': 5,  # 5件ずつ表示
            'image_validation': False
        }
    }
    
    db_manager = DatabaseManager()
    search_engine = SearchEngine(db_manager, config)
    search_engine.max_results = 20  # 20件まで取得
    
    embed_manager = EmbedManager(config)
    
    # 複数の検索クエリでテスト
    test_queries = [
        "*ソード*",     # ソード系アイテム
        "*ウッド*",     # ウッド系アイテム
        "アイアン",     # アイアン系アイテム
        "*",           # 全アイテム
    ]
    
    for query in test_queries:
        print(f"\n🔍 検索クエリ: '{query}'")
        
        # 検索実行
        results = await search_engine.search(query)
        
        if not results:
            print("  ❌ 結果なし")
            continue
        
        total_count = len(results)
        page_size = config['features']['pagination_size']
        total_pages = (total_count - 1) // page_size + 1
        
        print(f"  ✅ 総件数: {total_count}件")
        print(f"  📖 総ページ数: {total_pages}ページ")
        
        # 最初のページの表示をテスト
        print(f"\n  📄 1ページ目の表示:")
        
        embed, view = await embed_manager.create_search_results_embed(
            results, query, 0
        )
        
        # Embedのフィールドから検索結果を確認
        for field in embed.fields:
            if field.name == "検索結果:":
                print("    📋 実際の表示内容:")
                lines = field.value.split('\n')
                for line in lines:
                    # ゼロ幅スペースを除去して表示
                    clean_line = line.replace('\u200B', '')
                    print(f"      {clean_line}")
                break
        
        # 詳細な検証
        print("\n  🔍 表示内容の検証:")
        start_idx = 0
        end_idx = min(page_size, total_count)
        page_results = results[start_idx:end_idx]
        
        for i, item in enumerate(page_results, start=1):
            formal_name = item.get('formal_name', 'Unknown')
            item_type = item.get('item_type', 'unknown')
            common_name = item.get('common_name', '')
            required_level = item.get('required_level', '')
            
            print(f"    {i}. アイテム: {formal_name}")
            print(f"       タイプ: {item_type}")
            if common_name:
                print(f"       一般名称: {common_name} (表示されるべきでない)")
            else:
                print(f"       一般名称: なし")
            
            if item_type == 'mobs' and required_level:
                print(f"       必要レベル: {required_level}")
            
            # 期待される表示形式
            expected_format = f"• {i}. {formal_name} ({item_type})"
            if item_type == 'mobs' and required_level:
                try:
                    level_int = int(float(str(required_level).replace(',', '')))
                    expected_format += f" - Lv. {level_int}"
                except (ValueError, TypeError):
                    expected_format += f" - Lv. {required_level}"
            
            print(f"       期待表示: {expected_format}")
            print()
        
        print("  " + "-" * 60)
    
    print("\n✅ 検索結果一覧表示テスト完了!")

async def test_specific_items_with_common_names():
    """一般名称を持つアイテムの表示テスト"""
    print("\n📝 一般名称を持つアイテムの表示テスト...")
    
    config = {
        'features': {
            'pagination_size': 10,
            'image_validation': False
        }
    }
    
    db_manager = DatabaseManager()
    search_engine = SearchEngine(db_manager, config)
    embed_manager = EmbedManager(config)
    
    # 特定のアイテムを検索して一般名称の表示をチェック
    results = await search_engine.search("*")
    
    # 一般名称を持つアイテムがあるかチェック
    items_with_common_names = []
    for item in results:
        common_name = item.get('common_name', '')
        if common_name and str(common_name).strip():
            items_with_common_names.append(item)
    
    if items_with_common_names:
        print(f"  📊 一般名称を持つアイテム: {len(items_with_common_names)}件")
        
        # これらのアイテムを含む検索結果embedを作成
        embed, view = await embed_manager.create_search_results_embed(
            items_with_common_names[:5], "テスト", 0
        )
        
        print("  📋 表示結果:")
        for field in embed.fields:
            if field.name == "検索結果:":
                lines = field.value.split('\n')
                for line in lines:
                    clean_line = line.replace('\u200B', '').strip()
                    if clean_line:
                        print(f"    {clean_line}")
                        # 一般名称が含まれていないことを確認
                        if ' - ' in clean_line and 'Lv.' not in clean_line:
                            print("      ⚠️  警告: 一般名称らしき表示が検出されました")
                        else:
                            print("      ✅ 一般名称は表示されていません")
                break
    else:
        print("  📊 一般名称を持つアイテムが見つかりませんでした")
    
    print("✅ 一般名称テスト完了!")

if __name__ == "__main__":
    asyncio.run(test_search_results_display())
    asyncio.run(test_specific_items_with_common_names())