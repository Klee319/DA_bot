import asyncio
import sys
import os

# プロジェクトのルートディレクトリをsys.pathに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database import DatabaseManager
from src.search_engine import SearchEngine
from src.csv_manager import CSVManager
import json
import pandas as pd
import io

async def test_gathering_npc_integration():
    """gathering/npc関連機能の統合テスト"""
    
    # 設定読み込み
    with open('config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # データベース初期化
    db = DatabaseManager("./data/test_integration.db")
    await db.initialize_database()
    
    # CSVマネージャー初期化
    csv_manager = CSVManager(db, config)
    
    # サーチエンジン初期化
    search_engine = SearchEngine(db, config)
    
    print("=== Gathering/NPC 統合テスト開始 ===\n")
    
    # テストデータ作成
    # 1. Gatheringデータ
    gathering_data = """収集場所,収集方法,必要ツールレベル,入手素材,一言
セシド,採掘,炎牙・乾泥以上,"風化した化石, 紫の水晶, 夢見の勾玉",EXP:20
セシド,採取,炎牙・乾泥以上,"綺麗な果実, 泥まみれの骨",EXP:20
レポロ,釣り,初期から,"トトの肉, トロピカルフィッシュ","""
    
    # 2. NPCデータ
    npc_data = """配置場所,名前,対応業務,入手アイテム,必要素材,EXP,GOLD,一言,画像パス
レポロ,アヴィル,購入,"始まりの鍛治槌:1, 始まりの作業道具:1","50G, 120G",,,道具が50G,
レポロ,ライハ,購入,"小薬草:1, 小マナポーション:1","10G, 20G",,,薬屋,
セシド,交換員,交換,"風化した化石:1, 紫の水晶:1","綺麗な果実:3, 泥まみれの骨:2",,,素材交換,"""
    
    # 3. Materialデータ（入手元確認用）
    material_data = """正式名称,一般名称,入手カテゴリ,入手方法,利用カテゴリ,使用用途,一言,画像リンク
風化した化石,化石,採掘,採掘,素材,装備素材,,
紫の水晶,水晶,採掘,採掘,素材,装備素材,,
綺麗な果実,果実,採取,採取,素材,装備素材,,
泥まみれの骨,骨,採取,採取,素材,装備素材,,
トトの肉,肉,釣り,釣り,素材,料理素材,,
小薬草,薬草,NPC,購入,素材,回復アイテム,,
小マナポーション,マナポ,NPC,購入,素材,回復アイテム,,"""
    
    try:
        # データ挿入
        print("1. テストデータ挿入...")
        
        # Gatheringデータ挿入
        gathering_df = pd.read_csv(io.StringIO(gathering_data), encoding='utf-8')
        result = await csv_manager.insert_csv_data(
            await csv_manager.normalize_csv_data(gathering_df, 'gathering'),
            'gathering'
        )
        print(f"  - Gathering: {result}件挿入")
        
        # NPCデータ挿入
        npc_df = pd.read_csv(io.StringIO(npc_data), encoding='utf-8')
        result = await csv_manager.insert_csv_data(
            await csv_manager.normalize_csv_data(npc_df, 'npc'),
            'npc'
        )
        print(f"  - NPC: {result}件挿入")
        
        # Materialデータ挿入
        material_df = pd.read_csv(io.StringIO(material_data), encoding='utf-8')
        result = await csv_manager.insert_csv_data(
            await csv_manager.normalize_csv_data(material_df, 'material'),
            'material'
        )
        print(f"  - Material: {result}件挿入")
        
        print("\n2. 素材の入手元検索テスト...")
        
        # 採掘で入手できる素材の検索
        test_materials = ['風化した化石', '紫の水晶', '綺麗な果実', '小薬草']
        
        for material_name in test_materials:
            print(f"\n  【{material_name}】の入手元:")
            
            # 素材を検索
            search_results = await search_engine.search(material_name)
            if search_results:
                material_data = search_results[0]
                
                # 関連アイテム（入手元）を検索
                related_items = await search_engine.search_related_items(material_data)
                
                # 入手元の表示
                acquisition_sources = related_items.get('acquisition_sources', [])
                
                if acquisition_sources:
                    # タイプ別に分類
                    mob_sources = [s for s in acquisition_sources if s.get('relation_type') == 'drop_from_mob']
                    gathering_sources = [s for s in acquisition_sources if s.get('relation_type') == 'gathering_location']
                    npc_sources = [s for s in acquisition_sources if s.get('relation_type') == 'npc_source']
                    
                    if mob_sources:
                        print("    ◆ モブドロップ:")
                        for mob in mob_sources:
                            print(f"      - {mob['formal_name']} (エリア: {mob.get('area', '不明')})")
                    
                    if gathering_sources:
                        print("    ◆ 採集場所:")
                        for gathering in gathering_sources:
                            print(f"      - {gathering['location']} ({gathering['collection_method']})")
                            if gathering.get('required_tools'):
                                print(f"        必要ツール: {gathering['required_tools']}")
                    
                    if npc_sources:
                        print("    ◆ NPC:")
                        for npc in npc_sources:
                            print(f"      - {npc['name']} @ {npc['location']} ({npc['business_type']})")
                            if npc.get('relation_detail'):
                                print(f"        詳細: {npc['relation_detail']}")
                else:
                    print("    入手元情報なし")
            else:
                print(f"    素材が見つかりません")
        
        print("\n3. 採集場所の素材一覧テスト...")
        
        # 採集場所ごとの素材確認
        import aiosqlite
        async with aiosqlite.connect(db.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            cursor = await conn.execute("SELECT * FROM gatherings")
            gatherings = await cursor.fetchall()
            
            for gathering in gatherings:
                gathering_dict = dict(gathering)
                print(f"\n  【{gathering_dict['location']}】- {gathering_dict['collection_method']}:")
                materials = gathering_dict.get('obtained_materials', '')
                if materials:
                    material_list = [m.strip() for m in materials.split(',')]
                    for mat in material_list:
                        print(f"    - {mat}")
        
        print("\n4. NPCの取扱アイテムテスト...")
        
        # NPCごとのアイテム確認
        async with aiosqlite.connect(db.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            cursor = await conn.execute("SELECT * FROM npcs")
            npcs = await cursor.fetchall()
            
            for npc in npcs:
                npc_dict = dict(npc)
                print(f"\n  【{npc_dict['name']}】@ {npc_dict['location']} - {npc_dict['business_type']}:")
                items = npc_dict.get('obtainable_items', '')
                if items:
                    item_list = [i.strip() for i in items.split(',')]
                    for item in item_list:
                        print(f"    - {item}")
                        if npc_dict['business_type'] == '購入' and npc_dict.get('required_materials'):
                            prices = [p.strip() for p in npc_dict['required_materials'].split(',')]
                            if len(prices) > item_list.index(item):
                                print(f"      価格: {prices[item_list.index(item)]}")
        
        print("\n=== テスト完了 ===")
        
    except Exception as e:
        print(f"\nエラー発生: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # テスト用データベースの削除
        if os.path.exists("./data/test_integration.db"):
            os.remove("./data/test_integration.db")

if __name__ == "__main__":
    asyncio.run(test_gathering_npc_integration())