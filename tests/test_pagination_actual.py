#!/usr/bin/env python3
"""
実際のデータベースでのページネーション機能テスト
"""

import sys
import os
import asyncio
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.search_engine import SearchEngine
from src.database import DatabaseManager
from src.embed_manager import EmbedManager

async def test_actual_pagination():
    """実際のデータベースでページネーション機能をテスト"""
    print("📄 実際のデータでのページネーション機能テスト開始...")
    
    # 小さなページサイズで設定
    config = {
        'features': {
            'pagination_size': 2,  # 2件ずつ表示
            'image_validation': False
        }
    }
    
    db_manager = DatabaseManager()
    search_engine = SearchEngine(db_manager, config)
    embed_manager = EmbedManager(config)
    
    # 部分一致検索で多くの結果を得る
    test_queries = [
        "*",         # 全検索
        "ウッド",    # ウッド系アイテム
        "石",        # 石系アイテム
        "剣",        # 剣系アイテム（存在するかテスト）
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
        
        # 複数ページがある場合の詳細テスト
        if total_pages > 1:
            print(f"  🎯 複数ページ検出! ページネーション機能をテスト")
            
            # 最初の3ページを表示
            display_pages = min(total_pages, 3)
            
            for page_num in range(display_pages):
                print(f"\\n  --- ページ {page_num + 1}/{total_pages} ---")
                
                # Embedとビューを作成
                embed, view = await embed_manager.create_search_results_embed(
                    results, query, page_num
                )
                
                # このページの内容
                start_idx = page_num * page_size
                end_idx = min(start_idx + page_size, total_count)
                page_results = results[start_idx:end_idx]
                
                # アイテム表示
                for i, item in enumerate(page_results, start=start_idx + 1):
                    formal_name = item.get('formal_name', 'Unknown')
                    item_type = item.get('item_type', 'unknown')
                    print(f"    {i}. {formal_name} [{item_type}]")
                
                # ボタン状態の確認
                if view:
                    prev_disabled = view.prev_button.disabled
                    next_disabled = view.next_button.disabled
                    
                    print(f"    🎛️ ボタン状態:")
                    print(f"      ◀️ 前: {'🚫' if prev_disabled else '✅'}")
                    print(f"      ▶️ 次: {'🚫' if next_disabled else '✅'}")
                    
                    # 期待される状態
                    expected_prev = (page_num == 0)
                    expected_next = (page_num >= total_pages - 1)
                    
                    prev_correct = prev_disabled == expected_prev
                    next_correct = next_disabled == expected_next
                    
                    print(f"      ✅ 前ボタン: {'正常' if prev_correct else '異常'}")
                    print(f"      ✅ 次ボタン: {'正常' if next_correct else '異常'}")
                    
                    # セレクトメニューの確認
                    select_menus = [item for item in view.children if hasattr(item, 'options')]
                    if select_menus:
                        menu = select_menus[0]
                        print(f"      📋 セレクト: {len(menu.options)}個のオプション")
                
                # Embed情報
                if embed.footer:
                    print(f"    🔖 フッター: {embed.footer.text}")
            
            if display_pages < total_pages:
                print(f"\\n  ... 他{total_pages - display_pages}ページ")
                
                # 最後のページもテスト
                last_page = total_pages - 1
                print(f"\\n  --- 最後のページ {last_page + 1}/{total_pages} ---")
                embed, view = await embed_manager.create_search_results_embed(
                    results, query, last_page
                )
                
                if view:
                    print(f"    🎛️ 最後のページのボタン状態:")
                    print(f"      ◀️ 前: {'🚫' if view.prev_button.disabled else '✅'}")
                    print(f"      ▶️ 次: {'🚫' if view.next_button.disabled else '✅'}")
        else:
            print("  📄 単一ページ")
            
            # 単一ページの場合もボタン状態を確認
            embed, view = await embed_manager.create_search_results_embed(
                results, query, 0
            )
            
            if view:
                print(f"    🎛️ ボタン状態: 前={'🚫' if view.prev_button.disabled else '✅'}, 次={'🚫' if view.next_button.disabled else '✅'}")
        
        print("  " + "-" * 50)
    
    print("\\n✅ 実際のデータでのページネーション機能テスト完了!")

async def test_pagination_boundary_cases():
    """境界ケースのテスト"""
    print("\\n🔬 境界ケースのテスト開始...")
    
    config = {
        'features': {
            'pagination_size': 1,  # 1件ずつ（最小ページサイズ）
            'image_validation': False
        }
    }
    
    db_manager = DatabaseManager()
    search_engine = SearchEngine(db_manager, config)
    embed_manager = EmbedManager(config)
    
    # 何らかのアイテムを検索
    results = await search_engine.search("*")
    
    if len(results) >= 2:
        total_count = len(results)
        print(f"📊 {total_count}件のアイテムで境界ケーステスト")
        
        test_cases = [
            (0, "最初のページ"),
            (1, "2ページ目"),
            (total_count - 1, "最後のページ"),
        ]
        
        # 中間ページがある場合は追加
        if total_count > 3:
            middle = total_count // 2
            test_cases.insert(2, (middle, f"中間ページ({middle + 1}ページ目)"))
        
        for page_num, description in test_cases:
            if page_num < total_count:
                print(f"\\n🎯 {description} (ページ{page_num + 1}/{total_count}):")
                
                embed, view = await embed_manager.create_search_results_embed(
                    results, "*", page_num
                )
                
                if view:
                    prev_disabled = view.prev_button.disabled
                    next_disabled = view.next_button.disabled
                    
                    expected_prev = (page_num == 0)
                    expected_next = (page_num >= total_count - 1)
                    
                    print(f"  前ボタン: {'無効' if prev_disabled else '有効'} (期待: {'無効' if expected_prev else '有効'})")
                    print(f"  次ボタン: {'無効' if next_disabled else '有効'} (期待: {'無効' if expected_next else '有効'})")
                    
                    prev_ok = prev_disabled == expected_prev
                    next_ok = next_disabled == expected_next
                    
                    if prev_ok and next_ok:
                        print("  ✅ ボタン状態正常")
                    else:
                        print("  ❌ ボタン状態異常")
    else:
        print("❌ テストに十分なアイテムがありません")
    
    print("\\n✅ 境界ケーステスト完了!")

if __name__ == "__main__":
    asyncio.run(test_actual_pagination())
    asyncio.run(test_pagination_boundary_cases())