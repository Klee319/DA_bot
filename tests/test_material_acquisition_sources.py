#!/usr/bin/env python3
"""
material入手元詳細機能の拡張テスト
"""

import sys
import os
import asyncio
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.search_engine import SearchEngine
from src.database import DatabaseManager
from src.embed_manager import EmbedManager

async def test_material_acquisition_enhancement():
    """material入手元詳細機能の拡張テスト"""
    print("🔧 material入手元詳細機能拡張テスト開始...")
    
    config = {
        'features': {
            'pagination_size': 10,
            'image_validation': False
        }
    }
    
    db_manager = DatabaseManager()
    search_engine = SearchEngine(db_manager, config)
    embed_manager = EmbedManager(config)
    
    # テスト用素材データを作成
    test_materials = [
        {
            'formal_name': '石',
            'item_type': 'materials',
            'acquisition_category': '採掘',
            'acquisition_method': 'つるはしで採掘',
            'acquisition_location': '山岳地帯'
        },
        {
            'formal_name': '木材',
            'item_type': 'materials',
            'acquisition_category': '採取',
            'acquisition_method': '斧で伐採',
            'acquisition_location': '森林エリア'
        },
        {
            'formal_name': 'テスト素材',
            'item_type': 'materials',
            'acquisition_category': '討伐',
            'acquisition_method': 'モンスター討伐',
            'acquisition_location': 'ダンジョン'
        }
    ]
    
    for material in test_materials:
        material_name = material['formal_name']
        print(f"\n📦 テスト素材: {material_name}")
        print(f"   カテゴリ: {material.get('acquisition_category', '不明')}")
        print(f"   方法: {material.get('acquisition_method', '不明')}")
        print(f"   場所: {material.get('acquisition_location', '不明')}")
        
        # 関連アイテム検索を実行
        print("\n🔍 入手元検索実行...")
        related_items = await search_engine.search_related_items(material)
        
        # 結果の詳細表示
        print("📋 検索結果:")
        
        # 1. ドロップ元モブ
        acquisition_sources = related_items.get('acquisition_sources', [])
        print(f"   👹 ドロップ元モブ: {len(acquisition_sources)}件")
        for i, mob in enumerate(acquisition_sources[:3], 1):
            print(f"      {i}. {mob.get('formal_name', 'Unknown')} [{mob.get('item_type', 'unknown')}]")
        
        # 2. 採集場所情報（実装準備）
        gathering_locations = related_items.get('gathering_locations', [])
        print(f"   🌿 採集場所: {len(gathering_locations)}件")
        if gathering_locations:
            for i, location in enumerate(gathering_locations[:3], 1):
                print(f"      {i}. {location.get('location_name', 'Unknown')}")
        else:
            print("      (採集場所テーブル未実装)")
        
        # 3. NPC情報（実装準備）
        npc_sources = related_items.get('npc_sources', [])
        print(f"   👤 NPC交換・購入: {len(npc_sources)}件")
        if npc_sources:
            for i, npc in enumerate(npc_sources[:3], 1):
                print(f"      {i}. {npc.get('npc_name', 'Unknown')}")
        else:
            print("      (NPCテーブル未実装)")
        
        # 4. その他の入手情報
        acquisition_info = related_items.get('acquisition_info', {})
        if acquisition_info:
            print("   📝 その他の入手情報:")
            print(f"      カテゴリ: {acquisition_info.get('category', '不明')}")
            print(f"      方法: {acquisition_info.get('method', '不明')}")
            print(f"      場所: {acquisition_info.get('location', '不明')}")
        
        print("   " + "-" * 50)
    
    print("\n✅ material入手元詳細機能拡張テスト完了!")

async def test_embed_display():
    """Embed表示のテスト"""
    print("\n📑 Embed表示テスト開始...")
    
    config = {
        'features': {
            'pagination_size': 10,
            'image_validation': False
        }
    }
    
    embed_manager = EmbedManager(config)
    
    # モック素材データ
    mock_material = {
        'formal_name': 'テスト素材',
        'item_type': 'materials',
        'acquisition_category': '採取',
        'acquisition_method': '手で採取',
        'acquisition_location': 'テストフィールド'
    }
    
    # モック関連アイテムデータ
    mock_related_items = {
        'acquisition_sources': [
            {
                'formal_name': 'テストモブA',
                'item_type': 'mobs',
                'relation_type': 'drop_from_mob',
                'relation_detail': '討伐ドロップ'
            },
            {
                'formal_name': 'テストモブB',
                'item_type': 'mobs',
                'relation_type': 'drop_from_mob',
                'relation_detail': '討伐ドロップ'
            }
        ],
        'gathering_locations': [
            {
                'location_name': 'テスト採集地A',
                'method': '手で採取',
                'coordinates': '100,200'
            },
            {
                'location_name': 'テスト採集地B',
                'method': 'ツールで採取',
                'coordinates': '150,250'
            }
        ],
        'npc_sources': [
            {
                'npc_name': 'テスト商人',
                'exchange_type': '購入',
                'location': 'テスト町'
            },
            {
                'npc_name': 'テスト交換NPC',
                'exchange_type': '交換',
                'location': 'テストギルド'
            }
        ],
        'acquisition_info': {
            'category': '採取',
            'method': '手で採取',
            'location': 'テストフィールド'
        }
    }
    
    print("📊 モックデータ:")
    print(f"   素材名: {mock_material['formal_name']}")
    print(f"   ドロップ元: {len(mock_related_items['acquisition_sources'])}件")
    print(f"   採集場所: {len(mock_related_items['gathering_locations'])}件")
    print(f"   NPC: {len(mock_related_items['npc_sources'])}件")
    
    # Embedを作成（入手元詳細ボタンのシミュレーション）
    print("\n🎨 Embed作成シミュレーション...")
    
    # AcquisitionDetailsButtonの処理をシミュレート
    embed = discord.Embed(
        title=f"{mock_material['formal_name']} の入手元詳細",
        color=discord.Color.green()
    )
    
    # ドロップ元モブの表示
    if mock_related_items.get('acquisition_sources'):
        field_items = []
        for item in mock_related_items['acquisition_sources'][:5]:
            field_items.append(f"　• 👹 **{item['formal_name']}**")
        field_items[0] = "\u200B" + field_items[0]
        embed.add_field(
            name="**👹 入手元 (討伐):**",
            value="\n".join(field_items),
            inline=False
        )
    
    # 採集場所の表示
    if mock_related_items.get('gathering_locations'):
        gathering_items = []
        for location in mock_related_items['gathering_locations'][:5]:
            location_name = location.get('location_name', '不明')
            gathering_method = location.get('method', '')
            display_text = f"🌿 **{location_name}**"
            if gathering_method:
                display_text += f" ({gathering_method})"
            gathering_items.append(f"　• {display_text}")
        gathering_items[0] = "\u200B" + gathering_items[0]
        embed.add_field(
            name="**🌿 採集場所:**",
            value="\n".join(gathering_items),
            inline=False
        )
    
    # NPC交換・購入の表示
    if mock_related_items.get('npc_sources'):
        npc_items = []
        for npc in mock_related_items['npc_sources'][:5]:
            npc_name = npc.get('npc_name', '不明')
            exchange_type = npc.get('exchange_type', 'その他')
            npc_items.append(f"　• 👤 **{npc_name}** ({exchange_type})")
        npc_items[0] = "\u200B" + npc_items[0]
        embed.add_field(
            name="**👤 NPC交換・購入:**",
            value="\n".join(npc_items),
            inline=False
        )
    
    print("📑 Embed内容:")
    print(f"   タイトル: {embed.title}")
    print(f"   フィールド数: {len(embed.fields)}")
    
    for i, field in enumerate(embed.fields, 1):
        print(f"   フィールド{i}: {field.name}")
        # ゼロ幅スペースを除去して表示
        clean_value = field.value.replace('\u200B', '')
        lines = clean_value.split('\n')
        for line in lines:
            if line.strip():
                print(f"      {line.strip()}")
    
    print("\n✅ Embed表示テスト完了!")

async def test_implementation_readiness():
    """実装準備状況の確認"""
    print("\n🔬 実装準備状況確認...")
    
    print("📋 実装済み機能:")
    print("   ✅ ドロップ元モブ検索")
    print("   ✅ 基本的な入手情報表示")
    print("   ✅ Embed表示フォーマット")
    
    print("\n📋 実装準備済み機能:")
    print("   🔧 採集場所テーブル対応")
    print("   🔧 NPCテーブル対応")
    print("   🔧 複合検索ロジック")
    
    print("\n📋 未実装タスク:")
    print("   ⏳ 採集場所テーブルの作成・データ投入")
    print("   ⏳ NPCテーブルの作成・データ投入")
    print("   ⏳ search_engine._search_gathering_locations の実装")
    print("   ⏳ search_engine._search_npc_sources の実装")
    
    print("\n📋 仕様書:")
    print("   📄 /ref/table_specifications_todo.md に詳細設計を記載")
    
    print("\n✅ 実装準備状況確認完了!")

if __name__ == "__main__":
    # discord.py がインポートできない環境での代替
    try:
        import discord
    except ImportError:
        print("⚠️ discord.py が利用できません。Embedクラスをモック化します。")
        class MockEmbed:
            def __init__(self, title="", color=None):
                self.title = title
                self.color = color
                self.fields = []
            
            def add_field(self, name="", value="", inline=True):
                field = type('Field', (), {'name': name, 'value': value, 'inline': inline})()
                self.fields.append(field)
        
        class MockColor:
            @staticmethod
            def green():
                return "green"
        
        discord = type('discord', (), {
            'Embed': MockEmbed,
            'Color': MockColor
        })()
    
    asyncio.run(test_material_acquisition_enhancement())
    asyncio.run(test_embed_display())
    asyncio.run(test_implementation_readiness())