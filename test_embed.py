#!/usr/bin/env python3
"""
修正されたembed表示のテスト
"""

import asyncio
import sys
import os
import json
import logging
sys.path.append('./src')

from database import DatabaseManager
from embed_manager import EmbedManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_embed_display():
    """embedの表示テスト"""
    print("📝 Embed表示テスト開始...")
    
    try:
        # 設定読み込み
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # EmbedManager初期化
        embed_manager = EmbedManager(config)
        
        # テスト用のアイテムデータ（モブ）
        mob_item = {
            'id': 1,
            'formal_name': 'ゴブリン',
            'common_name': 'グリーンゴブリン',
            'area': '草原',
            'area_detail': '初心者の草原エリア',
            'required_level': 5,
            'drops': '木の棒,スライムゼリー,小さなナイフ',
            'exp': 15,
            'gold': 10,
            'required_defense': None,
            'description': '最も基本的なモンスター',
            'image_url': None,
            'item_type': 'mobs'
        }
        
        # Embed作成
        embed, view = await embed_manager.create_item_detail_embed(mob_item, "123456789")
        
        print("\n✅ Embed作成成功")
        print(f"タイトル: {embed.title}")
        print(f"色: {embed.color}")
        print(f"フィールド数: {len(embed.fields)}")
        
        print("\n📋 フィールド内容:")
        for field in embed.fields:
            print(f"\n[{field.name}]")
            print(f"{field.value[:100]}...")  # 最初の100文字のみ表示
        
        print("\n🎉 Embed表示テスト完了!")
        
        # 絵文字の確認
        has_emoji = False
        for field in embed.fields:
            if any(ord(c) > 127 and ord(c) not in range(0x3040, 0x30FF) and ord(c) not in range(0x4E00, 0x9FFF) for c in field.name):
                # ASCIIでなく、ひらがな・カタカナ・漢字でもない文字があれば絵文字の可能性
                if '**' not in field.name:  # マークダウンは除外
                    has_emoji = True
                    print(f"⚠️ 絵文字が含まれているフィールド: {field.name}")
        
        if not has_emoji:
            print("✅ 絵文字が正常に削除されています")
        
        return True
        
    except Exception as e:
        logger.error(f"Embed表示テストエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_embed_display())
    sys.exit(0 if success else 1)