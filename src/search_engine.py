import logging
import aiosqlite
import re
import jaconv
from fnmatch import fnmatch
from typing import List, Dict, Any, Optional
from database import DatabaseManager
from constants import WILDCARD_CHARS, WILDCARD_SET

logger = logging.getLogger(__name__)

class SearchEngine:
    def __init__(self, db_manager: DatabaseManager, config: Dict[str, Any]):
        self.db_manager = db_manager
        self.config = config
        self.fuzzy_map = {
            # 長音変換（ー、～、〜）
            'ー': ['−', '一', '～', '〜'],
            '−': ['ー', '一', '～', '〜'],
            '～': ['ー', '−', '一', '〜'],
            '〜': ['ー', '−', '一', '～'],
            
            # カタカナ表記ゆれ
            'ヴ': ['ブ', 'ビ'],
            'ヴァ': ['バ'],
            'ヴィ': ['ビ'],
            'ヴェ': ['ベ'],
            'ヴォ': ['ボ'],
            
            # ひらがな・カタカナ変換は個別に実装
            # 数字の全角半角も個別に実装
            
            # 特殊文字
            '&': ['＆', 'アンド'],
            '＆': ['&', 'アンド'],
            
            # よくある誤字
            'ず': ['づ'],
            'づ': ['ず'],
            'じ': ['ぢ'],
            'ぢ': ['じ'],
            
            # 助詞の省略/付加（「の」）
            # これは別途処理
        }
        
        # ひらがな・カタカナ・漢字の対応表
        self.reading_map = {
            # 武器・防具関連
            'つるぎ': ['剣', '刀', 'ツルギ'],
            'けん': ['剣', '刀', 'ケン'],
            'かたな': ['刀', '剣', 'カタナ'],
            'たて': ['盾', 'タテ'],
            'よろい': ['鎧', 'ヨロイ'],
            'かぶと': ['兜', 'カブト'],
            
            # 材料関連
            'いし': ['石', 'イシ'],
            'きんぞく': ['金属', 'キンゾク'],
            'ぬの': ['布', 'ヌノ'],
            'かわ': ['革', '皮', 'カワ'],
            'き': ['木', 'キ'],
            'もくざい': ['木材', 'モクザイ'],
            
            # モンスター関連
            'りゅう': ['竜', '龍', 'リュウ'],
            'ドラゴン': ['竜', '龍', 'どらごん'],
            'まじゅう': ['魔獣', 'マジュウ'],
            'ようせい': ['妖精', 'ヨウセイ'],
            'フェアリー': ['妖精', 'ふぇありー'],
            
            # 色関連
            'あか': ['赤', 'アカ'],
            'あお': ['青', 'アオ'],
            'きいろ': ['黄', 'キイロ'],
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
            
            # 3. レベル/ランク表記を除去して再検索
            cleaned_query = self._remove_level_rank_suffix(normalized_query)
            if cleaned_query != normalized_query and cleaned_query:
                logger.info(f"レベル/ランク除去: '{normalized_query}' → '{cleaned_query}'")
                # レベル/ランクを除去したクエリで再度検索
                level_removed_results = await self._search_with_cleaned_query(cleaned_query)
                if level_removed_results:
                    # オリジナルのクエリ情報を結果に含める
                    for result in level_removed_results:
                        result['original_query'] = query
                        result['cleaned_query'] = cleaned_query
                    return level_removed_results
            
            # 4. ワイルドカード検索（*や?が含まれている場合）
            if self._has_wildcards(query):
                results = await self._search_wildcard(query)
                if results:
                    # ワイルドカード検索の結果にもオリジナルクエリ情報を含める
                    for result in results:
                        result['original_query'] = query
                    return results
            
            # 5. 表記ゆれ対応検索
            results = await self._search_fuzzy(normalized_query)
            if results:
                return results
            
            # 6. 部分一致検索（最後の手段）
            results = await self._search_partial_match(normalized_query)
            if results:
                return results
            
            # 7. ワイルドカード形式での検索（例：「トト・ノーマルの破片」→「*破片」）
            # アイテム名の末尾部分を抽出してワイルドカード検索
            wildcard_results = await self._search_with_wildcard_suffix(normalized_query)
            return wildcard_results
            
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
    
    def _remove_level_rank_suffix(self, item_name: str) -> str:
        """アイテム名からレベル/ランク表記を除去"""
        try:
            # レベル表記のパターン（Lv1, Lv.1, レベル1など）
            # Lv、レベル、ランクの表記を除去
            patterns = [
                r'[Ll][Vv]\.?\s*\d+$',  # Lv1, Lv.1, lv1など
                r'レベル\s*\d+$',        # レベル1など
                r'ランク\s*[A-Za-z\d]+$', # ランクA, ランク1など
                r'[Rr]ank\s*[A-Za-z\d]+$', # RankA, Rank1など（英語表記）
                r'★+$',                  # ★★など
                r'\s*\d+$'               # 末尾の数字のみ（スペース含む）
            ]
            
            cleaned_name = item_name
            for pattern in patterns:
                cleaned_name = re.sub(pattern, '', cleaned_name).strip()
            
            return cleaned_name
            
        except Exception as e:
            logger.warning(f"レベル/ランク除去エラー: {e}")
            return item_name
    
    def _has_wildcards(self, query: str) -> bool:
        """ワイルドカードが含まれているかチェック（全角対応）"""
        return any(char in query for char in WILDCARD_CHARS)
    
    async def _search_exact_formal_name(self, query: str) -> List[Dict[str, Any]]:
        """正式名称の完全一致検索"""
        try:
            async with aiosqlite.connect(self.db_manager.db_path) as db:
                db.row_factory = aiosqlite.Row
                results = []
                
                # formal_nameを持つテーブル
                tables = ['equipments', 'materials', 'mobs']
                for table in tables:
                    cursor = await db.execute(
                        f"SELECT *, '{table}' as item_type FROM {table} WHERE LOWER(formal_name) = ?",
                        (query,)
                    )
                    rows = await cursor.fetchall()
                    results.extend([dict(row) for row in rows])
                
                # npcsテーブル（nameカラムを使用）
                cursor = await db.execute(
                    "SELECT *, 'npcs' as item_type, name as formal_name FROM npcs WHERE LOWER(name) = ?",
                    (query,)
                )
                rows = await cursor.fetchall()
                results.extend([dict(row) for row in rows])
                
                # gatheringsテーブル（locationカラムを使用）
                cursor = await db.execute(
                    "SELECT *, 'gatherings' as item_type, location as formal_name FROM gatherings WHERE LOWER(location) = ?",
                    (query,)
                )
                rows = await cursor.fetchall()
                results.extend([dict(row) for row in rows])
                
                return results
                
        except Exception as e:
            logger.error(f"正式名称検索エラー: {e}")
            return []
    
    async def _search_exact_common_name(self, query: str) -> List[Dict[str, Any]]:
        """一般名称の完全一致検索"""
        try:
            async with aiosqlite.connect(self.db_manager.db_path) as db:
                db.row_factory = aiosqlite.Row
                results = []
                
                # common_nameを持つテーブル
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
                
                # gatheringsテーブル（locationカラムを使用）
                cursor = await db.execute(
                    "SELECT *, 'gatherings' as item_type, location as formal_name FROM gatherings"
                )
                rows = await cursor.fetchall()
                
                for row in rows:
                    row_dict = dict(row)
                    location = row_dict.get('location', '')
                    
                    if fnmatch(location.lower(), normalized_query.lower()):
                        results.append(row_dict)
                
                return results
                
        except Exception as e:
            logger.error(f"ワイルドカード検索エラー: {e}")
            return []
    
    async def _search_fuzzy(self, query: str) -> List[Dict[str, Any]]:
        """表記ゆれ対応検索"""
        try:
            all_results = []
            
            # 1. ひらがな・カタカナ変換
            hiragana_query = jaconv.kata2hira(query)
            katakana_query = jaconv.hira2kata(query)
            
            if hiragana_query != query:
                results = await self._search_partial_match(hiragana_query)
                all_results.extend(results)
            
            if katakana_query != query:
                results = await self._search_partial_match(katakana_query)
                all_results.extend(results)
            
            # 2. 定義済みの表記ゆれ対応
            for original, alternatives in self.fuzzy_map.items():
                if original in query:
                    for alternative in alternatives:
                        variant_query = query.replace(original, alternative)
                        results = await self._search_partial_match(variant_query)
                        all_results.extend(results)
            
            # 3. 読み方マップの対応
            for reading, kanji_list in self.reading_map.items():
                if reading in query:
                    for kanji in kanji_list:
                        variant_query = query.replace(reading, kanji)
                        results = await self._search_partial_match(variant_query)
                        all_results.extend(results)
            
            # 4. 「の」の追加/削除
            if 'の' not in query:
                # 2文字以上の場合、途中に「の」を追加
                for i in range(1, len(query)):
                    variant_query = query[:i] + 'の' + query[i:]
                    results = await self._search_partial_match(variant_query)
                    all_results.extend(results)
            else:
                # 「の」を削除
                variant_query = query.replace('の', '')
                results = await self._search_partial_match(variant_query)
                all_results.extend(results)
            
            # 重複除去とスコアリング
            return self._deduplicate_and_score_results(all_results, query, limit=20)
            
        except Exception as e:
            logger.error(f"表記ゆれ検索エラー: {e}")
            return []
    
    async def _search_partial_match(self, query: str) -> List[Dict[str, Any]]:
        """部分一致検索"""
        try:
            async with aiosqlite.connect(self.db_manager.db_path) as db:
                db.row_factory = aiosqlite.Row
                results = []
                
                # formal_name/common_nameを持つテーブル
                tables = ['equipments', 'materials', 'mobs']
                
                for table in tables:
                    cursor = await db.execute(
                        f"SELECT *, '{table}' as item_type FROM {table} WHERE LOWER(formal_name) LIKE ? OR LOWER(common_name) LIKE ?",
                        (f'%{query}%', f'%{query}%')
                    )
                    rows = await cursor.fetchall()
                    results.extend([dict(row) for row in rows])
                
                # npcsテーブル
                cursor = await db.execute(
                    "SELECT *, 'npcs' as item_type, name as formal_name FROM npcs WHERE LOWER(name) LIKE ?",
                    (f'%{query}%',)
                )
                rows = await cursor.fetchall()
                results.extend([dict(row) for row in rows])
                
                # gatheringsテーブル
                cursor = await db.execute(
                    "SELECT *, 'gatherings' as item_type, location as formal_name FROM gatherings WHERE LOWER(location) LIKE ?",
                    (f'%{query}%',)
                )
                rows = await cursor.fetchall()
                results.extend([dict(row) for row in rows])
                
                return results
                
        except Exception as e:
            logger.error(f"部分一致検索エラー: {e}")
            return []
    
    async def _search_with_cleaned_query(self, cleaned_query: str) -> List[Dict[str, Any]]:
        """クリーンなクエリで再検索（完全一致・部分一致含む）"""
        try:
            all_results = []
            
            # 1. 正式名称での完全一致
            exact_formal = await self._search_exact_formal_name(cleaned_query)
            all_results.extend(exact_formal)
            
            # 2. 一般名称での完全一致
            exact_common = await self._search_exact_common_name(cleaned_query)
            for result in exact_common:
                if not any(r['id'] == result['id'] and r['item_type'] == result['item_type'] for r in all_results):
                    all_results.append(result)
            
            # 3. 部分一致
            partial = await self._search_partial_match(cleaned_query)
            for result in partial:
                if not any(r['id'] == result['id'] and r['item_type'] == result['item_type'] for r in all_results):
                    all_results.append(result)
            
            # 重複除去とスコアリング
            return self._deduplicate_and_score_results(all_results, cleaned_query)
            
        except Exception as e:
            logger.error(f"クリーンクエリ検索エラー: {e}")
            return []
    
    def _deduplicate_and_score_results(self, results: List[Dict[str, Any]], query: str, limit: int = None) -> List[Dict[str, Any]]:
        """重複除去とスコアリング"""
        try:
            # 重複除去（id + item_typeで識別）
            unique_results = {}
            for result in results:
                key = f"{result.get('id')}_{result.get('item_type')}"
                if key not in unique_results:
                    unique_results[key] = result
                    # スコアを計算
                    unique_results[key]['search_score'] = self._calculate_relevance_score(result, query)
            
            # スコアでソート
            sorted_results = sorted(unique_results.values(), key=lambda x: x.get('search_score', 0), reverse=True)
            
            # 制限がある場合は適用
            if limit is not None:
                return sorted_results[:limit]
            
            return sorted_results
            
        except Exception as e:
            logger.error(f"重複除去・スコアリングエラー: {e}")
            return results
    
    def _calculate_relevance_score(self, result: Dict[str, Any], query: str) -> float:
        """検索結果の関連性スコアを計算"""
        score = 0.0
        query_lower = query.lower()
        
        # formal_nameとcommon_nameを取得
        formal_name = (result.get('formal_name') or '').lower()
        common_name = (result.get('common_name') or '').lower()
        
        # 完全一致
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
                
                # 2. npcsテーブルで必要素材に含まれるもの（納品・交換）
                npcs_using = await self._search_npcs_using_material(item_name)
                for npc in npcs_using:
                    npc['relation_type'] = 'material_for_npc'
                    # 実際の交換データを解析して詳細を取得
                    exchange_detail = await self._extract_npc_material_usage(npc, item_name)
                    npc['exchange_data'] = exchange_detail
                    related_items['usage_destinations'].append(npc)
                
                # 入手元の検索
                # 1. mobsからのドロップ
                mobs_dropping = await self._search_mobs_dropping_item(item_name)
                for mob in mobs_dropping:
                    mob['relation_type'] = 'drop_from_mob'
                    related_items['acquisition_sources'].append(mob)
                
                # 2. gatheringの場所情報
                gathering_info = await self._search_gathering_info(item_name)
                if gathering_info:
                    # acquisition_infoとして格納
                    related_items['acquisition_info'] = gathering_info
                    
                    # gathering_locationsテーブルからも検索
                    gathering_locations = await self._search_gathering_locations(item_name)
                    for loc in gathering_locations:
                        loc['relation_type'] = 'gathering_location'
                        related_items['acquisition_sources'].append(loc)
                
                # 3. npcsからの取得（購入・交換・クエスト）
                npcs_providing = await self._search_npcs_providing_material(item_name)
                for npc in npcs_providing:
                    npc['relation_type'] = 'npc_source'
                    npc['source_type'] = 'obtainable'  # 入手元
                    # 実際の交換データを解析
                    exchange_detail = await self._extract_npc_exchange_detail(npc, item_name)
                    npc['exchange_data'] = exchange_detail
                    related_items['acquisition_sources'].append(npc)
                
                # 4. npcsへの納品（入手元と利用先を区別）
                npcs_requiring = await self._search_npcs_using_material(item_name)
                for npc in npcs_requiring:
                    # 既に利用先に含まれていない場合のみ追加
                    if not any(dest['id'] == npc['id'] for dest in related_items['usage_destinations'] if dest.get('relation_type') == 'material_for_npc'):
                        npc['relation_type'] = 'npc_source'
                        npc['source_type'] = 'required'  # 納品先
                        related_items['acquisition_sources'].append(npc)
                
            elif item_type == 'equipments':
                # equipment名の場合
                related_items['materials'] = []  # 必要素材
                related_items['acquisition_sources'] = []  # 入手元
                
                # 必要素材の抽出と検索
                required_materials = item_data.get('required_materials', '')
                if required_materials:
                    material_list = await self._parse_required_materials(required_materials)
                    for material_info in material_list:
                        material_name = material_info['name']
                        material_results = await self._search_material_by_name(material_name)
                        for material in material_results:
                            material['required_quantity'] = material_info.get('quantity', '')
                            related_items['materials'].append(material)
                
                # 入手元の検索
                # 1. mobsからのドロップ
                mobs_dropping = await self._search_mobs_dropping_item(item_name)
                for mob in mobs_dropping:
                    mob['relation_type'] = 'drop_from_mob'
                    related_items['acquisition_sources'].append(mob)
                
                # 2. npcsからの取得
                npcs_providing = await self._search_npcs_providing_material(item_name)
                for npc in npcs_providing:
                    npc['relation_type'] = 'npc_source'
                    npc['source_type'] = 'obtainable'
                    exchange_detail = await self._extract_npc_exchange_detail(npc, item_name)
                    npc['exchange_data'] = exchange_detail
                    related_items['acquisition_sources'].append(npc)
                
                # 3. 採集関連の情報（特定の装備が採集で得られる場合）
                gathering_info = await self._search_gathering_info(item_name)
                if gathering_info:
                    related_items['acquisition_info'] = gathering_info
                    
                    # gathering_locationsテーブルからも検索
                    gathering_locations = await self._search_gathering_locations(item_name)
                    for loc in gathering_locations:
                        loc['relation_type'] = 'gathering_location'
                        related_items['acquisition_sources'].append(loc)
                
            elif item_type == 'mobs':
                # mob名の場合
                related_items['dropped_items'] = []  # ドロップアイテム
                
                # ドロップアイテムの抽出と検索
                dropped_items = item_data.get('drops', '')  # カラム名を修正
                if dropped_items:
                    item_list = await self._parse_dropped_items(dropped_items)
                    for item_info in item_list:
                        item_name_to_search = item_info['name']
                        # equipmentsとmaterialsから検索
                        item_results = await self._search_item_by_name(item_name_to_search)
                        
                        # 見つからない場合は、ワイルドカード検索を試みる
                        if not item_results:
                            # レベル/ランクを除去してからワイルドカード検索
                            cleaned_item_name = self._remove_level_rank_suffix(item_name_to_search)
                            if cleaned_item_name != item_name_to_search:
                                # まず、レベル/ランクを除去した名前で通常検索
                                item_results = await self._search_item_by_name(cleaned_item_name)
                            
                            # それでも見つからない場合、ワイルドカードアイテムを検索
                            if not item_results:
                                wildcard_results = await self._find_matching_wildcard_items(item_name_to_search)
                                item_results.extend(wildcard_results)
                        
                        for item in item_results:
                            item['drop_info'] = item_info.get('drop_rate', '')
                            # ワイルドカードアイテムの場合、元のアイテム名も保持
                            if any(c in item.get('formal_name', '') for c in WILDCARD_CHARS):
                                item['original_drop_name'] = item_name_to_search
                            related_items['dropped_items'].append(item)
                
            elif item_type == 'npcs':
                # NPC名の場合
                related_items['obtainable_items'] = []  # 取得可能アイテム
                related_items['required_materials'] = []  # 必要素材
                
                # 取得可能アイテムの処理
                obtainable_items = item_data.get('obtainable_items', '')
                if obtainable_items:
                    # NPCExchangeParserを使用して交換情報を解析
                    from npc_parser import NPCExchangeParser
                    exchanges = NPCExchangeParser.parse_exchange_items(
                        obtainable_items,
                        item_data.get('required_materials', ''),
                        item_data.get('exp', ''),
                        item_data.get('gold', '')
                    )
                    
                    # 各交換パターンについてアイテムを検索
                    for exchange in exchanges:
                        # 取得可能アイテムを検索
                        obtainable_item = exchange.get('obtainable_item', '')
                        if obtainable_item:
                            item_name_only = obtainable_item.split(':')[0].strip()
                            item_results = await self._search_item_by_name(item_name_only)
                            for item in item_results:
                                item['exchange_info'] = exchange
                                related_items['obtainable_items'].append(item)
                        
                        # 必要素材を検索
                        required_mats = exchange.get('required_materials', '')
                        if required_mats:
                            material_list = await self._parse_required_materials(required_mats)
                            for mat_info in material_list:
                                mat_results = await self._search_material_by_name(mat_info['name'])
                                for mat in mat_results:
                                    mat['required_quantity'] = mat_info.get('quantity', '')
                                    mat['exchange_info'] = exchange
                                    # 重複チェック
                                    if not any(m['id'] == mat['id'] for m in related_items['required_materials']):
                                        related_items['required_materials'].append(mat)
            
            return related_items
            
        except Exception as e:
            logger.error(f"関連アイテム検索エラー: {e}")
            return {}
    
    async def _search_equipment_using_material(self, material_name: str) -> List[Dict[str, Any]]:
        """指定した素材を必要とする装備を検索"""
        try:
            async with aiosqlite.connect(self.db_manager.db_path) as db:
                db.row_factory = aiosqlite.Row
                results = []
                
                # required_materialsカラムに含まれる装備を検索
                cursor = await db.execute(
                    "SELECT *, 'equipments' as item_type FROM equipments WHERE required_materials LIKE ?",
                    (f'%{material_name}%',)
                )
                rows = await cursor.fetchall()
                
                for row in rows:
                    row_dict = dict(row)
                    # 素材リストを解析して実際に含まれているか確認
                    if self._check_material_in_requirements(row_dict.get('required_materials', ''), material_name):
                        results.append(row_dict)
                
                return results
                
        except Exception as e:
            logger.error(f"Equipment using material検索エラー: {e}")
            return []
    
    async def _search_mobs_dropping_item(self, item_name: str) -> List[Dict[str, Any]]:
        """指定したアイテムをドロップするモブを検索"""
        try:
            async with aiosqlite.connect(self.db_manager.db_path) as db:
                db.row_factory = aiosqlite.Row
                results = []
                
                # dropsカラムに含まれるモブを検索
                cursor = await db.execute(
                    "SELECT *, 'mobs' as item_type FROM mobs WHERE drops LIKE ?",
                    (f'%{item_name}%',)
                )
                rows = await cursor.fetchall()
                
                for row in rows:
                    row_dict = dict(row)
                    # ドロップアイテムリストを解析して実際に含まれているか確認
                    if self._check_item_in_drops(row_dict.get('drops', ''), item_name):
                        results.append(row_dict)
                
                return results
                
        except Exception as e:
            logger.error(f"Mobs dropping item検索エラー: {e}")
            return []
    
    async def _search_gathering_info(self, item_name: str) -> Optional[Dict[str, str]]:
        """アイテムの採集情報を検索（新しいテーブル構造対応）"""
        try:
            async with aiosqlite.connect(self.db_manager.db_path) as db:
                db.row_factory = aiosqlite.Row
                
                # materialsテーブルのacquisition_category, methodを確認
                cursor = await db.execute(
                    "SELECT acquisition_category, acquisition_method FROM materials WHERE formal_name = ?",
                    (item_name,)
                )
                row = await cursor.fetchone()
                
                if row:
                    category = row['acquisition_category']
                    method = row['acquisition_method']
                    
                    if category in ['採取', '採掘', '釣り']:
                        return {
                            'category': category,
                            'method': method or '',
                            'location': ''  # locationカラムは存在しないため空文字
                        }
                
                return None
                
        except Exception as e:
            logger.error(f"採集情報検索エラー: {e}")
            return None
    
    async def _search_gathering_locations(self, item_name: str) -> List[Dict[str, Any]]:
        """gathering_locationsテーブルから採集場所を検索"""
        try:
            async with aiosqlite.connect(self.db_manager.db_path) as db:
                db.row_factory = aiosqlite.Row
                results = []
                
                # gatheringsテーブルを検索
                cursor = await db.execute(
                    """
                    SELECT *, 'gatherings' as item_type 
                    FROM gatherings 
                    WHERE resource_name LIKE ?
                    """,
                    (f'%{item_name}%',)
                )
                rows = await cursor.fetchall()
                
                for row in rows:
                    row_dict = dict(row)
                    # resource_nameを確認
                    if item_name.lower() in row_dict.get('resource_name', '').lower():
                        results.append(row_dict)
                
                return results
                
        except Exception as e:
            logger.error(f"採集場所検索エラー: {e}")
            return []
    
    def _check_material_in_requirements(self, requirements_str: str, material_name: str) -> bool:
        """必要素材リストに特定の素材が含まれているかチェック"""
        try:
            if not requirements_str:
                return False
            
            # カンマまたは改行で分割
            materials = re.split(r'[,\n、]', requirements_str)
            for material in materials:
                material = material.strip()
                if ':' in material:
                    mat_name = material.split(':')[0].strip()
                else:
                    mat_name = material
                
                if mat_name == material_name or material_name in mat_name:
                    return True
            
            return False
            
        except Exception as e:
            logger.warning(f"素材チェックエラー: {e}")
            return False
    
    def _check_item_in_drops(self, drops_str: str, item_name: str) -> bool:
        """ドロップアイテムリストに特定のアイテムが含まれているかチェック"""
        try:
            if not drops_str:
                return False
            
            # カンマまたは改行で分割
            items = re.split(r'[,\n、]', drops_str)
            for item in items:
                item = item.strip()
                # ドロップ率の情報を除去
                if '(' in item:
                    item = item.split('(')[0].strip()
                
                if item == item_name or item_name in item:
                    return True
            
            return False
            
        except Exception as e:
            logger.warning(f"ドロップアイテムチェックエラー: {e}")
            return False
    
    def _check_item_in_obtainable_items(self, obtainable_str: str, item_name: str) -> bool:
        """取得可能アイテムリストに特定のアイテムが含まれているかチェック"""
        try:
            if not obtainable_str:
                return False
            
            # カンマまたは改行で分割
            items = re.split(r'[,\n、]', obtainable_str)
            for item in items:
                item = item.strip()
                # 数量情報を除去
                if ':' in item:
                    item = item.split(':')[0].strip()
                
                if item == item_name or item_name in item:
                    return True
            
            return False
            
        except Exception as e:
            logger.warning(f"取得可能アイテムチェックエラー: {e}")
            return False
    
    async def _parse_required_materials(self, materials_str: str) -> List[Dict[str, str]]:
        """必要素材文字列を解析"""
        try:
            materials = []
            
            if not materials_str:
                return materials
            
            # カンマまたは改行で分割
            items = re.split(r'[,\n、]', materials_str)
            for item in items:
                item = item.strip()
                if not item:
                    continue
                
                if ':' in item:
                    name, quantity = item.split(':', 1)
                    materials.append({
                        'name': name.strip(),
                        'quantity': quantity.strip()
                    })
                else:
                    materials.append({
                        'name': item,
                        'quantity': ''
                    })
            
            return materials
            
        except Exception as e:
            logger.error(f"必要素材解析エラー: {e}")
            return []
    
    async def _parse_dropped_items(self, drops_str: str) -> List[Dict[str, str]]:
        """ドロップアイテム文字列を解析"""
        try:
            drops = []
            
            if not drops_str:
                return drops
            
            # カンマまたは改行で分割
            items = re.split(r'[,\n、]', drops_str)
            for item in items:
                item = item.strip()
                if not item:
                    continue
                
                # ドロップ率情報を抽出
                drop_rate = ''
                if '(' in item:
                    parts = item.split('(')
                    item_name = parts[0].strip()
                    drop_rate = parts[1].rstrip(')')
                else:
                    item_name = item
                
                drops.append({
                    'name': item_name,
                    'drop_rate': drop_rate
                })
            
            return drops
            
        except Exception as e:
            logger.error(f"ドロップアイテム解析エラー: {e}")
            return []
    
    async def _search_material_by_name(self, material_name: str) -> List[Dict[str, Any]]:
        """素材名で素材を検索"""
        try:
            async with aiosqlite.connect(self.db_manager.db_path) as db:
                db.row_factory = aiosqlite.Row
                
                cursor = await db.execute(
                    "SELECT *, 'materials' as item_type FROM materials WHERE formal_name = ? OR common_name = ?",
                    (material_name, material_name)
                )
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"素材名検索エラー: {e}")
            return []
    
    async def _search_item_by_name(self, item_name: str) -> List[Dict[str, Any]]:
        """アイテム名で装備・素材を検索（ワイルドカードアイテムも含む）"""
        try:
            results = []
            
            # equipmentsから検索
            async with aiosqlite.connect(self.db_manager.db_path) as db:
                db.row_factory = aiosqlite.Row
                
                cursor = await db.execute(
                    "SELECT *, 'equipments' as item_type FROM equipments WHERE formal_name = ? OR common_name = ?",
                    (item_name, item_name)
                )
                rows = await cursor.fetchall()
                results.extend([dict(row) for row in rows])
                
                # materialsから検索
                cursor = await db.execute(
                    "SELECT *, 'materials' as item_type FROM materials WHERE formal_name = ? OR common_name = ?",
                    (item_name, item_name)
                )
                rows = await cursor.fetchall()
                results.extend([dict(row) for row in rows])
                
                # ワイルドカードアイテムも検索（*アイテム名の形式）
                wildcard_patterns = [f"*{item_name}", f"?{item_name}", f"＊{item_name}", f"？{item_name}"]
                for pattern in wildcard_patterns:
                    # equipmentsから検索
                    cursor = await db.execute(
                        "SELECT *, 'equipments' as item_type FROM equipments WHERE formal_name = ? OR common_name = ?",
                        (pattern, pattern)
                    )
                    rows = await cursor.fetchall()
                    results.extend([dict(row) for row in rows])
                    
                    # materialsから検索
                    cursor = await db.execute(
                        "SELECT *, 'materials' as item_type FROM materials WHERE formal_name = ? OR common_name = ?",
                        (pattern, pattern)
                    )
                    rows = await cursor.fetchall()
                    results.extend([dict(row) for row in rows])
            
            # 重複を除去
            unique_results = {}
            for result in results:
                key = f"{result.get('id')}_{result.get('item_type')}"
                if key not in unique_results:
                    unique_results[key] = result
            
            return list(unique_results.values())
            
        except Exception as e:
            logger.error(f"アイテム名検索エラー: {e}")
            return []
    
    async def _extract_material_usage(self, requirements_str: str, target_material: str) -> str:
        """必要素材リストから特定素材の使用情報を抽出"""
        try:
            if not requirements_str:
                return ""
            
            materials = re.split(r'[,\n、]', requirements_str)
            for material in materials:
                material = material.strip()
                if ':' in material:
                    mat_name, quantity = material.split(':', 1)
                    mat_name = mat_name.strip()
                    quantity = quantity.strip()
                    
                    if mat_name == target_material or target_material in mat_name:
                        return f"必要数: {quantity}"
                else:
                    if material == target_material or target_material in material:
                        return "必要素材"
            
            return ""
            
        except Exception as e:
            logger.warning(f"素材使用情報抽出エラー: {e}")
            return ""
    
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
    
    def _check_material_in_npc_requirements(self, requirements_str: str, material_name: str) -> bool:
        """NPC必要素材リストに特定の素材が含まれているかチェック"""
        return self._check_material_in_requirements(requirements_str, material_name)
    
    def _check_material_in_npc_obtainable(self, obtainable_str: str, material_name: str) -> bool:
        """NPC取得可能アイテムリストに特定の素材が含まれているかチェック"""
        return self._check_item_in_obtainable_items(obtainable_str, material_name)
    
    async def _extract_npc_exchange_detail(self, npc_data: Dict[str, Any], target_item: str) -> Optional[Dict[str, Any]]:
        """NPCの交換詳細から特定アイテムに関する情報を抽出"""
        try:
            # NPCExchangeParserを使用
            from npc_parser import NPCExchangeParser
            exchanges = NPCExchangeParser.parse_exchange_items(
                npc_data.get('obtainable_items', ''),
                npc_data.get('required_materials', ''),
                npc_data.get('exp', ''),
                npc_data.get('gold', '')
            )
            
            # 対象アイテムを含む交換を探す
            for exchange in exchanges:
                obtainable = exchange.get('obtainable_item', '')
                if obtainable:
                    item_name = obtainable.split(':')[0].strip()
                    if item_name == target_item or target_item in item_name:
                        return exchange
            
            return None
            
        except Exception as e:
            logger.warning(f"NPC交換詳細抽出エラー: {e}")
            return None
    
    async def _extract_npc_material_usage(self, npc_data: Dict[str, Any], target_material: str) -> Optional[Dict[str, Any]]:
        """NPCの必要素材から特定素材の使用情報を抽出"""
        try:
            # NPCExchangeParserを使用
            from npc_parser import NPCExchangeParser
            exchanges = NPCExchangeParser.parse_exchange_items(
                npc_data.get('obtainable_items', ''),
                npc_data.get('required_materials', ''),
                npc_data.get('exp', ''),
                npc_data.get('gold', '')
            )
            
            # 対象素材を含む交換を探す
            for exchange in exchanges:
                required = exchange.get('required_materials', '')
                if required and self._check_material_in_requirements(required, target_material):
                    return exchange
            
            return None
            
        except Exception as e:
            logger.warning(f"NPC素材使用詳細抽出エラー: {e}")
            return None
    
    async def _search_with_wildcard_suffix(self, query: str) -> List[Dict[str, Any]]:
        """アイテム名の末尾部分を使ったワイルドカード検索"""
        try:
            # レベル/ランクを除去
            cleaned_query = self._remove_level_rank_suffix(query)
            
            # ワイルドカードアイテムを検索
            wildcard_results = await self._find_matching_wildcard_items(query)
            
            if wildcard_results:
                # オリジナルクエリ情報を追加
                for result in wildcard_results:
                    result['original_query'] = query
                    result['wildcard_matched'] = True
                return wildcard_results
            
            # レベル/ランクを除去した名前でも検索
            if cleaned_query != query:
                wildcard_results = await self._find_matching_wildcard_items(cleaned_query)
                if wildcard_results:
                    for result in wildcard_results:
                        result['original_query'] = query
                        result['wildcard_matched'] = True
                    return wildcard_results
            
            # ワイルドカード分割検索は、データベースに該当するワイルドカードアイテムが存在する場合のみ実行
            # 「の」で分割して最後の部分を取得
            parts = query.split('の')
            if len(parts) > 1:
                suffix = parts[-1].strip()
                wildcard_query = f"*{suffix}"
                
                # まず、完全一致する「*破片」のようなワイルドカードアイテムを検索
                exact_wildcard_results = await self._search_exact_wildcard_item(wildcard_query)
                if exact_wildcard_results:
                    logger.info(f"ワイルドカード末尾検索: '{query}' → '{wildcard_query}'")
                    # オリジナルクエリ情報を追加
                    for result in exact_wildcard_results:
                        result['original_query'] = query
                        result['wildcard_matched'] = True
                    return exact_wildcard_results
            
            # 「・」で分割して最後の部分を取得
            parts = query.split('・')
            if len(parts) > 1:
                suffix = parts[-1].strip()
                wildcard_query = f"*{suffix}"
                
                exact_wildcard_results = await self._search_exact_wildcard_item(wildcard_query)
                if exact_wildcard_results:
                    logger.info(f"ワイルドカード末尾検索: '{query}' → '{wildcard_query}'")
                    for result in exact_wildcard_results:
                        result['original_query'] = query
                        result['wildcard_matched'] = True
                    return exact_wildcard_results
            
            return []
            
        except Exception as e:
            logger.error(f"ワイルドカード末尾検索エラー: {e}")
            return []
    
    async def _search_exact_wildcard_item(self, wildcard_query: str) -> List[Dict[str, Any]]:
        """ワイルドカードアイテムの完全一致検索（例：「*破片」という名前のアイテムを検索）"""
        try:
            async with aiosqlite.connect(self.db_manager.db_path) as db:
                db.row_factory = aiosqlite.Row
                results = []
                
                # 各テーブルでワイルドカード名と完全一致するアイテムを検索
                tables = ['equipments', 'materials', 'mobs']
                
                for table in tables:
                    # formal_nameが完全一致
                    cursor = await db.execute(
                        f"SELECT *, '{table}' as item_type FROM {table} WHERE formal_name = ?",
                        (wildcard_query,)
                    )
                    rows = await cursor.fetchall()
                    results.extend([dict(row) for row in rows])
                    
                    # common_nameが完全一致
                    cursor = await db.execute(
                        f"SELECT *, '{table}' as item_type FROM {table} WHERE common_name = ?",
                        (wildcard_query,)
                    )
                    rows = await cursor.fetchall()
                    results.extend([dict(row) for row in rows])
                
                # 重複を除去
                unique_results = {}
                for result in results:
                    key = f"{result.get('id')}_{result.get('item_type')}"
                    if key not in unique_results:
                        unique_results[key] = result
                
                return list(unique_results.values())
                
        except Exception as e:
            logger.error(f"ワイルドカードアイテム完全一致検索エラー: {e}")
            return []
    
    async def _find_matching_wildcard_items(self, item_name: str) -> List[Dict[str, Any]]:
        """指定されたアイテム名にマッチするワイルドカードアイテムを検索"""
        try:
            # レベル/ランクを除去
            cleaned_name = self._remove_level_rank_suffix(item_name)
            
            async with aiosqlite.connect(self.db_manager.db_path) as db:
                db.row_factory = aiosqlite.Row
                results = []
                
                # ワイルドカード文字のリスト
                wildcard_chars = ['*', '?', '＊', '？']
                
                # 各テーブルでワイルドカードアイテムを検索
                tables = ['equipments', 'materials']
                
                for table in tables:
                    # ワイルドカードを含むアイテムを取得
                    query = f"""
                        SELECT *, '{table}' as item_type FROM {table} 
                        WHERE formal_name LIKE '%*%' OR formal_name LIKE '%?%' 
                        OR formal_name LIKE '%＊%' OR formal_name LIKE '%？%'
                    """
                    cursor = await db.execute(query)
                    rows = await cursor.fetchall()
                    
                    for row in rows:
                        row_dict = dict(row)
                        wildcard_name = row_dict.get('formal_name', '')
                        
                        # ワイルドカードアイテムが元のアイテム名にマッチするかチェック
                        if self._matches_wildcard_pattern(wildcard_name, item_name):
                            results.append(row_dict)
                        # レベル/ランクを除去した名前でもチェック
                        elif cleaned_name != item_name and self._matches_wildcard_pattern(wildcard_name, cleaned_name):
                            results.append(row_dict)
                
                return results
                
        except Exception as e:
            logger.error(f"ワイルドカードアイテム検索エラー: {e}")
            return []
    
    def _matches_wildcard_pattern(self, wildcard_pattern: str, item_name: str) -> bool:
        """ワイルドカードパターンがアイテム名にマッチするかチェック"""
        try:
            # ワイルドカード文字を統一（全角も半角も*として扱う）
            wildcard_chars = WILDCARD_SET
            
            # パターンからワイルドカード文字の位置を特定
            wildcard_positions = []
            for i, char in enumerate(wildcard_pattern):
                if char in wildcard_chars:
                    wildcard_positions.append(i)
            
            if not wildcard_positions:
                return False
            
            # ワイルドカード以外の部分を抽出
            pattern_parts = []
            last_pos = 0
            
            for pos in wildcard_positions:
                if pos > last_pos:
                    pattern_parts.append(wildcard_pattern[last_pos:pos])
                pattern_parts.append('*')  # ワイルドカードマーカー
                last_pos = pos + 1
            
            if last_pos < len(wildcard_pattern):
                pattern_parts.append(wildcard_pattern[last_pos:])
            
            # マッチング処理
            if pattern_parts[0] == '*':
                # 前方ワイルドカード（例：*破片）
                suffix = ''.join(pattern_parts[1:])
                return item_name.endswith(suffix)
            elif pattern_parts[-1] == '*':
                # 後方ワイルドカード（例：グロースクリスタル*）
                prefix = ''.join(pattern_parts[:-1])
                return item_name.startswith(prefix)
            else:
                # 中間ワイルドカード（例：【圧縮】*アイテム）
                # ワイルドカード部分以外が完全一致しているかチェック
                item_pos = 0
                for part in pattern_parts:
                    if part == '*':
                        continue
                    pos = item_name.find(part, item_pos)
                    if pos == -1:
                        return False
                    item_pos = pos + len(part)
                return True
                
        except Exception as e:
            logger.warning(f"ワイルドカードパターンマッチングエラー: {e}")
            return False