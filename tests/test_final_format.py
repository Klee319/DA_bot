import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from database import DatabaseManager
from search_engine import SearchEngine
from embed_manager import EmbedManager, ItemDetailView
import json

async def test_final_format():
    """最終フォーマットのテスト"""
    
    # 設定ファイルを読み込む
    with open('config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    db = DatabaseManager()
    search_engine = SearchEngine(db, config)
    embed_manager = EmbedManager(config)
    
    print("=== 最終フォーマットのテスト ===\n")
    
    # テスト1: material（素材）のボタンテスト
    print("【テスト1: 石（素材）のボタンラベル確認】")
    material_results = await search_engine.search("石")
    if material_results:
        material = material_results[0]
        print(f"検索対象: {material['formal_name']} (type: {material['item_type']})")
        
        # ItemDetailViewを作成
        view = ItemDetailView(material, "test_user", embed_manager)
        
        # 追加されたボタンを確認
        button_labels = []
        for item in view.children:
            if hasattr(item, 'label'):
                button_labels.append(item.label)
        
        print(f"ボタンラベル: {button_labels}")
        
        # 関連アイテムを取得してフォーマット確認
        related_items = await search_engine.search_related_items(material)
        
        if related_items.get('usage_destinations'):
            print(f"利用先データ例:")
            for i, item in enumerate(related_items['usage_destinations'][:3]):
                usage_detail = item.get('relation_detail', '')
                print(f"  {i+1}. {item['formal_name']} - {usage_detail}")
    
    print("\n" + "-"*50 + "\n")
    
    # テスト2: mob（モンスター）のドロップアイテムフォーマット確認
    print("【テスト2: トト（モンスター）のドロップアイテムフォーマット】")
    mob_results = await search_engine.search("トト")
    if mob_results:
        mob = mob_results[0]
        print(f"検索対象: {mob['formal_name']} (type: {mob['item_type']})")
        
        # 基本のドロップ品データを確認
        drops = mob.get('drops', '')
        if drops:
            drop_items = [item.strip() for item in str(drops).split(',') if item.strip()]
            print(f"ドロップ品リスト: {drop_items}")
            
            # フォーマット例を表示
            print(f"新フォーマット例:")
            print(f"```")
            print(f"{', '.join(drop_items)}")
            print(f"```")
    
    print("\n" + "="*50)
    print("修正内容:")
    print("1. 絵文字をすべて削除")
    print("   - ボタンラベル: '入手元詳細', '利用先詳細'")
    print("   - embedのタイトル、フィールド名から絵文字削除")
    print("2. カテゴリ表記をテキストブロック形式に変更")
    print("   - 箇条書き（• item1, • item2）→ カンマ区切り（item1, item2）")
    print("   - テキストブロック（```内容```）で囲む")
    print("3. 項目見出しから「**」削除、「:」を付けず改行")
    print("   - 「**ドロップ品:**」→「ドロップ品」")

if __name__ == "__main__":
    asyncio.run(test_final_format())