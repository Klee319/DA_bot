#!/usr/bin/env python3
"""
検索結果一覧embedのテスト
"""

import sys
import os
import asyncio
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.embed_manager import EmbedManager

async def test_search_results():
    """検索結果一覧embedのテスト"""
    print("📝 検索結果一覧Embed表示テスト開始...")
    
    # 設定
    config = {
        'features': {
            'image_validation': False,
            'pagination_size': 10
        }
    }
    
    embed_manager = EmbedManager(config)
    
    # 検索結果のサンプルデータ
    results = [
        {
            'formal_name': 'ゴブリン',
            'item_type': 'mobs',
            'common_name': 'グリーンゴブリン',
            'required_level': '5'
        },
        {
            'formal_name': '鉄の剣',
            'item_type': 'equipments',
            'common_name': 'アイアンソード'
        },
        {
            'formal_name': '鉄鉱石',
            'item_type': 'materials',
            'common_name': 'アイアンオア'
        },
        {
            'formal_name': 'オークウォリアー',
            'item_type': 'mobs',
            'common_name': 'オーク戦士',
            'required_level': '15'
        }
    ]
    
    # 検索結果embed作成
    print("\n🔍 検索結果一覧 Embed:")
    embed, view = await embed_manager.create_search_results_embed(results, "テスト検索", page=0)
    print(f"タイトル: {embed.title}")
    print("📋 フィールド内容:")
    for field in embed.fields:
        field_value = field.value[:200] + "..." if len(field.value) > 200 else field.value
        print(f"[{field.name}] {field_value}")
    print(f"フッター: {embed.footer.text}")
    
    print("\n✅ 検索結果一覧Embed表示テスト完了!")

if __name__ == "__main__":
    asyncio.run(test_search_results())