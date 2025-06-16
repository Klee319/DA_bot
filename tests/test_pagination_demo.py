#!/usr/bin/env python3
"""
ページネーション機能のデモとテスト（小さなページサイズ）
"""

import sys
import os
import asyncio
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.search_engine import SearchEngine
from src.database import DatabaseManager
from src.embed_manager import EmbedManager

async def demo_pagination():
    """ページネーション機能のデモ"""
    print("📄 ページネーション機能デモ開始...")
    
    # 非常に小さなページサイズでテスト
    config = {
        'features': {
            'pagination_size': 2,  # 2件ずつ表示
            'image_validation': False
        }
    }
    
    db_manager = DatabaseManager()
    search_engine = SearchEngine(db_manager, config)
    embed_manager = EmbedManager(config)
    
    # 全体検索で最大の結果を得る
    print("🔍 全アイテム検索（ページサイズ2件）:")
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
    
    # 各ページを詳細表示
    for page_num in range(total_pages):
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
        
        # Embed情報
        print(f"📑 Embedタイトル: {embed.title}")
        print(f"📝 Embed説明: {embed.description}")
        
        if embed.footer:
            print(f"🔖 フッター: {embed.footer.text}")
        
        # ビューのボタン状態
        if view:
            print("🎛️ ボタン状態:")
            print(f"  ◀️ 前ページ: {'🚫 無効' if view.prev_button.disabled else '✅ 有効'}")
            print(f"  ▶️ 次ページ: {'🚫 無効' if view.next_button.disabled else '✅ 有効'}")
            
            # セレクトメニューの状態
            select_menus = [item for item in view.children if hasattr(item, 'options')]
            if select_menus:
                select_menu = select_menus[0]
                print(f"  📋 セレクトメニュー: {len(select_menu.options)}個のオプション")
                for option in select_menu.options:
                    print(f"    - {option.label}")
    
    print("\n✅ ページネーション機能デモ完了!")

async def test_edge_cases():
    """エッジケースのテスト"""
    print("\n🔬 エッジケーステスト開始...")
    
    config = {
        'features': {
            'pagination_size': 1,  # 1件ずつ表示
            'image_validation': False
        }
    }
    
    db_manager = DatabaseManager()
    search_engine = SearchEngine(db_manager, config)
    embed_manager = EmbedManager(config)
    
    # ケース1: 結果が0件
    print("\n📊 ケース1: 結果0件")
    empty_results = await search_engine.search("存在しないアイテム")
    print(f"結果数: {len(empty_results)}件")
    
    # ケース2: 結果が1件
    print("\n📊 ケース2: 結果1件")
    single_results = await search_engine.search("石")
    if single_results:
        print(f"結果数: {len(single_results)}件")
        embed, view = await embed_manager.create_search_results_embed(
            single_results, "石", 0
        )
        if view:
            print(f"前ボタン: {'無効' if view.prev_button.disabled else '有効'}")
            print(f"次ボタン: {'無効' if view.next_button.disabled else '有効'}")
    
    # ケース3: 複数ページ（ページサイズ1）
    print("\n📊 ケース3: 複数ページ（1件/ページ）")
    multi_results = await search_engine.search("*")
    if len(multi_results) > 1:
        total_pages = len(multi_results)
        print(f"結果数: {len(multi_results)}件")
        print(f"ページ数: {total_pages}ページ")
        
        # 最初のページ
        embed, view = await embed_manager.create_search_results_embed(
            multi_results, "*", 0
        )
        print("最初のページ:")
        if view:
            print(f"  前ボタン: {'無効' if view.prev_button.disabled else '有効'}")
            print(f"  次ボタン: {'無効' if view.next_button.disabled else '有効'}")
        
        # 中間のページ（もしあれば）
        if total_pages > 2:
            middle_page = total_pages // 2
            embed, view = await embed_manager.create_search_results_embed(
                multi_results, "*", middle_page
            )
            print(f"中間ページ({middle_page + 1}ページ目):")
            if view:
                print(f"  前ボタン: {'無効' if view.prev_button.disabled else '有効'}")
                print(f"  次ボタン: {'無効' if view.next_button.disabled else '有効'}")
        
        # 最後のページ
        last_page = total_pages - 1
        embed, view = await embed_manager.create_search_results_embed(
            multi_results, "*", last_page
        )
        print("最後のページ:")
        if view:
            print(f"  前ボタン: {'無効' if view.prev_button.disabled else '有効'}")
            print(f"  次ボタン: {'無効' if view.next_button.disabled else '有効'}")
    
    print("\n✅ エッジケーステスト完了!")

if __name__ == "__main__":
    asyncio.run(demo_pagination())
    asyncio.run(test_edge_cases())