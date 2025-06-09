#!/usr/bin/env python3
"""
大量結果でのページネーション機能テスト
"""

import sys
import os
import asyncio
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.search_engine import SearchEngine
from src.database import DatabaseManager
from src.embed_manager import EmbedManager

async def test_large_result_pagination():
    """大量の検索結果でのページネーション機能テスト"""
    print("📄 大量結果でのページネーション機能テスト開始...")
    
    # 小さなページサイズで設定
    config = {
        'features': {
            'pagination_size': 4,  # 4件ずつ表示
            'image_validation': False
        }
    }
    
    db_manager = DatabaseManager()
    search_engine = SearchEngine(db_manager, config)
    embed_manager = EmbedManager(config)
    
    # より包括的な検索クエリを試す
    test_queries = [
        "アイアン*",      # アイアン系アイテム
        "*ソード*",       # ソードを含むアイテム
        "*アックス*",     # アックスを含むアイテム
        "*",              # 全アイテム（制限付き）
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
        
        # アイテム一覧を表示
        print("  📋 検索結果:")
        for i, item in enumerate(results[:12], 1):  # 最初の12件
            formal_name = item.get('formal_name', 'Unknown')
            item_type = item.get('item_type', 'unknown')
            print(f"    {i}. {formal_name} [{item_type}]")
        if total_count > 12:
            print(f"    ... 他{total_count - 12}件")
        
        # 複数ページの場合はページネーション機能をテスト
        if total_pages > 1:
            print(f"  🎯 複数ページ検出! ページネーション機能をテスト")
            
            # 最初の3ページをテスト
            test_pages = min(total_pages, 3)
            
            for page_num in range(test_pages):
                print(f"\\n  --- ページ {page_num + 1}/{total_pages} ---")
                
                # Embedとビューを作成
                embed, view = await embed_manager.create_search_results_embed(
                    results, query, page_num
                )
                
                # ページ内容確認
                start_idx = page_num * page_size
                end_idx = min(start_idx + page_size, total_count)
                page_results = results[start_idx:end_idx]
                
                print("    📄 このページのアイテム:")
                for i, item in enumerate(page_results, start=start_idx + 1):
                    formal_name = item.get('formal_name', 'Unknown')
                    item_type = item.get('item_type', 'unknown')
                    print(f"      {i}. {formal_name} [{item_type}]")
                
                # Embed情報確認
                print(f"    📑 Embedタイトル: {embed.title}")
                print(f"    📝 Embed説明: {embed.description}")
                if embed.footer:
                    print(f"    🔖 フッター: {embed.footer.text}")
                
                # ボタン状態確認
                if view:
                    prev_disabled = view.prev_button.disabled
                    next_disabled = view.next_button.disabled
                    
                    # 期待される状態
                    expected_prev = (page_num == 0)
                    expected_next = (page_num >= total_pages - 1)
                    
                    print(f"    🎛️ ボタン状態:")
                    print(f"      ◀️ 前ページ: {'🚫 無効' if prev_disabled else '✅ 有効'} (期待: {'無効' if expected_prev else '有効'})")
                    print(f"      ▶️ 次ページ: {'🚫 無効' if next_disabled else '✅ 有効'} (期待: {'無効' if expected_next else '有効'})")
                    
                    # 正常性チェック
                    prev_ok = prev_disabled == expected_prev
                    next_ok = next_disabled == expected_next
                    
                    if prev_ok and next_ok:
                        print("      ✅ ボタン状態正常")
                    else:
                        print("      ❌ ボタン状態異常")
                        if not prev_ok:
                            print(f"        前ボタン異常: 実際={prev_disabled}, 期待={expected_prev}")
                        if not next_ok:
                            print(f"        次ボタン異常: 実際={next_disabled}, 期待={expected_next}")
                    
                    # セレクトメニュー確認
                    select_menus = [item for item in view.children if hasattr(item, 'options')]
                    if select_menus:
                        menu = select_menus[0]
                        print(f"      📋 セレクトメニュー: {len(menu.options)}個のオプション")
                        
                        # オプションの内容確認
                        for option in menu.options[:3]:  # 最初の3つのオプション
                            print(f"        - {option.label}")
                        if len(menu.options) > 3:
                            print(f"        ... 他{len(menu.options) - 3}個")
            
            # 最後のページも確認（前の3ページに含まれていない場合）
            if total_pages > 3:
                last_page = total_pages - 1
                print(f"\\n  --- 最後のページ {last_page + 1}/{total_pages} ---")
                
                embed, view = await embed_manager.create_search_results_embed(
                    results, query, last_page
                )
                
                if view:
                    print(f"    🎛️ 最後のページボタン状態:")
                    print(f"      ◀️ 前: {'🚫' if view.prev_button.disabled else '✅'}")
                    print(f"      ▶️ 次: {'🚫' if view.next_button.disabled else '✅'}")
                    
                    # 最後のページは前有効、次無効でなければならない
                    if not view.prev_button.disabled and view.next_button.disabled:
                        print("      ✅ 最後のページ状態正常")
                    else:
                        print("      ❌ 最後のページ状態異常")
        else:
            print("  📄 単一ページ（ページネーション不要）")
            
            # 単一ページでもボタン状態確認
            embed, view = await embed_manager.create_search_results_embed(
                results, query, 0
            )
            
            if view:
                if view.prev_button.disabled and view.next_button.disabled:
                    print("    ✅ 単一ページボタン状態正常（両方無効）")
                else:
                    print("    ❌ 単一ページボタン状態異常")
        
        print("  " + "=" * 60)
    
    print("\\n✅ 大量結果でのページネーション機能テスト完了!")

async def test_pagination_navigation_simulation():
    """ページネーション操作のシミュレーション"""
    print("\\n🎮 ページネーション操作シミュレーション開始...")
    
    config = {
        'features': {
            'pagination_size': 3,
            'image_validation': False
        }
    }
    
    db_manager = DatabaseManager()
    search_engine = SearchEngine(db_manager, config)
    embed_manager = EmbedManager(config)
    
    # 多くの結果が期待できる検索
    results = await search_engine.search("*ソード*")
    
    if len(results) > 3:  # 複数ページがある場合
        total_pages = (len(results) - 1) // 3 + 1
        print(f"📖 {len(results)}件の結果で{total_pages}ページのナビゲーションをシミュレート")
        
        # ページを順番に移動するシミュレーション
        for page in range(total_pages):
            print(f"\\n📄 ページ {page + 1} に移動:")
            
            embed, view = await embed_manager.create_search_results_embed(
                results, "*ソード*", page
            )
            
            # ページ内容表示
            start_idx = page * 3
            end_idx = min(start_idx + 3, len(results))
            for i in range(start_idx, end_idx):
                item = results[i]
                print(f"  {i + 1}. {item.get('formal_name', 'Unknown')}")
            
            # ナビゲーション状態
            if view:
                can_prev = not view.prev_button.disabled
                can_next = not view.next_button.disabled
                
                nav_options = []
                if can_prev:
                    nav_options.append("◀️ 前へ")
                if can_next:
                    nav_options.append("次へ ▶️")
                
                if nav_options:
                    print(f"  🎛️ 利用可能な操作: {', '.join(nav_options)}")
                else:
                    print("  🎛️ 利用可能な操作: なし（最初で最後のページ）")
        
        print("\\n✅ ナビゲーションシミュレーション完了")
    else:
        print("❌ 複数ページのデータが見つかりません")

if __name__ == "__main__":
    asyncio.run(test_large_result_pagination())
    asyncio.run(test_pagination_navigation_simulation())