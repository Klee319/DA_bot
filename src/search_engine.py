import asyncio
import logging
import re
from typing import List, Dict, Any, Optional, Tuple
import jaconv
import aiosqlite
from fnmatch import fnmatch

logger = logging.getLogger(__name__)

class SearchEngine:
    def __init__(self, db_manager, config):
        self.db_manager = db_manager
        self.config = config
        self.max_results = config['features']['pagination_size']
        
        # 同音異字の辞書（よく使われるゲーム用語）
        self.homophone_dict = {
            # 剣・武器関連
            'けん': ['剣', '健', '権', '見', '券'],
            'かたな': ['刀', 'カタナ'],
            'つるぎ': ['剣', '劔'],
            'そーど': ['ソード', 'そーど'],
            'あっくす': ['アックス', 'あっくす'],
            'すたっふ': ['スタッフ', 'すたっふ'],
            'ぼう': ['棒', '坊', '房', 'ボウ'],
            
            # 盾・防具関連
            'たて': ['盾', '建て', '立て'],
            'よろい': ['鎧', 'ヨロイ'],
            'かぶと': ['兜', 'カブト'],
            
            # 素材関連
            'いし': ['石', '意志', 'イシ'],
            'てつ': ['鉄', 'テツ'],
            'きん': ['金', '銀', 'キン'],
            'ぎん': ['銀', 'ギン'],
            'どう': ['銅', '道', 'ドウ'],
            'はがね': ['鋼', 'ハガネ'],
            'ほうせき': ['宝石', 'ホウセキ'],
            'たま': ['玉', '球', '魂', 'タマ'],
            'かけら': ['欠片', 'カケラ'],
            'はね': ['羽', '羽根', 'ハネ'],
            'かわ': ['皮', '革', 'カワ'],
            'きば': ['牙', 'キバ'],
            'つめ': ['爪', 'ツメ'],
            
            # モンスター関連
            'りゅう': ['龍', '竜', 'リュウ'],
            'どらごん': ['ドラゴン', 'どらごん'],
            'おに': ['鬼', 'オニ'],
            'あく': ['悪', 'アク'],
            'あくま': ['悪魔', 'アクマ'],
            'すらいむ': ['スライム', 'すらいむ'],
            'ごぶりん': ['ゴブリン', 'ごぶりん'],
            'おーく': ['オーク', 'おーく'],
            'とろる': ['トロル', 'とろる'],
            'おが': ['オーガ', 'おが'],
            'けんたうろす': ['ケンタウロス', 'けんたうろす'],
            
            # 魔法関連
            'まほう': ['魔法', 'マホウ'],
            'まりょく': ['魔力', 'マリョク'],
            'せいれい': ['精霊', 'セイレイ'],
            'まじゅつ': ['魔術', 'マジュツ'],
            
            # 宝石関連
            'ほうせき': ['宝石', 'ホウセキ'],
            'すいしょう': ['水晶', 'スイショウ'],
            'だいや': ['ダイヤ', 'ダイアモンド'],
            'るびー': ['ルビー', 'るびー'],
            'えめらるど': ['エメラルド', 'えめらるど'],
            'さふぁいあ': ['サファイア', 'さふぁいあ'],
            
            # 色関連
            'あか': ['赤', '紅', 'アカ'],
            'あお': ['青', '蒼', 'アオ'],
            'きいろ': ['黄', '黄色', 'キイロ'],
            'みどり': ['緑', 'ミドリ'],
            'くろ': ['黒', 'クロ'],
            'しろ': ['白', 'シロ'],
            'きん': ['金', 'キン'],
            'ぎん': ['銀', 'ギン'],
            
            # 自然・元素関連
            'ひかり': ['光', '輝', 'ヒカリ'],
            'やみ': ['闇', '暗', 'ヤミ'],
            'ほのお': ['炎', '焔', 'ホノオ'],
            'みず': ['水', 'ミズ'],
            'かぜ': ['風', 'カゼ'],
            'つち': ['土', '地', 'ツチ'],
            'こおり': ['氷', 'コオリ'],
            'かみなり': ['雷', 'カミナリ'],
            
            # その他
            'ちから': ['力', 'チカラ'],
            'こころ': ['心', 'ココロ'],
            'たましい': ['魂', 'タマシイ'],
            'せい': ['聖', '生', '性', 'セイ'],
            'あんこく': ['暗黒', 'アンコク'],
        }
    
    async def search(self, query: str) -> List[Dict[str, Any]]:
        """統合検索機能 - 優先順位に基づいて検索"""
        try:
            # クエリを正規化
            normalized_query = self._normalize_query(query)
            all_results = []
            
            # 1. 正式名称での完全一致検索
            exact_formal_results = await self._search_exact_formal_name(normalized_query)
            all_results.extend(exact_formal_results)
            
            # 2. 一般名称での完全一致検索
            exact_common_results = await self._search_exact_common_name(normalized_query)
            # 重複を除外しながら追加
            for result in exact_common_results:
                if not any(r['id'] == result['id'] and r['item_type'] == result['item_type'] for r in all_results):
                    all_results.append(result)
            
            # 完全一致が見つかった場合は、部分一致も含めて返す
            if all_results:
                # 部分一致も検索して追加
                partial_results = await self._search_partial_match(normalized_query)
                for result in partial_results:
                    if not any(r['id'] == result['id'] and r['item_type'] == result['item_type'] for r in all_results):
                        all_results.append(result)
                # 重複除去とスコアリングを行う（制限なし）
                sorted_results = self._deduplicate_and_score_results(all_results, normalized_query)
                return sorted_results
            
            # 3. ワイルドカード検索（*や?が含まれている場合）
            if self._has_wildcards(query):
                results = await self._search_wildcard(query)
                if results:
                    return results
            
            # 4. 表記ゆれ対応検索
            results = await self._search_fuzzy(normalized_query)
            if results:
                return results
            
            # 5. 部分一致検索（最後の手段）
            results = await self._search_partial_match(normalized_query)
            return results
            
        except Exception as e:
            logger.error(f"検索エラー: {e}")
            return []
    
    def _normalize_query(self, query: str) -> str:
        """クエリの正規化"""
        try:
            # 前後の空白を除去
            query = query.strip()
            
            # 全角→半角変換（数字とアルファベット）
            query = jaconv.z2h(query, kana=False, ascii=True, digit=True)
            
            # 半角カタカナ→全角カタカナ変換
            query = jaconv.h2z(query, kana=True, ascii=False, digit=False)
            
            # 大文字→小文字変換
            query = query.lower()
            
            return query
            
        except Exception as e:
            logger.warning(f"クエリ正規化エラー: {e}")
            return query.strip().lower()
    
    def _has_wildcards(self, query: str) -> bool:
        """ワイルドカードが含まれているかチェック（全角対応）"""
        return '*' in query or '?' in query or '＊' in query or '？' in query
    
    async def _search_exact_formal_name(self, query: str) -> List[Dict[str, Any]]:
        """正式名称での完全一致検索"""
        try:
            async with aiosqlite.connect(self.db_manager.db_path) as db:
                db.row_factory = aiosqlite.Row
                results = []
                
                # equipments, materials, mobsテーブルは formal_name で検索
                for table in ['equipments', 'materials', 'mobs']:
                    cursor = await db.execute(
                        f"SELECT *, '{table}' as item_type FROM {table} WHERE LOWER(formal_name) = ?",
                        (query,)
                    )
                    rows = await cursor.fetchall()
                    results.extend([dict(row) for row in rows])
                
                # npcsテーブルは name で検索
                cursor = await db.execute(
                    "SELECT *, 'npcs' as item_type, name as formal_name FROM npcs WHERE LOWER(name) = ?",
                    (query,)
                )
                rows = await cursor.fetchall()
                results.extend([dict(row) for row in rows])
                
                return results
                
        except Exception as e:
            logger.error(f"正式名称検索エラー: {e}")
            return []
    
    async def _search_exact_common_name(self, query: str) -> List[Dict[str, Any]]:
        """一般名称での完全一致検索"""
        try:
            async with aiosqlite.connect(self.db_manager.db_path) as db:
                db.row_factory = aiosqlite.Row
                results = []
                
                # gatheringsとnpcsにはcommon_nameがないため除外
                tables = ['equipments', 'materials', 'mobs']
                
                for table in tables:
                    # 複数の一般名称をカンマ区切りで格納している場合に対応
                    cursor = await db.execute(
                        f"SELECT *, '{table}' as item_type FROM {table} WHERE LOWER(common_name) = ? OR LOWER(common_name) LIKE ? OR LOWER(common_name) LIKE ? OR LOWER(common_name) LIKE ?",
                        (query, f'{query},%', f'%,{query},%', f'%,{query}')
                    )
                    rows = await cursor.fetchall()
                    results.extend([dict(row) for row in rows])
                
                return results
                
        except Exception as e:
            logger.error(f"一般名称検索エラー: {e}")
            return []
    
    async def _search_wildcard(self, query: str) -> List[Dict[str, Any]]:
        """ワイルドカード検索（全角ワイルドカード対応）"""
        try:
            # 全角ワイルドカードを半角に変換
            normalized_query = query.replace('＊', '*').replace('？', '?')
            
            async with aiosqlite.connect(self.db_manager.db_path) as db:
                db.row_factory = aiosqlite.Row
                results = []
                
                # テーブルごとに処理
                
                # formal_name/common_nameを持つテーブル
                for table in ['equipments', 'materials', 'mobs']:
                    cursor = await db.execute(
                        f"SELECT *, '{table}' as item_type FROM {table}"
                    )
                    rows = await cursor.fetchall()
                    
                    for row in rows:
                        row_dict = dict(row)
                        formal_name = row_dict.get('formal_name', '')
                        common_name = row_dict.get('common_name', '') or ''
                        
                        if (fnmatch(formal_name.lower(), normalized_query.lower()) or 
                            fnmatch(common_name.lower(), normalized_query.lower())):
                            results.append(row_dict)
                
                # npcsテーブル (nameカラムを使用)
                cursor = await db.execute(
                    "SELECT *, 'npcs' as item_type, name as formal_name FROM npcs"
                )
                rows = await cursor.fetchall()
                
                for row in rows:
                    row_dict = dict(row)
                    name = row_dict.get('name', '')
                    if fnmatch(name.lower(), normalized_query.lower()):
                        results.append(row_dict)
                
                # 制限なしで返す
                return results
                
        except Exception as e:
            logger.error(f"ワイルドカード検索エラー: {e}")
            return []
    
    async def _search_fuzzy(self, query: str) -> List[Dict[str, Any]]:
        """表記ゆれ対応検索"""
        try:
            # 複数のバリエーションを生成
            query_variations = self._generate_query_variations(query)
            
            async with aiosqlite.connect(self.db_manager.db_path) as db:
                db.row_factory = aiosqlite.Row
                results = []
                
                # formal_name/common_nameを持つテーブル
                for table in ['equipments', 'materials', 'mobs']:
                    for variation in query_variations:
                        # 正式名称での検索
                        cursor = await db.execute(
                            f"SELECT *, '{table}' as item_type FROM {table} WHERE LOWER(formal_name) = ?",
                            (variation,)
                        )
                        rows = await cursor.fetchall()
                        results.extend([dict(row) for row in rows])
                        
                        # 一般名称での検索
                        cursor = await db.execute(
                            f"SELECT *, '{table}' as item_type FROM {table} WHERE LOWER(common_name) = ? AND common_name IS NOT NULL",
                            (variation,)
                        )
                        rows = await cursor.fetchall()
                        results.extend([dict(row) for row in rows])
                
                # npcsテーブルの検索
                for variation in query_variations:
                    cursor = await db.execute(
                        "SELECT *, 'npcs' as item_type, name as formal_name FROM npcs WHERE LOWER(name) = ?",
                        (variation,)
                    )
                    rows = await cursor.fetchall()
                    results.extend([dict(row) for row in rows])
                
                # 重複を除去
                seen = set()
                unique_results = []
                for result in results:
                    key = (result['formal_name'], result['item_type'])
                    if key not in seen:
                        seen.add(key)
                        unique_results.append(result)
                
                # 制限なしで返す
                return unique_results
                
        except Exception as e:
            logger.error(f"表記ゆれ検索エラー: {e}")
            return []
    
    def _generate_query_variations(self, query: str) -> List[str]:
        """クエリのバリエーションを生成"""
        variations = [query]
        
        try:
            # ひらがな⇔カタカナ変換
            kata_query = jaconv.hira2kata(query)
            if kata_query != query:
                variations.append(kata_query)
            
            hira_query = jaconv.kata2hira(query)
            if hira_query != query:
                variations.append(hira_query)
            
            # 全角⇔半角変換
            han_query = jaconv.z2h(query, kana=True, ascii=True, digit=True)
            if han_query != query:
                variations.append(han_query)
            
            zen_query = jaconv.h2z(query, kana=True, ascii=True, digit=True)
            if zen_query != query:
                variations.append(zen_query)
            
            # 組み合わせパターン
            for var in variations[:]:
                # カタカナ→ひらがな
                hira_var = jaconv.kata2hira(var)
                if hira_var not in variations:
                    variations.append(hira_var)
                
                # ひらがな→カタカナ
                kata_var = jaconv.hira2kata(var)
                if kata_var not in variations:
                    variations.append(kata_var)
            
            # 重複を除去して正規化
            unique_variations = []
            for var in variations:
                normalized = self._normalize_query(var)
                if normalized not in unique_variations:
                    unique_variations.append(normalized)
            
            # 同音異字のバリエーションを追加
            homophone_variations = self._generate_homophone_variations(unique_variations)
            unique_variations.extend(homophone_variations)
            
            # 最終的な重複除去
            final_variations = []
            for var in unique_variations:
                if var not in final_variations:
                    final_variations.append(var)
            
            return final_variations
            
        except Exception as e:
            logger.warning(f"バリエーション生成エラー: {e}")
            return [query]
    
    def _generate_homophone_variations(self, base_variations: List[str]) -> List[str]:
        """同音異字のバリエーションを生成"""
        homophone_variations = []
        
        try:
            for base_query in base_variations:
                # ひらがなに変換
                hira_query = jaconv.kata2hira(base_query.lower())
                
                # 同音異字辞書でマッチングチェック
                for reading, kanji_list in self.homophone_dict.items():
                    if reading in hira_query:
                        # 読みを各漢字に置換
                        for kanji in kanji_list:
                            variant = hira_query.replace(reading, kanji)
                            if variant != base_query and variant not in homophone_variations:
                                homophone_variations.append(variant)
                        
                        # 部分マッチングも試行（より柔軟な検索のため）
                        if hira_query == reading:
                            homophone_variations.extend([k for k in kanji_list if k not in homophone_variations])
                
                # 逆方向（漢字→ひらがな）の変換も試行
                for reading, kanji_list in self.homophone_dict.items():
                    for kanji in kanji_list:
                        if kanji in base_query:
                            variant = base_query.replace(kanji, reading)
                            if variant != base_query and variant not in homophone_variations:
                                homophone_variations.append(variant)
                            
                            # カタカナバージョンも生成
                            kata_variant = jaconv.hira2kata(variant)
                            if kata_variant != variant and kata_variant not in homophone_variations:
                                homophone_variations.append(kata_variant)
            
            return homophone_variations
            
        except Exception as e:
            logger.warning(f"同音異字変換エラー: {e}")
            return []
    
    async def _search_partial_match(self, query: str) -> List[Dict[str, Any]]:
        """表記ゆれ対応の部分一致検索"""
        try:
            # 表記ゆれのバリエーションを生成
            query_variations = self._generate_query_variations(query)
            
            async with aiosqlite.connect(self.db_manager.db_path) as db:
                db.row_factory = aiosqlite.Row
                results = []
                
                # 各バリエーションで検索
                for variation in query_variations:
                    # formal_name/common_nameを持つテーブル
                    for table in ['equipments', 'materials', 'mobs']:
                        
                        # 前方一致を優先
                        cursor = await db.execute(
                            f"SELECT *, '{table}' as item_type, 'prefix' as match_type FROM {table} WHERE LOWER(formal_name) LIKE ? OR LOWER(common_name) LIKE ?",
                            (f'{variation}%', f'{variation}%')
                        )
                        rows = await cursor.fetchall()
                        results.extend([dict(row) for row in rows])
                        
                        # 部分一致（前方一致以外の部分一致）
                        cursor = await db.execute(
                            f"SELECT *, '{table}' as item_type, 'partial' as match_type FROM {table} WHERE (LOWER(formal_name) LIKE ? OR LOWER(common_name) LIKE ?)",
                            (f'%{variation}%', f'%{variation}%')
                        )
                        rows = await cursor.fetchall()
                        results.extend([dict(row) for row in rows])
                    
                    # npcsテーブル
                    # 前方一致
                    cursor = await db.execute(
                        "SELECT *, 'npcs' as item_type, name as formal_name, 'prefix' as match_type FROM npcs WHERE LOWER(name) LIKE ?",
                        (f'{variation}%',)
                    )
                    rows = await cursor.fetchall()
                    results.extend([dict(row) for row in rows])
                    
                    # 部分一致
                    cursor = await db.execute(
                        "SELECT *, 'npcs' as item_type, name as formal_name, 'partial' as match_type FROM npcs WHERE LOWER(name) LIKE ?",
                        (f'%{variation}%',)
                    )
                    rows = await cursor.fetchall()
                    results.extend([dict(row) for row in rows])
                
                # 重複除去と関連性スコアによるソート
                unique_results = self._deduplicate_and_score_results(results, query)
                # 部分一致検索では制限なしで返す（呼び出し元で制限する）
                return unique_results
                
        except Exception as e:
            logger.error(f"部分一致検索エラー: {e}")
            return []
    
    def _deduplicate_and_score_results(self, results: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        """重複除去と関連性スコアによるソート"""
        seen = set()
        scored_results = []
        
        for result in results:
            # NPCの場合は場所も含めて重複チェック
            if result['item_type'] == 'npcs':
                key = (result['formal_name'], result['item_type'], result.get('location', ''))
            else:
                key = (result['formal_name'], result['item_type'])
            
            if key in seen:
                continue
            seen.add(key)
            
            # 関連性スコアを計算
            score = self._calculate_relevance_score(result, query)
            result['_score'] = score
            scored_results.append(result)
        
        # スコアでソート（高い順）
        scored_results.sort(key=lambda x: x['_score'], reverse=True)
        
        # スコアフィールドを削除
        for result in scored_results:
            if '_score' in result:
                del result['_score']
        
        return scored_results
    
    def _calculate_relevance_score(self, result: Dict[str, Any], query: str) -> float:
        """関連性スコアを計算"""
        score = 0.0
        formal_name = (result.get('formal_name') or '').lower()
        common_name = (result.get('common_name') or '').lower()
        query_lower = query.lower()
        
        # 完全一致（最高スコア）
        if formal_name == query_lower:
            score += 100
        elif common_name == query_lower:
            score += 95
        
        # 前方一致
        if formal_name.startswith(query_lower):
            score += 50
        elif common_name and common_name.startswith(query_lower):
            score += 45
        
        # 部分一致（位置による重み付け）
        formal_pos = formal_name.find(query_lower)
        if formal_pos >= 0:
            score += 30 - (formal_pos * 2)  # 前の方にあるほど高スコア
        
        if common_name:
            common_pos = common_name.find(query_lower)
            if common_pos >= 0:
                score += 25 - (common_pos * 2)
        
        # 長さによる重み付け（短い名前ほど関連性が高い）
        name_length_factor = 20 / max(len(formal_name), 1)
        score += name_length_factor
        
        return score
    
    async def search_related_items(self, item_data: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
        """関連アイテムを検索（新仕様）"""
        try:
            item_name = item_data.get('formal_name')
            item_type = item_data.get('item_type')
            
            if not item_name:
                return {}
            
            related_items = {}
            
            if item_type == 'materials':
                # material名の場合
                related_items['usage_destinations'] = []  # 利用先
                related_items['acquisition_sources'] = []  # 入手元
                
                # 利用先の検索
                # 1. equipmentテーブルで必要素材に含まれるもの
                equipment_using = await self._search_equipment_using_material(item_name)
                for eq in equipment_using:
                    eq['relation_type'] = 'material_for_equipment'
                    eq['relation_detail'] = await self._extract_material_usage(eq.get('required_materials', ''), item_name)
                    related_items['usage_destinations'].append(eq)
                
                # 2. NPCテーブルの必要素材に含まれるもの（利用先として）
                npc_using = await self._search_npcs_using_material(item_name)
                for npc in npc_using:
                    npc['relation_type'] = 'material_for_npc'
                    npc['relation_detail'] = await self._extract_npc_material_usage(npc.get('required_materials', ''), item_name)
                    related_items['usage_destinations'].append(npc)
                
                # 3. NPCテーブルの入手可能アイテムに含まれるもの
                npc_providing = await self._search_npcs_providing_material(item_name)
                for npc in npc_providing:
                    npc['relation_type'] = 'npc_source'
                    npc['source_type'] = 'obtainable'  # 入手可能
                    related_items['acquisition_sources'].append(npc)
                
                # 入手元の包括的検索
                await self._search_material_acquisition_sources(item_name, item_data, related_items)
            
            elif item_type == 'equipments':
                # equipment名の場合
                related_items['materials'] = []  # 必要素材
                related_items['acquisition_sources'] = []  # 入手元
                related_items['usage_destinations'] = []  # 利用先
                
                # 必要素材の検索
                if item_data.get('required_materials'):
                    materials = await self._parse_material_list_with_quantity(item_data['required_materials'])
                    for mat_name, quantity in materials:
                        mat_info = await self.search(mat_name)
                        if mat_info:
                            mat_info[0]['required_quantity'] = quantity
                            mat_info[0]['relation_type'] = 'required_material'
                            related_items['materials'].append(mat_info[0])
                
                # 入手元の検索
                acquisition_category = item_data.get('acquisition_category', '')
                
                if acquisition_category in ['討伐', 'モブ討伐']:
                    # このequipmentをドロップするmob
                    dropped_by = await self._search_mobs_dropping_item(item_name)
                    for mob in dropped_by:
                        mob['relation_type'] = 'drop_from_mob'
                        related_items['acquisition_sources'].append(mob)
                elif acquisition_category == 'NPC':
                    # NPCから入手可能なequipment
                    npc_providing = await self._search_npcs_providing_material(item_name)
                    for npc in npc_providing:
                        npc['relation_type'] = 'npc_source'
                        npc['source_type'] = 'obtainable'
                        related_items['acquisition_sources'].append(npc)
                
                # 利用先の検索（NPCの必要素材に含まれるequipment）
                npc_using = await self._search_npcs_using_material(item_name)
                for npc in npc_using:
                    npc['relation_type'] = 'material_for_npc'
                    npc['relation_detail'] = await self._extract_npc_material_usage(npc.get('required_materials', ''), item_name)
                    related_items['usage_destinations'].append(npc)
            
            elif item_type == 'mobs':
                # mob名の場合
                related_items['dropped_items'] = []  # ドロップアイテム
                
                # ドロップアイテムの検索
                if item_data.get('drops'):
                    drop_items = await self._parse_drop_list(item_data['drops'])
                    for drop_name in drop_items:
                        # 直接データベースから検索（全テーブル対象）
                        drop_info = await self._search_drop_item_directly(drop_name)
                        if drop_info:
                            drop_info['relation_type'] = 'drops_from_mob'
                            related_items['dropped_items'].append(drop_info)
            
            # NPCテーブルは未実装のためスキップ
            
            return related_items
            
        except Exception as e:
            logger.error(f"関連アイテム検索エラー: {e}")
            return {}
    
    async def _parse_material_list(self, materials_str: str) -> List[str]:
        """必要素材文字列をパース"""
        try:
            if not materials_str:
                return []
            
            # 「木の棒:8,トトの羽:4」形式をパース
            materials = []
            items = materials_str.split(',')
            
            for item in items:
                item = item.strip()
                if ':' in item:
                    material_name = item.split(':')[0].strip()
                    materials.append(material_name)
                else:
                    materials.append(item)
            
            return materials
            
        except Exception as e:
            logger.warning(f"素材リストパースエラー: {e}")
            return []
    
    async def _parse_drop_list(self, drops_str: str) -> List[str]:
        """ドロップアイテム文字列をパース"""
        try:
            if not drops_str:
                return []
            
            # 「木の棒:8,トトの羽:4」形式をパース
            drops = []
            items = drops_str.split(',')
            
            for item in items:
                item = item.strip()
                if ':' in item:
                    drop_name = item.split(':')[0].strip()
                    drops.append(drop_name)
                else:
                    drops.append(item)
            
            return drops
            
        except Exception as e:
            logger.warning(f"ドロップリストパースエラー: {e}")
            return []
    
    async def _search_items_using_material(self, material_name: str) -> List[Dict[str, Any]]:
        """指定した素材を使用するアイテムを検索"""
        try:
            async with aiosqlite.connect(self.db_manager.db_path) as db:
                db.row_factory = aiosqlite.Row
                results = []
                
                tables = ['equipments', 'materials']
                
                for table in tables:
                    cursor = await db.execute(
                        f"SELECT *, '{table}' as item_type FROM {table} WHERE required_materials LIKE ? AND required_materials IS NOT NULL",
                        (f'%{material_name}%',)
                    )
                    rows = await cursor.fetchall()
                    results.extend([dict(row) for row in rows])
                
                return results
                
        except Exception as e:
            logger.error(f"素材使用アイテム検索エラー: {e}")
            return []
    
    async def _search_drop_item_directly(self, item_name: str) -> Optional[Dict[str, Any]]:
        """ドロップアイテムを直接データベースから検索（完全一致優先）"""
        try:
            async with aiosqlite.connect(self.db_manager.db_path) as db:
                db.row_factory = aiosqlite.Row
                
                # 検索対象テーブル
                tables = ['equipments', 'materials', 'mobs']
                
                # 完全一致検索
                for table in tables:
                    cursor = await db.execute(
                        f"SELECT *, '{table}' as item_type FROM {table} WHERE formal_name = ?",
                        (item_name,)
                    )
                    row = await cursor.fetchone()
                    if row:
                        return dict(row)
                
                # 「の破片」を除いて再検索（例：「トト・ノーマルの破片」→「トト・ノーマル」）
                if item_name.endswith('の破片'):
                    base_name = item_name.replace('の破片', '')
                    for table in tables:
                        cursor = await db.execute(
                            f"SELECT *, '{table}' as item_type FROM {table} WHERE formal_name = ?",
                            (base_name,)
                        )
                        row = await cursor.fetchone()
                        if row:
                            return dict(row)
                
                # 完全一致がなければ部分一致検索
                for table in tables:
                    cursor = await db.execute(
                        f"SELECT *, '{table}' as item_type FROM {table} WHERE formal_name LIKE ?",
                        (f'%{item_name}%',)
                    )
                    row = await cursor.fetchone()
                    if row:
                        return dict(row)
                
                return None
                
        except Exception as e:
            logger.error(f"ドロップアイテム直接検索エラー: {e}")
            return None
    
    async def _search_equipment_using_material(self, material_name: str) -> List[Dict[str, Any]]:
        """指定した素材を使用する装備を検索（部分一致を除外）"""
        try:
            async with aiosqlite.connect(self.db_manager.db_path) as db:
                db.row_factory = aiosqlite.Row
                results = []
                
                # 全装備を取得してPythonで精密なマッチング
                cursor = await db.execute(
                    "SELECT *, 'equipments' as item_type FROM equipments WHERE required_materials IS NOT NULL AND required_materials != ''"
                )
                rows = await cursor.fetchall()
                
                for row in rows:
                    row_dict = dict(row)
                    required_materials = row_dict.get('required_materials', '')
                    
                    # 素材リストをパースして完全一致をチェック
                    if self._material_exactly_matches(required_materials, material_name):
                        results.append(row_dict)
                
                return results
                
        except Exception as e:
            logger.error(f"装備検索エラー: {e}")
            return []
    
    def _material_exactly_matches(self, materials_str: str, target_material: str) -> bool:
        """素材リスト内に指定した素材が完全一致で含まれるかチェック"""
        try:
            if not materials_str:
                return False
            
            # カンマ区切りで素材を分割
            items = materials_str.split(',')
            
            for item in items:
                item = item.strip()
                if ':' in item:
                    # 「素材名:数量」形式
                    material_name = item.split(':', 1)[0].strip()
                    if material_name == target_material:
                        return True
                else:
                    # 素材名のみ
                    if item == target_material:
                        return True
            
            return False
            
        except Exception as e:
            logger.warning(f"素材マッチングエラー: {e}")
            return False
    
    async def _search_mob_by_name(self, mob_name: str) -> Optional[Dict[str, Any]]:
        """モブ名で検索"""
        try:
            results = await self.search(mob_name)
            for result in results:
                if result.get('item_type') == 'mobs':
                    return result
            return None
        except Exception as e:
            logger.error(f"モブ検索エラー: {e}")
            return None
    
    async def _parse_material_list_with_quantity(self, materials_str: str) -> List[Tuple[str, str]]:
        """必要素材文字列をパース（数量付き）"""
        try:
            if not materials_str:
                return []
            
            materials = []
            items = materials_str.split(',')
            
            for item in items:
                item = item.strip()
                if ':' in item:
                    parts = item.split(':', 1)
                    material_name = parts[0].strip()
                    quantity = parts[1].strip()
                    materials.append((material_name, quantity))
                else:
                    materials.append((item, '1'))
            
            return materials
            
        except Exception as e:
            logger.warning(f"素材リストパースエラー: {e}")
            return []
    
    async def _extract_material_usage(self, materials_str: str, target_material: str) -> str:
        """素材の使用方法を抽出"""
        try:
            if not materials_str:
                return ''
            
            items = materials_str.split(',')
            for item in items:
                item = item.strip()
                if ':' in item:
                    parts = item.split(':', 1)
                    material_name = parts[0].strip()
                    if material_name == target_material:
                        return f"必要数: {parts[1].strip()}"
            return ''
        except Exception as e:
            logger.warning(f"使用方法抽出エラー: {e}")
            return ''
    
    async def _search_mobs_dropping_item(self, item_name: str) -> List[Dict[str, Any]]:
        """指定したアイテムをドロップするモブを検索（部分一致を除外）"""
        try:
            async with aiosqlite.connect(self.db_manager.db_path) as db:
                db.row_factory = aiosqlite.Row
                results = []
                
                # 全モブを取得してPythonで精密なマッチング
                cursor = await db.execute(
                    "SELECT *, 'mobs' as item_type FROM mobs WHERE drops IS NOT NULL AND drops != ''"
                )
                rows = await cursor.fetchall()
                
                for row in rows:
                    row_dict = dict(row)
                    drops = row_dict.get('drops', '')
                    
                    # ドロップリストをパースして完全一致をチェック
                    if self._drop_exactly_matches(drops, item_name):
                        results.append(row_dict)
                
                return results
                
        except Exception as e:
            logger.error(f"ドロップモブ検索エラー: {e}")
            return []
    
    def _drop_exactly_matches(self, drops_str: str, target_item: str) -> bool:
        """ドロップリスト内に指定したアイテムが完全一致で含まれるかチェック"""
        try:
            if not drops_str:
                return False
            
            # カンマ区切りでアイテムを分割
            items = drops_str.split(',')
            
            for item in items:
                item = item.strip()
                if item == target_item:
                    return True
                # 「・ノーマル」系の特殊処理
                # equipmentが「XXX・ノーマル」で、ドロップが「XXX・ノーマルの破片」の場合
                if target_item.endswith('・ノーマル') and item == target_item + 'の破片':
                    return True
            
            return False
            
        except Exception as e:
            logger.warning(f"ドロップマッチングエラー: {e}")
            return False
    
    async def _search_material_acquisition_sources(self, item_name: str, item_data: Dict[str, Any], related_items: Dict[str, List]):
        """素材の入手元を包括的に検索"""
        try:
            acquisition_category = item_data.get('acquisition_category', '')
            acquisition_method = item_data.get('acquisition_method', '')
            acquisition_location = item_data.get('acquisition_location', '')
            
            # 1. ドロップ元のmobを検索（discussionに関係なく常に検索）
            dropped_by = await self._search_mobs_dropping_item(item_name)
            for mob in dropped_by:
                mob['relation_type'] = 'drop_from_mob'
                mob['relation_detail'] = '討伐ドロップ'
                related_items['acquisition_sources'].append(mob)
            
            # 2. 採集場所の情報を取得
            gathering_info = await self._search_gathering_locations(item_name, acquisition_category, acquisition_location)
            for gathering in gathering_info:
                gathering['relation_type'] = 'gathering_location'
                related_items['acquisition_sources'].append(gathering)
            
            # 3. NPC交換・購入情報を取得
            npc_sources = await self._search_npc_sources(item_name)
            for npc in npc_sources:
                npc['relation_type'] = 'npc_source'
                related_items['acquisition_sources'].append(npc)
            
            # 4. その他の入手方法
            if acquisition_category and acquisition_category not in ['討伐', '採取', '採掘', '釣り', 'NPC', 'ギルドクエスト']:
                related_items['acquisition_info'] = {
                    'category': acquisition_category,
                    'method': acquisition_method,
                    'location': acquisition_location
                }
                
        except Exception as e:
            logger.error(f"素材入手元検索エラー: {e}")
            # エラー時はフォールバック処理
            if acquisition_category:
                related_items['acquisition_info'] = {
                    'category': acquisition_category,
                    'method': acquisition_method or '',
                    'location': acquisition_location or ''
                }
    
    async def _search_gathering_locations(self, item_name: str, category: str, location: str) -> List[Dict[str, Any]]:
        """採集場所テーブルから採集情報を検索"""
        try:
            async with aiosqlite.connect(self.db_manager.db_path) as db:
                db.row_factory = aiosqlite.Row
                results = []
                
                # gatheringsテーブルから入手素材に含まれる採集場所を検索
                cursor = await db.execute(
                    "SELECT *, 'gatherings' as item_type FROM gatherings WHERE obtained_materials LIKE ? AND obtained_materials IS NOT NULL",
                    (f'%{item_name}%',)
                )
                rows = await cursor.fetchall()
                
                for row in rows:
                    row_dict = dict(row)
                    obtained_materials = row_dict.get('obtained_materials', '')
                    
                    # 素材リストをパースして完全一致をチェック
                    if self._material_exactly_matches(obtained_materials, item_name):
                        row_dict['relation_type'] = 'gathering_location'
                        row_dict['relation_detail'] = f"{row_dict.get('collection_method', '')}で採集"
                        results.append(row_dict)
                
                return results
            
        except Exception as e:
            logger.warning(f"採集場所検索エラー: {e}")
            return []
    
    async def _search_npc_sources(self, item_name: str) -> List[Dict[str, Any]]:
        """NPCテーブルから交換・購入情報を検索"""
        try:
            async with aiosqlite.connect(self.db_manager.db_path) as db:
                db.row_factory = aiosqlite.Row
                results = []
                
                # 1. npcsテーブルから入手アイテムに含まれるNPCを検索
                cursor = await db.execute(
                    "SELECT *, 'npcs' as item_type FROM npcs WHERE obtainable_items LIKE ? AND obtainable_items IS NOT NULL",
                    (f'%{item_name}%',)
                )
                rows = await cursor.fetchall()
                
                for row in rows:
                    row_dict = dict(row)
                    obtainable_items = row_dict.get('obtainable_items', '')
                    
                    # アイテムリストをパースして完全一致をチェック
                    if self._material_exactly_matches(obtainable_items, item_name):
                        row_dict['relation_type'] = 'npc_source'
                        row_dict['source_type'] = 'obtainable'  # 入手可能アイテムからの検索
                        
                        # NPCの業務タイプに応じた詳細設定
                        business_type = row_dict.get('business_type', '')
                        if business_type == '購入':
                            row_dict['relation_detail'] = f"購入 ({row_dict.get('gold', '')}G)"
                        elif business_type == '交換':
                            row_dict['relation_detail'] = f"交換 (必要: {row_dict.get('required_materials', '')})"
                        else:
                            row_dict['relation_detail'] = business_type
                            
                        results.append(row_dict)
                
                # 2. 必要素材フィールドからもアイテム名を検索（素材・装備の場合）
                cursor = await db.execute(
                    "SELECT *, 'npcs' as item_type FROM npcs WHERE required_materials LIKE ? AND required_materials IS NOT NULL",
                    (f'%{item_name}%',)
                )
                rows = await cursor.fetchall()
                
                for row in rows:
                    row_dict = dict(row)
                    required_materials = row_dict.get('required_materials', '')
                    
                    # 必要素材リストをパースして完全一致をチェック
                    if self._material_exactly_matches(required_materials, item_name):
                        # 既に入手元として追加されていないかチェック
                        already_added = False
                        for existing in results:
                            if existing.get('id') == row_dict.get('id'):
                                already_added = True
                                break
                        
                        if not already_added:
                            row_dict['relation_type'] = 'npc_source'
                            row_dict['source_type'] = 'required'  # 必要素材からの検索
                            
                            # 素材を必要とするアイテムを検索
                            obtainable_items = row_dict.get('obtainable_items', '')
                            business_type = row_dict.get('business_type', '')
                            
                            if business_type == 'クエスト':
                                # クエストの場合は納品要求として表示
                                row_dict['relation_detail'] = f"クエスト納品 ({item_name})"
                            elif business_type == '交換':
                                # 交換の場合は、その素材で何が入手できるかを表示
                                row_dict['relation_detail'] = f"交換元 (入手: {obtainable_items})"
                            else:
                                row_dict['relation_detail'] = f"{business_type} (素材使用)"
                            
                            results.append(row_dict)
                
                return results
            
        except Exception as e:
            logger.warning(f"NPC検索エラー: {e}")
            return []
    
    async def search_npcs(self, npc_name: str) -> List[Dict[str, Any]]:
        """NPC名で検索"""
        try:
            normalized_name = self._normalize_query(npc_name)
            
            async with aiosqlite.connect(self.db_manager.db_path) as db:
                db.row_factory = aiosqlite.Row
                
                # 完全一致検索
                cursor = await db.execute(
                    "SELECT * FROM npcs WHERE LOWER(name) = LOWER(?)",
                    (normalized_name,)
                )
                results = await cursor.fetchall()
                
                if results:
                    return [dict(row) for row in results]
                
                # 部分一致検索
                cursor = await db.execute(
                    "SELECT * FROM npcs WHERE LOWER(name) LIKE LOWER(?)",
                    (f'%{normalized_name}%',)
                )
                results = await cursor.fetchall()
                
                return [dict(row) for row in results]
                
        except Exception as e:
            logger.error(f"NPC検索エラー: {e}")
            return []
    
    async def get_search_suggestions(self, partial_query: str, limit: int = 5) -> List[str]:
        """検索候補を取得"""
        try:
            if len(partial_query) < 2:
                return []
            
            async with aiosqlite.connect(self.db_manager.db_path) as db:
                db.row_factory = aiosqlite.Row
                suggestions = set()
                
                # formal_nameとcommon_nameを持つテーブル
                tables_with_formal_name = ['equipments', 'materials', 'mobs']
                
                for table in tables_with_formal_name:
                    # 正式名称から候補を取得
                    cursor = await db.execute(
                        f"SELECT formal_name FROM {table} WHERE LOWER(formal_name) LIKE ? LIMIT ?",
                        (f'{partial_query.lower()}%', limit)
                    )
                    rows = await cursor.fetchall()
                    suggestions.update([row['formal_name'] for row in rows])
                    
                    # 一般名称から候補を取得
                    cursor = await db.execute(
                        f"SELECT common_name FROM {table} WHERE LOWER(common_name) LIKE ? AND common_name IS NOT NULL LIMIT ?",
                        (f'{partial_query.lower()}%', limit)
                    )
                    rows = await cursor.fetchall()
                    suggestions.update([row['common_name'] for row in rows])
                
                # gatheringsテーブルのlocationから候補を取得
                cursor = await db.execute(
                    "SELECT location FROM gatherings WHERE LOWER(location) LIKE ? LIMIT ?",
                    (f'{partial_query.lower()}%', limit)
                )
                rows = await cursor.fetchall()
                suggestions.update([row['location'] for row in rows])
                
                # npcsテーブルのnameから候補を取得
                cursor = await db.execute(
                    "SELECT name FROM npcs WHERE LOWER(name) LIKE ? LIMIT ?",
                    (f'{partial_query.lower()}%', limit)
                )
                rows = await cursor.fetchall()
                suggestions.update([row['name'] for row in rows])
                
                return sorted(list(suggestions))[:limit]
                
        except Exception as e:
            logger.error(f"検索候補取得エラー: {e}")
            return []
    
    async def _search_npcs_using_material(self, material_name: str) -> List[Dict[str, Any]]:
        """指定した素材を必要とするNPCを検索"""
        try:
            async with aiosqlite.connect(self.db_manager.db_path) as db:
                db.row_factory = aiosqlite.Row
                results = []
                
                # required_materialsカラムに含まれるNPCを検索
                cursor = await db.execute(
                    "SELECT * FROM npcs WHERE required_materials LIKE ?",
                    (f'%{material_name}%',)
                )
                rows = await cursor.fetchall()
                
                for row in rows:
                    row_dict = dict(row)
                    # 素材リストを解析して実際に含まれているか確認
                    if self._check_material_in_npc_requirements(row_dict.get('required_materials', ''), material_name):
                        row_dict['formal_name'] = row_dict.get('name', '')
                        row_dict['item_type'] = 'npcs'
                        results.append(row_dict)
                
                return results
                
        except Exception as e:
            logger.error(f"NPCs using material検索エラー: {e}")
            return []
    
    async def _search_npcs_providing_material(self, material_name: str) -> List[Dict[str, Any]]:
        """指定した素材/装備を提供するNPCを検索"""
        try:
            async with aiosqlite.connect(self.db_manager.db_path) as db:
                db.row_factory = aiosqlite.Row
                results = []
                
                # obtainable_itemsカラムに含まれるNPCを検索
                cursor = await db.execute(
                    "SELECT * FROM npcs WHERE obtainable_items LIKE ?",
                    (f'%{material_name}%',)
                )
                rows = await cursor.fetchall()
                
                for row in rows:
                    row_dict = dict(row)
                    # アイテムリストを解析して実際に含まれているか確認
                    if self._check_material_in_npc_obtainable(row_dict.get('obtainable_items', ''), material_name):
                        row_dict['formal_name'] = row_dict.get('name', '')
                        row_dict['item_type'] = 'npcs'
                        results.append(row_dict)
                
                return results
                
        except Exception as e:
            logger.error(f"NPCs providing material検索エラー: {e}")
            return []
    
    def _check_material_in_npc_requirements(self, requirements_str: str, target_material: str) -> bool:
        """NPC必要素材に指定した素材が含まれているかチェック"""
        try:
            if not requirements_str:
                return False
            
            # カンマ区切りで分割
            materials = requirements_str.split(',')
            
            for material in materials:
                material = material.strip()
                # 「素材名:数量」形式の場合は素材名のみ抽出
                if ':' in material:
                    material_name = material.split(':')[0].strip()
                else:
                    material_name = material
                
                # RankXX や LvXX を除去
                material_name_cleaned = self._remove_rank_and_level(material_name)
                target_material_cleaned = self._remove_rank_and_level(target_material)
                
                # 完全一致または部分一致でチェック
                if material_name_cleaned == target_material_cleaned or target_material_cleaned in material_name_cleaned:
                    return True
            
            return False
            
        except Exception as e:
            logger.warning(f"NPC必要素材チェックエラー: {e}")
            return False
    
    def _check_material_in_npc_obtainable(self, obtainable_str: str, target_material: str) -> bool:
        """NPC入手可能アイテムに指定したアイテムが含まれているかチェック"""
        try:
            if not obtainable_str:
                return False
            
            # カンマ区切りで分割
            items = obtainable_str.split(',')
            
            for item in items:
                item = item.strip()
                # 「アイテム名:数量」形式の場合はアイテム名のみ抽出
                if ':' in item:
                    item_name = item.split(':')[0].strip()
                else:
                    item_name = item
                
                # RankXX や LvXX を除去
                item_name_cleaned = self._remove_rank_and_level(item_name)
                target_material_cleaned = self._remove_rank_and_level(target_material)
                
                # 完全一致または部分一致でチェック
                if item_name_cleaned == target_material_cleaned or target_material_cleaned in item_name_cleaned:
                    return True
            
            return False
            
        except Exception as e:
            logger.warning(f"NPC入手可能アイテムチェックエラー: {e}")
            return False
    
    def _remove_rank_and_level(self, item_name: str) -> str:
        """アイテム名からRankXXやLvXXを除去"""
        import re
        
        # Rankの除去（数値またはF〜SSSのアルファベット）
        # Rank1, RankS, RankSS, RankSSS などにマッチ
        item_name = re.sub(r'\s*Rank\s*(?:\d+|[F-S]{1,3})\s*', '', item_name, flags=re.IGNORECASE)
        
        # Lvの除去（数値またはF〜SSSのアルファベット）
        # Lv1, Lv.1, LvS, Lv.SS などにマッチ
        item_name = re.sub(r'\s*Lv\.?\s*(?:\d+|[F-S]{1,3})\s*', '', item_name, flags=re.IGNORECASE)
        
        # 前後の空白を削除
        return item_name.strip()
    
    async def _extract_npc_material_usage(self, requirements_str: str, target_material: str) -> str:
        """NPC必要素材から指定した素材の使用詳細を抽出"""
        try:
            if not requirements_str:
                return ""
            
            # カンマ区切りで分割
            materials = requirements_str.split(',')
            
            for material in materials:
                material = material.strip()
                # 「素材名:数量」形式をチェック
                if ':' in material:
                    material_name, quantity = material.split(':', 1)
                    material_name = material_name.strip()
                    quantity = quantity.strip()
                    
                    if material_name == target_material or target_material in material_name:
                        return f"必要数: {quantity}"
                else:
                    if material == target_material or target_material in material:
                        return "必要素材"
            
            return ""
            
        except Exception as e:
            logger.warning(f"NPC素材使用詳細抽出エラー: {e}")
            return ""