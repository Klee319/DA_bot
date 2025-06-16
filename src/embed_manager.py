import discord
from discord.ext import commands
import logging
import aiohttp
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

class EmbedManager:
    def __init__(self, config):
        self.config = config
        self.type_colors = {
            'equipments': discord.Color.blue(),
            'materials': discord.Color.green(),
            'mobs': discord.Color.red(),
            'gatherings': discord.Color.orange(),
            'npcs': discord.Color.purple()
        }
        self.type_emojis = {
            'equipments': '⚔️',
            'materials': '🧪',
            'mobs': '👹',
            'gatherings': '🌿',
            'npcs': '🏪'
        }
    
    async def create_item_detail_embed(self, item_data: Dict[str, Any], user_id: str) -> Tuple[discord.Embed, discord.ui.View]:
        """アイテム詳細のEmbedとViewを作成"""
        try:
            item_type = item_data.get('item_type', 'equipments')
            formal_name = item_data.get('formal_name', 'Unknown')
            
            # Embedを作成
            embed = discord.Embed(
                title=f"**{formal_name}**",
                color=self.type_colors.get(item_type, discord.Color.default())
            )
            
            # 基本情報を最初に表示
            await self._add_basic_info_section(embed, item_data, item_type)
            
            # タイプ別の詳細情報を追加
            await self._add_detailed_info_section(embed, item_data, item_type)
            
            # 画像URLが有効な場合は画像を設定
            image_url = item_data.get('image_url')
            if image_url and await self._is_valid_image_url(image_url):
                embed.set_thumbnail(url=image_url)
            
            # フッターは削除（ジャンル表示不要）
            
            # インタラクティブなViewを作成
            view = ItemDetailView(item_data, user_id, self)
            
            return embed, view
            
        except Exception as e:
            logger.error(f"アイテム詳細Embed作成エラー: {e}")
            # エラー時のフォールバック
            embed = discord.Embed(
                title="❌ エラー",
                description="アイテム情報の表示中にエラーが発生しました",
                color=discord.Color.red()
            )
            return embed, None
    
    async def _add_basic_info_section(self, embed: discord.Embed, item_data: Dict[str, Any], item_type: str):
        """基本情報セクションを追加"""
        # 一般名称（別名）を個別フィールドとして追加（常に箇条書き形式）
        common_name = item_data.get('common_name')
        if common_name and str(common_name).strip():
            if ',' in str(common_name):
                name_list = [f"　• `{name.strip()}`" for name in str(common_name).split(',') if name.strip()]
            else:
                name_list = [f"　• `{common_name}`"]
            # 1行目にゼロ幅スペースを挿入
            name_list[0] = "\u200B" + name_list[0]
            embed.add_field(
                name="一般名称:",
                value="\n".join(name_list),
                inline=False
            )
        
        # タイプ別の重要情報を個別フィールドとして追加
        if item_type == 'mobs':
            # モブの場合（必要レベルは詳細セクションで表示）
            area = item_data.get('area')
            if area:
                # 単一値の場合は改行なし、複数値の場合は箇条書き
                if ',' in str(area):
                    area_list = [f"　• `{a.strip()}`" for a in str(area).split(',') if a.strip()]
                    # 1行目にゼロ幅スペースを挿入
                    area_list[0] = "\u200B" + area_list[0]
                    embed.add_field(
                        name="出没エリア:",
                        value="\n".join(area_list),
                        inline=False
                    )
                else:
                    # 単一値の場合も改行とインデント有りで表示
                    embed.add_field(
                        name="出没エリア:",
                        value=f"\u200B　`{area}`",
                        inline=False
                    )
        elif item_type == 'equipments':
            # 装備の場合
            equipment_type = item_data.get('type')
            acquisition_category = item_data.get('acquisition_category')
            if equipment_type:
                if ',' in str(equipment_type):
                    type_list = [f"　• `{t.strip()}`" for t in str(equipment_type).split(',') if t.strip()]
                    # 1行目にゼロ幅スペースを挿入
                    type_list[0] = "\u200B" + type_list[0]
                    embed.add_field(
                        name="種類:",
                        value="\n".join(type_list),
                        inline=False
                    )
                else:
                    embed.add_field(
                        name="種類:",
                        value=f"\u200B　`{equipment_type}`",
                        inline=False
                    )
            if acquisition_category:
                if ',' in str(acquisition_category):
                    cat_list = [f"　• `{cat.strip()}`" for cat in str(acquisition_category).split(',') if cat.strip()]
                    # 1行目にゼロ幅スペースを挿入
                    cat_list[0] = "\u200B" + cat_list[0]
                    embed.add_field(
                        name="入手方法:",
                        value="\n".join(cat_list),
                        inline=False
                    )
                else:
                    embed.add_field(
                        name="入手方法:",
                        value=f"\u200B　`{acquisition_category}`",
                        inline=False
                    )
        elif item_type == 'materials':
            # 素材の場合
            acquisition_category = item_data.get('acquisition_category')
            if acquisition_category:
                if ',' in str(acquisition_category):
                    cat_list = [f"　• `{cat.strip()}`" for cat in str(acquisition_category).split(',') if cat.strip()]
                    # 1行目にゼロ幅スペースを挿入
                    cat_list[0] = "\u200B" + cat_list[0]
                    embed.add_field(
                        name="入手カテゴリ:",
                        value="\n".join(cat_list),
                        inline=False
                    )
                else:
                    embed.add_field(
                        name="入手カテゴリ:",
                        value=f"\u200B　`{acquisition_category}`",
                        inline=False
                    )
        elif item_type == 'gatherings':
            # 採集の場合
            collection_method = item_data.get('collection_method')
            if collection_method:
                if ',' in str(collection_method):
                    method_list = [f"　• `{method.strip()}`" for method in str(collection_method).split(',') if method.strip()]
                    # 1行目にゼロ幅スペースを挿入
                    method_list[0] = "\u200B" + method_list[0]
                    embed.add_field(
                        name="収集方法:",
                        value="\n".join(method_list),
                        inline=False
                    )
                else:
                    embed.add_field(
                        name="収集方法:",
                        value=f"\u200B　`{collection_method}`",
                        inline=False
                    )
    
    async def _add_detailed_info_section(self, embed: discord.Embed, item_data: Dict[str, Any], item_type: str):
        """詳細情報セクションを追加"""
        if item_type == 'mobs':
            await self._add_mob_details(embed, item_data)
        elif item_type == 'equipments':
            await self._add_equipment_details(embed, item_data)
        elif item_type == 'materials':
            await self._add_material_details(embed, item_data)
        elif item_type == 'gatherings':
            await self._add_gathering_details(embed, item_data)
    
    async def _add_mob_details(self, embed: discord.Embed, item_data: Dict[str, Any]):
        """モブの詳細情報を追加"""
        # 必要レベル（EXPの上に配置）
        required_level = item_data.get('required_level')
        if required_level:
            try:
                level_int = int(float(str(required_level).replace(',', '')))
                embed.add_field(
                    name="必要レベル:",
                    value=f"\u200B　`{level_int} lv`",
                    inline=False
                )
            except (ValueError, TypeError):
                embed.add_field(
                    name="必要レベル:",
                    value=f"\u200B　`{required_level} lv`",
                    inline=False
                )
        
        # EXP
        exp = item_data.get('exp')
        if exp:
            try:
                exp_int = int(float(str(exp).replace(',', '')))
                embed.add_field(
                    name="EXP:",
                    value=f"\u200B　`{exp_int:,} exp`",
                    inline=False
                )
            except (ValueError, TypeError):
                embed.add_field(
                    name="EXP:",
                    value=f"\u200B　`{exp} exp`",
                    inline=False
                )
        
        # Gold
        gold = item_data.get('gold')
        if gold:
            try:
                gold_int = int(float(str(gold).replace(',', '')))
                embed.add_field(
                    name="Gold:",
                    value=f"\u200B　`{gold_int:,} G`",
                    inline=False
                )
            except (ValueError, TypeError):
                embed.add_field(
                    name="Gold:",
                    value=f"\u200B　`{gold} G`",
                    inline=False
                )
        
        # 必要守備力（Goldの下に配置）
        required_defense = item_data.get('required_defense')
        if required_defense:
            try:
                defense_int = int(float(str(required_defense).replace(',', '')))
                embed.add_field(
                    name="必要守備力:",
                    value=f"\u200B　`{defense_int:,}`",
                    inline=False
                )
            except (ValueError, TypeError):
                embed.add_field(
                    name="必要守備力:",
                    value=f"\u200B　`{required_defense}`",
                    inline=False
                )
        
        # ドロップ品（関連アイテム検索可能にする）
        drops = item_data.get("drops")
        if drops and str(drops).strip():
            drop_items = [item.strip() for item in str(drops).split(",") if item.strip()]
            drop_list = [f"　• `{item}`" for item in drop_items[:10]]

            drop_text = "\u200B" + "\n".join(drop_list)   # ←追加した \u200B と先頭改行
            embed.add_field(
                name="ドロップ品:",
                value=drop_text,
                inline=False
            )
        
        # エリア詳細
        area_detail = item_data.get('area_detail')
        if area_detail and str(area_detail).strip():
            embed.add_field(
                name="エリア詳細:",
                value=f"\u200B　`{area_detail}`",
                inline=False
            )
        
        # 説明（旧：一言）
        description = item_data.get('description')
        if description and str(description).strip():
            embed.add_field(
                name="説明:",
                value=f"　`{description}`",
                inline=False
            )
        
        # ドロップ品がある場合は※説明文を最下部に追加
        drops = item_data.get('drops')
        if drops and str(drops).strip():
            embed.add_field(
                name="\u200b",  # 空白フィールド名
                value="*※ 下のボタンでドロップアイテム詳細を検索*",
                inline=False
            )
    
    async def _add_equipment_details(self, embed: discord.Embed, item_data: Dict[str, Any]):
        """装備の詳細情報を追加"""
        # 必要素材（関連アイテム検索可能にする）
        required_materials = item_data.get('required_materials')
        if required_materials and str(required_materials).strip():
            material_items = [item.strip() for item in str(required_materials).split(',') if item.strip()]
            # :を×に置換
            material_list = [f"　• `{item.replace(':', '×')}`" for item in material_items[:10]]
            # 1行目にゼロ幅スペースを挿入
            material_list[0] = "\u200B" + material_list[0]
            
            embed.add_field(
                name="必要素材:",
                value="\n".join(material_list),
                inline=False
            )
        
        # 効果
        item_effect = item_data.get('item_effect')
        if item_effect and str(item_effect).strip():
            embed.add_field(
                name="効果:",
                value=f"\u200B　`{item_effect}`",
                inline=False
            )
        
        # 入手場所
        acquisition_location = item_data.get('acquisition_location')
        if acquisition_location and str(acquisition_location).strip():
            embed.add_field(
                name="入手場所:",
                value=f"\u200B　`{acquisition_location}`",
                inline=False
            )
        
        # 説明（旧：一言）
        description = item_data.get('description')
        if description and str(description).strip():
            embed.add_field(
                name="説明:",
                value=f"　`{description}`",
                inline=False
            )
        
        # 必要素材がある場合は※説明文を最下部に追加
        required_materials = item_data.get('required_materials')
        if required_materials and str(required_materials).strip():
            # 入手方法に応じてメッセージを変更
            acquisition_category = item_data.get('acquisition_category', '')
            if acquisition_category == 'モブ討伐':
                button_message = "*※ 下のボタンで入手モブ詳細を検索*"
            else:
                button_message = "*※ 下のボタンで必要素材詳細を検索*"
            
            embed.add_field(
                name="\u200b",  # 空白フィールド名
                value=button_message,
                inline=False
            )
    
    async def _add_material_details(self, embed: discord.Embed, item_data: Dict[str, Any]):
        """素材の詳細情報を追加"""
        # 入手方法
        acquisition_method = item_data.get('acquisition_method')
        if acquisition_method and str(acquisition_method).strip():
            method_list = [f"　• `{item.strip()}`" for item in str(acquisition_method).split(',') if item.strip()]
            # 1行目にゼロ幅スペースを挿入
            method_list[0] = "\u200B" + method_list[0]
            embed.add_field(
                name="入手方法:",
                value="\n".join(method_list[:5]),
                inline=False
            )
        
        # 利用カテゴリ（利用用途より上に移動）
        usage_category = item_data.get('usage_category')
        if usage_category and str(usage_category).strip():
            if ',' in str(usage_category):
                category_list = [f"　• `{cat.strip()}`" for cat in str(usage_category).split(',') if cat.strip()]
            else:
                category_list = [f"　• `{usage_category}`"]
            # 1行目にゼロ幅スペースを挿入
            category_list[0] = "\u200B" + category_list[0]
            embed.add_field(
                name="利用カテゴリ:",
                value="\n".join(category_list),
                inline=False
            )
        
        # 利用用途
        usage_purpose = item_data.get('usage_purpose')
        if usage_purpose and str(usage_purpose).strip():
            usage_list = [f"　• `{item.strip()}`" for item in str(usage_purpose).split(',') if item.strip()]
            # 1行目にゼロ幅スペースを挿入
            usage_list[0] = "\u200B" + usage_list[0]
            embed.add_field(
                name="利用用途:",
                value="\n".join(usage_list[:5]),
                inline=False
            )
        
        # 説明（旧：一言）
        description = item_data.get('description')
        if description and str(description).strip():
            embed.add_field(
                name="説明:",
                value=f"　`{description}`",
                inline=False
            )
        
        # 素材の場合は常に※説明文を追加
        embed.add_field(
            name="\u200b",  # 空白フィールド名
            value="*※ 下のボタンで素材詳細を検索*",
            inline=False
        )
    
    async def _add_gathering_details(self, embed: discord.Embed, item_data: Dict[str, Any]):
        """採集の詳細情報を追加"""
        # 入手素材
        obtained_materials = item_data.get('obtained_materials')
        if obtained_materials and str(obtained_materials).strip():
            material_list = [f"　• `{item.strip()}`" for item in str(obtained_materials).split(',') if item.strip()]
            # 1行目にゼロ幅スペースを挿入
            material_list[0] = "\u200B" + material_list[0]
            embed.add_field(
                name="入手素材:",
                value="\n".join(material_list[:10]),
                inline=False
            )
        
        # 必要ツール
        required_tools = item_data.get('required_tools')
        if required_tools and str(required_tools).strip():
            embed.add_field(
                name="必要ツールレベル:",
                value=f"\u200B　`{required_tools}`",
                inline=False
            )
        
        # 説明（旧：一言）
        description = item_data.get('description')
        if description and str(description).strip():
            embed.add_field(
                name="説明:",
                value=f"　`{description}`",
                inline=False
            )
    
    def _get_type_display_name(self, item_type: str) -> str:
        """アイテムタイプの表示名を取得"""
        type_names = {
            'equipments': '装備',
            'materials': '素材',
            'mobs': 'モンスター',
            'gatherings': '採集'
        }
        return type_names.get(item_type, item_type)
    
    def _get_field_mapping(self, item_type: str) -> Dict[str, str]:
        """アイテムタイプに応じたフィールドマッピングを取得"""
        mappings = {
            'equipments': {
                'common_name': '一般名称',
                'acquisition_category': '入手カテゴリ',
                'type': '種類',
                'required_materials': '必要素材',
                'required_level': '必要レベル',
                'item_effect': 'アイテム効果',
                'description': '一言'
            },
            'materials': {
                'common_name': '一般名称',
                'acquisition_category': '入手カテゴリ',
                'type': '種類',
                'required_materials': '必要素材',
                'required_level': '必要レベル',
                'item_effect': 'アイテム効果',
                'description': '一言'
            },
            'mobs': {
                'common_name': '一般名称',
                'area': '出没エリア',
                'area_detail': '出没エリア詳細',
                'required_level': '必要レベル',
                'drops': 'ドロップ品',
                'exp': 'EXP',
                'gold': 'Gold',
                'required_defense': '必要守備力',
                'description': '一言'
            },
            'gatherings': {
                'collection_method': '収集方法',
                'obtained_materials': '入手素材',
                'usage': '使用用途',
                'required_tools': '必要ツール',
                'description': '一言'
            }
        }
        return mappings.get(item_type, {})
    
    async def _format_field_value(self, field_name: str, value: str) -> str:
        """フィールド値をフォーマット（アイテム名のリンク化など）"""
        try:
            # アイテムリストが含まれるフィールド
            item_fields = ['required_materials', 'drops', 'obtained_materials']
            
            if field_name in item_fields:
                return self._format_item_list(value)
            
            return value
            
        except Exception as e:
            logger.warning(f"フィールド値フォーマットエラー: {e}")
            return value
    
    def _format_item_list(self, item_list: str) -> str:
        """アイテムリスト文字列をフォーマット（リンク化）"""
        try:
            if not item_list:
                return item_list
            
            # 「木の棒:8,トトの羽:4」形式をパース
            items = item_list.split(',')
            formatted_items = []
            
            for item in items:
                item = item.strip()
                if ':' in item:
                    name, quantity = item.split(':', 1)
                    name = name.strip()
                    quantity = quantity.strip()
                    # Discord Button形式でのリンクは後でViewで実装
                    formatted_items.append(f"**{name}**: {quantity}")
                else:
                    formatted_items.append(f"**{item}**")
            
            return '\n'.join(formatted_items)
            
        except Exception as e:
            logger.warning(f"アイテムリストフォーマットエラー: {e}")
            return item_list
    
    async def _is_valid_image_url(self, url: str) -> bool:
        """画像URLの有効性をチェック"""
        if not self.config['features']['image_validation']:
            return True
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.head(url, timeout=5) as response:
                    if response.status == 200:
                        content_type = response.headers.get('content-type', '').lower()
                        return content_type.startswith('image/')
            return False
            
        except Exception as e:
            logger.warning(f"画像URL検証エラー: {e}")
            return False
    
    async def create_search_results_embed(self, results: List[Dict[str, Any]], query: str, page: int = 0) -> Tuple[discord.Embed, discord.ui.View]:
        """検索結果一覧のEmbedとViewを作成"""
        try:
            page_size = self.config['features']['pagination_size']
            start_idx = page * page_size
            end_idx = start_idx + page_size
            page_results = results[start_idx:end_idx]
            
            embed = discord.Embed(
                title=f"**検索結果: {query}**",
                description=f"**{len(results)}件**の結果が見つかりました",
                color=discord.Color.blue()
            )
            
            # 箇条書き形式で一覧表示
            item_list = []
            for i, item in enumerate(page_results, start=start_idx + 1):
                formal_name = item.get('formal_name', 'Unknown')
                item_type = item.get('item_type', 'unknown')
                required_level = item.get('required_level', '')
                
                # アイテム情報を表示（一般名称は表示しない）
                item_info = f"• {i}. {formal_name} ({item_type})"
                
                # mobの場合は必要レベルも表示
                if item_type == 'mobs' and required_level:
                    try:
                        level_int = int(float(str(required_level).replace(',', '')))
                        item_info += f" - Lv. {level_int}"
                    except (ValueError, TypeError):
                        item_info += f" - Lv. {required_level}"
                
                item_list.append(item_info)
            
            if item_list:
                # 各アイテムにインデントを追加
                indented_items = [f"　{item}" for item in item_list]
                # 1行目にゼロ幅スペースを挿入
                indented_items[0] = "\u200B" + indented_items[0]
                embed.add_field(
                    name="検索結果:",
                    value="\n".join(indented_items),
                    inline=False
                )
            
            # ページ情報をフッターに表示
            total_pages = (len(results) - 1) // page_size + 1
            embed.set_footer(text=f"ページ {page + 1}/{total_pages}")
            
            # ページネーションViewを作成
            view = SearchResultsView(results, query, page, self)
            
            return embed, view
            
        except Exception as e:
            logger.error(f"検索結果Embed作成エラー: {e}")
            embed = discord.Embed(
                title="エラー",
                description="検索結果の表示中にエラーが発生しました",
                color=discord.Color.red()
            )
            return embed, None
    
    async def create_favorites_embed(self, favorites: List[Dict[str, Any]], user_id: str) -> Tuple[discord.Embed, discord.ui.View]:
        """お気に入り一覧のEmbedとViewを作成"""
        try:
            embed = discord.Embed(
                title="⭐ お気に入りアイテム",
                description=f"**{len(favorites)}件**のアイテムがお気に入りに登録されています",
                color=discord.Color.gold()
            )
            
            for i, fav in enumerate(favorites[:10], 1):  # 最大10件表示
                item_name = fav.get('item_name', 'Unknown')
                item_type = fav.get('item_type', 'unknown')
                created_at = fav.get('created_at', '')
                
                embed.add_field(
                    name=f"{i}. {item_name}",
                    value=f"{self.type_emojis.get(item_type, '❓')} {item_type}\n登録: {created_at[:10]}",
                    inline=True
                )
            
            view = FavoritesView(favorites, user_id, self)
            
            return embed, view
            
        except Exception as e:
            logger.error(f"お気に入りEmbed作成エラー: {e}")
            embed = discord.Embed(
                title="エラー",
                description="お気に入り表示中にエラーが発生しました",
                color=discord.Color.red()
            )
            return embed, None
    
    async def create_history_embed(self, history: List[Dict[str, Any]]) -> discord.Embed:
        """検索履歴のEmbedを作成"""
        try:
            embed = discord.Embed(
                title="📜 検索履歴",
                description=f"最近の検索履歴 (**{len(history)}件**)",
                color=discord.Color.purple()
            )
            
            for i, entry in enumerate(history[:10], 1):  # 最大10件表示
                query = entry.get('query', 'Unknown')
                result_count = entry.get('result_count', 0)
                searched_at = entry.get('searched_at', '')
                
                embed.add_field(
                    name=f"{i}. {query}",
                    value=f"結果: {result_count}件\n{searched_at[:16]}",
                    inline=True
                )
            
            return embed
            
        except Exception as e:
            logger.error(f"履歴Embed作成エラー: {e}")
            return discord.Embed(
                title="エラー",
                description="履歴表示中にエラーが発生しました",
                color=discord.Color.red()
            )
    
    async def create_stats_embed(self, stats_data: List[Dict[str, Any]], stats_type: str) -> discord.Embed:
        """統計情報のEmbedを作成"""
        try:
            if stats_type == 'search_ranking':
                embed = discord.Embed(
                    title="📊 検索ランキング",
                    description="人気のアイテム検索ランキング",
                    color=discord.Color.gold()
                )
                
                for i, item in enumerate(stats_data[:10], 1):
                    item_name = item.get('item_name', 'Unknown')
                    search_count = item.get('search_count', 0)
                    last_searched = item.get('last_searched', '')
                    
                    embed.add_field(
                        name=f"{i}. {item_name}",
                        value=f"検索回数: **{search_count}**回\n最終検索: {last_searched[:10]}",
                        inline=True
                    )
            
            return embed
            
        except Exception as e:
            logger.error(f"統計Embed作成エラー: {e}")
            return discord.Embed(
                title="エラー",
                description="統計表示中にエラーが発生しました",
                color=discord.Color.red()
            )

# Viewクラス定義
class ItemDetailView(discord.ui.View):
    def __init__(self, item_data: Dict[str, Any], user_id: str, embed_manager):
        super().__init__(timeout=600)  # 10分に延長
        self.item_data = item_data
        self.user_id = user_id
        self.embed_manager = embed_manager
        self.processing = False
        
        # アイテムタイプに応じてボタンを動的に追加
        self._add_dynamic_buttons()
    
    async def on_timeout(self):
        """タイムアウト時の処理"""
        try:
            # 全てのボタンを無効化
            for item in self.children:
                if hasattr(item, 'disabled'):
                    item.disabled = True
        except Exception as e:
            logger.warning(f"タイムアウト処理エラー: {e}")
    
    def _disable_all_buttons(self):
        """全てのボタンを無効化"""
        for item in self.children:
            if hasattr(item, 'disabled'):
                item.disabled = True
    
    def _enable_all_buttons(self):
        """全てのボタンを有効化"""
        for item in self.children:
            if hasattr(item, 'disabled'):
                item.disabled = False
    
    
    def _add_dynamic_buttons(self):
        """アイテムタイプに応じてボタンを追加"""
        item_type = self.item_data.get('item_type', '')
        acquisition_category = self.item_data.get('acquisition_category', '')
        
        if item_type == 'materials':
            # 素材: 利用先と入手元がある
            self.add_item(AcquisitionDetailsButton(item_type, acquisition_category))
            self.add_item(UsageDetailsButton(item_type))
        elif item_type == 'equipments':
            # 装備: 必要素材(入手元)がある
            self.add_item(AcquisitionDetailsButton(item_type, acquisition_category))
        elif item_type == 'mobs':
            # モブ: ドロップアイテム(利用先)がある
            self.add_item(UsageDetailsButton(item_type))
    
    async def _get_related_items(self):
        """関連アイテムを取得"""
        from search_engine import SearchEngine
        from database import DatabaseManager
        
        db = DatabaseManager()
        search_engine = SearchEngine(db, self.embed_manager.config)
        return await search_engine.search_related_items(self.item_data)


class AcquisitionDetailsButton(discord.ui.Button):
    def __init__(self, item_type='', acquisition_category=''):
        if item_type == 'equipments':
            if acquisition_category == 'モブ討伐':
                label = "入手モブ詳細"
            else:
                label = "必要素材詳細"
        else:
            label = "入手元詳細"
        super().__init__(label=label, style=discord.ButtonStyle.secondary)
    
    async def callback(self, interaction: discord.Interaction):
        view = self.view
        if view.processing:
            await interaction.response.send_message("⏳ 処理中です。しばらくお待ちください...", ephemeral=True)
            return
            
        view.processing = True
        view._disable_all_buttons()
        
        try:
            related_items = await view._get_related_items()
            
            embed = discord.Embed(
                title=f"{view.item_data['formal_name']} の入手元詳細",
                color=discord.Color.green()
            )
            
            options = []
            option_index = 0
            item_type = view.item_data.get('item_type', '')
            
            if item_type == 'materials':
                # 素材の入手元包括表示
                
                # 1. ドロップ元のmob表示
                mob_sources = [item for item in related_items.get('acquisition_sources', []) if item.get('relation_type') == 'drop_from_mob']
                if mob_sources:
                    field_items = []
                    for item in mob_sources[:5]:
                        # mobの場合はformal_nameがある
                        display_name = item.get('formal_name', '不明')
                        field_items.append(f"　• **{display_name}**")
                        options.append(discord.SelectOption(
                            label=display_name[:25],
                            value=f"source_{option_index}",
                            description="ドロップ元"
                        ))
                        option_index += 1
                    # 1行目にゼロ幅スペースを挿入
                    if field_items:
                        field_items[0] = "\u200B" + field_items[0]
                        embed.add_field(
                            name="**入手元 (討伐):**",
                            value="\n".join(field_items),
                            inline=False
                        )
                
                # 2. 採集場所の表示
                gathering_sources = [item for item in related_items.get('acquisition_sources', []) if item.get('relation_type') == 'gathering_location']
                if gathering_sources:
                    gathering_items = []
                    for location in gathering_sources[:5]:
                        location_name = location.get('location', '不明')
                        collection_method = location.get('collection_method', '')
                        display_text = f"**{location_name}**"
                        if collection_method:
                            display_text += f" ({collection_method})"
                        gathering_items.append(f"　• {display_text}")
                        options.append(discord.SelectOption(
                            label=f"{location_name} - {collection_method}"[:25],
                            value=f"gathering_{option_index}",
                            description="採集場所"
                        ))
                        option_index += 1
                    if gathering_items:
                        gathering_items[0] = "\u200B" + gathering_items[0]
                        embed.add_field(
                            name="**採集場所:**",
                            value="\n".join(gathering_items),
                            inline=False
                        )
                elif related_items.get('acquisition_info'):
                    # 採集場所テーブル未実装時のフォールバック
                    info = related_items['acquisition_info']
                    if info['category'] in ['採取', '採掘', '釣り']:
                        method_text = info.get('method', '')
                        location_text = info.get('location', '')
                        display_text = f"　**{info['category']}**"
                        if method_text:
                            display_text += f"\n　• 方法: `{method_text}`"
                        if location_text:
                            display_text += f"\n　• 場所: `{location_text}`"
                        embed.add_field(
                            name="**入手方法:**",
                            value=display_text,
                            inline=False
                        )
                
                # 3. NPC交換・購入の表示
                npc_sources = [item for item in related_items.get('acquisition_sources', []) if item.get('relation_type') == 'npc_source']
                if npc_sources:
                    npc_items = []
                    for npc in npc_sources[:5]:
                        npc_name = npc.get('name', '不明')
                        npc_location = npc.get('location', '')
                        business_type = npc.get('business_type', 'その他')
                        display_text = f"**{npc_name}**"
                        if npc_location:
                            display_text += f" ({npc_location})"
                        display_text += f" - {business_type}"
                        npc_items.append(f"　• {display_text}")
                        options.append(discord.SelectOption(
                            label=f"{npc_name} ({business_type})"[:25],
                            value=f"npc_{option_index}",
                            description=npc_location[:50] if npc_location else "NPC"
                        ))
                        option_index += 1
                    if npc_items:
                        npc_items[0] = "\u200B" + npc_items[0]
                        embed.add_field(
                            name="**NPC交換・購入:**",
                            value="\n".join(npc_items),
                            inline=False
                        )
                
                # 4. その他の入手方法
                if related_items.get('acquisition_info') and not related_items.get('gathering_locations'):
                    info = related_items['acquisition_info']
                    if info['category'] not in ['採取', '採掘', '釣り', 'NPC', 'ギルドクエスト']:
                        method_text = info.get('method', info['category'])
                        location_text = info.get('location', '')
                        display_text = f"　**{method_text}**"
                        if location_text:
                            display_text += f"\n　• 場所: `{location_text}`"
                        embed.add_field(
                            name="**その他の入手方法:**",
                            value=display_text,
                            inline=False
                        )
            
            elif item_type == 'equipments':
                # 装備の必要素材と入手元
                if related_items.get('materials'):
                    material_list = []
                    for item in related_items['materials'][:5]:
                        quantity = item.get('required_quantity', '1')
                        material_list.append(f"　• `{item['formal_name']} x{quantity}`")
                        options.append(discord.SelectOption(
                            label=f"{item['formal_name']} x{quantity}",
                            value=f"material_{option_index}",
                            description="必要素材"
                        ))
                        option_index += 1
                    # 1行目にゼロ幅スペースを挿入
                    material_list[0] = "\u200B" + material_list[0]
                    embed.add_field(
                        name="必要素材:",
                        value="\n".join(material_list),
                        inline=False
                    )
                
                # 装備の入手元（mob/gathering/npc）
                acquisition_sources = related_items.get('acquisition_sources', [])
                if acquisition_sources:
                    # タイプ別に分類
                    mob_sources = [s for s in acquisition_sources if s.get('relation_type') == 'drop_from_mob']
                    gathering_sources = [s for s in acquisition_sources if s.get('relation_type') == 'gathering_location']
                    npc_sources = [s for s in acquisition_sources if s.get('relation_type') == 'npc_source']
                    
                    # Mobドロップ
                    if mob_sources:
                        drop_list = []
                        for item in mob_sources[:5]:
                            display_name = item.get('formal_name', '不明')
                            drop_list.append(f"　• `{display_name}`")
                            options.append(discord.SelectOption(
                                label=display_name[:25],
                                value=f"source_{option_index}",
                                description="ドロップ元"
                            ))
                            option_index += 1
                        if drop_list:
                            drop_list[0] = "\u200B" + drop_list[0]
                            embed.add_field(
                                name="入手元 (討伐):",
                                value="\n".join(drop_list),
                                inline=False
                            )
                    
                    # 採集場所
                    if gathering_sources:
                        gathering_list = []
                        for location in gathering_sources[:5]:
                            location_name = location.get('location', '不明')
                            method = location.get('collection_method', '')
                            display_text = f"`{location_name}`"
                            if method:
                                display_text += f" - {method}"
                            gathering_list.append(f"　• {display_text}")
                            options.append(discord.SelectOption(
                                label=f"{location_name} - {method}"[:25],
                                value=f"gathering_{option_index}",
                                description="採集場所"
                            ))
                            option_index += 1
                        if gathering_list:
                            gathering_list[0] = "\u200B" + gathering_list[0]
                            embed.add_field(
                                name="採集場所:",
                                value="\n".join(gathering_list),
                                inline=False
                            )
                    
                    # NPC
                    if npc_sources:
                        npc_list = []
                        for npc in npc_sources[:5]:
                            npc_name = npc.get('name', '不明')
                            npc_location = npc.get('location', '')
                            business_type = npc.get('business_type', '')
                            display_text = f"`{npc_name}`"
                            if npc_location:
                                display_text += f" @ {npc_location}"
                            if business_type:
                                display_text += f" ({business_type})"
                            npc_list.append(f"　• {display_text}")
                            options.append(discord.SelectOption(
                                label=f"{npc_name} ({business_type})"[:25],
                                value=f"npc_{option_index}",
                                description=npc_location[:50] if npc_location else "NPC"
                            ))
                            option_index += 1
                        if npc_list:
                            npc_list[0] = "\u200B" + npc_list[0]
                            embed.add_field(
                                name="NPC:",
                                value="\n".join(npc_list),
                                inline=False
                            )
            
            if not options and not related_items.get('acquisition_info'):
                embed.description = "入手元情報が見つかりませんでした"
                await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                if options:
                    # アイテム選択用のViewを作成 - optionsとアイテムを直接マッピング
                    item_list = []
                    
                    # materialsの場合
                    if item_type == 'materials':
                        # mob sources
                        mob_sources = [s for s in related_items.get('acquisition_sources', []) if s.get('relation_type') == 'drop_from_mob']
                        item_list.extend(mob_sources)
                        
                        # gathering sources
                        gathering_sources = [s for s in related_items.get('acquisition_sources', []) if s.get('relation_type') == 'gathering_location']
                        item_list.extend(gathering_sources)
                        
                        # npc sources
                        npc_sources = [s for s in related_items.get('acquisition_sources', []) if s.get('relation_type') == 'npc_source']
                        item_list.extend(npc_sources)
                    
                    # equipmentsの場合
                    elif item_type == 'equipments':
                        # materials
                        item_list.extend(related_items.get('materials', []))
                        
                        # acquisition sources
                        acquisition_sources = related_items.get('acquisition_sources', [])
                        mob_sources = [s for s in acquisition_sources if s.get('relation_type') == 'drop_from_mob']
                        gathering_sources = [s for s in acquisition_sources if s.get('relation_type') == 'gathering_location']
                        npc_sources = [s for s in acquisition_sources if s.get('relation_type') == 'npc_source']
                        
                        item_list.extend(mob_sources)
                        item_list.extend(gathering_sources)
                        item_list.extend(npc_sources)
                    
                    detailed_view = NewRelatedItemsView(related_items, view.embed_manager, options, item_list)
                    embed.set_footer(text="アイテムを選択して詳細を表示")
                    await interaction.response.send_message(embed=embed, view=detailed_view, ephemeral=True)
                else:
                    await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"入手元詳細エラー: {e}")
            await interaction.response.send_message("❌ 入手元詳細取得中にエラーが発生しました", ephemeral=True)
        finally:
            view.processing = False
            view._enable_all_buttons()


class UsageDetailsButton(discord.ui.Button):
    def __init__(self, item_type=''):
        if item_type == 'mobs':
            label = "ドロップ詳細"
        else:
            label = "利用先詳細"
        super().__init__(label=label, style=discord.ButtonStyle.secondary)
    
    async def callback(self, interaction: discord.Interaction):
        view = self.view
        if view.processing:
            await interaction.response.send_message("⏳ 処理中です。しばらくお待ちください...", ephemeral=True)
            return
            
        view.processing = True
        view._disable_all_buttons()
        
        try:
            related_items = await view._get_related_items()
            
            embed = discord.Embed(
                title=f"{view.item_data['formal_name']} の利用先詳細",
                color=discord.Color.orange()
            )
            
            options = []
            option_index = 0
            item_type = view.item_data.get('item_type', '')
            
            if item_type == 'materials':
                # 素材の利用先
                if related_items.get('usage_destinations'):
                    usage_list = []
                    for item in related_items['usage_destinations'][:5]:
                        usage_detail = item.get('relation_detail', '')
                        if usage_detail and '必要数' in usage_detail:
                            usage_list.append(f"　• `{item['formal_name']}` ({usage_detail})")
                        else:
                            usage_list.append(f"　• `{item['formal_name']}`")
                        options.append(discord.SelectOption(
                            label=item['formal_name'][:25],
                            value=f"usage_{option_index}",
                            description=f"{usage_detail if usage_detail else '必要素材'}"
                        ))
                        option_index += 1
                    # 1行目にゼロ幅スペースを挿入
                    usage_list[0] = "\u200B" + usage_list[0]
                    embed.add_field(
                        name="利用先:",
                        value="\n".join(usage_list),
                        inline=False
                    )
            
            elif item_type == 'mobs':
                # モブのドロップアイテム
                if related_items.get('dropped_items'):
                    drop_list = []
                    for item in related_items['dropped_items'][:5]:
                        drop_list.append(f"　• `{item['formal_name']}`")
                        options.append(discord.SelectOption(
                            label=item['formal_name'][:25],
                            value=f"drop_{option_index}",
                            description="ドロップアイテム"
                        ))
                        option_index += 1
                    # 1行目にゼロ幅スペースを挿入
                    drop_list[0] = "\u200B" + drop_list[0]
                    embed.add_field(
                        name="ドロップアイテム:",
                        value="\n".join(drop_list),
                        inline=False
                    )
            
            if not options:
                embed.description = "利用先情報が見つかりませんでした"
                await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                # アイテム選択用のViewを作成 - optionsとアイテムを直接マッピング
                item_list = []
                
                if item_type == 'materials':
                    item_list.extend(related_items.get('usage_destinations', []))
                elif item_type == 'mobs':
                    item_list.extend(related_items.get('dropped_items', []))
                
                detailed_view = NewRelatedItemsView(related_items, view.embed_manager, options, item_list)
                embed.set_footer(text="アイテムを選択して詳細を表示")
                await interaction.response.send_message(embed=embed, view=detailed_view, ephemeral=True)
            
        except Exception as e:
            logger.error(f"利用先詳細エラー: {e}")
            await interaction.response.send_message("❌ 利用先詳細取得中にエラーが発生しました", ephemeral=True)
        finally:
            view.processing = False
            view._enable_all_buttons()

    # 旧関連アイテムボタンのメソッドを削除
    async def search_related_items_old(self, interaction: discord.Interaction, button: discord.ui.Button):
        """旧関連アイテム検索メソッド（削除済み）"""
        pass
    

class SearchResultsView(discord.ui.View):
    def __init__(self, results: List[Dict[str, Any]], query: str, current_page: int, embed_manager):
        super().__init__(timeout=600)  # 10分に延長
        self.results = results
        self.query = query
        self.current_page = current_page
        self.embed_manager = embed_manager
        self.page_size = embed_manager.config['features']['pagination_size']
        
        # ページネーションボタンの有効/無効を設定
        total_pages = (len(results) - 1) // self.page_size + 1
        self.prev_button.disabled = current_page == 0
        self.next_button.disabled = current_page >= total_pages - 1
        
        # アイテム選択用セレクトメニューを追加
        self._add_item_select_menu()
    
    def _add_item_select_menu(self):
        """現在のページのアイテム選択メニューを追加"""
        start_idx = self.current_page * self.page_size
        end_idx = start_idx + self.page_size
        page_results = self.results[start_idx:end_idx]
        
        if len(page_results) > 0:
            options = []
            for i, item in enumerate(page_results):
                formal_name = item.get('formal_name', 'Unknown')
                item_type = item.get('item_type', 'unknown')
                emoji = self.embed_manager.type_emojis.get(item_type, '❓')
                item_number = start_idx + i + 1
                
                # 選択肢を作成（番号付き）
                option = discord.SelectOption(
                    label=f"{item_number}. {formal_name}"[:100],  # Discord制限により100文字まで
                    description=f"{emoji} {item_type}",
                    value=str(start_idx + i)
                )
                options.append(option)
            
            # セレクトメニューを追加
            select_menu = ItemSelectMenu(self.results, self.embed_manager, options)
            self.add_item(select_menu)
    
    @discord.ui.button(label="◀️ 前", style=discord.ButtonStyle.secondary)
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        new_page = max(0, self.current_page - 1)
        embed, view = await self.embed_manager.create_search_results_embed(
            self.results, self.query, new_page
        )
        await interaction.response.edit_message(embed=embed, view=view)
    
    @discord.ui.button(label="▶️ 次", style=discord.ButtonStyle.secondary)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        total_pages = (len(self.results) - 1) // self.page_size + 1
        new_page = min(total_pages - 1, self.current_page + 1)
        embed, view = await self.embed_manager.create_search_results_embed(
            self.results, self.query, new_page
        )
        await interaction.response.edit_message(embed=embed, view=view)

class ItemSelectMenu(discord.ui.Select):
    def __init__(self, results: List[Dict[str, Any]], embed_manager, options: List[discord.SelectOption]):
        super().__init__(
            placeholder="アイテムを選択して詳細を表示...",
            min_values=1,
            max_values=1,
            options=options
        )
        self.results = results
        self.embed_manager = embed_manager
    
    async def callback(self, interaction: discord.Interaction):
        try:
            # 選択されたアイテムのインデックスを取得
            selected_index = int(self.values[0])
            selected_item = self.results[selected_index]
            
            # アイテム詳細のEmbedとViewを作成
            embed, view = await self.embed_manager.create_item_detail_embed(
                selected_item, str(interaction.user.id)
            )
            
            # 新しいメッセージとして送信
            await interaction.response.send_message(embed=embed, view=view)
            
        except Exception as e:
            logger.error(f"アイテム選択エラー: {e}")
            await interaction.response.send_message("❌ アイテム詳細の取得中にエラーが発生しました", ephemeral=True)

class RelatedItemsView(discord.ui.View):
    def __init__(self, related_items: List[Dict[str, Any]], embed_manager):
        super().__init__(timeout=300)
        self.related_items = related_items
        self.embed_manager = embed_manager
        
        # 関連アイテム選択用セレクトメニューを追加
        if len(related_items) > 0:
            self._add_related_select_menu()
    
    def _add_related_select_menu(self):
        """関連アイテム選択メニューを追加"""
        options = []
        for i, item in enumerate(self.related_items[:25]):  # Discord制限により最大25件
            formal_name = item.get('formal_name', 'Unknown')
            item_type = item.get('item_type', 'unknown')
            emoji = self.embed_manager.type_emojis.get(item_type, '❓')
            
            option = discord.SelectOption(
                label=formal_name[:100],
                description=f"{emoji} {item_type}",
                value=str(i)
            )
            options.append(option)
        
        if options:
            select_menu = RelatedItemSelectMenu(self.related_items, self.embed_manager, options)
            self.add_item(select_menu)

class RelatedItemSelectMenu(discord.ui.Select):
    def __init__(self, related_items: List[Dict[str, Any]], embed_manager, options: List[discord.SelectOption]):
        super().__init__(
            placeholder="関連アイテムを選択して詳細を表示...",
            min_values=1,
            max_values=1,
            options=options
        )
        self.related_items = related_items
        self.embed_manager = embed_manager
    
    async def callback(self, interaction: discord.Interaction):
        try:
            selected_index = int(self.values[0])
            selected_item = self.related_items[selected_index]
            
            embed, view = await self.embed_manager.create_item_detail_embed(
                selected_item, str(interaction.user.id)
            )
            
            await interaction.response.send_message(embed=embed, view=view)
            
        except Exception as e:
            logger.error(f"関連アイテム選択エラー: {e}")
            await interaction.response.send_message("❌ アイテム詳細の取得中にエラーが発生しました", ephemeral=True)

class FavoritesView(discord.ui.View):
    def __init__(self, favorites: List[Dict[str, Any]], user_id: str, embed_manager):
        super().__init__(timeout=300)
        self.favorites = favorites
        self.user_id = user_id
        self.embed_manager = embed_manager
    
    @discord.ui.button(label="🗑️ 削除", style=discord.ButtonStyle.danger)
    async def remove_favorite(self, interaction: discord.Interaction, button: discord.ui.Button):
        # お気に入り削除用のセレクトメニューを表示
        if not self.favorites:
            await interaction.response.send_message("削除するお気に入りがありません", ephemeral=True)
            return
        
        # 簡単な実装：最初のお気に入りを削除
        try:
            from database import DatabaseManager
            db = DatabaseManager()
            
            first_fav = self.favorites[0]
            success = await db.remove_favorite(
                str(interaction.user.id),
                first_fav['item_name'],
                first_fav['item_type']
            )
            
            if success:
                await interaction.response.send_message("🗑️ お気に入りから削除しました", ephemeral=True)
            else:
                await interaction.response.send_message("❌ 削除に失敗しました", ephemeral=True)
                
        except Exception as e:
            logger.error(f"お気に入り削除エラー: {e}")
            await interaction.response.send_message("❌ 削除中にエラーが発生しました", ephemeral=True)


class RelatedItemSearchView(discord.ui.View):
    def __init__(self, options: List[discord.SelectOption], embed_manager):
        super().__init__(timeout=180)  # 3分でタイムアウト
        self.embed_manager = embed_manager
        
        # セレクトメニューを追加
        if options:
            select = RelatedItemSelect(options, embed_manager)
            self.add_item(select)
    
    async def on_timeout(self):
        """タイムアウト時の処理"""
        for item in self.children:
            if hasattr(item, 'disabled'):
                item.disabled = True


class RelatedItemSelect(discord.ui.Select):
    def __init__(self, options: List[discord.SelectOption], embed_manager):
        super().__init__(
            placeholder="検索したいアイテムを選択してください...",
            min_values=1,
            max_values=1,
            options=options
        )
        self.embed_manager = embed_manager
    
    async def callback(self, interaction: discord.Interaction):
        """選択されたアイテムを検索"""
        try:
            selected_item_name = self.values[0]
            
            # 検索エンジンを使用してアイテムを検索
            from search_engine import SearchEngine
            from database import DatabaseManager
            from main import ItemReferenceBot
            
            # Bot設定を取得
            import json
            with open('config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            db_manager = DatabaseManager()
            search_engine = SearchEngine(db_manager, config)
            
            # アイテム検索実行
            search_results = await search_engine.search(selected_item_name)
            
            if not search_results:
                await interaction.response.send_message(
                    f"🔍 「{selected_item_name}」に一致するアイテムが見つかりませんでした",
                    ephemeral=True
                )
                return
            
            if len(search_results) == 1:
                # 単一結果の場合は詳細表示
                embed, view = await self.embed_manager.create_item_detail_embed(
                    search_results[0], str(interaction.user.id)
                )
                await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
            else:
                # 複数結果の場合はリスト表示
                embed, view = await self.embed_manager.create_search_results_embed(
                    search_results, selected_item_name, page=0
                )
                await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
                
        except Exception as e:
            logger.error(f"関連アイテム検索コールバックエラー: {e}")
            await interaction.response.send_message(
                "❌ アイテム検索中にエラーが発生しました", 
                ephemeral=True
            )


class NewRelatedItemsView(discord.ui.View):
    def __init__(self, related_items: Dict[str, List[Dict[str, Any]]], embed_manager, options: List[discord.SelectOption], item_list: List[Dict[str, Any]] = None):
        super().__init__(timeout=300)
        self.related_items = related_items
        self.embed_manager = embed_manager
        self.all_items = []
        self.item_mapping = {}  # valueからアイテムへのマッピング
        
        # item_listが提供されている場合は、それを使用してマッピング
        if item_list and len(item_list) == len(options):
            for i, (option, item) in enumerate(zip(options, item_list)):
                self.item_mapping[option.value] = item
        else:
            # フォールバック: 従来の方法
            logger.warning(f"Item list length mismatch: options={len(options)}, items={len(item_list) if item_list else 0}")
        
        # セレクトメニューを追加
        if options:
            select = NewRelatedItemSelect(self.item_mapping, embed_manager, options)
            self.add_item(select)


class NewRelatedItemSelect(discord.ui.Select):
    def __init__(self, item_mapping: Dict[str, Dict[str, Any]], embed_manager, options: List[discord.SelectOption]):
        super().__init__(
            placeholder="詳細を表示するアイテムを選択...",
            min_values=1,
            max_values=1,
            options=options
        )
        self.item_mapping = item_mapping
        self.embed_manager = embed_manager
    
    async def callback(self, interaction: discord.Interaction):
        try:
            selected_value = self.values[0]
            
            # マッピングからアイテムを取得
            if selected_value in self.item_mapping:
                selected_item = self.item_mapping[selected_value]
                
                # gathering/npcの場合は簡易表示
                if selected_value.startswith('gathering_') or selected_value.startswith('npc_'):
                    # gathering/npcは詳細表示ではなく情報表示
                    embed = discord.Embed(
                        title=f"詳細情報",
                        color=discord.Color.blue()
                    )
                    
                    if selected_value.startswith('gathering_'):
                        # 採集場所の詳細
                        location = selected_item.get('location', '不明')
                        method = selected_item.get('collection_method', '')
                        materials = selected_item.get('obtained_materials', '')
                        tools = selected_item.get('required_tools', '')
                        desc = selected_item.get('description', '')
                        
                        embed.add_field(name="採集場所", value=f"`{location}`", inline=False)
                        embed.add_field(name="採集方法", value=f"`{method}`", inline=False)
                        if tools:
                            embed.add_field(name="必要ツール", value=f"`{tools}`", inline=False)
                        if materials:
                            mat_list = [f"• {m.strip()}" for m in materials.split(',')]
                            embed.add_field(name="入手可能素材", value="\n".join(mat_list[:10]), inline=False)
                        if desc:
                            embed.add_field(name="備考", value=f"`{desc}`", inline=False)
                    
                    elif selected_value.startswith('npc_'):
                        # NPCの詳細
                        name = selected_item.get('name', '不明')
                        location = selected_item.get('location', '')
                        business_type = selected_item.get('business_type', '')
                        items = selected_item.get('obtainable_items', '')
                        materials = selected_item.get('required_materials', '')
                        desc = selected_item.get('description', '')
                        
                        embed.add_field(name="NPC名", value=f"`{name}`", inline=False)
                        embed.add_field(name="場所", value=f"`{location}`", inline=False)
                        embed.add_field(name="業務", value=f"`{business_type}`", inline=False)
                        if items:
                            item_list = [f"• {i.strip()}" for i in items.split(',')]
                            embed.add_field(name="取扱アイテム", value="\n".join(item_list[:10]), inline=False)
                        if materials and business_type in ['購入', '交換']:
                            mat_list = [f"• {m.strip()}" for m in materials.split(',')]
                            label = "価格" if business_type == '購入' else "必要素材"
                            embed.add_field(name=label, value="\n".join(mat_list[:10]), inline=False)
                        if desc:
                            embed.add_field(name="備考", value=f"`{desc}`", inline=False)
                    
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                else:
                    # 通常のアイテム詳細表示
                    embed, view = await self.embed_manager.create_item_detail_embed(
                        selected_item, str(interaction.user.id)
                    )
                    
                    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
            else:
                await interaction.response.send_message("❌ 選択されたアイテムが見つかりません", ephemeral=True)
                
        except Exception as e:
            logger.error(f"関連アイテム選択エラー: {e}")
            await interaction.response.send_message("❌ アイテム詳細の取得中にエラーが発生しました", ephemeral=True)
