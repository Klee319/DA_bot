import discord
from discord.ext import commands
import logging
import aiohttp
import asyncio
import aiosqlite
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
            
            # NPCの場合は取引内容のプルダウンを追加
            if item_type == 'npcs':
                await self._add_npc_dropdown_to_view(view, item_data)
            # モブの場合はドロップアイテムのプルダウンを追加
            elif item_type == 'mobs':
                await self._add_mob_dropdown_to_view(view, item_data)
            # 装備の場合、必要素材がある場合はプルダウンを追加
            elif item_type == 'equipments':
                required_materials = item_data.get('required_materials')
                if required_materials and str(required_materials).strip():
                    await self._add_equipment_dropdown_to_view(view, item_data)
            
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
        elif item_type == 'npcs':
            # NPCの場合
            location = item_data.get('location')
            business_type = item_data.get('business_type')
            if location:
                embed.add_field(
                    name="場所:",
                    value=f"\u200B　`{location}`",
                    inline=False
                )
            if business_type:
                embed.add_field(
                    name="業種:",
                    value=f"\u200B　`{business_type}`",
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
        elif item_type == 'npcs':
            await self._add_npc_details(embed, item_data)
    
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
        
        # 効果（紋章系は特別な表示形式）
        item_effect = item_data.get('item_effect')
        item_type_value = item_data.get('type', '')
        if item_effect and str(item_effect).strip():
            # 紋章系の場合は改行を保持して箇条書き形式で表示
            if '紋章' in str(item_type_value):
                # 改行で分割して処理
                effect_lines = str(item_effect).strip().split('\n')
                formatted_effects = []
                level_info = None
                
                for line in effect_lines:
                    line = line.strip()
                    if line:
                        if 'レベル:' in line or 'Lv.' in line:
                            # レベル情報は別途保存
                            level_info = line
                        else:
                            # 効果項目は箇条書きに
                            if not line.startswith('・'):
                                line = f"・{line}"
                            formatted_effects.append(f"　{line}")
                
                # 効果セクション
                if formatted_effects:
                    # 1行目にゼロ幅スペースを挿入
                    formatted_effects[0] = "\u200B" + formatted_effects[0]
                    embed.add_field(
                        name="効果:",
                        value="\n".join(formatted_effects),
                        inline=False
                    )
                
                # 使用可能レベルセクション
                if level_info:
                    embed.add_field(
                        name="使用可能レベル:",
                        value=f"\u200B　`{level_info.replace('使用可能レベル:', '').strip()}`",
                        inline=False
                    )
            else:
                # 通常の装備の場合
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
                button_message = "※下記から必要素材詳細を確認"
            
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
    
    async def _add_npc_details(self, embed: discord.Embed, item_data: Dict[str, Any]):
        """NPCの詳細情報を追加"""
        try:
            from npc_parser import NPCExchangeParser
            
            business_type = item_data.get('business_type', '')
            obtainable_items = item_data.get('obtainable_items', '')
            required_materials = item_data.get('required_materials', '')
            exp_str = item_data.get('exp', '')
            gold_str = item_data.get('gold', '')
            
            # 交換パターンをパース
            exchanges = NPCExchangeParser.parse_exchange_items(
                obtainable_items, required_materials, exp_str, gold_str
            )
            
            if exchanges and any(ex.get('obtainable_item') or ex.get('required_materials') for ex in exchanges):
                # 交換内容のリストを作成
                exchange_list = []
                
                for i, exchange in enumerate(exchanges):
                    obtainable = exchange.get('obtainable_item') or ''
                    required = exchange.get('required_materials') or ''
                    obtainable = obtainable.strip()
                    required = required.strip()
                    exp = exchange.get('exp')
                    gold = exchange.get('gold')
                    
                    if not obtainable and not required:
                        continue
                    
                    if business_type == 'クエスト':
                        # クエストの場合は受注内容として表示（EXP/Gold表記は除外）
                        if required:
                            exchange_list.append(f"{required}")
                    else:
                        # 購入・交換の場合は販売商品として表示（入手アイテムのみ）
                        if obtainable:
                            # アイテム名:数量の形式をアイテム名×数量に変換
                            if ':' in obtainable:
                                item_name, quantity = obtainable.split(':', 1)
                                exchange_list.append(f"{item_name.strip()}×{quantity.strip()}")
                            else:
                                exchange_list.append(f"{obtainable}")
                
                if exchange_list:
                    # フィールド名を業種に応じて設定
                    if business_type == 'クエスト':
                        field_name = "受注内容:"
                    else:
                        field_name = "入手アイテム:"
                    
                    # 各行をコードブロックで表示
                    formatted_list = []
                    for i, item in enumerate(exchange_list[:10]):  # 最大10件表示
                        if i == 0:
                            formatted_list.append(f"\u200B　• `{item}`")
                        else:
                            formatted_list.append(f"　• `{item}`")
                    embed.add_field(
                        name=field_name,
                        value="\n".join(formatted_list),
                        inline=False
                    )
                    
                    # 複数の交換パターンがある場合はフッターで示す
                    if len(exchange_list) > 10:
                        embed.set_footer(text=f"※他にも{len(exchange_list) - 10}件の取引があります。プルダウンメニューから確認できます。")
                    
                    # 取引詳細の確認方法を追加
                    embed.add_field(
                        name="\u200b",  # 空白フィールド名
                        value="※下記から取引詳細を確認",
                        inline=False
                    )
        
        except Exception as e:
            logger.error(f"NPC詳細情報追加エラー: {e}")
            # エラー時はシンプルな表示にフォールバック
            business_type = item_data.get('business_type', '')
            if business_type == 'クエスト':
                required_materials = item_data.get('required_materials', '')
                if required_materials:
                    # カンマ区切りを箇条書きに変換
                    items = [item.strip() for item in required_materials.split(',') if item.strip()]
                    if items:
                        formatted_items = []
                        for i, item in enumerate(items[:10]):
                            if i == 0:
                                formatted_items.append(f"\u200B　• `{item}`")
                            else:
                                formatted_items.append(f"　• `{item}`")
                        embed.add_field(
                            name="受注内容:",
                            value="\n".join(formatted_items),
                            inline=False
                        )
            else:
                obtainable_items = item_data.get('obtainable_items', '')
                if obtainable_items:
                    # カンマ区切りを箇条書きに変換
                    items = [item.strip() for item in obtainable_items.split(',') if item.strip()]
                    if items:
                        # アイテム名:数量の形式をアイテム名×数量に変換
                        formatted_items = []
                        for i, item in enumerate(items[:10]):
                            if ':' in item:
                                item_name, quantity = item.split(':', 1)
                                if i == 0:
                                    formatted_items.append(f"\u200B　• `{item_name.strip()}×{quantity.strip()}`")
                                else:
                                    formatted_items.append(f"　• `{item_name.strip()}×{quantity.strip()}`")
                            else:
                                if i == 0:
                                    formatted_items.append(f"\u200B　• `{item}`")
                                else:
                                    formatted_items.append(f"　• `{item}`")
                        embed.add_field(
                            name="入手アイテム:" if business_type != 'クエスト' else "受注内容:",
                            value="\n".join(formatted_items),
                            inline=False
                        )
                    else:
                        embed.add_field(
                            name="入手アイテム:" if business_type != 'クエスト' else "受注内容:",
                            value=f"\u200B　`{obtainable_items}`",
                            inline=False
                        )
                
                # 取引詳細の確認方法を追加（エラー時も表示）
                embed.add_field(
                    name="\u200b",  # 空白フィールド名
                    value="※下記から取引詳細を確認",
                    inline=False
                )
    
    async def _add_npc_dropdown_to_view(self, view: discord.ui.View, item_data: Dict[str, Any]):
        """取引詳細ボタンの代わりにプルダウンを追加"""
        try:
            from npc_parser import NPCExchangeParser
            
            business_type = item_data.get('business_type', '')
            obtainable_items = item_data.get('obtainable_items', '')
            required_materials = item_data.get('required_materials', '')
            exp_str = item_data.get('exp', '')
            gold_str = item_data.get('gold', '')
            
            # 交換パターンをパース
            exchanges = NPCExchangeParser.parse_exchange_items(
                obtainable_items, required_materials, exp_str, gold_str
            )
            
            if exchanges and any(ex.get('obtainable_item') or ex.get('required_materials') for ex in exchanges):
                # プルダウンの選択肢を作成
                select_options = []
                exchange_data = []
                
                for i, exchange in enumerate(exchanges[:25]):  # Discordの制限で最大25件
                    obtainable = exchange.get('obtainable_item', '').strip()
                    required = exchange.get('required_materials', '').strip()
                    exp = exchange.get('exp')
                    gold = exchange.get('gold')
                    
                    if not obtainable and not required:
                        continue
                    
                    # 選択肢のラベルを作成
                    if business_type == 'クエスト':
                        label = required if required else "クエスト"
                        description = "受注内容"
                    else:
                        label = obtainable if obtainable else required
                        if business_type == '購入' and required:
                            description = f"{required} で購入"
                        elif business_type == '交換' and required:
                            description = f"{required} と交換"
                        else:
                            description = business_type
                    
                    # アイテム名:数量の形式をアイテム名×数量に変換
                    if ':' in label:
                        item_name, quantity = label.split(':', 1)
                        label = f"{item_name.strip()}×{quantity.strip()}"
                    
                    # 説明が長すぎる場合は省略
                    if len(description) > 50:
                        description = description[:47] + "..."
                    
                    select_options.append(discord.SelectOption(
                        label=label[:100],  # ラベルの文字数制限
                        value=f"npc_exchange_{i}",
                        description=description
                    ))
                    
                    # データを保存
                    exchange_data.append(exchange)
                
                # 選択肢がある場合のみプルダウンを追加
                if select_options:
                    select = NPCExchangeSelect(select_options, exchange_data, item_data, self)
                    view.add_item(select)
        
        except Exception as e:
            logger.error(f"NPCプルダウン追加エラー: {e}")
    
    async def _add_mob_dropdown_to_view(self, view: discord.ui.View, item_data: Dict[str, Any]):
        """ドロップ詳細ボタンの代わりにプルダウンを追加"""
        try:
            # 関連アイテムを取得
            from search_engine import SearchEngine
            from database import DatabaseManager
            
            db = DatabaseManager()
            search_engine = SearchEngine(db, self.config)
            related_items = await search_engine.search_related_items(item_data)
            
            # ドロップアイテムを取得
            dropped_items = related_items.get('dropped_items', [])
            
            if dropped_items:
                # プルダウンの選択肢を作成
                select_options = []
                
                for i, item in enumerate(dropped_items[:25]):  # Discordの制限で最大25件
                    item_name = item.get('formal_name', 'Unknown')
                    item_type = item.get('item_type', '')
                    
                    # アイテムタイプの表示名
                    type_display = {
                        'equipments': '装備',
                        'materials': '素材'
                    }.get(item_type, item_type)
                    
                    select_options.append(discord.SelectOption(
                        label=item_name[:100],  # ラベルの文字数制限
                        value=f"drop_{i}",
                        description=f"ドロップアイテム ({type_display})"
                    ))
                
                # 選択肢がある場合のみプルダウンを追加
                if select_options:
                    select = MobDropSelect(select_options, dropped_items, self)
                    view.add_item(select)
        
        except Exception as e:
            logger.error(f"モブプルダウン追加エラー: {e}")
    
    async def _add_equipment_dropdown_to_view(self, view: discord.ui.View, item_data: Dict[str, Any]):
        """必要素材プルダウンを追加"""
        try:
            required_materials = item_data.get('required_materials', '')
            
            if required_materials:
                # 必要素材をパース
                material_items = [item.strip() for item in str(required_materials).split(',') if item.strip()]
                
                if material_items:
                    # プルダウンの選択肢を作成
                    select_options = []
                    materials_data = []
                    
                    for i, material in enumerate(material_items[:25]):  # Discordの制限で最大25件
                        # :を×に置換
                        if ':' in material:
                            item_name, quantity = material.split(':', 1)
                            display_name = f"{item_name.strip()}×{quantity.strip()}"
                            material_name = item_name.strip()
                        else:
                            display_name = material
                            material_name = material
                        
                        select_options.append(discord.SelectOption(
                            label=display_name[:100],  # ラベルの文字数制限
                            value=f"material_{i}",
                            description="必要素材"
                        ))
                        
                        # 素材名のみを保存（検索用）
                        materials_data.append(material_name)
                    
                    # 選択肢がある場合のみプルダウンを追加
                    if select_options:
                        select = EquipmentMaterialSelect(select_options, materials_data, self)
                        view.add_item(select)
        
        except Exception as e:
            logger.error(f"装備プルダウン追加エラー: {e}")
    
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
            
            # 同名NPCの検出
            npc_names = {}
            for item in results:
                if item.get('item_type') == 'npcs':
                    name = item.get('formal_name', '')
                    if name not in npc_names:
                        npc_names[name] = []
                    npc_names[name].append(item)
            
            # 同名NPCがあるかチェック
            has_duplicate_npcs = any(len(npcs) > 1 for npcs in npc_names.values())
            
            embed = discord.Embed(
                title=f"**検索結果: {query}**",
                description=f"**{len(results)}件**の結果が見つかりました",
                color=discord.Color.blue()
            )
            
            # 同名NPCがある場合の注意メッセージ
            if has_duplicate_npcs:
                duplicate_names = [name for name, npcs in npc_names.items() if len(npcs) > 1]
                embed.add_field(
                    name="⚠️ 同名のNPCが複数存在します",
                    value=f"以下のNPCは複数の場所に存在します: **{', '.join(duplicate_names)}**\n場所と業種を確認してください。",
                    inline=False
                )
            
            # 箇条書き形式で一覧表示
            item_list = []
            for i, item in enumerate(page_results, start=start_idx + 1):
                formal_name = item.get('formal_name', 'Unknown')
                item_type = item.get('item_type', 'unknown')
                required_level = item.get('required_level', '')
                
                # アイテム情報を表示（一般名称は表示しない）
                item_info = f"• {i}. {formal_name} ({item_type})"
                
                # NPCの場合は場所と説明を表示（改善版）
                if item_type == 'npcs':
                    location = item.get('location', '')
                    business_type = item.get('business_type', '')
                    description = item.get('description', '')
                    
                    # 同名NPCがある場合は詳細表示
                    if formal_name in npc_names and len(npc_names[formal_name]) > 1:
                        item_info = f"• {i}. **{formal_name}**"
                        if location:
                            item_info += f"\n　　📍 場所: **{location}**"
                        # 業種は重複NPCの場合は表示しない
                        if description and description.strip():
                            # 説明は30文字で省略
                            desc_short = description[:30] + '...' if len(description) > 30 else description
                            item_info += f"\n　　💬 {desc_short}"
                    else:
                        # 通常表示
                        if location:
                            item_info += f" - {location}"
                        if business_type:
                            item_info += f" ({business_type})"
                        if description:
                            # 説明は20文字で省略
                            desc_short = description[:20] + '...' if len(description) > 20 else description
                            item_info += f" - {desc_short}"
                
                # mobの場合は必要レベルも表示
                elif item_type == 'mobs' and required_level:
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
        elif item_type == 'equipments':
            # 装備: 必要素材ボタンは表示しない（プルダウンで対応）
            # モブ討伐装備の場合は入手モブ詳細ボタンを表示
            if acquisition_category == 'モブ討伐':
                self.add_item(AcquisitionDetailsButton(item_type, acquisition_category))
        elif item_type == 'mobs':
            # モブ: ドロップ詳細ボタンは表示しない（プルダウンで対応）
            pass
        elif item_type == 'npcs':
            # NPC: 取引詳細ボタンは表示しない（プルダウンで対応）
            pass
    
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
                title=f"{view.item_data['formal_name']} の入手元一覧",
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
                    # 最初の10件を表示
                    display_count = min(len(mob_sources), 10)
                    for i, item in enumerate(mob_sources[:display_count]):
                        # mobの場合はformal_nameがある
                        display_name = item.get('formal_name', '不明')
                        if i == 0:
                            field_items.append(f"\u200B　• `{display_name}`")
                        else:
                            field_items.append(f"　• `{display_name}`")
                        options.append(discord.SelectOption(
                            label=display_name[:25],
                            value=f"source_{option_index}",
                            description="ドロップ元"
                        ))
                        option_index += 1
                    
                    # 残りがある場合は表示
                    if field_items:
                        if len(mob_sources) > display_count:
                            field_items.append(f"...他{len(mob_sources) - display_count}体")
                        embed.add_field(
                            name="モブ討伐:",
                            value="\n".join(field_items),
                            inline=False
                        )
                
                # 2. 採集場所の表示
                gathering_sources = [item for item in related_items.get('acquisition_sources', []) if item.get('relation_type') == 'gathering_location']
                if gathering_sources:
                    logger.debug(f"gathering_sources 件数: {len(gathering_sources)}")
                    gathering_items = []
                    display_count = min(len(gathering_sources), 10)
                    for i, location in enumerate(gathering_sources[:display_count]):
                        location_name = location.get('location', '不明')
                        collection_method = location.get('collection_method', '')
                        logger.debug(f"gathering_source[{i}] - location: {location_name}, collection_method: {collection_method}, 元データ: {location}")
                        display_text = f"`{location_name}`"
                        if collection_method:
                            display_text += f" ({collection_method})"
                        if i == 0:
                            gathering_items.append(f"\u200B　• {display_text}")
                        else:
                            gathering_items.append(f"　• {display_text}")
                        options.append(discord.SelectOption(
                            label=f"{location_name} - {collection_method}"[:25],
                            value=f"gathering_{option_index}",
                            description="採集場所"
                        ))
                        option_index += 1
                    if gathering_items:
                        if len(gathering_sources) > display_count:
                            gathering_items.append(f"...他{len(gathering_sources) - display_count}箇所")
                        embed.add_field(
                            name="ギャザリング:",
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
                    # 入手元と納品先を分類
                    obtainable_npcs = []
                    required_npcs = []
                    
                    for npc in npc_sources:
                        if npc.get('source_type') == 'obtainable':
                            obtainable_npcs.append(npc)
                        elif npc.get('source_type') == 'required':
                            required_npcs.append(npc)
                    
                    # 入手元の表示
                    if obtainable_npcs:
                        npc_items = []
                        for i, npc in enumerate(obtainable_npcs[:5]):
                            npc_name = npc.get('name', '不明')
                            npc_location = npc.get('location', '')
                            business_type = npc.get('business_type', 'その他')
                            display_text = f"`{npc_name}`"
                            if npc_location:
                                display_text += f" ({npc_location})"
                            display_text += f" - {business_type}"
                            
                            # NPCが複数の交換パターンを持つ場合の処理
                            obtainable_items = npc.get('obtainable_items', '')
                            if business_type in ['交換', '購入', 'クエスト'] and obtainable_items:
                                from npc_parser import NPCExchangeParser
                                exchanges = NPCExchangeParser.parse_exchange_items(
                                    obtainable_items,
                                    npc.get('required_materials', ''),
                                    npc.get('exp', ''),
                                    npc.get('gold', '')
                                )
                                
                                # 該当アイテムを含む交換パターンを特定
                                item_exchanges = []
                                for exchange in exchanges:
                                    if exchange.get('obtainable_item') and view.item_data['formal_name'] in exchange['obtainable_item']:
                                        item_exchanges.append(exchange)
                                
                            
                            if i == 0:
                                npc_items.append(f"\u200B　• {display_text}")
                            else:
                                npc_items.append(f"　• {display_text}")
                            options.append(discord.SelectOption(
                                label=f"{npc_name} ({business_type})"[:25],
                                value=f"npc_{option_index}",
                                description=npc_location[:50] if npc_location else "NPC"
                            ))
                            option_index += 1
                        if npc_items:
                            embed.add_field(
                                name="NPC:",
                                value="\n".join(npc_items),
                                inline=False
                            )
                    
                    # 納品先・使用先の表示
                    if required_npcs:
                        required_items = []
                        for i, npc in enumerate(required_npcs[:5]):
                            npc_name = npc.get('name', '不明')
                            npc_location = npc.get('location', '')
                            business_type = npc.get('business_type', 'その他')
                            display_text = f"`{npc_name}`"
                            if npc_location:
                                display_text += f" ({npc_location})"
                            
                            if business_type == 'クエスト':
                                display_text += f" - クエスト納品"
                            elif business_type == '交換':
                                display_text += f" - 交換素材として使用"
                            else:
                                display_text += f" - {business_type}"
                            
                            if i == 0:
                                required_items.append(f"\u200B　• {display_text}")
                            else:
                                required_items.append(f"　• {display_text}")
                            options.append(discord.SelectOption(
                                label=f"{npc_name} (納品/使用)"[:25],
                                value=f"npc_{option_index}",
                                description=npc_location[:50] if npc_location else "NPC"
                            ))
                            option_index += 1
                        if required_items:
                            embed.add_field(
                                name="納品先・使用先:",
                                value="\n".join(required_items),
                                inline=False
                            )
                
                # 4. その他の入手方法
                if related_items.get('acquisition_info'):
                    info = related_items['acquisition_info']
                    # gathering_locationsがある場合、または特定のカテゴリの場合は表示しない
                    if not related_items.get('gathering_locations') and info['category'] not in ['採取', '採掘', '釣り', 'NPC', 'ギルドクエスト']:
                        method_text = info.get('method', info['category'])
                        location_text = info.get('location', '')
                        
                        # method_textが有効な場合のみ表示
                        if method_text and method_text != 'None':
                            display_text = f"`{method_text}`"
                            if location_text and location_text != 'None':
                                display_text += f"\n• 場所: `{location_text}`"
                            embed.add_field(
                                name="その他の入手方法:",
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
                            drop_list.append(f"• `{display_name}`")
                            options.append(discord.SelectOption(
                                label=display_name[:25],
                                value=f"source_{option_index}",
                                description="ドロップ元"
                            ))
                            option_index += 1
                        if drop_list:
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
                            gathering_list.append(f"• {display_text}")
                            options.append(discord.SelectOption(
                                label=f"{location_name} - {method}"[:25],
                                value=f"gathering_{option_index}",
                                description="採集場所"
                            ))
                            option_index += 1
                        if gathering_list:
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
                            npc_list.append(f"• {display_text}")
                            options.append(discord.SelectOption(
                                label=f"{npc_name} ({business_type})"[:25],
                                value=f"npc_{option_index}",
                                description=npc_location[:50] if npc_location else "NPC"
                            ))
                            option_index += 1
                        if npc_list:
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
                        # optionsと同じ順序で追加（mob → gathering → npc）
                        
                        # mob sources
                        mob_sources = [s for s in related_items.get('acquisition_sources', []) if s.get('relation_type') == 'drop_from_mob']
                        item_list.extend(mob_sources[:10])
                        
                        # gathering sources
                        if related_items.get('gathering_locations'):
                            item_list.extend(related_items['gathering_locations'][:10])
                        else:
                            # gathering_sourcesから追加
                            gathering_sources = [s for s in related_items.get('acquisition_sources', []) if s.get('relation_type') == 'gathering_location']
                            logger.debug(f"item_listに追加するgathering_sources: {len(gathering_sources)}件")
                            for idx, source in enumerate(gathering_sources[:10]):
                                logger.debug(f"  [{idx}] location={source.get('location')}, collection_method={source.get('collection_method')}, 全データ={source}")
                            item_list.extend(gathering_sources[:10])
                        
                        # npc sources（入手元のみ）
                        npc_sources = [s for s in related_items.get('acquisition_sources', []) if s.get('relation_type') == 'npc_source' and s.get('source_type') == 'obtainable']
                        item_list.extend(npc_sources[:5])
                        
                        # npc sources（納品先）
                        npc_required = [s for s in related_items.get('acquisition_sources', []) if s.get('relation_type') == 'npc_source' and s.get('source_type') == 'required']
                        item_list.extend(npc_required[:5])
                    
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
                    
                    # Discord.pyの制限: SelectMenuは最大25個の選択肢
                    if len(options) > 25:
                        # 最初の24個 + 「もっと見る」オプション
                        truncated_options = options[:24]
                        truncated_options.append(discord.SelectOption(
                            label="...もっと見る",
                            value="show_more",
                            description=f"他{len(options) - 24}件のアイテム"
                        ))
                        truncated_item_list = item_list[:24] if len(item_list) > 24 else item_list
                        
                        detailed_view = NewRelatedItemsView(related_items, view.embed_manager, truncated_options, truncated_item_list, view.item_data)
                        embed.set_footer(text=f"※下記から入手元詳細を確認（全{len(options)}件中24件を表示）")
                    else:
                        detailed_view = NewRelatedItemsView(related_items, view.embed_manager, options, item_list, view.item_data)
                        embed.add_field(
                            name="\u200b",  # 空白フィールド名
                            value="※下記から入手元詳細を確認",
                            inline=False
                        )
                    
                    await interaction.response.send_message(embed=embed, view=detailed_view, ephemeral=True)
                else:
                    await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"入手元詳細エラー: {e}")
            await interaction.response.send_message("❌ 入手元詳細取得中にエラーが発生しました", ephemeral=True)
        finally:
            view.processing = False
            view._enable_all_buttons()


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
    def __init__(self, related_items: Dict[str, List[Dict[str, Any]]], embed_manager, options: List[discord.SelectOption], item_list: List[Dict[str, Any]] = None, item_data: Dict[str, Any] = None):
        super().__init__(timeout=300)
        self.related_items = related_items
        self.embed_manager = embed_manager
        self.all_items = []
        self.item_mapping = {}  # valueからアイテムへのマッピング
        self.item_data = item_data  # 元のアイテムデータを保持
        
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
            select.parent_view = self  # 親ビューへの参照を設定
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
        self.parent_view = None  # 親ビューへの参照を保持
    
    async def callback(self, interaction: discord.Interaction):
        try:
            selected_value = self.values[0]
            
            # マッピングからアイテムを取得
            if selected_value in self.item_mapping:
                selected_item = self.item_mapping[selected_value]
                
                # gathering/npc/exchangeの場合は簡易表示
                if selected_value.startswith('gathering_') or selected_value.startswith('npc_') or selected_value.startswith('exchange_'):
                    # gathering/npcは詳細表示ではなく情報表示
                    embed = discord.Embed(
                        title=f"詳細情報",
                        color=discord.Color.blue()
                    )
                    
                    if selected_value.startswith('gathering_'):
                        # 採集場所の詳細 - 入手元詳細から選択された場合の処理
                        logger.debug(f"gathering選択 - selected_value: {selected_value}, selected_item: {selected_item}")
                        location = selected_item.get('location', '不明')
                        method = selected_item.get('collection_method', '')
                        
                        # 元のアイテム名を取得（これが検索された素材名）
                        original_item_name = ''
                        if hasattr(self, 'parent_view') and self.parent_view and hasattr(self.parent_view, 'item_data'):
                            original_item_name = self.parent_view.item_data.get('formal_name', '')
                        
                        logger.info(f"採集情報表示 - 元アイテム名: {original_item_name}, 場所: {location}, 方法: {method}")
                        
                        # 同じ場所・採集方法のデータから、この素材が含まれているものを検索
                        from database import DatabaseManager
                        db = DatabaseManager()
                        
                        try:
                            async with aiosqlite.connect(db.db_path) as conn:
                                conn.row_factory = aiosqlite.Row
                                
                                # 特定の素材が含まれる採集情報を取得
                                if original_item_name:
                                    # 元の素材名を含む採集情報を検索
                                    cursor = await conn.execute(
                                        "SELECT * FROM gatherings WHERE location = ? AND collection_method = ? AND obtained_materials LIKE ?",
                                        (location, method, f'%{original_item_name}%')
                                    )
                                else:
                                    # フォールバック：場所と方法のみで検索
                                    cursor = await conn.execute(
                                        "SELECT * FROM gatherings WHERE location = ? AND collection_method = ?",
                                        (location, method)
                                    )
                                    
                                rows = await cursor.fetchall()
                                gathering_data = [dict(row) for row in rows]
                                
                                if gathering_data:
                                    # タイトルを設定（素材名を含む）
                                    if original_item_name:
                                        embed.title = f"**{original_item_name}** の採集情報"
                                        embed.add_field(name="採集場所:", value=f"`{location}`", inline=True)
                                        embed.add_field(name="採集方法:", value=f"`{method}`", inline=True)
                                        embed.add_field(name="\u200b", value="\u200b", inline=True)  # 空白フィールドで改行
                                    else:
                                        embed.title = f"**{location}** の **{method}** 情報"
                                    
                                    # この場所・方法で入手可能な素材のリスト（素材名をハイライト）
                                    all_materials = []
                                    for data in gathering_data:
                                        materials_str = data.get('obtained_materials', '')
                                        if materials_str:
                                            materials = [m.strip() for m in materials_str.split(',')]
                                            all_materials.extend(materials)
                                    
                                    # 重複を除去してソート
                                    unique_materials = sorted(list(set(all_materials)))
                                    
                                    # 後でViewに渡すために保存
                                    selected_item['unique_materials'] = unique_materials
                                    
                                    if unique_materials:
                                        materials_list = []
                                        for i, mat in enumerate(unique_materials[:20]):
                                            if original_item_name and mat == original_item_name:
                                                # 検索された素材を強調表示
                                                if i == 0:
                                                    materials_list.append(f"\u200B　• **`{mat}`**")
                                                else:
                                                    materials_list.append(f"　• **`{mat}`**")
                                            else:
                                                if i == 0:
                                                    materials_list.append(f"\u200B　• `{mat}`")
                                                else:
                                                    materials_list.append(f"　• `{mat}`")
                                        embed.add_field(
                                            name="入手可能素材:",
                                            value="\n".join(materials_list),
                                            inline=False
                                        )
                                    
                                    # 必要ツール
                                    tools = gathering_data[0].get('required_tools', '')
                                    if tools:
                                        embed.add_field(name="必要ツール:", value=f"`{tools}`", inline=False)
                                    
                                    # 備考
                                    desc = gathering_data[0].get('description', '')
                                    if desc:
                                        embed.add_field(name="備考:", value=f"`{desc}`", inline=False)
                                    
                                    # 素材詳細ボタンの案内
                                    embed.add_field(
                                        name="\u200b",
                                        value="*※ 下のボタンで素材詳細を検索*",
                                        inline=False
                                    )
                                else:
                                    # データが見つからない場合
                                    embed.title = "採集情報が見つかりません"
                                    embed.add_field(name="採集場所:", value=f"`{location}`", inline=False)
                                    embed.add_field(name="採集方法:", value=f"`{method}`", inline=False)
                                    embed.add_field(
                                        name="注意:",
                                        value="この場所・方法の詳細情報が見つかりませんでした。",
                                        inline=False
                                    )
                                    
                        except Exception as e:
                            logger.error(f"採集場所詳細取得エラー: {e}")
                            # エラー時のフォールバック
                            embed.title = "エラーが発生しました"
                            embed.add_field(name="採集場所:", value=f"`{location}`", inline=False)
                            embed.add_field(name="採集方法:", value=f"`{method}`", inline=False)
                            embed.add_field(name="エラー:", value="詳細情報の取得中にエラーが発生しました。", inline=False)
                    
                    elif selected_value.startswith('npc_'):
                        # NPCの詳細
                        name = selected_item.get('name', '不明')
                        location = selected_item.get('location', '')
                        business_type = selected_item.get('business_type', '')
                        items = selected_item.get('obtainable_items', '')
                        materials = selected_item.get('required_materials', '')
                        exp_str = selected_item.get('exp', '')
                        gold_str = selected_item.get('gold', '')
                        desc = selected_item.get('description', '')
                        
                        embed.title = f"{name} の詳細情報"
                        embed.add_field(name="NPC名:", value=f"`{name}`", inline=True)
                        embed.add_field(name="場所:", value=f"`{location}`", inline=True)
                        embed.add_field(name="業務:", value=f"`{business_type}`", inline=True)
                        
                        # 複数交換パターンの解析
                        if items and business_type in ['購入', '交換', 'クエスト']:
                            from npc_parser import NPCExchangeParser
                            exchanges = NPCExchangeParser.parse_exchange_items(
                                items, materials, exp_str, gold_str
                            )
                            
                            if business_type == 'クエスト':
                                # クエストの受注内容一覧
                                quest_list = []
                                for i, exchange in enumerate(exchanges[:10]):
                                    req_mat = exchange.get('required_materials', '')
                                    if req_mat:
                                        if len(quest_list) == 0:
                                            quest_list.append(f"\u200B　• `{req_mat}`")
                                        else:
                                            quest_list.append(f"　• `{req_mat}`")
                                if quest_list:
                                    embed.add_field(
                                        name="受注内容:",
                                        value="\n".join(quest_list),
                                        inline=False
                                    )
                            else:
                                # 購入・交換の販売商品一覧
                                item_list = []
                                unique_items = set()  # 重複除去用
                                for exchange in exchanges:
                                    obtainable = exchange.get('obtainable_item', '')
                                    if obtainable and obtainable not in unique_items:
                                        unique_items.add(obtainable)
                                        # アイテム名から個数を分離
                                        if ':' in obtainable:
                                            item_name, quantity = obtainable.split(':', 1)
                                            if len(item_list) == 0:
                                                item_list.append(f"\u200B　• `{item_name.strip()}×{quantity.strip()}`")
                                            else:
                                                item_list.append(f"　• `{item_name.strip()}×{quantity.strip()}`")
                                        else:
                                            if len(item_list) == 0:
                                                item_list.append(f"\u200B　• `{obtainable}`")
                                            else:
                                                item_list.append(f"　• `{obtainable}`")
                                
                                if item_list:
                                    embed.add_field(
                                        name="販売商品:",
                                        value="\n".join(item_list[:10]),
                                        inline=False
                                    )
                                    if len(item_list) > 10:
                                        embed.add_field(
                                            name="\u200b",
                                            value=f"...他{len(item_list) - 10}種類",
                                            inline=False
                                        )
                        elif items:
                            # 旧形式のフォールバック
                            item_list = [f"• `{i.strip()}`" for i in items.split(',')]
                            embed.add_field(name="取扱アイテム", value="\n".join(item_list[:10]), inline=False)
                        
                        if desc:
                            embed.add_field(name="備考", value=f"`{desc}`", inline=False)
                        
                        # 取引詳細の確認方法を追加
                        embed.add_field(
                            name="\u200b",
                            value="※下記から取引詳細を確認",
                            inline=False
                        )
                        
                        # NPCのプルダウンを追加するためのViewを作成
                        view = discord.ui.View(timeout=300)
                        await self.embed_manager._add_npc_dropdown_to_view(view, selected_item)
                    
                    elif selected_value.startswith('exchange_'):
                        # NPC交換の個別詳細
                        exchange_data = selected_item.get('exchange_data', {})
                        business_type = selected_item.get('business_type', '')
                        
                        obtainable = exchange_data.get('obtainable_item', '')
                        required = exchange_data.get('required_materials', '')
                        exp = exchange_data.get('exp')
                        gold = exchange_data.get('gold')
                        
                        if business_type == 'クエスト':
                            embed.title = f"クエスト詳細"
                            
                            # 受注内容（カンマ区切りを箇条書きに）
                            if required:
                                if ',' in required:
                                    # カンマ区切りの場合は箇条書きに
                                    required_items = [item.strip() for item in required.split(',') if item.strip()]
                                    formatted_items = []
                                    for i, item in enumerate(required_items):
                                        if ':' in item:
                                            item_name, quantity = item.split(':', 1)
                                            if i == 0:
                                                formatted_items.append(f"\u200B　• `{item_name.strip()}×{quantity.strip()}`")
                                            else:
                                                formatted_items.append(f"　• `{item_name.strip()}×{quantity.strip()}`")
                                        else:
                                            if i == 0:
                                                formatted_items.append(f"\u200B　• `{item}`")
                                            else:
                                                formatted_items.append(f"　• `{item}`")
                                    embed.add_field(name="受注内容:", value="\n".join(formatted_items), inline=False)
                                else:
                                    # 単一アイテムの場合
                                    if ':' in required:
                                        item_name, quantity = required.split(':', 1)
                                        formatted_required = f"{item_name.strip()}×{quantity.strip()}"
                                    else:
                                        formatted_required = required
                                    embed.add_field(name="受注内容:", value=f"\u200B　• `{formatted_required}`", inline=False)
                            
                            # 報酬情報（入手アイテムも含める）
                            reward_sections = []
                            
                            # アイテム報酬
                            if obtainable:
                                item_rewards = []
                                
                                # 複数アイテムのパース（エフォート・エビデンスLv1:1魔法石Lv1:20のような形式に対応）
                                remaining = obtainable
                                while remaining:
                                    # コロンの位置を探す
                                    colon_pos = remaining.find(':')
                                    if colon_pos == -1:
                                        # コロンがない場合、残りの文字列を単一アイテムとして処理
                                        if remaining.strip():
                                            item_rewards.append(f"　　• `{remaining.strip()}`")
                                        break
                                    
                                    # アイテム名を取得
                                    item_name = remaining[:colon_pos].strip()
                                    
                                    # 数量を取得（数字が続く限り）
                                    qty_start = colon_pos + 1
                                    qty_end = qty_start
                                    while qty_end < len(remaining) and remaining[qty_end].isdigit():
                                        qty_end += 1
                                    
                                    if qty_end > qty_start:  # 数量が見つかった場合
                                        quantity = remaining[qty_start:qty_end]
                                        item_rewards.append(f"　　• `{item_name}×{quantity}`")
                                        remaining = remaining[qty_end:].strip()
                                    else:
                                        # 数量がない場合は残り全体を単一アイテムとして処理
                                        item_rewards.append(f"　　• `{remaining.strip()}`")
                                        break
                                
                                if item_rewards:
                                    reward_sections.append(f"\u200B　• アイテム:\n" + "\n".join(item_rewards))
                            
                            # EXP報酬
                            if exp:
                                reward_sections.append(f"　• EXP:\n　　`{exp}`")
                            
                            # Gold報酬
                            if gold:
                                reward_sections.append(f"　• Gold:\n　　`{gold}`")
                            
                            if reward_sections:
                                embed.add_field(name="報酬:", value="\n".join(reward_sections), inline=False)
                        else:
                            embed.title = f"{business_type}詳細"
                            if obtainable:
                                # アイテム名:数量の形式をアイテム名×数量に変換
                                if ':' in obtainable:
                                    item_name, quantity = obtainable.split(':', 1)
                                    formatted_obtainable = f"{item_name.strip()}×{quantity.strip()}"
                                else:
                                    formatted_obtainable = obtainable
                                embed.add_field(name="入手アイテム:", value=f"\u200B　• `{formatted_obtainable}`", inline=False)
                            
                            if required:
                                # 複数素材の場合は箇条書きに
                                if ' + ' in required:
                                    required_items = required.split(' + ')
                                    formatted_items = []
                                    for i, item in enumerate(required_items):
                                        if ':' in item:
                                            item_name, quantity = item.split(':', 1)
                                            if i == 0:
                                                formatted_items.append(f"\u200B　• `{item_name.strip()}×{quantity.strip()}`")
                                            else:
                                                formatted_items.append(f"　• `{item_name.strip()}×{quantity.strip()}`")
                                        else:
                                            if i == 0:
                                                formatted_items.append(f"\u200B　• `{item}`")
                                            else:
                                                formatted_items.append(f"　• `{item}`")
                                    embed.add_field(name="必要素材/価格", value="\n".join(formatted_items), inline=False)
                                else:
                                    # 単一素材の場合
                                    if ':' in required:
                                        item_name, quantity = required.split(':', 1)
                                        formatted_required = f"{item_name.strip()}×{quantity.strip()}"
                                    else:
                                        formatted_required = required
                                    embed.add_field(name="必要素材/価格:", value=f"\u200B　• `{formatted_required}`", inline=False)
                    
                    # gathering_の場合は素材詳細ボタン、npc_の場合は取引詳細ボタンを追加
                    if selected_value.startswith('gathering_'):
                        # gatheringアイテム用のviewを作成
                        # unique_materialsをselected_itemから取得
                        unique_materials = selected_item.get('unique_materials', [])
                        view = GatheringDetailView(selected_item, str(interaction.user.id), self.embed_manager, unique_materials)
                    elif selected_value.startswith('npc_'):
                        # npc_アイテム用のviewは既に作成済み（_add_npc_dropdown_to_viewで追加）
                        # viewは上で作成したものを使用
                    else:
                        # exchange_の場合はviewなし
                        view = None
                    
                    if view:
                        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
                    else:
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


class LocationAcquisitionView(discord.ui.View):
    def __init__(self, options, acquisition_method, location, embed_manager, search_engine):
        super().__init__(timeout=300)
        self.acquisition_method = acquisition_method
        self.location = location
        self.embed_manager = embed_manager
        self.search_engine = search_engine
        
        # セレクトメニューを追加
        select = LocationAcquisitionSelect(options, acquisition_method, location, embed_manager, search_engine)
        self.add_item(select)


class LocationAcquisitionSelect(discord.ui.Select):
    def __init__(self, options, acquisition_method, location, embed_manager, search_engine):
        super().__init__(
            placeholder="選択してください...",
            min_values=1,
            max_values=1,
            options=options
        )
        self.acquisition_method = acquisition_method
        self.location = location
        self.embed_manager = embed_manager
        self.search_engine = search_engine
    
    async def callback(self, interaction: discord.Interaction):
        try:
            # 選択された値を分解
            selected = self.values[0]
            method, location = selected.split('_', 1)
            
            # 検索条件を決定
            if self.acquisition_method:
                # 入手手段から場所を選択した場合
                await self.search_and_display(interaction, method, location)
            else:
                # 場所から入手手段を選択した場合
                await self.search_and_display(interaction, method, location)
                
        except Exception as e:
            logger.error(f"場所・入手手段選択エラー: {e}")
            await interaction.response.send_message("❌ 検索中にエラーが発生しました", ephemeral=True)
    
    async def search_and_display(self, interaction, method, location):
        """選択された条件で検索して結果を表示"""
        try:
            # データベースから直接検索
            results = await self.search_by_method_and_location(method, location)
            
            if not results:
                embed = discord.Embed(
                    title="検索結果",
                    description=f"**{location}** の **{method}** に該当するデータが見つかりませんでした",
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # 結果のタイプを判定
            if method == 'クエスト' and len(results) == 1 and results[0].get('item_type') == 'npcs':
                # クエストNPCの詳細表示
                embed, view = await self.embed_manager.create_item_detail_embed(
                    results[0], str(interaction.user.id)
                )
                await interaction.response.send_message(embed=embed, view=view)
            elif len(results) == 1:
                # gathering_locationタイプの場合は特別な表示
                if results[0].get('item_type') == 'gathering_location':
                    # 採集情報の表示（入手元詳細から遷移した際と統一）
                    embed = discord.Embed(
                        title=f"**{location}** の **{method}** 情報",
                        color=discord.Color.orange()
                    )
                    
                    embed.add_field(name="採集場所:", value=f"`{location}`", inline=True)
                    embed.add_field(name="採集方法:", value=f"`{method}`", inline=True)
                    embed.add_field(name="\u200b", value="\u200b", inline=True)  # 空白フィールドで改行
                    
                    # 入手可能素材のリスト
                    unique_materials = results[0].get('unique_materials', [])
                    if unique_materials:
                        materials_list = []
                        for i, mat in enumerate(unique_materials[:20]):
                            if i == 0:
                                materials_list.append(f"\u200B　• `{mat}`")
                            else:
                                materials_list.append(f"　• `{mat}`")
                        
                        embed.add_field(
                            name="入手可能素材:",
                            value="\n".join(materials_list),
                            inline=False
                        )
                    
                    # 元のデータから必要ツールと備考を取得
                    original_data = results[0].get('original_data', [])
                    if original_data and len(original_data) > 0:
                        # 必要ツール
                        tools = original_data[0].get('required_tools', '')
                        if tools:
                            embed.add_field(name="必要ツール:", value=f"`{tools}`", inline=False)
                        
                        # 備考
                        desc = original_data[0].get('description', '')
                        if desc:
                            embed.add_field(name="備考:", value=f"`{desc}`", inline=False)
                    
                    # 素材詳細ボタンの案内
                    embed.add_field(
                        name="\u200b",
                        value="*※ 下のボタンで素材詳細を検索*",
                        inline=False
                    )
                    
                    # Viewを作成（プルダウン付き）
                    view = GatheringDetailView(
                        results[0], 
                        str(interaction.user.id), 
                        self.embed_manager, 
                        unique_materials
                    )
                    
                    await interaction.response.send_message(embed=embed, view=view)
                else:
                    # 通常の詳細表示
                    embed, view = await self.embed_manager.create_item_detail_embed(
                        results[0], str(interaction.user.id)
                    )
                    await interaction.response.send_message(embed=embed, view=view)
            else:
                # 複数結果のリスト表示
                query = f"{location} {method}"
                embed, view = await self.embed_manager.create_search_results_embed(
                    results, query, page=0
                )
                await interaction.response.send_message(embed=embed, view=view)
                
        except Exception as e:
            logger.error(f"検索結果表示エラー: {e}")
            await interaction.response.send_message("❌ 結果表示中にエラーが発生しました", ephemeral=True)
    
    async def search_by_method_and_location(self, method, location):
        """入手手段と場所で検索"""
        try:
            from database import DatabaseManager
            db = DatabaseManager()
            
            async with aiosqlite.connect(db.db_path) as conn:
                conn.row_factory = aiosqlite.Row
                results = []
                
                if method == 'クエスト':
                    # NPCテーブルからクエストマスターを検索
                    cursor = await conn.execute(
                        "SELECT *, 'npcs' as item_type, name as formal_name FROM npcs WHERE location = ? AND business_type = ?",
                        (location, method)
                    )
                    rows = await cursor.fetchall()
                    results.extend([dict(row) for row in rows])
                    
                elif method == '購入' or method == '交換':
                    # NPCテーブルから購入・交換NPCを検索
                    cursor = await conn.execute(
                        "SELECT *, 'npcs' as item_type, name as formal_name FROM npcs WHERE location = ? AND business_type = ?",
                        (location, method)
                    )
                    rows = await cursor.fetchall()
                    results.extend([dict(row) for row in rows])
                    
                elif method == 'モブ':
                    # mobsテーブルから該当エリアのモブを検索
                    cursor = await conn.execute(
                        "SELECT *, 'mobs' as item_type FROM mobs WHERE area LIKE ?",
                        (f'%{location}%',)
                    )
                    rows = await cursor.fetchall()
                    results.extend([dict(row) for row in rows])
                    
                elif method in ['採取', '採掘', '釣り']:
                    # gatheringsテーブルから採集情報を取得
                    try:
                        cursor = await conn.execute(
                            "SELECT * FROM gatherings WHERE location = ? AND collection_method = ?",
                            (location, method)
                        )
                        rows = await cursor.fetchall()
                        gathering_data = [dict(row) for row in rows]
                        
                        if gathering_data:
                            # gatheringsデータを採集情報用の特別な形式で返す
                            # 採集情報は単一のembedで表示するため、1つのデータとして返す
                            all_materials = []
                            for data in gathering_data:
                                materials_str = data.get('obtained_materials', '')
                                if materials_str:
                                    materials = [m.strip() for m in materials_str.split(',')]
                                    all_materials.extend(materials)
                            
                            # 重複を除去してソート
                            unique_materials = sorted(list(set(all_materials)))
                            
                            # gatheringsのデータを特別な形式で返す
                            gathering_result = {
                                'item_type': 'gathering_location',
                                'location': location,
                                'collection_method': method,
                                'unique_materials': unique_materials,
                                'formal_name': f'{location} - {method}',
                                'original_data': gathering_data  # 元のデータも保持
                            }
                            return [gathering_result]
                    except Exception as e:
                        logger.debug(f"gatherings検索エラー: {e}")
                    
                    # フォールバック: materialsテーブルから検索
                    cursor = await conn.execute(
                        "SELECT *, 'materials' as item_type FROM materials WHERE acquisition_category = ? AND acquisition_method LIKE ?",
                        (method, f'%{location}%')
                    )
                    rows = await cursor.fetchall()
                    results.extend([dict(row) for row in rows])
                
                return results
                
        except Exception as e:
            logger.error(f"場所・入手手段検索エラー: {e}")
            return []


class GatheringDetailView(discord.ui.View):
    """採集詳細画面用のView（ドロップアイテムのプルダウン付き）"""
    def __init__(self, gathering_data: Dict[str, Any], user_id: str, embed_manager, materials: List[str]):
        super().__init__(timeout=600)
        self.gathering_data = gathering_data
        self.user_id = user_id
        self.embed_manager = embed_manager
        self.materials = materials
        
        # ドロップアイテムのプルダウンを追加
        if materials:
            select_options = []
            for i, material in enumerate(materials[:25]):  # Discord制限で最大25個
                select_options.append(discord.SelectOption(
                    label=material[:100],  # ラベルの文字数制限
                    value=f"material_{i}",
                    description="ドロップアイテム"
                ))
            
            select = DropItemSelect(select_options, materials, embed_manager)
            self.add_item(select)


class DropItemSelect(discord.ui.Select):
    """ドロップアイテム選択用のプルダウン"""
    def __init__(self, options: List[discord.SelectOption], materials: List[str], embed_manager):
        super().__init__(
            placeholder="ドロップアイテムを選択...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="drop_item_select"
        )
        self.materials = materials
        self.embed_manager = embed_manager
    
    async def callback(self, interaction: discord.Interaction):
        try:
            # 選択された値から素材名を取得
            selected_value = self.values[0]
            material_index = int(selected_value.split('_')[1])
            material_name = self.materials[material_index]
            
            # 素材検索を実行
            from search_engine import SearchEngine
            from database import DatabaseManager
            
            db = DatabaseManager()
            search_engine = SearchEngine(db, self.embed_manager.config)
            
            # 素材を検索
            results = await search_engine.search(material_name)
            
            if results:
                if len(results) == 1:
                    # 単一結果の場合は詳細表示
                    embed, view = await self.embed_manager.create_item_detail_embed(
                        results[0], str(interaction.user.id)
                    )
                    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
                else:
                    # 複数結果の場合はリスト表示
                    embed, view = await self.embed_manager.create_search_results_embed(
                        results, material_name, page=0
                    )
                    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
            else:
                embed = discord.Embed(
                    title="検索結果",
                    description=f"「{material_name}」の詳細情報が見つかりませんでした",
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                
        except Exception as e:
            logger.error(f"ドロップアイテム選択エラー: {e}")
            await interaction.response.send_message("❌ アイテム詳細の取得中にエラーが発生しました", ephemeral=True)


class NPCExchangeSelect(discord.ui.Select):
    """取引詳細選択用のプルダウン"""
    def __init__(self, options: List[discord.SelectOption], exchange_data: List[Dict[str, Any]], 
                 npc_data: Dict[str, Any], embed_manager):
        super().__init__(
            placeholder="取引内容を選択...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="npc_exchange_select"
        )
        self.exchange_data = exchange_data
        self.npc_data = npc_data
        self.embed_manager = embed_manager
    
    async def callback(self, interaction: discord.Interaction):
        try:
            # 選択された値から交換データを取得
            selected_value = self.values[0]
            exchange_index = int(selected_value.split('_')[2])
            exchange = self.exchange_data[exchange_index]
            
            # 詳細表示用のEmbedを作成
            embed = discord.Embed(
                title=f"{self.npc_data['formal_name']} - 取引詳細",
                color=discord.Color.purple()
            )
            
            business_type = self.npc_data.get('business_type', '')
            obtainable = exchange.get('obtainable_item', '').strip()
            required = exchange.get('required_materials', '').strip()
            exp = exchange.get('exp')
            gold = exchange.get('gold')
            
            # 業種に応じた表示
            if business_type == 'クエスト':
                if required:
                    embed.add_field(
                        name="受注内容:",
                        value=f"\u200B\u3000\u2022 `{required}`",
                        inline=False
                    )
                if obtainable:
                    embed.add_field(
                        name="報酬:",
                        value=f"\u200B\u3000\u2022 `{obtainable}`",
                        inline=False
                    )
            else:
                if obtainable:
                    # アイテム名:数量の形式をアイテム名×数量に変換
                    if ':' in obtainable:
                        item_name, quantity = obtainable.split(':', 1)
                        formatted_obtainable = f"{item_name.strip()}×{quantity.strip()}"
                    else:
                        formatted_obtainable = obtainable
                    
                    embed.add_field(
                        name="入手アイテム:",
                        value=f"\u200B\u3000\u2022 `{formatted_obtainable}`",
                        inline=False
                    )
                
                if required and business_type == '交換':
                    embed.add_field(
                        name="必要素材:",
                        value=f"\u200B\u3000\u2022 `{required}`",
                        inline=False
                    )
            
            # EXP・Gold情報
            if exp or gold:
                cost_info = []
                if exp:
                    cost_info.append(f"EXP: **{exp}**")
                if gold:
                    cost_info.append(f"Gold: **{gold}G**")
                
                embed.add_field(
                    name="コスト:",
                    value="\u3000" + " / ".join(cost_info),
                    inline=False
                )
            
            # アイテム検索用のボタンを追加
            view = discord.ui.View(timeout=300)
            
            # 入手アイテムの検索ボタン
            if obtainable:
                item_name = obtainable.split(':')[0].strip() if ':' in obtainable else obtainable
                search_button = NPCItemSearchButton(item_name, "入手アイテムを検索", self.embed_manager)
                view.add_item(search_button)
            
            # 必要素材の検索ボタン（交換の場合のみ）
            if required and business_type == '交換':
                # 複数素材の場合は最初の素材を検索
                material_name = required.split(',')[0].strip()
                if ':' in material_name:
                    material_name = material_name.split(':')[0].strip()
                material_button = NPCItemSearchButton(material_name, "必要素材を検索", self.embed_manager)
                view.add_item(material_button)
            
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
            
        except Exception as e:
            logger.error(f"NPC交換選択エラー: {e}")
            await interaction.response.send_message("❌ 取引詳細の表示中にエラーが発生しました", ephemeral=True)


class NPCItemSearchButton(discord.ui.Button):
    """アイテム検索ボタン"""
    def __init__(self, item_name: str, label: str, embed_manager):
        super().__init__(label=label, style=discord.ButtonStyle.secondary)
        self.item_name = item_name
        self.embed_manager = embed_manager
    
    async def callback(self, interaction: discord.Interaction):
        try:
            # アイテムを検索
            from search_engine import SearchEngine
            from database import DatabaseManager
            
            db = DatabaseManager()
            search_engine = SearchEngine(db, self.embed_manager.config)
            
            results = await search_engine.search(self.item_name)
            
            if results:
                if len(results) == 1:
                    # 単一結果の場合は詳細表示
                    embed, view = await self.embed_manager.create_item_detail_embed(
                        results[0], str(interaction.user.id)
                    )
                    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
                else:
                    # 複数結果の場合はリスト表示
                    embed, view = await self.embed_manager.create_search_results_embed(
                        results, self.item_name, page=0
                    )
                    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
            else:
                embed = discord.Embed(
                    title="検索結果",
                    description=f"「{self.item_name}」の詳細情報が見つかりませんでした",
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                
        except Exception as e:
            logger.error(f"アイテム検索エラー: {e}")
            await interaction.response.send_message("❌ アイテム検索中にエラーが発生しました", ephemeral=True)


class MobDropSelect(discord.ui.Select):
    """ドロップアイテム選択用のプルダウン"""
    def __init__(self, options: List[discord.SelectOption], dropped_items: List[Dict[str, Any]], embed_manager):
        super().__init__(
            placeholder="ドロップアイテムを選択...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="mob_drop_select"
        )
        self.dropped_items = dropped_items
        self.embed_manager = embed_manager
    
    async def callback(self, interaction: discord.Interaction):
        try:
            # 選択された値からアイテムデータを取得
            selected_value = self.values[0]
            item_index = int(selected_value.split('_')[1])
            item_data = self.dropped_items[item_index]
            
            # アイテム詳細を表示
            embed, view = await self.embed_manager.create_item_detail_embed(
                item_data, str(interaction.user.id)
            )
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
            
        except Exception as e:
            logger.error(f"ドロップアイテム選択エラー: {e}")
            await interaction.response.send_message("❌ アイテム詳細の表示中にエラーが発生しました", ephemeral=True)


class EquipmentMaterialSelect(discord.ui.Select):
    """必要素材選択用のプルダウン"""
    def __init__(self, options: List[discord.SelectOption], materials: List[str], embed_manager):
        super().__init__(
            placeholder="必要素材を選択...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="equipment_material_select"
        )
        self.materials = materials
        self.embed_manager = embed_manager
    
    async def callback(self, interaction: discord.Interaction):
        try:
            # 選択された値から素材名を取得
            selected_value = self.values[0]
            material_index = int(selected_value.split('_')[1])
            material_name = self.materials[material_index]
            
            # 素材を検索
            from search_engine import SearchEngine
            from database import DatabaseManager
            
            db = DatabaseManager()
            search_engine = SearchEngine(db, self.embed_manager.config)
            
            results = await search_engine.search(material_name)
            
            if results:
                if len(results) == 1:
                    # 単一結果の場合は詳細表示
                    embed, view = await self.embed_manager.create_item_detail_embed(
                        results[0], str(interaction.user.id)
                    )
                    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
                else:
                    # 複数結果の場合はリスト表示
                    embed, view = await self.embed_manager.create_search_results_embed(
                        results, material_name, page=0
                    )
                    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
            else:
                embed = discord.Embed(
                    title="検索結果",
                    description=f"「{material_name}」の詳細情報が見つかりませんでした",
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                
        except Exception as e:
            logger.error(f"必要素材選択エラー: {e}")
            await interaction.response.send_message("❌ 素材詳細の表示中にエラーが発生しました", ephemeral=True)