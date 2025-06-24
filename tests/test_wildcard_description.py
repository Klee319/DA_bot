#!/usr/bin/env python3
"""ワイルドカードアイテムの説明表示テスト"""

import asyncio
import sys
from pathlib import Path

# プロジェクトのルートディレクトリをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.embed_manager import EmbedManager
from src.database import DatabaseManager
import json

async def test_wildcard_description():
    """ワイルドカード説明機能のテスト"""
    # 設定を読み込む
    with open('config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    db_manager = DatabaseManager()
    embed_manager = EmbedManager(config)
    embed_manager.db_manager = db_manager  # 手動でセット
    
    # テストケース
    test_cases = [
        ("*エフォート・エビデンス", "materials"),
        ("重厚な石剣*", "equipments"),
        ("魔法石*", "materials"),
        ("ゴブリン*", "mobs")
    ]
    
    print("=== ワイルドカード説明検索テスト ===")
    for item_name, item_type in test_cases:
        print(f"\nアイテム名: {item_name} (タイプ: {item_type})")
        
        # ワイルドカード説明を検索
        description = await embed_manager._find_wildcard_item_description(item_name, item_type)
        
        if description:
            print(f"  ✓ 説明が見つかりました: {description[:50]}...")
        else:
            print(f"  ✗ 説明が見つかりませんでした")
            
            # デバッグ情報：クリーンな名前を表示
            import re
            cleaned_name = re.sub(r'[*＊?？]', '', item_name).strip()
            print(f"  → クリーンな名前: {cleaned_name}")

async def test_item_detail_with_wildcard():
    """ワイルドカードアイテムの詳細表示テスト"""
    with open('config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    db_manager = DatabaseManager()
    embed_manager = EmbedManager(config)
    embed_manager.db_manager = db_manager  # 手動でセット
    
    # テスト用のワイルドカードアイテムデータ
    test_item = {
        'id': 999,
        'formal_name': '*テストアイテム',
        'common_name': None,
        'item_type': 'materials',
        'acquisition_category': 'モブ討伐',
        'description': None  # 説明がない
    }
    
    print("\n=== ワイルドカードアイテムの詳細表示テスト ===")
    print(f"アイテム: {test_item['formal_name']} (説明なし)")
    
    # create_item_detail_embedメソッドの部分的なテスト
    # 実際のembedオブジェクトは作成せず、説明検索のみテスト
    description = await embed_manager._find_wildcard_item_description(
        test_item['formal_name'], 
        test_item['item_type']
    )
    
    if description:
        print(f"  ✓ ワイルドカード一致で説明を発見: {description}")
    else:
        print(f"  ✗ 説明が見つかりませんでした")

async def main():
    """メイン処理"""
    print("ワイルドカードアイテムの説明表示機能のテスト\n")
    
    # ワイルドカード説明検索のテスト
    await test_wildcard_description()
    
    # 詳細表示でのワイルドカード対応テスト
    await test_item_detail_with_wildcard()

if __name__ == "__main__":
    asyncio.run(main())