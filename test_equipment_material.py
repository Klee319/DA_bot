#!/usr/bin/env python3
"""
Equipment と Material の embed 表示テスト
"""

import sys
import os
import asyncio
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.embed_manager import EmbedManager

async def test_equipment_material_embeds():
    """Equipment と Material の embed 表示テスト"""
    print("📝 Equipment/Material Embed表示テスト開始...")
    
    # 設定
    config = {
        'features': {
            'image_validation': False,
            'pagination_size': 10
        }
    }
    
    embed_manager = EmbedManager(config)
    
    # Equipment データ（鍛冶）
    equipment_data = {
        'formal_name': '鋼鉄の剣',
        'item_type': 'equipments',
        'common_name': 'スチールソード',
        'type': '武器',
        'acquisition_category': '鍛冶',
        'required_materials': '鉄鉱石:3,炭:5,皮革:2',
        'item_effect': '攻撃力+50',
        'acquisition_location': '武器屋',
        'description': '基本的な鋼鉄製の剣'
    }
    
    # Equipment データ（モブ討伐）
    equipment_mob_data = {
        'formal_name': '魔獣の牙',
        'item_type': 'equipments',
        'common_name': 'ビーストファング',
        'type': '武器',
        'acquisition_category': 'モブ討伐',
        'required_materials': '獣の牙:10,魔力の結晶:5',
        'item_effect': '攻撃力+80',
        'acquisition_location': 'ボスドロップ',
        'description': '魔獣から入手する強力な武器'
    }
    
    # Material データ
    material_data = {
        'formal_name': '鉄鉱石',
        'item_type': 'materials',
        'common_name': 'アイアンオア',
        'acquisition_category': '採掘',
        'acquisition_method': '地下洞窟での採掘,鉱山での採取',
        'usage_category': '金属加工',
        'usage_purpose': '武器製作,防具製作,装飾品製作',
        'description': '基本的な鉱石素材'
    }
    
    # Equipment embed作成（鍛冶）
    print("\n🛡️ Equipment Embed（鍛冶）:")
    equipment_embed, equipment_view = await embed_manager.create_item_detail_embed(equipment_data, "test_user")
    print(f"タイトル: {equipment_embed.title}")
    print("📋 フィールド内容:")
    for field in equipment_embed.fields:
        field_value = field.value[:100] + "..." if len(field.value) > 100 else field.value
        print(f"[{field.name}] {field_value}")
    
    # Equipment embed作成（モブ討伐）
    print("\n⚔️ Equipment Embed（モブ討伐）:")
    equipment_mob_embed, equipment_mob_view = await embed_manager.create_item_detail_embed(equipment_mob_data, "test_user")
    print(f"タイトル: {equipment_mob_embed.title}")
    print("📋 フィールド内容:")
    for field in equipment_mob_embed.fields:
        field_value = field.value[:100] + "..." if len(field.value) > 100 else field.value
        print(f"[{field.name}] {field_value}")
    
    # Material embed作成
    print("\n🧪 Material Embed:")
    material_embed, material_view = await embed_manager.create_item_detail_embed(material_data, "test_user")
    print(f"タイトル: {material_embed.title}")
    print("📋 フィールド内容:")
    for field in material_embed.fields:
        field_value = field.value[:100] + "..." if len(field.value) > 100 else field.value
        print(f"[{field.name}] {field_value}")
    
    print("\n✅ Equipment/Material Embed表示テスト完了!")

if __name__ == "__main__":
    asyncio.run(test_equipment_material_embeds())