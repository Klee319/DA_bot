#!/usr/bin/env python3
"""
テスト用のBOT起動スクリプト
サンプルデータでBOTの動作確認を行う
"""

import asyncio
import sys
import os
import pandas as pd
from pathlib import Path

# srcディレクトリをパスに追加
sys.path.append(str(Path(__file__).parent / 'src'))

from database import DatabaseManager
from csv_manager import CSVManager
from search_engine import SearchEngine

async def test_database_setup():
    """データベースの初期化テスト"""
    print("📁 データベースの初期化テスト開始...")
    
    db = DatabaseManager("./data/test_items.db")
    await db.initialize_database()
    
    print("✅ データベースの初期化完了")
    return db

async def test_csv_import(db):
    """CSVインポートテスト"""
    print("\n📊 CSVインポートテスト開始...")
    
    # 設定ファイルを読み込み
    import json
    with open('config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    csv_manager = CSVManager(db, config)
    
    # equipmentデータをインポート
    equipment_path = "./sampleCSVdata/DA_data_equipment - シート1.csv"
    if os.path.exists(equipment_path):
        df = pd.read_csv(equipment_path, encoding='utf-8')
        print(f"📋 equipmentデータ: {len(df)}件読み込み")
        
        # データを正規化
        normalized_df = await csv_manager.normalize_csv_data(df, 'equipment')
        
        # データベースに挿入
        count = await csv_manager.insert_csv_data(normalized_df, 'equipment')
        print(f"✅ equipmentデータ: {count}件挿入完了")
    
    # materialデータがあれば同様にインポート
    material_path = "./sampleCSVdata/DA_data_material - シート1.csv"
    if os.path.exists(material_path):
        df = pd.read_csv(material_path, encoding='utf-8')
        print(f"📋 materialデータ: {len(df)}件読み込み")
        
        normalized_df = await csv_manager.normalize_csv_data(df, 'material')
        count = await csv_manager.insert_csv_data(normalized_df, 'material')
        print(f"✅ materialデータ: {count}件挿入完了")
    
    # mobデータがあれば同様にインポート
    mob_path = "./sampleCSVdata/DA_data_mob - シート1.csv"
    if os.path.exists(mob_path):
        df = pd.read_csv(mob_path, encoding='utf-8')
        print(f"📋 mobデータ: {len(df)}件読み込み")
        
        normalized_df = await csv_manager.normalize_csv_data(df, 'mob')
        count = await csv_manager.insert_csv_data(normalized_df, 'mob')
        print(f"✅ mobデータ: {count}件挿入完了")

async def test_search_functionality(db):
    """検索機能テスト"""
    print("\n🔍 検索機能テスト開始...")
    
    # 設定ファイルを読み込み
    import json
    with open('config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    search_engine = SearchEngine(db, config)
    
    # テストクエリ
    test_queries = [
        "ウッドソード",
        "木の棒",
        "ウッド*",
        "剣",
        "存在しないアイテム"
    ]
    
    for query in test_queries:
        print(f"\n🔎 検索クエリ: '{query}'")
        results = await search_engine.search(query)
        
        if results:
            print(f"  📋 {len(results)}件の結果:")
            for i, result in enumerate(results[:3], 1):  # 最大3件表示
                name = result.get('formal_name', 'Unknown')
                type_name = result.get('item_type', 'unknown')
                print(f"    {i}. {name} ({type_name})")
        else:
            print("  ❌ 結果なし")

async def test_favorite_functionality(db):
    """お気に入り機能テスト"""
    print("\n⭐ お気に入り機能テスト開始...")
    
    test_user_id = "123456789"
    
    # お気に入り追加テスト
    success = await db.add_favorite(test_user_id, "ウッドソード", "equipments")
    print(f"📌 お気に入り追加: {'成功' if success else '失敗'}")
    
    # お気に入り一覧取得テスト
    favorites = await db.get_user_favorites(test_user_id)
    print(f"📋 お気に入り一覧: {len(favorites)}件")
    for fav in favorites:
        print(f"  - {fav['item_name']} ({fav['item_type']})")

async def test_search_history(db):
    """検索履歴機能テスト"""
    print("\n📜 検索履歴機能テスト開始...")
    
    test_user_id = "123456789"
    
    # 検索履歴追加テスト
    await db.add_search_history(test_user_id, "ウッドソード", 1)
    await db.add_search_history(test_user_id, "木の棒", 0)
    print("📝 検索履歴追加完了")
    
    # 検索履歴取得テスト
    history = await db.get_search_history(test_user_id)
    print(f"📋 検索履歴: {len(history)}件")
    for entry in history:
        print(f"  - {entry['query']} (結果: {entry['result_count']}件)")

async def main():
    """メインテスト実行"""
    print("🚀 Discord アイテム参照BOT テスト開始\n")
    
    try:
        # データベース初期化
        db = await test_database_setup()
        
        # CSVインポート
        await test_csv_import(db)
        
        # 検索機能テスト
        await test_search_functionality(db)
        
        # お気に入り機能テスト
        await test_favorite_functionality(db)
        
        # 検索履歴テスト
        await test_search_history(db)
        
        print("\n🎉 全テスト完了！BOTの基本機能が正常に動作しています。")
        print("\n次のステップ:")
        print("1. .envファイルにDISCORD_TOKENを設定")
        print("2. config.jsonの管理者設定を更新")
        print("3. python src/main.py でBOTを起動")
        
    except Exception as e:
        print(f"\n❌ テスト中にエラーが発生: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())