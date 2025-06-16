#!/usr/bin/env python3
"""
ボタンラベルのテスト
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.embed_manager import EmbedManager, ItemDetailView

def test_button_labels():
    """ボタンラベルのテスト"""
    print("🔘 ボタンラベルテスト開始...")
    
    # 設定
    config = {
        'features': {
            'image_validation': False,
            'pagination_size': 10
        }
    }
    
    embed_manager = EmbedManager(config)
    
    # モブデータ
    mob_data = {
        'formal_name': 'ゴブリン',
        'item_type': 'mobs',
        'common_name': 'グリーンゴブリン',
        'area': '草原',
        'required_level': '5',
        'exp': '15',
        'gold': '10',
        'drops': '木の棒,スライムゼリー,小さなナイフ',
        'area_detail': '初心者の草原エリア',
        'description': '最も基本的なモンスター'
    }
    
    # 素材データ
    material_data = {
        'formal_name': '鉄鉱石',
        'item_type': 'materials',
        'common_name': 'アイアンオア',
        'acquisition_category': '採掘',
        'acquisition_method': '地下洞窟での採掘',
        'usage_category': '金属加工',
        'usage_purpose': '武器製作,防具製作',
        'description': '基本的な鉱石'
    }
    
    # ビューを作成してボタンを確認
    print("\n📱 モブ用ビュー:")
    mob_view = ItemDetailView(mob_data, "test_user", embed_manager)
    for item in mob_view.children:
        if hasattr(item, 'label'):
            print(f"  ボタン: {item.label}")
    
    print("\n📱 素材用ビュー:")
    material_view = ItemDetailView(material_data, "test_user", embed_manager)
    for item in material_view.children:
        if hasattr(item, 'label'):
            print(f"  ボタン: {item.label}")
    
    print("\n✅ ボタンラベルテスト完了!")

if __name__ == "__main__":
    test_button_labels()