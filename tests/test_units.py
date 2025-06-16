#!/usr/bin/env python3
"""
単位付き数値表示のテスト
"""

import sys
import os
import asyncio
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.embed_manager import EmbedManager

async def test_units():
    """単位付き数値表示のテスト"""
    print("📝 単位付き数値表示テスト開始...")
    
    # 設定
    config = {
        'features': {
            'image_validation': False,
            'pagination_size': 10
        }
    }
    
    embed_manager = EmbedManager(config)
    
    # 大きな数値のモブデータ
    mob_data = {
        'formal_name': 'ドラゴンキング',
        'item_type': 'mobs',
        'common_name': 'レッドドラゴン',
        'area': '魔王の城',
        'required_level': '85',
        'exp': '12500',
        'gold': '50000',
        'required_defense': '2500',
        'drops': 'ドラゴンの鱗,魔力の結晶,伝説の剣',
        'area_detail': '最終ダンジョン',
        'description': '最強のボスモンスター'
    }
    
    # Embed作成
    print("\n🐉 大きな数値のモブ Embed:")
    embed, view = await embed_manager.create_item_detail_embed(mob_data, "test_user")
    print(f"タイトル: {embed.title}")
    print("📋 フィールド内容:")
    for field in embed.fields:
        field_value = field.value[:100] + "..." if len(field.value) > 100 else field.value
        print(f"[{field.name}] {field_value}")
    
    print("\n✅ 単位付き数値表示テスト完了!")

if __name__ == "__main__":
    asyncio.run(test_units())