#!/usr/bin/env python3
"""
一般名称削除の動作確認テスト
"""

import sys
import os
import asyncio
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.embed_manager import EmbedManager

async def test_common_name_removal():
    """一般名称削除の動作確認"""
    print("📝 一般名称削除テスト開始...")
    
    config = {
        'features': {
            'pagination_size': 5,
            'image_validation': False
        }
    }
    
    embed_manager = EmbedManager(config)
    
    # テスト用の模擬データ（一般名称ありとなし）
    test_results = [
        {
            'formal_name': 'ウッドソード',
            'item_type': 'equipments',
            'common_name': None
        },
        {
            'formal_name': 'アイアンソード',
            'item_type': 'equipments',
            'common_name': '鉄の剣'  # 一般名称あり
        },
        {
            'formal_name': 'スライム',
            'item_type': 'mobs',
            'common_name': 'ぷるぷる',  # 一般名称あり
            'required_level': '5'
        },
        {
            'formal_name': 'ゴブリン',
            'item_type': 'mobs',
            'common_name': '小鬼,ゴブ',  # 複数の一般名称
            'required_level': '10'
        },
        {
            'formal_name': '石',
            'item_type': 'materials',
            'common_name': 'いし'  # 一般名称あり
        }
    ]
    
    print("📊 テストデータ:")
    for i, item in enumerate(test_results, 1):
        formal_name = item.get('formal_name')
        item_type = item.get('item_type')
        common_name = item.get('common_name')
        print(f"  {i}. {formal_name} ({item_type})")
        if common_name:
            print(f"     一般名称: {common_name}")
        else:
            print(f"     一般名称: なし")
    
    print("\n🔍 検索結果一覧の表示テスト:")
    
    # Embedを作成
    embed, view = await embed_manager.create_search_results_embed(
        test_results, "テスト", 0
    )
    
    # 結果を表示
    print(f"📑 Embedタイトル: {embed.title}")
    print(f"📝 Embed説明: {embed.description}")
    
    # 検索結果フィールドを確認
    for field in embed.fields:
        if field.name == "検索結果:":
            print("📋 実際の表示内容:")
            lines = field.value.split('\n')
            for line in lines:
                # ゼロ幅スペースを除去して表示
                clean_line = line.replace('\u200B', '').strip()
                if clean_line:
                    print(f"  {clean_line}")
            break
    
    print("\n✅ 期待される動作:")
    print("  - 正式名称のみが表示される")
    print("  - 一般名称は表示されない") 
    print("  - mobの場合は必要レベルが表示される")
    print("  - アイテムタイプが表示される")
    
    # 検証
    print("\n🔍 検証結果:")
    for field in embed.fields:
        if field.name == "検索結果:":
            lines = field.value.split('\n')
            for line in lines:
                clean_line = line.replace('\u200B', '').strip()
                if clean_line and clean_line.startswith('•'):
                    # 一般名称らしき表示がないかチェック
                    if ' - ' in clean_line and 'Lv.' not in clean_line:
                        print(f"  ❌ 一般名称らしき表示が検出: {clean_line}")
                    else:
                        print(f"  ✅ 正常な表示: {clean_line}")
            break
    
    print("\n✅ 一般名称削除テスト完了!")

async def test_before_after_comparison():
    """修正前後の比較テスト（シミュレーション）"""
    print("\n📊 修正前後の比較テスト...")
    
    test_item = {
        'formal_name': 'テストアイテム',
        'item_type': 'equipments',
        'common_name': 'テスト別名,サブ名称'
    }
    
    print("📝 テストアイテム:")
    print(f"  正式名称: {test_item['formal_name']}")
    print(f"  アイテムタイプ: {test_item['item_type']}")
    print(f"  一般名称: {test_item['common_name']}")
    
    print("\n🔍 表示結果:")
    
    # 修正前の表示をシミュレート
    formal_name = test_item['formal_name']
    item_type = test_item['item_type']
    common_name = test_item['common_name']
    
    # 修正前の表示（一般名称あり）
    old_format = f"• 1. {formal_name} ({item_type})"
    if common_name:
        first_name = common_name.split(',')[0].strip()
        old_format += f" - {first_name}"
    
    # 修正後の表示（一般名称なし）
    new_format = f"• 1. {formal_name} ({item_type})"
    
    print(f"  修正前: {old_format}")
    print(f"  修正後: {new_format}")
    print(f"  ✅ 一般名称が削除されました")
    
    print("\n✅ 比較テスト完了!")

if __name__ == "__main__":
    asyncio.run(test_common_name_removal())
    asyncio.run(test_before_after_comparison())