import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from database import DatabaseManager
from search_engine import SearchEngine
from embed_manager import EmbedManager, ItemDetailView
import json

async def test_new_buttons():
    """新しいボタン構成のテスト"""
    
    # 設定ファイルを読み込む
    with open('config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    db = DatabaseManager()
    search_engine = SearchEngine(db, config)
    embed_manager = EmbedManager(config)
    
    print("=== 新しいボタン構成のテスト ===\n")
    
    # テスト1: material（素材）- 両方のボタンが表示されるはず
    print("【テスト1: 石（素材）- 入手元詳細・利用先詳細両方が表示】")
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
        
        print(f"表示されるボタン: {button_labels}")
        print(f"ボタン数: {len(button_labels)}")
    
    print("\n" + "-"*50 + "\n")
    
    # テスト2: equipment（装備）- 入手元詳細のみ表示されるはず
    print("【テスト2: ウッドソード（装備）- 入手元詳細のみが表示】")
    equipment_results = await search_engine.search("ウッドソード")
    if equipment_results:
        equipment = equipment_results[0]
        print(f"検索対象: {equipment['formal_name']} (type: {equipment['item_type']})")
        
        # ItemDetailViewを作成
        view = ItemDetailView(equipment, "test_user", embed_manager)
        
        # 追加されたボタンを確認
        button_labels = []
        for item in view.children:
            if hasattr(item, 'label'):
                button_labels.append(item.label)
        
        print(f"表示されるボタン: {button_labels}")
        print(f"ボタン数: {len(button_labels)}")
    
    print("\n" + "-"*50 + "\n")
    
    # テスト3: mob（モンスター）- 利用先詳細のみ表示されるはず
    print("【テスト3: トト（モンスター）- 利用先詳細のみが表示】")
    mob_results = await search_engine.search("トト")
    if mob_results:
        mob = mob_results[0]
        print(f"検索対象: {mob['formal_name']} (type: {mob['item_type']})")
        
        # ItemDetailViewを作成
        view = ItemDetailView(mob, "test_user", embed_manager)
        
        # 追加されたボタンを確認
        button_labels = []
        for item in view.children:
            if hasattr(item, 'label'):
                button_labels.append(item.label)
        
        print(f"表示されるボタン: {button_labels}")
        print(f"ボタン数: {len(button_labels)}")
    
    print("\n" + "="*50)
    print("修正内容:")
    print("1. お気に入り機能と更新機能を削除")
    print("2. 関連アイテムボタンを「入手元詳細」「利用先詳細」に分割")
    print("3. アイテムタイプに応じて適切なボタンのみ表示")
    print("   - materials: 両方のボタン")
    print("   - equipments: 入手元詳細のみ") 
    print("   - mobs: 利用先詳細のみ")

if __name__ == "__main__":
    asyncio.run(test_new_buttons())