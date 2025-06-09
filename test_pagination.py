#!/usr/bin/env python3
"""
ページネーション機能のテスト
"""

import sys
import os
import asyncio
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.search_engine import SearchEngine
from src.database import DatabaseManager
from src.embed_manager import EmbedManager

async def test_pagination():
    """ページネーション機能のテスト"""
    print("📄 ページネーション機能テスト開始...")
    
    # 設定
    config = {
        'features': {
            'pagination_size': 3,  # テスト用に小さく設定
            'image_validation': False
        }
    }
    
    db_manager = DatabaseManager()
    search_engine = SearchEngine(db_manager, config)
    embed_manager = EmbedManager(config)
    
    # 複数の結果が得られる検索を実行
    test_queries = [
        "*",        # 全てのアイテム（大量の結果）
        "*ソード*", # ソードを含むアイテム
        "ウッド*",  # ウッドで始まるアイテム
        "*石*",     # 石を含むアイテム
    ]
    
    for query in test_queries:
        print(f"\n🔍 検索クエリ: '{query}'")
        
        # 検索実行
        results = await search_engine.search(query)
        
        if not results:
            print("  ❌ 結果なし")
            continue
        
        print(f"  ✅ {len(results)}件の結果")
        
        # ページネーション計算
        page_size = config['features']['pagination_size']
        total_pages = (len(results) - 1) // page_size + 1
        
        print(f"  📄 ページ数: {total_pages}ページ（1ページあたり{page_size}件）")
        
        # 各ページの内容を確認
        for page in range(min(total_pages, 3)):  # 最初の3ページのみ表示
            print(f"\n  📖 ページ {page + 1}:")
            
            # Embedを作成（実際のDiscord送信はしない）
            embed, view = await embed_manager.create_search_results_embed(
                results, query, page
            )
            
            # ページの内容を確認
            start_idx = page * page_size
            end_idx = start_idx + page_size
            page_results = results[start_idx:end_idx]
            
            for i, item in enumerate(page_results, start=start_idx + 1):
                formal_name = item.get('formal_name', 'Unknown')
                item_type = item.get('item_type', 'unknown')
                print(f"    {i}. {formal_name} [{item_type}]")
            
            # Embedの情報を確認
            print(f"    Embedタイトル: {embed.title}")
            print(f"    Embed説明: {embed.description}")
            print(f"    フッター: {embed.footer.text if embed.footer else 'なし'}")
            
            # Viewのボタン状態を確認
            if view:
                prev_disabled = view.prev_button.disabled
                next_disabled = view.next_button.disabled
                print(f"    前ボタン: {'無効' if prev_disabled else '有効'}")
                print(f"    次ボタン: {'無効' if next_disabled else '有効'}")
        
        if total_pages > 3:
            print(f"  ... 他{total_pages - 3}ページ")
        
        print("  " + "-" * 40)
    
    print("\n✅ ページネーション機能テスト完了!")

async def test_specific_pagination_scenarios():
    """特定のページネーションシナリオをテスト"""
    print("\n📄 特定シナリオのテスト...")
    
    config = {
        'features': {
            'pagination_size': 5,
            'image_validation': False
        }
    }
    
    db_manager = DatabaseManager()
    search_engine = SearchEngine(db_manager, config)
    embed_manager = EmbedManager(config)
    
    scenarios = [
        ("結果が1件のみ", "石"),
        ("結果がちょうどページサイズ", "*ソード*"),
        ("結果がページサイズ+1", "*"),
    ]
    
    for scenario_name, query in scenarios:
        print(f"\n🎯 シナリオ: {scenario_name}")
        print(f"   クエリ: '{query}'")
        
        results = await search_engine.search(query)
        result_count = len(results)
        page_size = config['features']['pagination_size']
        total_pages = (result_count - 1) // page_size + 1 if result_count > 0 else 0
        
        print(f"   結果数: {result_count}件")
        print(f"   ページ数: {total_pages}ページ")
        
        if result_count > 0:
            # 最初のページ
            embed, view = await embed_manager.create_search_results_embed(
                results, query, 0
            )
            
            if view:
                print(f"   1ページ目 - 前ボタン: {'無効' if view.prev_button.disabled else '有効'}")
                print(f"   1ページ目 - 次ボタン: {'無効' if view.next_button.disabled else '有効'}")
            
            # 最後のページ（複数ページある場合）
            if total_pages > 1:
                last_page = total_pages - 1
                embed, view = await embed_manager.create_search_results_embed(
                    results, query, last_page
                )
                
                if view:
                    print(f"   最終ページ - 前ボタン: {'無効' if view.prev_button.disabled else '有効'}")
                    print(f"   最終ページ - 次ボタン: {'無効' if view.next_button.disabled else '有効'}")
        else:
            print("   ❌ 結果なし")
    
    print("\n✅ 特定シナリオテスト完了!")

if __name__ == "__main__":
    asyncio.run(test_pagination())
    asyncio.run(test_specific_pagination_scenarios())