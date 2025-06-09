#!/usr/bin/env python3
"""
強制的にページネーション機能をテストするため、大きなmax_resultsで検索
"""

import sys
import os
import asyncio
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.search_engine import SearchEngine
from src.database import DatabaseManager
from src.embed_manager import EmbedManager

async def test_forced_pagination():
    """強制的にページネーション機能をテスト"""
    print("📄 強制ページネーションテスト開始...")
    
    # より大きなmax_resultsと小さなページサイズで設定
    config = {
        'features': {
            'pagination_size': 2,  # 2件ずつ表示（小さく）
            'image_validation': False
        }
    }
    
    db_manager = DatabaseManager()
    search_engine = SearchEngine(db_manager, config)
    
    # max_resultsを大きく設定
    search_engine.max_results = 50  # 直接設定
    
    embed_manager = EmbedManager(config)
    
    print(f"🔧 SearchEngine max_results: {search_engine.max_results}")
    print(f"🔧 EmbedManager pagination_size: {config['features']['pagination_size']}")
    
    # 部分一致検索で多くの結果を狙う
    test_queries = [
        "*",           # 全検索
        "*ソード*",    # ソード系
        "*ウッド*",    # ウッド系
        "アイアン",    # アイアン（部分一致）
    ]
    
    for query in test_queries:
        print(f"\n🔍 検索クエリ: '{query}'")
        
        # 検索実行
        results = await search_engine.search(query)
        
        total_count = len(results)
        page_size = config['features']['pagination_size']
        total_pages = (total_count - 1) // page_size + 1 if total_count > 0 else 0
        
        print(f"  📊 検索結果: {total_count}件")
        print(f"  📖 ページ数: {total_pages}ページ")
        
        # 結果の詳細表示
        if results:
            print("  📋 検索結果一覧:")
            for i, item in enumerate(results, 1):
                formal_name = item.get('formal_name', 'Unknown')
                item_type = item.get('item_type', 'unknown')
                print(f"    {i}. {formal_name} [{item_type}]")
        
        # 複数ページがある場合
        if total_pages > 1:
            print(f"  🎯 複数ページ検出! ({total_pages}ページ)")
            
            # 全ページをテスト
            for page_num in range(total_pages):
                print(f"\\n  📄 ページ {page_num + 1}/{total_pages}:")
                
                # Embedとビューを作成
                embed, view = await embed_manager.create_search_results_embed(
                    results, query, page_num
                )
                
                # ページ内容
                start_idx = page_num * page_size
                end_idx = min(start_idx + page_size, total_count)
                page_results = results[start_idx:end_idx]
                
                print("    📋 このページのアイテム:")
                for i, item in enumerate(page_results, start=start_idx + 1):
                    formal_name = item.get('formal_name', 'Unknown')
                    item_type = item.get('item_type', 'unknown')
                    print(f"      {i}. {formal_name} [{item_type}]")
                
                # Embed確認
                print(f"    📑 Embedタイトル: {embed.title}")
                print(f"    📝 Embed説明: {embed.description}")
                if embed.footer:
                    print(f"    🔖 フッター: {embed.footer.text}")
                
                # ボタン状態の詳細確認
                if view:
                    prev_disabled = view.prev_button.disabled
                    next_disabled = view.next_button.disabled
                    
                    # 期待される状態
                    expected_prev_disabled = (page_num == 0)
                    expected_next_disabled = (page_num >= total_pages - 1)
                    
                    print(f"    🎛️ ボタン状態詳細:")
                    print(f"      現在ページ: {page_num + 1}/{total_pages}")
                    print(f"      ◀️ 前ボタン: {'🚫 無効' if prev_disabled else '✅ 有効'}")
                    print(f"      ▶️ 次ボタン: {'🚫 無効' if next_disabled else '✅ 有効'}")
                    print(f"      期待値 - 前: {'無効' if expected_prev_disabled else '有効'}, 次: {'無効' if expected_next_disabled else '有効'}")
                    
                    # 検証
                    prev_correct = prev_disabled == expected_prev_disabled
                    next_correct = next_disabled == expected_next_disabled
                    
                    if prev_correct and next_correct:
                        print("      ✅ ボタン状態完全正常")
                    else:
                        print("      ❌ ボタン状態異常")
                        if not prev_correct:
                            print(f"        前ボタン異常: 実際={prev_disabled}, 期待={expected_prev_disabled}")
                        if not next_correct:
                            print(f"        次ボタン異常: 実際={next_disabled}, 期待={expected_next_disabled}")
                    
                    # セレクトメニューの確認
                    select_menus = [item for item in view.children if hasattr(item, 'options') and hasattr(item, 'placeholder')]
                    if select_menus:
                        menu = select_menus[0]
                        print(f"      📋 セレクトメニュー:")
                        print(f"        プレースホルダー: {menu.placeholder}")
                        print(f"        オプション数: {len(menu.options)}個")
                        print(f"        選択範囲: {menu.min_values}-{menu.max_values}")
                        
                        # オプション内容
                        for j, option in enumerate(menu.options):
                            print(f"        {j + 1}. {option.label} (値: {option.value})")
                else:
                    print("    ❌ Viewが作成されませんでした")
            
            print(f"\\n  ✅ ページネーション機能動作確認完了 ({total_pages}ページ)")
        else:
            print("  📄 単一ページまたは結果なし")
        
        print("  " + "=" * 70)
    
    print("\\n✅ 強制ページネーションテスト完了!")

if __name__ == "__main__":
    asyncio.run(test_forced_pagination())